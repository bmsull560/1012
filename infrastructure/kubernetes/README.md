# 🚀 ValueVerse Platform - Kubernetes Infrastructure

**Complete Production-Ready Kubernetes Deployment**

---

## 📋 Overview

This directory contains complete Kubernetes manifests for deploying the ValueVerse platform with:

- ✅ **High Availability**: Multi-replica deployments with pod anti-affinity
- ✅ **Auto-Scaling**: HPA for pods, cluster autoscaling for nodes
- ✅ **Security**: Network policies, encrypted storage, RBAC, secrets management
- ✅ **Monitoring**: Prometheus, Grafana, Loki for full observability
- ✅ **SSL/TLS**: Automated certificate management with cert-manager
- ✅ **Database HA**: PostgreSQL primary-replica with PgBouncer pooling
- ✅ **Zero Downtime**: Rolling updates with health checks and PDBs

---

## 📁 File Structure

```
kubernetes/
├── namespace.yaml                  # Namespaces for app and monitoring
├── configmap.yaml                  # Application configuration
├── secrets.yaml                    # Secrets (template - DO NOT commit real secrets!)
├── storage-class.yaml              # AWS EBS/EFS storage classes
├── network-policy.yaml             # Zero-trust network policies
│
├── postgres-statefulset.yaml       # PostgreSQL primary + replicas + PgBouncer
├── redis-deployment.yaml           # Redis with Sentinel for HA
├── backend-deployment.yaml         # Backend API with HPA (3-20 replicas)
├── frontend-deployment.yaml        # Frontend with HPA (2-10 replicas)
│
├── ingress.yaml                    # NGINX Ingress with SSL/TLS
├── monitoring.yaml                 # Prometheus + Grafana + Loki
│
├── deploy.sh                       # Automated deployment script
└── README.md                       # This file
```

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │  Load Balancer │ (AWS ALB/NLB)
         │   (Ingress)    │
         └───────┬───────┘
                 │
         ┌───────┴────────┐
         │                │
    ┌────▼────┐      ┌───▼──────┐
    │Frontend │      │  Backend  │ (HPA: 3-20 pods)
    │(2-10)   │      │  + WS     │
    └─────────┘      └────┬──────┘
                          │
              ┌───────────┴────────────┐
              │                        │
         ┌────▼────┐              ┌───▼───┐
         │PostgreSQL│              │ Redis │
         │Primary+  │              │+Sntnel│
         │Replicas  │              └───────┘
         └──────────┘
              │
         ┌────▼─────┐
         │PgBouncer │ (Connection Pooling)
         └──────────┘

Monitoring:
┌──────────┐    ┌─────────┐    ┌──────┐
│Prometheus│◄───┤ Grafana │◄───┤ Loki │
└──────────┘    └─────────┘    └──────┘
```

---

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes Cluster** (EKS, GKE, AKS, or self-hosted)
   - Kubernetes 1.24+
   - At least 3 worker nodes (t3.xlarge or equivalent)
   - 16 GB RAM minimum per node

2. **Tools Installed**:
   ```bash
   # Required
   kubectl >= 1.24
   aws-cli >= 2.0 (for EKS)
   
   # Recommended
   helm >= 3.0
   eksctl (for EKS cluster creation)
   ```

3. **AWS Resources** (if using AWS):
   - EKS cluster or EC2 instances
   - EBS volumes for persistent storage
   - KMS key for encryption
   - IAM roles configured

---

## 📦 Installation

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Navigate to kubernetes directory
cd kubernetes

# 2. Make deploy script executable
chmod +x deploy.sh

# 3. Configure environment
export CLUSTER_NAME="valueverse-prod-cluster"
export AWS_REGION="us-east-1"

# 4. Run deployment
./deploy.sh
```

### Option 2: Manual Deployment

```bash
# 1. Create namespaces
kubectl apply -f namespace.yaml

# 2. Deploy storage classes
kubectl apply -f storage-class.yaml

# 3. Deploy secrets (UPDATE FIRST!)
kubectl apply -f secrets.yaml

# 4. Deploy configmaps
kubectl apply -f configmap.yaml

# 5. Deploy database
kubectl apply -f postgres-statefulset.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n valueverse-prod --timeout=300s

# 6. Deploy Redis
kubectl apply -f redis-deployment.yaml
kubectl wait --for=condition=ready pod -l app=redis -n valueverse-prod --timeout=120s

# 7. Deploy backend
kubectl apply -f backend-deployment.yaml
kubectl wait --for=condition=available deployment/backend -n valueverse-prod --timeout=300s

# 8. Deploy frontend
kubectl apply -f frontend-deployment.yaml
kubectl wait --for=condition=available deployment/frontend -n valueverse-prod --timeout=300s

# 9. Deploy monitoring
kubectl apply -f monitoring.yaml

# 10. Deploy network policies
kubectl apply -f network-policy.yaml

# 11. Deploy ingress
kubectl apply -f ingress.yaml
```

