# Infrastructure Upgrade Specifications
## Achieving 1M+ Events/Minute with High Availability

### Current Infrastructure Bottlenecks

| Component | Current | Bottleneck | Required |
|-----------|---------|------------|----------|
| **Database** | 8 vCPU, 32GB RAM | CPU at 85% | 16 vCPU, 64GB RAM |
| **Application Servers** | 4 instances × 2 vCPU | Memory pressure | 8 instances × 4 vCPU |
| **Redis Cache** | Single node, 8GB | Connection limits | Cluster mode, 32GB |
| **Kafka Cluster** | Not deployed | N/A | 3 brokers minimum |
| **Load Balancer** | Single ALB | 500K conn/min | Multi-region NLB |

## Target Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Global Load Balancer                      │
│                    (Route 53 + CloudFront)                   │
└─────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                              │
┌───────▼────────┐                          ┌─────────▼────────┐
│   US-EAST-1    │                          │   EU-WEST-1      │
│  Primary Region│                          │ Secondary Region │
└────────────────┘                          └──────────────────┘
        │                                              │
┌───────▼────────────────────────────────────────────▼────────┐
│                    Application Layer (EKS)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  8 × FastAPI Pods (4 vCPU, 8GB RAM each)            │  │
│  │  - Horizontal Pod Autoscaler (HPA)                   │  │
│  │  - Target CPU: 60%                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│                              │                               │
▼                              ▼                               ▼
┌─────────────┐      ┌─────────────────┐         ┌────────────┐
│   Kafka     │      │  Write-Behind   │         │   Redis    │
│   Cluster   │      │     Cache       │         │   Cluster  │
└─────────────┘      └─────────────────┘         └────────────┘
│ 3 Brokers   │      │ Redis Sentinel  │         │ 6 Nodes    │
│ m6i.xlarge  │      │ 3 Nodes         │         │ 32GB Total │
└─────────────┘      └─────────────────┘         └────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│                     Sharded Database Layer                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Shard 0   │  │  Shard 1   │  │  Shard 2   │  ...      │
│  │ Primary +  │  │ Primary +  │  │ Primary +  │           │
│  │ 2 Replicas │  │ 2 Replicas │  │ 2 Replicas │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│   RDS r6g.2xl     RDS r6g.2xl     RDS r6g.2xl             │
│   8vCPU, 64GB     8vCPU, 64GB     8vCPU, 64GB             │
└──────────────────────────────────────────────────────────────┘
```

## Detailed Component Specifications

### 1. Application Servers (Kubernetes/EKS)

**EKS Cluster Configuration:**
```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: valueverse-billing-prod
  region: us-east-1
  version: "1.28"

nodeGroups:
  - name: app-nodes
    instanceType: m6i.xlarge  # 4 vCPU, 16 GB RAM
    desiredCapacity: 8
    minSize: 4
    maxSize: 16
    volumeSize: 100
    volumeType: gp3
    ebsOptimized: true
    
  - name: kafka-nodes
    instanceType: m6i.xlarge
    desiredCapacity: 3
    minSize: 3
    maxSize: 5
    volumeSize: 500
    volumeType: gp3
    taints:
      - key: workload
        value: kafka
        effect: NoSchedule
```

**Pod Specifications:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: billing-api
spec:
  replicas: 8
  template:
    spec:
      containers:
      - name: billing-api
        image: valueverse/billing-api:latest
        resources:
          requests:
            cpu: "3"
            memory: "6Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
        env:
        - name: WORKERS
          value: "8"  # Uvicorn workers
        - name: MAX_CONNECTIONS
          value: "1000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Database Infrastructure (RDS + Aurora)

**Primary Database Cluster:**
```terraform
resource "aws_rds_cluster" "billing_primary" {
  cluster_identifier      = "billing-cluster-primary"
  engine                  = "aurora-postgresql"
  engine_version          = "15.4"
  master_username         = "billing_admin"
  master_password         = var.db_password
  database_name          = "billing_db"
  
  # High availability
  availability_zones      = ["us-east-1a", "us-east-1b", "us-east-1c"]
  backup_retention_period = 30
  preferred_backup_window = "03:00-04:00"
  
  # Performance
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.billing.name
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  # Storage
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn
}

