#!/bin/bash
# Production Deployment Script for ValueVerse Platform
# This script handles the complete production deployment process

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
NAMESPACE="valueverse-prod"
REGISTRY="ghcr.io/valueverse"
KUBECTL_CONTEXT="valueverse-production"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check helm (optional but recommended)
    if ! command -v helm &> /dev/null; then
        print_warning "Helm is not installed (optional)"
    fi
    
    # Check if connected to correct cluster
    CURRENT_CONTEXT=$(kubectl config current-context)
    if [ "$CURRENT_CONTEXT" != "$KUBECTL_CONTEXT" ]; then
        print_warning "Not connected to production cluster. Switching context..."
        kubectl config use-context $KUBECTL_CONTEXT || {
            print_error "Failed to switch to production context"
            exit 1
        }
    fi
    
    print_success "Prerequisites check passed"
}

# Function to load environment variables
load_environment() {
    print_status "Loading environment configuration..."
    
    if [ -f ".env.production" ]; then
        export $(cat .env.production | grep -v '^#' | xargs)
        print_success "Production environment loaded"
    else
        print_error ".env.production file not found"
        exit 1
    fi
}

# Function to create Kubernetes secrets
create_secrets() {
    print_status "Creating Kubernetes secrets..."
    
    # Database credentials
    kubectl create secret generic db-credentials \
        --from-literal=username="$DB_USER" \
        --from-literal=password="$DB_PASSWORD" \
        --from-literal=connection-string="$DATABASE_URL" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Redis credentials
    kubectl create secret generic redis-credentials \
        --from-literal=password="$REDIS_PASSWORD" \
        --from-literal=connection-string="$REDIS_URL" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Supabase credentials
    kubectl create secret generic supabase-credentials \
        --from-literal=url="$NEXT_PUBLIC_SUPABASE_URL" \
        --from-literal=anon-key="$NEXT_PUBLIC_SUPABASE_ANON_KEY" \
        --from-literal=service-role-key="$SUPABASE_SERVICE_ROLE_KEY" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # OpenAI credentials
    kubectl create secret generic openai-credentials \
        --from-literal=api-key="$OPENAI_API_KEY" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Stripe credentials
    kubectl create secret generic stripe-credentials \
        --from-literal=secret-key="$STRIPE_SECRET_KEY" \
        --from-literal=webhook-secret="$STRIPE_WEBHOOK_SECRET" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Secrets created/updated"
}

# Function to build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Login to registry
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
    
    # Build and push each service
    SERVICES=("frontend" "services/value-architect" "services/value-committer" "services/value-executor" "billing-system/backend")
    
    for SERVICE in "${SERVICES[@]}"; do
        SERVICE_NAME=$(basename $SERVICE)
        print_status "Building $SERVICE_NAME..."
        
        docker build -t "$REGISTRY/$SERVICE_NAME:latest" \
                     -t "$REGISTRY/$SERVICE_NAME:$GIT_COMMIT" \
                     ./$SERVICE
        
        docker push "$REGISTRY/$SERVICE_NAME:latest"
        docker push "$REGISTRY/$SERVICE_NAME:$GIT_COMMIT"
        
        print_success "$SERVICE_NAME image pushed"
    done
}

