# Single Dockerfile for Uganda E-Gov WhatsApp Helpdesk
# Includes Redis, all dependencies, and production-ready configuration
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.12-slim-bookworm as builder

# Set build environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    build-essential \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Install google-adk from GitHub (latest version)
RUN pip install git+https://github.com/google/adk-python.git@main

# Production stage
FROM python:3.12-slim-bookworm

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    REDIS_URL=redis://localhost:6379

# Install runtime dependencies including Redis
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    redis-server \
    redis-tools \
    supervisor \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Install Playwright and browsers (required for browser automation)
RUN pip install --no-cache-dir playwright==1.42.0 && \
    playwright install --with-deps chromium firefox && \
    playwright install-deps

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/tmp /app/browser_use_logs /app/whatsapp_session \
             /var/log/supervisor /var/run/redis /var/lib/redis /var/log/redis && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /var/run/redis /var/lib/redis /var/log/redis && \
    chmod 755 /var/lib/redis /var/run/redis /var/log/redis

# Create Redis configuration file with proper permissions
RUN echo "# Redis configuration for Uganda E-Gov WhatsApp Helpdesk" > /etc/redis/redis-custom.conf && \
    echo "bind 127.0.0.1" >> /etc/redis/redis-custom.conf && \
    echo "port 6379" >> /etc/redis/redis-custom.conf && \
    echo "daemonize no" >> /etc/redis/redis-custom.conf && \
    echo "supervised no" >> /etc/redis/redis-custom.conf && \
    echo "dir /var/lib/redis" >> /etc/redis/redis-custom.conf && \
    echo "logfile /var/log/redis/redis-server.log" >> /etc/redis/redis-custom.conf && \
    echo "loglevel notice" >> /etc/redis/redis-custom.conf && \
    echo "maxmemory 256mb" >> /etc/redis/redis-custom.conf && \
    echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis-custom.conf && \
    echo "save 900 1" >> /etc/redis/redis-custom.conf && \
    echo "save 300 10" >> /etc/redis/redis-custom.conf && \
    echo "save 60 10000" >> /etc/redis/redis-custom.conf && \
    echo "stop-writes-on-bgsave-error yes" >> /etc/redis/redis-custom.conf && \
    echo "rdbcompression yes" >> /etc/redis/redis-custom.conf && \
    echo "rdbchecksum yes" >> /etc/redis/redis-custom.conf && \
    echo "dbfilename dump.rdb" >> /etc/redis/redis-custom.conf && \
    echo "appendonly no" >> /etc/redis/redis-custom.conf && \
    chown appuser:appuser /etc/redis/redis-custom.conf && \
    chmod 644 /etc/redis/redis-custom.conf

# Create supervisor configuration
RUN echo "[supervisord]" > /etc/supervisor/conf.d/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "user=root" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "logfile=/var/log/supervisor/supervisord.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "pidfile=/var/run/supervisord.pid" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "childlogdir=/var/log/supervisor" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:redis]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=redis-server /etc/redis/redis-custom.conf" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "user=appuser" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/var/log/supervisor/redis.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/var/log/supervisor/redis_error.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "priority=100" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:app]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1 --access-log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "directory=/app" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "user=appuser" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile=/var/log/supervisor/app.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile=/var/log/supervisor/app_error.log" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stdout_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "stderr_logfile_maxbytes=10MB" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "priority=200" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "depends_on=redis" >> /etc/supervisor/conf.d/supervisord.conf

# Create startup script with better error handling
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'set -e' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "🇺🇬 Starting Uganda E-Gov WhatsApp Helpdesk..."' >> /app/start.sh && \
    echo 'echo "================================================"' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Check environment variables' >> /app/start.sh && \
    echo 'echo "🔍 Checking environment configuration..."' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'required_vars=("WHATSAPP_ACCESS_TOKEN" "WHATSAPP_PHONE_NUMBER_ID" "WHATSAPP_VERIFY_TOKEN" "JWT_SECRET_KEY" "ENCRYPTION_KEY")' >> /app/start.sh && \
    echo 'missing_vars=()' >> /app/start.sh && \
    echo 'for var in "${required_vars[@]}"; do' >> /app/start.sh && \
    echo '    if [ -z "${!var}" ]; then' >> /app/start.sh && \
    echo '        missing_vars+=("$var")' >> /app/start.sh && \
    echo '    fi' >> /app/start.sh && \
    echo 'done' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'if [ ${#missing_vars[@]} -ne 0 ]; then' >> /app/start.sh && \
    echo '    echo "❌ Missing required environment variables:"' >> /app/start.sh && \
    echo '    printf "   - %s\n" "${missing_vars[@]}"' >> /app/start.sh && \
    echo '    echo ""' >> /app/start.sh && \
    echo '    echo "Please set these variables before starting the application."' >> /app/start.sh && \
    echo '    exit 1' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "✅ All required environment variables are set"' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Create log directories' >> /app/start.sh && \
    echo 'mkdir -p /app/logs /app/tmp /app/browser_use_logs /app/whatsapp_session' >> /app/start.sh && \
    echo 'mkdir -p /var/log/supervisor /var/log/redis' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Test Redis configuration' >> /app/start.sh && \
    echo 'echo "🧪 Testing Redis configuration..."' >> /app/start.sh && \
    echo 'if redis-server /etc/redis/redis-custom.conf --test-config 2>/dev/null; then' >> /app/start.sh && \
    echo '    echo "✅ Redis configuration is valid"' >> /app/start.sh && \
    echo 'else' >> /app/start.sh && \
    echo '    echo "⚠️  Redis configuration test failed, but continuing..."' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Start supervisor to manage both Redis and the app' >> /app/start.sh && \
    echo 'echo "🚀 Starting services with supervisor..."' >> /app/start.sh && \
    echo 'echo "================================================"' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf' >> /app/start.sh && \
    chmod +x /app/start.sh

# Create entrypoint script for compatibility
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'set -e' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo 'echo "🇺🇬 Starting Uganda E-Gov WhatsApp Helpdesk..."' >> /app/entrypoint.sh && \
    echo 'echo "================================================"' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Check if Redis is needed' >> /app/entrypoint.sh && \
    echo 'if [[ "$REDIS_URL" == *"localhost"* ]] || [[ "$REDIS_URL" == *"127.0.0.1"* ]]; then' >> /app/entrypoint.sh && \
    echo '    echo "🔧 Local Redis required - starting Redis server..."' >> /app/entrypoint.sh && \
    echo '    redis-server /etc/redis/redis-custom.conf --daemonize yes' >> /app/entrypoint.sh && \
    echo '    sleep 3' >> /app/entrypoint.sh && \
    echo '    echo "✅ Redis started"' >> /app/entrypoint.sh && \
    echo 'fi' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Create necessary directories' >> /app/entrypoint.sh && \
    echo 'mkdir -p /app/logs /app/tmp /app/browser_use_logs /app/whatsapp_session' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Execute the main command' >> /app/entrypoint.sh && \
    echo 'exec "$@"' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose application port
EXPOSE 8080

# Add comprehensive health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Labels for metadata
LABEL maintainer="Uganda E-Gov Team" \
      description="Uganda E-Government WhatsApp Helpdesk - Complete Setup with Redis" \
      version="2.0.0" \
      org.opencontainers.image.title="Uganda E-Gov WhatsApp Helpdesk" \
      org.opencontainers.image.description="Multi-Agent AI System with Redis and all dependencies included" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.vendor="Uganda E-Gov Team" \
      org.opencontainers.image.licenses="MIT"

# Use the startup script as the default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]