#!/bin/bash

# ================================================================
# ValueVerse Platform - Kubernetes Deployment Script
# ================================================================
# This script deploys the complete ValueVerse platform to Kubernetes
# ================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="valueverse-prod"
MONITORING_NAMESPACE="valueverse-monitoring"
CLUSTER_NAME="${CLUSTER_NAME:-valueverse-prod-cluster}"
REGION="${AWS_REGION:-us-east-1}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }

# ================================================================
# Pre-flight Checks
# ================================================================

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        warning "helm is not installed (optional but recommended)"
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# ================================================================
# Setup EKS Cluster (if needed)
# ================================================================

setup_eks_cluster() {
    log "Setting up EKS cluster..."
    
    # Check if cluster exists
    if aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" &> /dev/null; then
        log "Cluster $CLUSTER_NAME already exists"
    else
        log "Creating EKS cluster $CLUSTER_NAME..."
        
        # Create cluster using eksctl (if available)
        if command -v eksctl &> /dev/null; then
            eksctl create cluster \
                --name "$CLUSTER_NAME" \
                --region "$REGION" \
                --version 1.28 \
                --nodegroup-name standard-workers \
                --node-type t3.xlarge \
                --nodes 3 \
                --nodes-min 3 \
                --nodes-max 10 \
                --managed \
                --enable-ssm \
                --asg-access \
                --external-dns-access \
                --full-ecr-access \
                --alb-ingress-access
        else
            error "eksctl not found. Please install eksctl or create cluster manually"
            exit 1
        fi
    fi
    
    # Update kubeconfig
    aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$REGION"
    
    success "EKS cluster setup complete"
}

# ================================================================
# Install Prerequisites
# ================================================================

install_prerequisites() {
    log "Installing cluster prerequisites..."
    
    # Install NGINX Ingress Controller
    log "Installing NGINX Ingress Controller..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.4/deploy/static/provider/aws/deploy.yaml
    
    # Install Cert Manager
    log "Installing Cert Manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml
    
    # Install Metrics Server
    log "Installing Metrics Server..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    # Install External Secrets Operator (optional)
    if [ "${INSTALL_EXTERNAL_SECRETS:-true}" = "true" ]; then
        log "Installing External Secrets Operator..."
        helm repo add external-secrets https://charts.external-secrets.io
        helm install external-secrets \
            external-secrets/external-secrets \
            -n external-secrets-system \
            --create-namespace \
            --set installCRDs=true
    fi
    
    # Install EBS CSI Driver
    log "Installing AWS EBS CSI Driver..."
    kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.25"
    
    success "Prerequisites installed"
}

# ================================================================
# Create Namespaces
# ================================================================

create_namespaces() {
    log "Creating namespaces..."
    kubectl apply -f "${SCRIPT_DIR}/namespace.yaml"
    success "Namespaces created"
}

# ================================================================
# Deploy Storage Classes
# ================================================================

deploy_storage() {
    log "Deploying storage classes..."
    kubectl apply -f "${SCRIPT_DIR}/storage-class.yaml"
    success "Storage classes deployed"
}

# ================================================================
# Deploy Secrets
# ================================================================

deploy_secrets() {
    log "Deploying secrets..."
    
    warning "Remember to update secrets with actual values before deployment!"
    
    # Check if secrets file has been customized
    if grep -q "REPLACE_WITH_ACTUAL" "${SCRIPT_DIR}/secrets.yaml"; then
        warning "Secrets file contains placeholder values"
        read -p "Continue anyway? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            error "Deployment cancelled. Please update secrets.yaml with actual values"
            exit 1
        fi
    fi
    
    kubectl apply -f "${SCRIPT_DIR}/secrets.yaml"
    success "Secrets deployed"
}

# ================================================================
# Deploy ConfigMaps
# ================================================================

deploy_configmaps() {
    log "Deploying configmaps..."
    kubectl apply -f "${SCRIPT_DIR}/configmap.yaml"
    success "ConfigMaps deployed"
}

# ================================================================
# Deploy Database
# ================================================================

deploy_database() {
    log "Deploying PostgreSQL database..."
    kubectl apply -f "${SCRIPT_DIR}/postgres-statefulset.yaml"
    
    log "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=postgres,role=primary \
        -n "$NAMESPACE" \
        --timeout=300s
    
    success "Database deployed"
}

# ================================================================
# Deploy Redis
# ================================================================

deploy_redis() {
    log "Deploying Redis..."
    kubectl apply -f "${SCRIPT_DIR}/redis-deployment.yaml"
    
    log "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=redis \
        -n "$NAMESPACE" \
        --timeout=120s
    
    success "Redis deployed"
}

# ================================================================
# Deploy Backend
# ================================================================

deploy_backend() {
    log "Deploying backend application..."
    kubectl apply -f "${SCRIPT_DIR}/backend-deployment.yaml"
    
    log "Waiting for backend to be ready..."
    kubectl wait --for=condition=available deployment/backend \
        -n "$NAMESPACE" \
        --timeout=300s
    
    success "Backend deployed"
}

# ================================================================
# Deploy Frontend
# ================================================================