---

## ⚙️ Configuration

### 1. Update Secrets

**CRITICAL**: Before deployment, update `secrets.yaml` with actual values:

```bash
# Edit secrets file
vi secrets.yaml

# Replace all "REPLACE_WITH_ACTUAL_*" placeholders with real values
```

**Recommended**: Use External Secrets Operator with AWS Secrets Manager:

```bash
# Install External Secrets Operator
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Secrets will be automatically synced from AWS Secrets Manager
```

### 2. Configure Storage

Update `storage-class.yaml` with your KMS key:

```yaml
parameters:
  kmsKeyId: "alias/your-kms-key-name"  # Your KMS key
```

### 3. Configure Domain Names

Update `ingress.yaml` with your domains:

```yaml
spec:
  tls:
    - hosts:
        - your-domain.com
        - api.your-domain.com
```

### 4. Resource Limits

Adjust resource requests/limits in deployment files based on your workload:

```yaml
resources:
  requests:
    memory: "1Gi"    # Adjust as needed
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

---

## 📊 Scaling Configuration

### Backend Auto-Scaling

```yaml
# backend-deployment.yaml
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          averageUtilization: 70  # Scale at 70% CPU
    - type: Resource
      resource:
        name: memory
        target:
          averageUtilization: 80  # Scale at 80% memory
```

### Manual Scaling

```bash
# Scale backend manually
kubectl scale deployment backend --replicas=10 -n valueverse-prod

# Scale frontend manually
kubectl scale deployment frontend --replicas=5 -n valueverse-prod
```

### Cluster Auto-Scaling (AWS)

```bash
# Enable cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Configure autoscaler
kubectl -n kube-system annotate deployment.apps/cluster-autoscaler \
  cluster-autoscaler.kubernetes.io/safe-to-evict="false"
```

---

## 🔒 Security Features

### 1. Network Policies (Zero Trust)

- Default deny all ingress
- Allow only necessary communication paths
- Database accessible only from backend
- Redis accessible only from backend

### 2. Pod Security

- Run as non-root user
- Read-only root filesystem
- Drop all capabilities
- No privilege escalation

### 3. Secrets Management

- Encrypted at rest (KMS)
- External Secrets Operator integration
- No secrets in environment variables (from files)

### 4. Storage Encryption

- EBS volumes encrypted with KMS
- Snapshots encrypted
- Encryption in transit (TLS)

---

## 📈 Monitoring & Observability

### Access Monitoring

```bash
# Port-forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n valueverse-monitoring

# Access: http://localhost:3000
# Default credentials: admin / <from secrets>
```

### Prometheus Queries

Access Prometheus:
```bash
kubectl port-forward svc/prometheus-server 9090:9090 -n valueverse-monitoring
```

Example queries:
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes
```

### Logs

```bash
# View backend logs
kubectl logs -f deployment/backend -n valueverse-prod

# View all pod logs
kubectl logs -f -l app=backend -n valueverse-prod --tail=100

# Stern (if installed) - stream logs from multiple pods
stern backend -n valueverse-prod
```

---

## 🔧 Maintenance

### Database Backups

```bash
# Manual backup
kubectl exec -it postgres-primary-0 -n valueverse-prod -- \
  pg_dump -U postgres valueverse | gzip > backup.sql.gz

# Automated backups (CronJob)
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: valueverse-prod
spec:
  schedule: "0 * * * *"  # Hourly
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - pg_dump -h postgres-primary-service -U postgres valueverse | gzip > /backup/backup-\$(date +%Y%m%d-%H%M%S).sql.gz
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
EOF
```

### Database Restore

```bash
# Restore from backup
kubectl exec -it postgres-primary-0 -n valueverse-prod -- \
  bash -c "gunzip < /backup/backup.sql.gz | psql -U postgres valueverse"
```

### Certificate Renewal

Certificates are automatically renewed by cert-manager. To check status:

