#!/bin/bash
set -e

echo "🇺🇬 Starting Uganda E-Gov WhatsApp Helpdesk..."
echo "================================================"

# Function to check if a service is available
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $service_name to be available at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name is available!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to become available after $max_attempts attempts"
    return 1
}

# Check environment variables
echo "🔍 Checking environment configuration..."

required_vars=(
    "WHATSAPP_ACCESS_TOKEN"
    "WHATSAPP_PHONE_NUMBER_ID"
    "WHATSAPP_VERIFY_TOKEN"
    "JWT_SECRET_KEY"
    "ENCRYPTION_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   - %s\n' "${missing_vars[@]}"
    echo ""
    echo "Please set these variables before starting the application."
    exit 1
fi

echo "✅ All required environment variables are set"

# Wait for Redis if REDIS_URL is set
if [ -n "$REDIS_URL" ]; then
    # Extract host and port from Redis URL
    redis_host=$(echo "$REDIS_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
    
    if [ -n "$redis_host" ] && [ -n "$redis_port" ]; then
        wait_for_service "$redis_host" "$redis_port" "Redis"
    fi
fi

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Set up browser automation directories
mkdir -p /app/browser_use_logs
mkdir -p /app/whatsapp_session

echo "🚀 Starting application with command: $*"
echo "================================================"

# Execute the main command
exec "$@"