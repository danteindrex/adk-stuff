# Multi-stage build for Uganda E-Gov WhatsApp Helpdesk
# Optimized for production deployment with WhatsApp Business API integration

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
    LOG_LEVEL=INFO

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
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

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/tmp /app/browser_use_logs /app/whatsapp_session && \
    chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command - run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--access-log"]

# Labels for metadata
LABEL maintainer="Uganda E-Gov Team" \
      description="Uganda E-Government WhatsApp Helpdesk - Multi-Agent AI System" \
      version="2.0.0" \
      org.opencontainers.image.title="Uganda E-Gov WhatsApp Helpdesk" \
      org.opencontainers.image.description="Multi-Agent AI System for Government Service Access via WhatsApp Business API" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.vendor="Uganda E-Gov Team" \
      org.opencontainers.image.licenses="MIT"