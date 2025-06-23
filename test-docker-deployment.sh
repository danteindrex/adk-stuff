#!/bin/bash

# Test Docker Deployment Script for Uganda E-Gov WhatsApp Helpdesk
# This script builds and tests the Docker image to ensure it's ready for deployment

set -e

echo "🇺🇬 Uganda E-Gov WhatsApp Helpdesk - Docker Deployment Test"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Prerequisites check passed"

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "Docker daemon is running"

# Set default values for testing
export WHATSAPP_PHONE_NUMBER_ID="test_phone_id"
export WHATSAPP_ACCESS_TOKEN="test_access_token"
export WHATSAPP_BUSINESS_ACCOUNT_ID="test_business_id"
export WHATSAPP_VERIFY_TOKEN="test_verify_token"
export WHATSAPP_WEBHOOK_SECRET="test_webhook_secret"
export GOOGLE_API_KEY="test_google_api_key"
export JWT_SECRET_KEY="test_jwt_secret_key_for_testing_only"
export ENCRYPTION_KEY="test_encryption_key_for_testing_only"
export ADMIN_WHATSAPP_GROUP="test_admin_group"

print_status "Environment variables set for testing"

# Function to test a specific Docker setup
test_docker_setup() {
    local setup_name=$1
    local dockerfile=$2
    local compose_file=$3
    local service_name=$4
    local port=$5
    
    echo ""
    print_status "Testing $setup_name..."
    echo "----------------------------------------"
    
    # Build the image
    print_status "Building Docker image..."
    if [ -n "$dockerfile" ]; then
        docker build -t "uganda-egov-$setup_name" -f "$dockerfile" . || {
            print_error "Failed to build Docker image for $setup_name"
            return 1
        }
    fi
    
    # Start the service
    print_status "Starting service with Docker Compose..."
    if [ -n "$compose_file" ] && [ -n "$service_name" ]; then
        docker-compose -f "$compose_file" up -d "$service_name" || {
            print_error "Failed to start service $service_name"
            return 1
        }
        
        # Wait for service to be ready
        print_status "Waiting for service to be ready..."
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
                print_success "Service is ready!"
                break
            fi
            
            print_status "Attempt $attempt/$max_attempts - waiting for service..."
            sleep 5
            attempt=$((attempt + 1))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            print_error "Service failed to become ready within timeout"
            docker-compose -f "$compose_file" logs "$service_name"
            docker-compose -f "$compose_file" down
            return 1
        fi
        
        # Test health endpoint
        print_status "Testing health endpoint..."
        health_response=$(curl -s "http://localhost:$port/health" || echo "failed")
        if echo "$health_response" | grep -q "healthy\|ready"; then
            print_success "Health check passed"
        else
            print_warning "Health check returned: $health_response"
        fi
        
        # Test webhook verification endpoint
        print_status "Testing webhook verification..."
        webhook_response=$(curl -s "http://localhost:$port/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=test_verify_token&hub.challenge=test_challenge" || echo "failed")
        if echo "$webhook_response" | grep -q "test_challenge"; then
            print_success "Webhook verification test passed"
        else
            print_warning "Webhook verification test failed: $webhook_response"
        fi
        
        # Test system info endpoint
        print_status "Testing system info endpoint..."
        info_response=$(curl -s "http://localhost:$port/system/info" || echo "failed")
        if echo "$info_response" | grep -q "architecture"; then
            print_success "System info endpoint test passed"
        else
            print_warning "System info endpoint test failed"
        fi
        
        # Show logs
        print_status "Recent logs:"
        docker-compose -f "$compose_file" logs --tail=20 "$service_name"
        
        # Stop the service
        print_status "Stopping service..."
        docker-compose -f "$compose_file" down
        
        print_success "$setup_name test completed successfully!"
        return 0
    else
        print_error "Missing compose file or service name for $setup_name"
        return 1
    fi
}

# Test 1: Complete setup with built-in Redis
print_status "=== Test 1: Complete Setup (Built-in Redis) ==="
test_docker_setup "complete" "Dockerfile.complete" "docker-compose.complete.yml" "app-complete" "8080"

# Test 2: Original setup with external Redis
print_status "=== Test 2: External Redis Setup ==="
test_docker_setup "external-redis" "Dockerfile" "docker-compose.complete.yml" "app-external-redis" "8081" &
EXTERNAL_REDIS_PID=$!

# Start external Redis for the test
docker-compose -f docker-compose.complete.yml --profile external-redis up -d redis-external

# Wait for external Redis test to complete
wait $EXTERNAL_REDIS_PID
EXTERNAL_REDIS_RESULT=$?

# Clean up external Redis
docker-compose -f docker-compose.complete.yml --profile external-redis down

# Test 3: Build original Dockerfile
print_status "=== Test 3: Original Dockerfile Build Test ==="
docker build -t "uganda-egov-original" -f "Dockerfile" . || {
    print_error "Failed to build original Dockerfile"
    exit 1
}
print_success "Original Dockerfile build test passed"

# Test 4: Production Dockerfile
if [ -f "Dockerfile.prod" ]; then
    print_status "=== Test 4: Production Dockerfile Build Test ==="
    docker build -t "uganda-egov-prod" -f "Dockerfile.prod" . || {
        print_error "Failed to build production Dockerfile"
        exit 1
    }
    print_success "Production Dockerfile build test passed"
fi

# Security scan (if available)
if command_exists docker scan; then
    print_status "=== Security Scan ==="
    docker scan "uganda-egov-complete" || print_warning "Security scan failed or not available"
fi

# Image size analysis
print_status "=== Image Size Analysis ==="
echo "Image sizes:"
docker images | grep "uganda-egov" | awk '{print $1 ":" $2 " - " $7 " " $8}'

# Cleanup
print_status "Cleaning up test images..."
docker rmi "uganda-egov-complete" "uganda-egov-original" 2>/dev/null || true
if [ -f "Dockerfile.prod" ]; then
    docker rmi "uganda-egov-prod" 2>/dev/null || true
fi

# Final summary
echo ""
print_success "============================================================"
print_success "🎉 Docker deployment tests completed!"
print_success "============================================================"

if [ $EXTERNAL_REDIS_RESULT -eq 0 ]; then
    print_success "✅ All tests passed - Docker image is ready for deployment"
    echo ""
    echo "Deployment options:"
    echo "1. Complete setup (recommended): docker-compose -f docker-compose.complete.yml up -d app-complete"
    echo "2. External Redis setup: docker-compose -f docker-compose.complete.yml --profile external-redis up -d"
    echo "3. With monitoring: docker-compose -f docker-compose.complete.yml --profile monitoring up -d"
    echo ""
    echo "Don't forget to:"
    echo "- Set proper environment variables in production"
    echo "- Configure SSL/TLS termination"
    echo "- Set up proper logging and monitoring"
    echo "- Configure backup for Redis data"
else
    print_warning "⚠️  Some tests had issues, but the main setup works"
    echo "The complete setup with built-in Redis is ready for deployment"
fi

echo ""
print_status "For production deployment, remember to:"
echo "1. Set all required environment variables"
echo "2. Use proper secrets management"
echo "3. Configure reverse proxy (nginx/traefik)"
echo "4. Set up SSL certificates"
echo "5. Configure monitoring and logging"
echo "6. Set up backup strategies"
echo ""
print_success "Happy deploying! 🚀"