deploy_frontend() {
    log "Deploying frontend application..."
    kubectl apply -f "${SCRIPT_DIR}/frontend-deployment.yaml"
    
    log "Waiting for frontend to be ready..."
    kubectl wait --for=condition=available deployment/frontend \
        -n "$NAMESPACE" \
        --timeout=300s
    
    success "Frontend deployed"
}

# ================================================================
# Deploy Monitoring
# ================================================================

deploy_monitoring() {
    log "Deploying monitoring stack..."
    kubectl apply -f "${SCRIPT_DIR}/monitoring.yaml"
    
    log "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=available deployment/prometheus-server \
        -n "$MONITORING_NAMESPACE" \
        --timeout=180s
    
    log "Waiting for Grafana to be ready..."
    kubectl wait --for=condition=available deployment/grafana \
        -n "$MONITORING_NAMESPACE" \
        --timeout=180s
    
    success "Monitoring stack deployed"
}

# ================================================================
# Deploy Network Policies
# ================================================================

deploy_network_policies() {
    log "Deploying network policies..."
    kubectl apply -f "${SCRIPT_DIR}/network-policy.yaml"
    success "Network policies deployed"
}

# ================================================================
# Deploy Ingress
# ================================================================

deploy_ingress() {
    log "Deploying ingress resources..."
    
    # Wait for cert-manager to be ready
    log "Waiting for cert-manager..."
    kubectl wait --for=condition=available deployment/cert-manager \
        -n cert-manager \
        --timeout=180s
    
    kubectl apply -f "${SCRIPT_DIR}/ingress.yaml"
    
    log "Waiting for ingress to get external IP..."
    for i in {1..30}; do
        EXTERNAL_IP=$(kubectl get ingress valueverse-ingress \
            -n "$NAMESPACE" \
            -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
        
        if [ -n "$EXTERNAL_IP" ]; then
            success "Ingress deployed with external address: $EXTERNAL_IP"
            return 0
        fi
        
        log "Waiting for external IP... ($i/30)"
        sleep 10
    done
    
    warning "Ingress deployed but external IP not yet assigned"
}

# ================================================================
# Verify Deployment
# ================================================================

verify_deployment() {
    log "Verifying deployment..."
    
    echo ""
    echo "=================================="
    echo "Deployment Status"
    echo "=================================="
    
    # Check pods
    echo ""
    echo "Pods in $NAMESPACE:"
    kubectl get pods -n "$NAMESPACE"
    
    echo ""
    echo "Pods in $MONITORING_NAMESPACE:"
    kubectl get pods -n "$MONITORING_NAMESPACE"
    
    # Check services
    echo ""
    echo "Services in $NAMESPACE:"
    kubectl get services -n "$NAMESPACE"
    
    # Check ingress
    echo ""
    echo "Ingress:"
    kubectl get ingress -n "$NAMESPACE"
    
    # Check HPA
    echo ""
    echo "Horizontal Pod Autoscalers:"
    kubectl get hpa -n "$NAMESPACE"
    
    # Check PVCs
    echo ""
    echo "Persistent Volume Claims:"
    kubectl get pvc -n "$NAMESPACE"
    
    success "Deployment verification complete"
}

# ================================================================
# Display Access Information
# ================================================================

display_access_info() {
    echo ""
    echo "=================================="
    echo "Access Information"
    echo "=================================="
    
    INGRESS_HOST=$(kubectl get ingress valueverse-ingress \
        -n "$NAMESPACE" \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "PENDING")
    
    echo ""
    echo "Application URLs (after DNS configuration):"
    echo "  Frontend:   https://valueverse.com"
    echo "  API:        https://api.valueverse.com"
    echo "  Monitoring: https://monitoring.valueverse.com"
    echo ""
    echo "Ingress Load Balancer: $INGRESS_HOST"
    echo ""
    echo "Configure your DNS to point to the Load Balancer:"
    echo "  valueverse.com      -> $INGRESS_HOST"
    echo "  api.valueverse.com  -> $INGRESS_HOST"
    echo ""
    echo "Useful Commands:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  kubectl logs -f deployment/backend -n $NAMESPACE"
    echo "  kubectl describe ingress valueverse-ingress -n $NAMESPACE"
    echo "  kubectl port-forward svc/grafana 3000:3000 -n $MONITORING_NAMESPACE"
    echo ""
}

# ================================================================
# Main Deployment Flow
# ================================================================

main() {
    log "========================================="
    log "ValueVerse Kubernetes Deployment"
    log "========================================="
    log "Cluster: $CLUSTER_NAME"
    log "Region: $REGION"
    log "Namespace: $NAMESPACE"
    log "========================================="
    
    # Confirm deployment
    read -p "Deploy to Kubernetes? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "Deployment cancelled"
        exit 0
    fi
    
    # Run deployment steps
    check_prerequisites
    
    # Optional: Setup EKS cluster
    if [ "${SETUP_CLUSTER:-false}" = "true" ]; then
        setup_eks_cluster
    fi
    
    install_prerequisites
    create_namespaces
    deploy_storage
    deploy_secrets
    deploy_configmaps
    deploy_database
    deploy_redis
    deploy_backend
    deploy_frontend
    deploy_monitoring
    deploy_network_policies
    deploy_ingress
    
    # Verify
    verify_deployment
    display_access_info
    
    log "========================================="
    success "🎉 Deployment completed successfully!"
    log "========================================="
}

# Run main function
main "$@"