resource "aws_rds_cluster_instance" "billing_instances" {
  count              = 3
  identifier         = "billing-instance-${count.index}"
  cluster_identifier = aws_rds_cluster.billing_primary.id
  instance_class     = "db.r6g.2xlarge"  # 8 vCPU, 64 GB RAM
  engine             = aws_rds_cluster.billing_primary.engine
  engine_version     = aws_rds_cluster.billing_primary.engine_version
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
}

resource "aws_rds_cluster_parameter_group" "billing" {
  family = "aurora-postgresql15"
  name   = "billing-cluster-params"
  
  parameter {
    name  = "max_connections"
    value = "2000"
  }
  
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/4}"
  }
  
  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory*3/4}"
  }
  
  parameter {
    name  = "work_mem"
    value = "16384"  # 16MB
  }
  
  parameter {
    name  = "maintenance_work_mem"
    value = "2097152"  # 2GB
  }
  
  parameter {
    name  = "autovacuum_max_workers"
    value = "8"
  }
  
  parameter {
    name  = "max_wal_size"
    value = "8192"  # 8GB
  }
}
```

### 3. Kafka Cluster Configuration

**Docker Compose for Development:**
```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-logs:/var/lib/zookeeper/log

  kafka1:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka1:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 2
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      KAFKA_LOG_RETENTION_HOURS: 168  # 7 days
      KAFKA_LOG_SEGMENT_BYTES: 1073741824  # 1GB
      KAFKA_COMPRESSION_TYPE: lz4
      KAFKA_NUM_PARTITIONS: 10
      KAFKA_NUM_REPLICA_FETCHERS: 4
      KAFKA_SOCKET_SEND_BUFFER_BYTES: 102400
      KAFKA_SOCKET_RECEIVE_BUFFER_BYTES: 102400
      KAFKA_SOCKET_REQUEST_MAX_BYTES: 104857600
      JMX_PORT: 9999
      KAFKA_JMX_OPTS: "-Xms2G -Xmx4G"
    volumes:
      - kafka1-data:/var/lib/kafka/data

  kafka2:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 2
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka2:29093,PLAINTEXT_HOST://localhost:9093
      # ... (same as kafka1)
    volumes:
      - kafka2-data:/var/lib/kafka/data

  kafka3:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9094:9094"
    environment:
      KAFKA_BROKER_ID: 3
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka3:29094,PLAINTEXT_HOST://localhost:9094
      # ... (same as kafka1)
    volumes:
      - kafka3-data:/var/lib/kafka/data

volumes:
  zookeeper-data:
  zookeeper-logs:
  kafka1-data:
  kafka2-data:
  kafka3-data:
```

### 4. Redis Cluster Configuration

**Redis Sentinel for High Availability:**
```yaml
# redis-sentinel.conf
port 26379
sentinel monitor mymaster redis-master 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
sentinel auth-pass mymaster yourpassword

# redis.conf for master
port 6379
maxmemory 8gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
tcp-keepalive 60
tcp-backlog 511
databases 16

# Performance tuning
hz 50
slowlog-log-slower-than 10000
slowlog-max-len 128
```

**ElastiCache Configuration (Production):**
```terraform
resource "aws_elasticache_replication_group" "billing_cache" {
  replication_group_id       = "billing-cache-cluster"
  replication_group_description = "Redis cluster for billing system"
  
  engine               = "redis"
  engine_version       = "7.0"
  node_type           = "cache.r6g.xlarge"  # 4 vCPU, 26 GB
  number_cache_clusters = 3
  port                = 6379
  
  # High availability
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  # Backup
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  
  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = var.redis_auth_token
  
  # Subnet
  subnet_group_name = aws_elasticache_subnet_group.billing.name
  security_group_ids = [aws_security_group.redis.id]
  
  # Parameters
  parameter_group_name = aws_elasticache_parameter_group.billing.name
}

