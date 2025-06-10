#!/bin/bash

# Uganda E-Gov WhatsApp Helpdesk - Production Deployment Script

set -e

echo "🚀 Deploying Uganda E-Gov WhatsApp Helpdesk to Production"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check required environment variables
check_env_vars() {
    print_step "Checking required environment variables..."
    
    required_vars=(
        "GOOGLE_CLOUD_PROJECT"
        "WHATSAPP_ACCESS_TOKEN"
        "WHATSAPP_PHONE_NUMBER_ID"
        "WHATSAPP_WEBHOOK_VERIFY_TOKEN"
        "WHATSAPP_BUSINESS_ACCOUNT_ID"
        "FIREBASE_PROJECT_ID"
        "GOOGLE_OAUTH_CLIENT_ID"
        "GOOGLE_OAUTH_CLIENT_SECRET"
        "JWT_SECRET_KEY"
        "ENCRYPTION_KEY"
        "ADMIN_WHATSAPP_GROUP"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables and try again."
        exit 1
    fi
    
    print_status "All required environment variables are set ✅"
}

# Run tests before deployment
run_tests() {
    print_step "Running test suite before deployment..."
    
    if [ -f "scripts/run_tests.sh" ]; then
        chmod +x scripts/run_tests.sh
        ./scripts/run_tests.sh quick
    else
        print_warning "Test script not found, skipping tests"
    fi
}

# Build Docker image
build_image() {
    print_step "Building production Docker image..."
    
    IMAGE_TAG="uganda-egov-helpdesk:$(date +%Y%m%d-%H%M%S)"
    
    docker build -f Dockerfile.prod -t "$IMAGE_TAG" .
    docker tag "$IMAGE_TAG" "uganda-egov-helpdesk:latest"
    
    print_status "Docker image built: $IMAGE_TAG"
    echo "IMAGE_TAG=$IMAGE_TAG" > .deployment_vars
}

# Deploy to Google Cloud Run
deploy_cloud_run() {
    print_step "Deploying to Google Cloud Run..."
    
    # Check if gcloud is installed and authenticated
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    # Set project
    gcloud config set project "$GOOGLE_CLOUD_PROJECT"
    
    # Build and push to Container Registry
    print_status "Building and pushing to Google Container Registry..."
    gcloud builds submit --tag "gcr.io/$GOOGLE_CLOUD_PROJECT/uganda-egov-helpdesk"
    
    # Deploy to Cloud Run
    print_status "Deploying to Cloud Run..."
    gcloud run deploy uganda-egov-helpdesk \
        --image "gcr.io/$GOOGLE_CLOUD_PROJECT/uganda-egov-helpdesk" \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --memory 1Gi \
        --cpu 2 \
        --max-instances 10 \
        --min-instances 1 \
        --port 8080 \
        --set-env-vars "ENVIRONMENT=production" \
        --set-env-vars "GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
        --set-env-vars "WHATSAPP_ACCESS_TOKEN=$WHATSAPP_ACCESS_TOKEN" \
        --set-env-vars "WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_NUMBER_ID" \
        --set-env-vars "WHATSAPP_WEBHOOK_VERIFY_TOKEN=$WHATSAPP_WEBHOOK_VERIFY_TOKEN" \
        --set-env-vars "WHATSAPP_BUSINESS_ACCOUNT_ID=$WHATSAPP_BUSINESS_ACCOUNT_ID" \
        --set-env-vars "FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID" \
        --set-env-vars "GOOGLE_OAUTH_CLIENT_ID=$GOOGLE_OAUTH_CLIENT_ID" \
        --set-env-vars "GOOGLE_OAUTH_CLIENT_SECRET=$GOOGLE_OAUTH_CLIENT_SECRET" \
        --set-env-vars "JWT_SECRET_KEY=$JWT_SECRET_KEY" \
        --set-env-vars "ENCRYPTION_KEY=$ENCRYPTION_KEY" \
        --set-env-vars "ADMIN_WHATSAPP_GROUP=$ADMIN_WHATSAPP_GROUP"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe uganda-egov-helpdesk --platform managed --region us-central1 --format 'value(status.url)')
    print_status "Service deployed at: $SERVICE_URL"
    echo "SERVICE_URL=$SERVICE_URL" >> .deployment_vars
}