```bash
# Check certificates
kubectl get certificates -n valueverse-prod

# Check certificate details
kubectl describe certificate valueverse-tls-cert -n valueverse-prod
```

---

## 🚨 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n valueverse-prod

# Describe pod for events
kubectl describe pod <pod-name> -n valueverse-prod

# Check logs
kubectl logs <pod-name> -n valueverse-prod

# Check previous container logs (if crashed)
kubectl logs <pod-name> -n valueverse-prod --previous
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h postgres-primary-service.valueverse-prod.svc.cluster.local -U postgres

# Check database logs
kubectl logs postgres-primary-0 -n valueverse-prod
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress valueverse-ingress -n valueverse-prod

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Check certificate status
kubectl get certificates -n valueverse-prod
kubectl describe certificate valueverse-tls-cert -n valueverse-prod
```

### High Memory Usage

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n valueverse-prod

# Check HPA status
kubectl get hpa -n valueverse-prod

# Manually scale if needed
kubectl scale deployment backend --replicas=5 -n valueverse-prod
```

---

## 🔄 Updating Deployments

### Rolling Update (Zero Downtime)

```bash
# Update backend image
kubectl set image deployment/backend \
  backend=valueverse/backend:v2.0.0 \
  -n valueverse-prod

# Check rollout status
kubectl rollout status deployment/backend -n valueverse-prod

# Rollback if needed
kubectl rollout undo deployment/backend -n valueverse-prod

# Check rollout history
kubectl rollout history deployment/backend -n valueverse-prod
```

### Update Configuration

```bash
# Update configmap
kubectl apply -f configmap.yaml

# Restart pods to pick up new config
kubectl rollout restart deployment/backend -n valueverse-prod
kubectl rollout restart deployment/frontend -n valueverse-prod
```

---

## 🧪 Testing

### Health Checks

```bash
# Test backend health
kubectl run curl --image=curlimages/curl -i --rm --restart=Never -- \
  curl http://backend-service.valueverse-prod.svc.cluster.local:8000/health

# Test database
kubectl run psql --image=postgres:15 -i --rm --restart=Never -- \
  pg_isready -h postgres-primary-service.valueverse-prod.svc.cluster.local
```

### Load Testing

```bash
# Install K6
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: k6-script
data:
  script.js: |
    import http from 'k6/http';
    export default function () {
      http.get('http://backend-service.valueverse-prod.svc.cluster.local:8000/health');
    }
---
apiVersion: batch/v1
kind: Job
metadata:
  name: k6-load-test
spec:
  template:
    spec:
      containers:
      - name: k6
        image: grafana/k6
        command: ['k6', 'run', '--vus', '100', '--duration', '1m', '/scripts/script.js']
        volumeMounts:
        - name: script
          mountPath: /scripts
      volumes:
      - name: script
        configMap:
          name: k6-script
      restartPolicy: Never
EOF
```

---

## 📚 Additional Resources

### Useful Commands

```bash
# Get all resources
kubectl get all -n valueverse-prod

# Watch pod status
kubectl get pods -n valueverse-prod -w

# Execute command in pod
kubectl exec -it backend-xxx -n valueverse-prod -- /bin/bash

# Copy files from pod
kubectl cp valueverse-prod/backend-xxx:/app/logs ./logs

# Port forward to service
kubectl port-forward svc/backend-service 8000:8000 -n valueverse-prod
```

### Cost Optimization

```bash
# Use spot instances for non-critical workloads
# Configure in node groups

# Right-size resources
kubectl top pods -n valueverse-prod
kubectl top nodes

# Use cluster autoscaler to scale down unused nodes
```

---

## 🎯 Production Checklist

Before going to production:

- [ ] Update all secrets in `secrets.yaml`
- [ ] Configure proper domain names in `ingress.yaml`
- [ ] Set up DNS records pointing to load balancer
- [ ] Configure KMS encryption for storage
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery procedures
- [ ] Set up log aggregation
- [ ] Configure network policies
- [ ] Enable pod security policies
- [ ] Set up RBAC properly
- [ ] Configure resource quotas
- [ ] Test auto-scaling behavior
- [ ] Perform load testing
- [ ] Security audit
- [ ] Document runbooks

---

## 📞 Support

**Issues**: https://github.com/valueverse/platform/issues  
**Documentation**: https://docs.valueverse.com  
**Monitoring**: https://monitoring.valueverse.com

---

**Created**: October 13, 2025  
**Version**: 1.0.0  
**Platform**: Kubernetes 1.24+
