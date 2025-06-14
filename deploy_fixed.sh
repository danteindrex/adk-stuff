#!/bin/bash
# Deployment script for Uganda E-Gov WhatsApp Helpdesk
# Fixed version with internal MCP tools

set -e

echo "🇺🇬 Uganda E-Gov WhatsApp Helpdesk - Deployment Script"
echo "======================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with required environment variables"
    echo "You can copy from .env.production.template"
    exit 1
fi

# Check required environment variables
echo "📋 Checking environment variables..."
required_vars=("TWILIO_ACCOUNT_SID" "TWILIO_AUTH_TOKEN" "TWILIO_WHATSAPP_NUMBER" "JWT_SECRET_KEY" "ENCRYPTION_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '%s\n' "${missing_vars[@]}"
    echo "Please set these variables in your .env file"
    exit 1
fi

echo "✅ All required environment variables are set"

# Check if Docker is running
echo "🐳 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        echo "❌ docker-compose or 'docker compose' not found"
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "✅ Docker Compose is available"

# Build and start services
echo "🔨 Building and starting services..."
$COMPOSE_CMD down --remove-orphans
$COMPOSE_CMD build --no-cache
$COMPOSE_CMD up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

# Check Redis
if $COMPOSE_CMD exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    $COMPOSE_CMD logs redis
    exit 1
fi

# Check main application
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Application is healthy"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts - Waiting for application to be ready..."
        sleep 5
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Application health check failed after $max_attempts attempts"
    echo "📋 Application logs:"
    $COMPOSE_CMD logs app
    exit 1
fi

# Test webhook endpoint
echo "🧪 Testing webhook endpoint..."
webhook_response=$(curl -s -X POST http://localhost:8080/whatsapp/webhook \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "Body=Hello&From=whatsapp:+256701234567" \
    --write-out "%{http_code}")

if [[ $webhook_response == *"200"* ]]; then
    echo "✅ Webhook endpoint is working"
else
    echo "❌ Webhook endpoint test failed"
    echo "Response: $webhook_response"
fi

# Show deployment information
echo ""
echo "🎉 Deployment completed successfully!"
echo "======================================="
echo ""
echo "📊 Service Status:"
$COMPOSE_CMD ps

echo ""
echo "🌐 Available Endpoints:"
echo "  • Health Check:     http://localhost:8080/health"
echo "  • WhatsApp Webhook: http://localhost:8080/whatsapp/webhook"
echo "  • Admin Dashboard:  http://localhost:8080/admin/dashboard"
echo "  • System Info:      http://localhost:8080/system/info"
echo "  • Metrics:          http://localhost:8080/metrics"
echo ""
echo "📊 Monitoring:"
echo "  • Prometheus:       http://localhost:9090"
echo "  • Grafana:          http://localhost:3000 (admin/admin123)"
echo ""
echo "🔧 Management Commands:"
echo "  • View logs:        $COMPOSE_CMD logs -f app"
echo "  • Stop services:    $COMPOSE_CMD down"
echo "  • Restart:          $COMPOSE_CMD restart app"
echo ""
echo "📱 WhatsApp Configuration:"
echo "  Set your webhook URL to: https://your-domain.com/whatsapp/webhook"
echo ""
echo "✅ Uganda E-Gov WhatsApp Helpdesk is ready to serve citizens!"