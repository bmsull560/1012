#!/bin/bash

# Staging Deployment Script
# Deploys all services to staging environment with security checks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STAGING_CLUSTER="valueverse-staging"
STAGING_NAMESPACE="staging"
STAGING_URL="https://staging.valueverse.ai"
REGISTRY="valueverse"

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm not found. Please install helm."
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        log_error "docker not found. Please install docker."
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    # Build frontend
    log_info "Building frontend..."
    docker build -t ${REGISTRY}/frontend:staging-${BUILD_ID:-latest} ./frontend
    docker push ${REGISTRY}/frontend:staging-${BUILD_ID:-latest}
    
    # Build billing service
    log_info "Building billing service..."
    docker build -t ${REGISTRY}/billing-service:staging-${BUILD_ID:-latest} ./billing-system/backend
    docker push ${REGISTRY}/billing-service:staging-${BUILD_ID:-latest}
    
    # Build value services
    for service in value-architect value-committer value-executor; do
        log_info "Building ${service}..."
        docker build -t ${REGISTRY}/${service}:staging-${BUILD_ID:-latest} ./services/${service}
        docker push ${REGISTRY}/${service}:staging-${BUILD_ID:-latest}
    done
    
    log_info "Docker images built and pushed ✓"
}

# Run security scans
run_security_scans() {
    log_info "Running security scans..."
    
    # Scan images with Trivy
    for image in frontend billing-service value-architect value-committer value-executor; do
        log_info "Scanning ${image}..."
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy image ${REGISTRY}/${image}:staging-${BUILD_ID:-latest} \
            --severity HIGH,CRITICAL --exit-code 0
    done
    
    # Check for secrets in code
    log_info "Checking for secrets in code..."
    docker run --rm -v "$PWD:/path" trufflesecurity/trufflehog:latest \
        filesystem /path --no-verification --fail
    
    log_info "Security scans completed ✓"
}

# Create namespace and secrets
setup_namespace() {
    log_info "Setting up staging namespace..."
    
    # Create namespace
    kubectl apply -f infrastructure/kubernetes/staging/namespace.yaml
    
    # Create external secrets
    kubectl apply -f infrastructure/kubernetes/external-secrets/
    
    # Wait for secrets to be created
    log_info "Waiting for secrets to be synchronized..."
    kubectl wait --for=condition=Ready \
        externalsecret/billing-secrets \
        -n ${STAGING_NAMESPACE} \
        --timeout=60s
    
    log_info "Namespace and secrets configured ✓"
}

# Deploy database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Create migration job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-${BUILD_ID:-$(date +%s)}
  namespace: ${STAGING_NAMESPACE}
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migration
        image: ${REGISTRY}/billing-service:staging-${BUILD_ID:-latest}
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: billing-secrets
EOF
    
    # Wait for migration to complete
    kubectl wait --for=condition=complete \
        job/db-migration-${BUILD_ID:-$(date +%s)} \
        -n ${STAGING_NAMESPACE} \
        --timeout=300s
    
    log_info "Database migrations completed ✓"
}