resource "aws_elasticache_parameter_group" "billing" {
  name   = "billing-redis-params"
  family = "redis7"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
  
  parameter {
    name  = "timeout"
    value = "300"
  }
  
  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }
  
  parameter {
    name  = "maxclients"
    value = "65000"
  }
}
```

### 5. Load Balancer Configuration

**Application Load Balancer:**
```terraform
resource "aws_lb" "billing_alb" {
  name               = "billing-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public.*.id
  
  enable_deletion_protection = true
  enable_http2              = true
  enable_cross_zone_load_balancing = true
  
  tags = {
    Environment = "production"
    Service     = "billing"
  }
}

resource "aws_lb_target_group" "billing_api" {
  name     = "billing-api-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
  
  deregistration_delay = 30
  
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
}
```

## Performance Tuning Parameters

### Operating System (Ubuntu/Amazon Linux 2)

```bash
# /etc/sysctl.conf
# Network optimization
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# File descriptors
fs.file-max = 2097152
fs.nr_open = 2097152

# Memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Apply settings
sudo sysctl -p
```

### Python/FastAPI Optimization

```python
# gunicorn_config.py
import multiprocessing

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Timeouts
timeout = 30
keepalive = 5
graceful_timeout = 30

# Performance
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

## Cost Estimation (AWS)

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| **EKS Cluster** | | |
| - Control Plane | 1 cluster | $73 |
| - Worker Nodes | 8 × m6i.xlarge | $1,094 |
| - Kafka Nodes | 3 × m6i.xlarge | $410 |
| **RDS Aurora** | | |
| - Primary | 3 × r6g.2xlarge | $2,074 |
| - Storage | 1TB | $100 |
| - Backups | 1TB | $95 |
| **ElastiCache** | | |
| - Redis Cluster | 3 × r6g.xlarge | $1,166 |
| **Load Balancer** | | |
| - ALB | 1 instance | $25 |
| - Data Transfer | 10TB | $900 |
| **CloudWatch** | | |
| - Logs | 500GB | $250 |
| - Metrics | Custom | $100 |
| **Total** | | **$6,287/month** |

## Implementation Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Week 1** | 5 days | Provision Kafka cluster, test event ingestion |
| **Week 2** | 5 days | Deploy write-behind cache, Redis Sentinel |
| **Week 3** | 5 days | Implement database sharding, test routing |
| **Week 4** | 5 days | Scale application servers, load testing |
| **Week 5** | 5 days | Performance tuning, monitoring setup |
| **Week 6** | 5 days | Failover testing, documentation |

## Monitoring & Alerts

### Key Metrics to Monitor

```yaml
# prometheus-alerts.yml
groups:
  - name: billing-performance
    rules:
      - alert: HighEventLatency
        expr: histogram_quantile(0.95, rate(event_processing_duration_seconds_bucket[5m])) > 0.1
        for: 5m
        annotations:
          summary: "P95 latency above 100ms"
      
      - alert: LowThroughput
        expr: rate(events_processed_total[1m]) < 15000
        for: 5m
        annotations:
          summary: "Event throughput below 900K/min"
      
      - alert: KafkaLag
        expr: kafka_consumer_lag > 10000
        for: 5m
        annotations:
          summary: "Kafka consumer lag high"
      
      - alert: CacheHitRateLow
        expr: redis_cache_hit_ratio < 0.8
        for: 10m
        annotations:
          summary: "Cache hit rate below 80%"
```

## Success Metrics

- [ ] Sustained 1M+ events/minute for 24 hours
- [ ] P95 latency < 100ms under load
- [ ] 99.99% availability (< 4.38 minutes downtime/month)
- [ ] Zero data loss during failover
- [ ] <5 second recovery time objective (RTO)
- [ ] <1 minute recovery point objective (RPO)

## Next Steps

1. **Immediate (Week 1):**
   - Deploy Kafka cluster
   - Implement write-behind cache
   - Begin sharding implementation

2. **Short-term (Month 1):**
   - Complete infrastructure upgrade
   - Load test at 1.5M events/minute
   - Implement monitoring

3. **Long-term (Quarter):**
   - Multi-region deployment
   - 10M events/minute capability
   - Cost optimization
