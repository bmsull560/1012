# 🚨 Critical Fixes - Implementation Guide

This guide provides step-by-step instructions for addressing the most critical production blockers.

---

## 🔴 PRIORITY 1: Secrets Management (Days 1-3)

### Current Problem
Hardcoded credentials in `docker-compose.yml`, `.env`, and configuration files.

### Solution: AWS Secrets Manager (Recommended)

#### Step 1: Create Secrets in AWS
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create secret for database
aws secretsmanager create-secret \
  --name valueverse/prod/database \
  --description "Production database credentials" \
  --secret-string '{
    "username": "prod_user",
    "password": "GENERATED_SECURE_PASSWORD",
    "host": "prod-db.example.com",
    "port": "5432",
    "database": "valueverse_prod"
  }'

# Create secret for API keys
aws secretsmanager create-secret \
  --name valueverse/prod/api-keys \
  --secret-string '{
    "openai_api_key": "sk-...",
    "jwt_secret": "GENERATED_SECRET_KEY"
  }'
```

#### Step 2: Update Application Code

**Backend (`valueverse/backend/app/core/config.py`)**:
```python
import boto3
import json
from functools import lru_cache

@lru_cache()
def get_secret(secret_name: str):
    """Retrieve secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        # Fallback to environment variables in development
        raise Exception(f"Could not retrieve secret {secret_name}: {e}")

class Settings(BaseSettings):
    # Load from Secrets Manager
    _db_secret = get_secret("valueverse/prod/database")
    _api_secret = get_secret("valueverse/prod/api-keys")
    
    DATABASE_URL: str = (
        f"postgresql://{_db_secret['username']}:{_db_secret['password']}"
        f"@{_db_secret['host']}:{_db_secret['port']}/{_db_secret['database']}"
    )
    JWT_SECRET: str = _api_secret['jwt_secret']
    OPENAI_API_KEY: str = _api_secret['openai_api_key']
```

#### Step 3: Update Docker Configuration

**docker-compose.prod.yml**:
```yaml
services:
  backend:
    environment:
      AWS_REGION: us-east-1
      AWS_DEFAULT_REGION: us-east-1
      # IAM role will provide credentials
    # Remove all hardcoded secrets
```

#### Step 4: IAM Role Configuration
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:valueverse/prod/*"
      ]
    }
  ]
}
```

---

## 🔴 PRIORITY 2: Database High Availability (Days 4-7)

### Solution: RDS PostgreSQL with Multi-AZ

#### Step 1: Create RDS Instance
```bash
aws rds create-db-instance \
  --db-instance-identifier valueverse-prod-primary \
  --db-instance-class db.r6g.xlarge \
  --engine postgres \
  --engine-version 15.4 \
  --master-username valueverse_admin \
  --master-user-password "$(aws secretsmanager get-random-password --output text)" \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --kms-key-id "alias/valueverse-db-key" \
  --multi-az \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --enable-cloudwatch-logs-exports '["postgresql","upgrade"]' \
  --auto-minor-version-upgrade \
  --publicly-accessible false \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name valueverse-db-subnet
```

#### Step 2: Create Read Replica
```bash
aws rds create-db-instance-read-replica \
  --db-instance-identifier valueverse-prod-replica-1 \
  --source-db-instance-identifier valueverse-prod-primary \
  --db-instance-class db.r6g.large \
  --multi-az false
```

#### Step 3: Configure Connection Pooling (PgBouncer)

**pgbouncer.ini**:
```ini
[databases]
valueverse = host=valueverse-prod-primary.xxx.rds.amazonaws.com port=5432 dbname=valueverse

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
```

#### Step 4: Automated Backups Script
```bash
#!/bin/bash
# backup.sh - Run via cron every hour

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="valueverse_backup_${TIMESTAMP}.sql.gz"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d valueverse | gzip > /tmp/$BACKUP_FILE

# Upload to S3
aws s3 cp /tmp/$BACKUP_FILE s3://valueverse-backups/database/$BACKUP_FILE \
  --storage-class STANDARD_IA

# Cleanup old local backups
find /tmp -name "valueverse_backup_*.sql.gz" -mtime +1 -delete

# Test backup integrity
gunzip -t /tmp/$BACKUP_FILE
if [ $? -eq 0 ]; then
  echo "Backup successful: $BACKUP_FILE"
else
  echo "Backup FAILED: $BACKUP_FILE" | mail -s "CRITICAL: Backup Failed" ops@valueverse.com
fi
```

---

## 🔴 PRIORITY 3: SSL/TLS Configuration (Days 2-3)

### Solution: AWS ACM + Application Load Balancer

#### Step 1: Request SSL Certificate
```bash
# Request certificate from ACM
aws acm request-certificate \
  --domain-name valueverse.com \
  --subject-alternative-names "*.valueverse.com" \
  --validation-method DNS

# Validate via DNS (follow ACM console instructions)
```

#### Step 2: Create Application Load Balancer
```bash
aws elbv2 create-load-balancer \
  --name valueverse-prod-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4
```

#### Step 3: Configure HTTPS Listener
```bash
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --ssl-policy ELBSecurityPolicy-TLS-1-2-2017-01 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

#### Step 4: Update Backend to Enforce HTTPS

**FastAPI Middleware**:
```python
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Force HTTPS in production
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["valueverse.com", "*.valueverse.com"]
    )

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## 🔴 PRIORITY 4: Authentication & Authorization (Days 4-7)

### Solution: OAuth2 + JWT with MFA

#### Step 1: Install Dependencies
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart pyotp qrcode
```

#### Step 2: Implement OAuth2 with MFA

**auth.py**:
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire = 15  # minutes
        self.refresh_token_expire = 7  # days
    
    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_mfa_secret(self) -> str:
        return pyotp.random_base32()
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    async def authenticate_user(
        self, 
        db, 
        email: str, 
        password: str, 
        mfa_token: str = None
    ):
        user = await db.get_user_by_email(email)
        if not user or not self.verify_password(password, user.password_hash):
            return None
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_token:
                return {"mfa_required": True, "user_id": user.id}
            if not self.verify_mfa_token(user.mfa_secret, mfa_token):
                return None
        
        return user
```

#### Step 3: Implement RBAC

**rbac.py**:
```python
from enum import Enum
from typing import List

class Permission(str, Enum):
    READ_VALUE_MODELS = "read:value_models"
    WRITE_VALUE_MODELS = "write:value_models"
    DELETE_VALUE_MODELS = "delete:value_models"
    ADMIN_USERS = "admin:users"
    ADMIN_TENANTS = "admin:tenants"

class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

ROLE_PERMISSIONS = {
    Role.VIEWER: [Permission.READ_VALUE_MODELS],
    Role.ANALYST: [
        Permission.READ_VALUE_MODELS,
        Permission.WRITE_VALUE_MODELS,
    ],
    Role.MANAGER: [
        Permission.READ_VALUE_MODELS,
        Permission.WRITE_VALUE_MODELS,
        Permission.DELETE_VALUE_MODELS,
    ],
    Role.ADMIN: [
        Permission.READ_VALUE_MODELS,
        Permission.WRITE_VALUE_MODELS,
        Permission.DELETE_VALUE_MODELS,
        Permission.ADMIN_USERS,
    ],
    Role.SUPER_ADMIN: list(Permission),
}

def check_permission(user_role: Role, required_permission: Permission) -> bool:
    return required_permission in ROLE_PERMISSIONS.get(user_role, [])
```

---

## 🔴 PRIORITY 5: Monitoring Setup (Days 5-7)

### Solution: Prometheus + Grafana + Loki

#### Step 1: Deploy Monitoring Stack

**docker-compose.monitoring.yml**:
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
  
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: grafana-piechart-panel
  
  loki:
    image: grafana/loki:latest
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
  
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

volumes:
  prometheus_data:
  grafana_data:
```

#### Step 2: Configure Application Metrics

**FastAPI Metrics**:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response
import time

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users',
    ['tenant']
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

#### Step 3: Create Alert Rules

**prometheus-alerts.yml**:
```yaml
groups:
  - name: valueverse_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is {{ $value }}s"
      
      - alert: DatabaseConnectionPoolExhaustion
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool near exhaustion"
```

---

## 📋 Quick Start Checklist

**Day 1-2: Immediate Actions**
- [ ] Audit all hardcoded credentials
- [ ] Setup AWS Secrets Manager
- [ ] Migrate database credentials to secrets
- [ ] Request SSL certificates
- [ ] Create RDS instance plan

**Day 3-4: Security Foundation**
- [ ] Implement OAuth2 authentication
- [ ] Add MFA support
- [ ] Configure SSL/TLS
- [ ] Setup RBAC

**Day 5-7: Infrastructure & Monitoring**
- [ ] Deploy monitoring stack
- [ ] Configure database HA
- [ ] Setup load balancer
- [ ] Create automated backups
- [ ] Test disaster recovery

---

## 🆘 Emergency Contacts

**Critical Issues**: Escalate immediately
- Security Team Lead: security@valueverse.com
- DevOps On-Call: +1-555-DEVOPS
- Database Team: dba@valueverse.com

**Vendor Support**:
- AWS Support: Enterprise tier
- Database Support: PostgreSQL professional services
