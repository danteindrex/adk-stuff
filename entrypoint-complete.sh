 #!/bin/bash
set -e

echo "🇺🇬 Starting Uganda E-Gov WhatsApp Helpdesk (Complete Setup)..."
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

# Function to check Redis with redis-cli
wait_for_redis() {
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for Redis to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if redis-cli -h 127.0.0.1 -p 6379 ping > /dev/null 2>&1; then
            echo "✅ Redis is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - Redis not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Redis failed to become available after $max_attempts attempts"
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

# Check if Redis is running locally (for complete setup)
if [ "$REDIS_URL" = "redis://localhost:6379" ] || [ "$REDIS_URL" = "redis://127.0.0.1:6379" ]; then
    echo "🔍 Checking local Redis setup..."
    
    # Check if Redis is already running
    if ! redis-cli -h 127.0.0.1 -p 6379 ping > /dev/null 2>&1; then
        echo "⚠️  Redis not running locally, attempting to start..."
        
        # Try to start Redis in the background
        redis-server /etc/redis/redis.conf &
        REDIS_PID=$!
        
        # Wait for Redis to start
        wait_for_redis
        
        echo "✅ Redis started successfully (PID: $REDIS_PID)"
    else
        echo "✅ Redis is already running"
    fi
else
    # Wait for external Redis if REDIS_URL is set to external service
    if [ -n "$REDIS_URL" ]; then
        # Extract host and port from Redis URL
        redis_host=$(echo "$REDIS_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
        
        if [ -n "$redis_host" ] && [ -n "$redis_port" ]; then
            wait_for_service "$redis_host" "$redis_port" "Redis"
        fi
    fi
fi

# Create necessary directories
echo "📁 Setting up directories..."
mkdir -p /app/logs
mkdir -p /app/tmp
mkdir -p /app/browser_use_logs
mkdir -p /app/whatsapp_session

# Set proper permissions
chown -R appuser:appuser /app/logs /app/tmp /app/browser_use_logs /app/whatsapp_session 2>/dev/null || true

# Test Redis connection
echo "🧪 Testing Redis connection..."
if redis-cli -h 127.0.0.1 -p 6379 ping > /dev/null 2>&1; then
    echo "✅ Redis connection test successful"
    
    # Set a test key to verify write access
    if redis-cli -h 127.0.0.1 -p 6379 set test_key "test_value" > /dev/null 2>&1; then
        echo "✅ Redis write test successful"
        redis-cli -h 127.0.0.1 -p 6379 del test_key > /dev/null 2>&1
    else
        echo "⚠️  Redis write test failed"
    fi
else
    echo "❌ Redis connection test failed"
    echo "   The application will continue but session persistence may not work"
fi

# Check Python dependencies
echo "🐍 Checking Python environment..."
python -c "import fastapi, uvicorn, redis, playwright; print('✅ Core dependencies available')" || {
    echo "❌ Missing critical Python dependencies"
    exit 1
}

# Check Playwright browsers
echo "🎭 Checking Playwright browsers..."
if python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright available')" 2>/dev/null; then
    echo "✅ Playwright is ready"
else
    echo "⚠️  Playwright may not be properly installed"
fi

echo "🚀 Starting application with command: $*"
echo "================================================"

# Execute the main command
exec "$@"