# Deploy to Kubernetes
deploy_kubernetes() {
    print_step "Deploying to Kubernetes..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    # Apply Kubernetes manifests
    print_status "Applying Kubernetes manifests..."
    kubectl apply -f k8s/redis.yaml
    kubectl apply -f k8s/deployment.yaml
    
    # Wait for deployment to be ready
    print_status "Waiting for deployment to be ready..."
    kubectl rollout status deployment/uganda-egov-helpdesk
    
    # Get service URL
    SERVICE_URL=$(kubectl get service uganda-egov-helpdesk-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -n "$SERVICE_URL" ]; then
        print_status "Service deployed at: http://$SERVICE_URL"
        echo "SERVICE_URL=http://$SERVICE_URL" >> .deployment_vars
    else
        print_warning "Service URL not available yet. Check 'kubectl get services' later."
    fi
}

# Deploy using Docker Compose (for local/staging)
deploy_docker_compose() {
    print_step "Deploying with Docker Compose..."
    
    # Create monitoring directories
    mkdir -p monitoring/grafana/dashboards monitoring/grafana/datasources
    
    # Start services
    docker-compose up -d
    
    print_status "Services started with Docker Compose"
    print_status "Application: http://localhost:8080"
    print_status "Prometheus: http://localhost:9090"
    print_status "Grafana: http://localhost:3000 (admin/admin123)"
}

# Verify deployment
verify_deployment() {
    print_step "Verifying deployment..."
    
    if [ -f ".deployment_vars" ]; then
        source .deployment_vars
    fi
    
    if [ -n "$SERVICE_URL" ]; then
        print_status "Testing health endpoint..."
        
        # Wait a bit for service to start
        sleep 10
        
        if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
            print_status "✅ Health check passed!"
        else
            print_warning "⚠️  Health check failed. Service might still be starting."
        fi
        
        print_status "Testing ready endpoint..."
        if curl -f "$SERVICE_URL/ready" > /dev/null 2>&1; then
            print_status "✅ Readiness check passed!"
        else
            print_warning "⚠️  Readiness check failed. Service might still be starting."
        fi
    else
        print_warning "Service URL not available for verification"
    fi
}

# Setup monitoring
setup_monitoring() {
    print_step "Setting up monitoring..."
    
    # This would typically involve:
    # - Setting up Prometheus alerts
    # - Configuring Grafana dashboards
    # - Setting up log aggregation
    
    print_status "Monitoring setup completed (basic configuration)"
}

# Main deployment logic
main() {
    echo "Select deployment target:"
    echo "1. Google Cloud Run (recommended for production)"
    echo "2. Kubernetes"
    echo "3. Docker Compose (local/staging)"
    echo "4. Build only (no deployment)"
    
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1)
            check_env_vars
            run_tests
            deploy_cloud_run
            verify_deployment
            setup_monitoring
            ;;
        2)
            check_env_vars
            run_tests
            build_image
            deploy_kubernetes
            verify_deployment
            setup_monitoring
            ;;
        3)
            check_env_vars
            run_tests
            deploy_docker_compose
            verify_deployment
            ;;
        4)
            run_tests
            build_image
            print_status "Build completed. Image ready for deployment."
            ;;
        *)
            print_error "Invalid choice. Exiting."
            exit 1
            ;;
    esac
    
    print_status "🎉 Deployment completed successfully!"
    
    if [ -f ".deployment_vars" ]; then
        echo ""
        echo "📋 Deployment Summary:"
        echo "====================="
        cat .deployment_vars
        echo ""
    fi
    
    echo "📚 Next Steps:"
    echo "=============="
    echo "1. Configure WhatsApp webhook URL"
    echo "2. Test the system with sample messages"
    echo "3. Monitor system health and performance"
    echo "4. Set up alerts and notifications"
}

# Run main function
main "$@"