# Function to run database migrations
run_database_migrations() {
    print_status "Running database migrations..."
    
    # Create a temporary migration job
    kubectl run migration-job \
        --image=postgres:15-alpine \
        --namespace=$NAMESPACE \
        --rm -i --restart=Never -- \
        bash -c "
            export PGPASSWORD='$DB_PASSWORD'
            for migration in /migrations/*.sql; do
                echo \"Applying migration: \$migration\"
                psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f \"\$migration\"
            done
        "
    
    print_success "Database migrations completed"
}

# Function to deploy Kubernetes resources
deploy_kubernetes_resources() {
    print_status "Deploying Kubernetes resources..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    kubectl apply -f k8s/production/deployment.yaml
    kubectl apply -f k8s/production/services.yaml
    kubectl apply -f monitoring/prometheus-config.yaml
    kubectl apply -f monitoring/alert-rules.yaml
    
    print_success "Kubernetes resources deployed"
}

# Function to wait for deployments to be ready
wait_for_deployments() {
    print_status "Waiting for deployments to be ready..."
    
    DEPLOYMENTS=("frontend" "value-architect" "value-committer" "value-executor" "billing-service")
    
    for DEPLOYMENT in "${DEPLOYMENTS[@]}"; do
        print_status "Waiting for $DEPLOYMENT..."
        kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s
        print_success "$DEPLOYMENT is ready"
    done
}

# Function to run smoke tests
run_smoke_tests() {
    print_status "Running smoke tests..."
    
    # Get service endpoints
    FRONTEND_URL=$(kubectl get ingress valueverse-ingress -n $NAMESPACE -o jsonpath='{.spec.rules[0].host}')
    API_URL="https://api.valueverse.com"
    
    # Test frontend
    if curl -f -s -o /dev/null -w "%{http_code}" https://$FRONTEND_URL | grep -q "200"; then
        print_success "Frontend is accessible"
    else
        print_error "Frontend is not accessible"
        exit 1
    fi
    
    # Test API endpoints
    ENDPOINTS=("/architect/health" "/committer/health" "/executor/health" "/billing/health")
    
    for ENDPOINT in "${ENDPOINTS[@]}"; do
        if curl -f -s -o /dev/null -w "%{http_code}" $API_URL$ENDPOINT | grep -q "200"; then
            print_success "API endpoint $ENDPOINT is healthy"
        else
            print_error "API endpoint $ENDPOINT is not healthy"
            exit 1
        fi
    done
    
    print_success "All smoke tests passed"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Import Grafana dashboards
    if command -v grafana-cli &> /dev/null; then
        grafana-cli admin reset-admin-password "$GRAFANA_ADMIN_PASSWORD"
        
        # Import dashboard
        curl -X POST \
            -H "Authorization: Bearer $GRAFANA_API_KEY" \
            -H "Content-Type: application/json" \
            -d @monitoring/grafana-dashboards.json \
            https://grafana.valueverse.com/api/dashboards/db
    fi
    
    print_success "Monitoring setup completed"
}

# Function to notify deployment status
notify_deployment() {
    STATUS=$1
    MESSAGE=$2
    
    # Slack notification
    if [ ! -z "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Deployment $STATUS: $MESSAGE\"}" \
            $SLACK_WEBHOOK
    fi
    
    # Email notification (using sendgrid)
    if [ ! -z "$SENDGRID_API_KEY" ]; then
        curl -X POST https://api.sendgrid.com/v3/mail/send \
            -H "Authorization: Bearer $SENDGRID_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{
                \"personalizations\": [{
                    \"to\": [{\"email\": \"devops@valueverse.com\"}]
                }],
                \"from\": {\"email\": \"deployments@valueverse.com\"},
                \"subject\": \"Deployment $STATUS\",
                \"content\": [{
                    \"type\": \"text/plain\",
                    \"value\": \"$MESSAGE\"
                }]
            }"
    fi
}

# Function to rollback deployment
rollback_deployment() {
    print_error "Deployment failed. Rolling back..."
    
    DEPLOYMENTS=("frontend" "value-architect" "value-committer" "value-executor" "billing-service")
    
    for DEPLOYMENT in "${DEPLOYMENTS[@]}"; do
        kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
    done
    
    notify_deployment "FAILED" "Deployment rolled back due to failures"
    exit 1
}

# Main deployment flow
main() {
    print_status "Starting ValueVerse Production Deployment"
    print_status "Environment: $ENVIRONMENT"
    print_status "Namespace: $NAMESPACE"
    
    # Set error trap
    trap rollback_deployment ERR
    
    # Execute deployment steps
    check_prerequisites
    load_environment
    create_secrets
    
    # Optional: Build and push images (skip if using CI/CD)
    if [ "$BUILD_IMAGES" == "true" ]; then
        build_and_push_images
    fi
    
    run_database_migrations
    deploy_kubernetes_resources
    wait_for_deployments
    run_smoke_tests
    setup_monitoring
    
    # Success notification
    print_success "🎉 Deployment completed successfully!"
    notify_deployment "SUCCESS" "ValueVerse platform deployed to production successfully"
    
    # Print summary
    echo ""
    print_status "Deployment Summary:"
    echo "  Frontend URL: https://valueverse.com"
    echo "  API URL: https://api.valueverse.com"
    echo "  Grafana: https://grafana.valueverse.com"
    echo "  Prometheus: https://prometheus.valueverse.com"
    echo ""
    print_status "Next steps:"
    echo "  1. Verify all services in Grafana dashboard"
    echo "  2. Check alert manager for any warnings"
    echo "  3. Run full integration test suite"
    echo "  4. Monitor error rates for the next hour"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_IMAGES=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            ENVIRONMENT=$1
            shift
            ;;
    esac
done

# Run main deployment
main