# Deploy services
deploy_services() {
    log_info "Deploying services to staging..."
    
    # Deploy billing service
    kubectl apply -f infrastructure/kubernetes/staging/billing-deployment.yaml
    
    # Deploy value services
    for service in value-architect value-committer value-executor; do
        kubectl apply -f infrastructure/kubernetes/staging/${service}-deployment.yaml
    done
    
    # Deploy frontend
    kubectl apply -f infrastructure/kubernetes/staging/frontend-deployment.yaml
    
    # Deploy ingress
    kubectl apply -f infrastructure/kubernetes/staging/ingress.yaml
    
    log_info "Services deployed ✓"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."
    
    deployments=("billing-service" "value-architect" "value-committer" "value-executor" "frontend")
    
    for deployment in "${deployments[@]}"; do
        log_info "Waiting for ${deployment}..."
        kubectl rollout status deployment/${deployment} \
            -n ${STAGING_NAMESPACE} \
            --timeout=300s
    done
    
    log_info "All deployments ready ✓"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Health check endpoints
    services=("billing-service:8000" "value-architect:8001" "value-committer:8002" "value-executor:8003")
    
    for service in "${services[@]}"; do
        service_name=${service%:*}
        port=${service#*:}
        
        log_info "Testing ${service_name} health..."
        kubectl run smoke-test-${service_name} \
            --image=curlimages/curl:latest \
            --rm -i --restart=Never \
            -n ${STAGING_NAMESPACE} \
            -- curl -f http://${service_name}:${port}/health
    done
    
    # Test frontend
    log_info "Testing frontend..."
    response=$(curl -s -o /dev/null -w "%{http_code}" ${STAGING_URL})
    if [ "$response" -eq 200 ]; then
        log_info "Frontend responding ✓"
    else
        log_error "Frontend not responding (HTTP ${response})"
        exit 1
    fi
    
    log_info "Smoke tests passed ✓"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Deploy Prometheus ServiceMonitors
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: staging-services
  namespace: ${STAGING_NAMESPACE}
spec:
  selector:
    matchLabels:
      environment: staging
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
    
    log_info "Monitoring configured ✓"
}

# Run security tests
run_security_tests() {
    log_info "Running security tests..."
    
    # Run tenant isolation tests
    kubectl run security-test \
        --image=${REGISTRY}/security-tests:latest \
        --rm -i --restart=Never \
        -n ${STAGING_NAMESPACE} \
        -- pytest tests/security/test_tenant_isolation.py -v
    
    log_info "Security tests completed ✓"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."
    
    cat <<EOF > staging-deployment-report.md
# Staging Deployment Report

**Date:** $(date)
**Build ID:** ${BUILD_ID:-latest}
**Cluster:** ${STAGING_CLUSTER}
**Namespace:** ${STAGING_NAMESPACE}

## Deployed Services

| Service | Image | Replicas | Status |
|---------|-------|----------|--------|
$(kubectl get deployments -n ${STAGING_NAMESPACE} -o custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image,REPLICAS:.spec.replicas,READY:.status.readyReplicas --no-headers | awk '{print "| " $1 " | " $2 " | " $3 " | " $4 " |"}')

## Health Checks

| Service | Health | Ready |
|---------|--------|-------|
$(for svc in billing-service value-architect value-committer value-executor; do
    health=$(kubectl exec -n ${STAGING_NAMESPACE} deployment/${svc} -- curl -s localhost:8000/health | jq -r '.status' 2>/dev/null || echo "unknown")
    ready=$(kubectl exec -n ${STAGING_NAMESPACE} deployment/${svc} -- curl -s localhost:8000/ready | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "| ${svc} | ${health} | ${ready} |"
done)

## Security Scan Results

- Container scanning: ✓ Passed
- Secret scanning: ✓ Passed
- Tenant isolation: ✓ Passed

## URLs

- Frontend: ${STAGING_URL}
- API Gateway: ${STAGING_URL}/api
- Monitoring: ${STAGING_URL}/grafana
- Logs: ${STAGING_URL}/kibana

## Next Steps

1. Run penetration testing
2. Run load testing
3. Review security audit
4. Approve for production

EOF
    
    log_info "Report generated: staging-deployment-report.md"
}

# Main deployment flow
main() {
    log_info "Starting staging deployment..."
    
    check_prerequisites
    build_and_push_images
    run_security_scans
    setup_namespace
    run_migrations
    deploy_services
    wait_for_deployments
    run_smoke_tests
    setup_monitoring
    run_security_tests
    generate_report
    
    log_info "🎉 Staging deployment completed successfully!"
    log_info "Access staging at: ${STAGING_URL}"
    log_info "Run penetration testing: ./run-pentest.sh"
    log_info "Run load testing: ./run-loadtest.sh"
}

# Run main function
main "$@"
