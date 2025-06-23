# Uganda E-Gov WhatsApp Helpdesk - Docker Deployment Guide

This guide provides comprehensive instructions for deploying the Uganda E-Gov WhatsApp Helpdesk using Docker with Redis and all necessary dependencies.

## 🏗️ Architecture Overview

The project supports multiple deployment configurations:

1. **Complete Setup** (Recommended): Single container with built-in Redis
2. **External Redis Setup**: Separate Redis container
3. **Production Setup**: Optimized for production environments
4. **Monitoring Setup**: Includes Prometheus and Grafana

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space
- Internet connection for downloading dependencies

## 🚀 Quick Start

### Option 1: Complete Setup (Recommended)

This is the easiest way to get started with everything included in one container:

```bash
# 1. Clone the repository
git clone <repository-url>
cd adk-stuff

# 2. Set environment variables
cp .env.example .env
# Edit .env with your actual values

# 3. Start the complete setup
docker-compose -f docker-compose.complete.yml up -d app-complete

# 4. Check status
docker-compose -f docker-compose.complete.yml ps
docker-compose -f docker-compose.complete.yml logs app-complete
```

### Option 2: External Redis Setup

For production environments where you want separate Redis management:

```bash
# Start with external Redis
docker-compose -f docker-compose.complete.yml --profile external-redis up -d

# Check status
docker-compose -f docker-compose.complete.yml --profile external-redis ps
```

### Option 3: With Monitoring

Include Prometheus and Grafana for monitoring:

```bash
# Start with monitoring
docker-compose -f docker-compose.complete.yml --profile monitoring up -d app-complete prometheus grafana

# Access Grafana at http://localhost:3000 (admin/admin123)
# Access Prometheus at http://localhost:9090
```

## 🔧 Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# WhatsApp Business API Configuration
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_whatsapp_business_account_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret

# Google API Configuration
GOOGLE_API_KEY=your_google_api_key

# Security Configuration
JWT_SECRET_KEY=your_jwt_secret_key_change_this_in_production
ENCRYPTION_KEY=your_encryption_key_change_this_in_production

# Optional: Admin Configuration
ADMIN_WHATSAPP_GROUP=admin_group_id

# Optional: Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Optional: Monitoring
GRAFANA_PASSWORD=your_grafana_password
```

### Application Settings

The following settings can be customized via environment variables:

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS=1000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Browser Automation
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=300
BROWSER_MAX_RETRIES=3
BROWSER_USE_MODEL=gemini-2.0-flash-exp
```

## 🐳 Docker Images

### Available Dockerfiles

1. **Dockerfile**: Original production-ready image
2. **Dockerfile.complete**: Complete setup with built-in Redis
3. **Dockerfile.prod**: Optimized production image

### Building Images Manually

```bash
# Build complete image
docker build -t uganda-egov-complete -f Dockerfile.complete .

# Build production image
docker build -t uganda-egov-prod -f Dockerfile.prod .

# Build original image
docker build -t uganda-egov-original -f Dockerfile .
```

## 🧪 Testing the Deployment

Use the provided test script to verify your deployment:

```bash
# Run comprehensive deployment tests
./test-docker-deployment.sh
```

This script will:
- Build all Docker images
- Test different deployment configurations
- Verify health endpoints
- Check webhook functionality
- Perform security scans (if available)
- Provide deployment recommendations

## 📊 Monitoring and Logging

### Health Checks

The application provides several health check endpoints:

- `GET /health` - Application health status
- `GET /ready` - Kubernetes readiness probe
- `GET /metrics` - Basic metrics
- `GET /system/info` - System architecture information

### Viewing Logs

```bash
# View application logs
docker-compose -f docker-compose.complete.yml logs app-complete

# Follow logs in real-time
docker-compose -f docker-compose.complete.yml logs -f app-complete

# View Redis logs (if using external Redis)
docker-compose -f docker-compose.complete.yml logs redis-external
```

### Monitoring with Grafana

If you started with monitoring enabled:

1. Access Grafana at http://localhost:3000
2. Login with admin/admin123 (or your configured password)
3. Import dashboards from `monitoring/grafana/dashboards/`
4. Configure data sources pointing to Prometheus

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Change default passwords and secrets
- [ ] Use proper SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable Docker security options
- [ ] Use non-root user (already configured)
- [ ] Regularly update base images
- [ ] Monitor for security vulnerabilities
- [ ] Implement proper backup strategies

### Network Security

```bash
# Create custom network for better isolation
docker network create uganda-egov-network

# Use the network in docker-compose
networks:
  default:
    external:
      name: uganda-egov-network
```

## 🚀 Production Deployment

### Cloud Deployment Options

#### Google Cloud Run

```bash
# Build and push to Google Container Registry
docker build -t gcr.io/YOUR_PROJECT/uganda-egov -f Dockerfile.complete .
docker push gcr.io/YOUR_PROJECT/uganda-egov

# Deploy to Cloud Run
gcloud run deploy uganda-egov \
  --image gcr.io/YOUR_PROJECT/uganda-egov \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --port 8080
```

#### AWS ECS/Fargate

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t uganda-egov -f Dockerfile.complete .
docker tag uganda-egov:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/uganda-egov:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/uganda-egov:latest
```

#### Azure Container Instances

```bash
# Build and push to ACR
az acr build --registry YOUR_REGISTRY --image uganda-egov:latest -f Dockerfile.complete .

# Deploy to ACI
az container create \
  --resource-group YOUR_RG \
  --name uganda-egov \
  --image YOUR_REGISTRY.azurecr.io/uganda-egov:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8080
```

### Kubernetes Deployment

Example Kubernetes manifests are available in the `k8s/` directory:

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

## 🔧 Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker-compose -f docker-compose.complete.yml logs app-complete

# Check container status
docker-compose -f docker-compose.complete.yml ps

# Inspect container
docker inspect uganda-egov-complete
```

#### Redis Connection Issues

```bash
# Test Redis connection
docker exec -it uganda-egov-complete redis-cli ping

# Check Redis logs
docker-compose -f docker-compose.complete.yml logs redis-external
```

#### Memory Issues

```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

#### Browser Automation Issues

```bash
# Check Playwright installation
docker exec -it uganda-egov-complete python -c "from playwright.sync_api import sync_playwright; print('OK')"

# Check browser installation
docker exec -it uganda-egov-complete playwright install --dry-run
```

### Performance Tuning

#### Resource Optimization

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 3G
    reservations:
      cpus: '0.5'
      memory: 1G
```

#### Redis Optimization

```bash
# Redis configuration for production
redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --appendonly yes
```

## 📚 Additional Resources

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Google ADK Documentation](https://github.com/google/adk-python)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs app-complete`
2. Verify environment variables are set correctly
3. Ensure all required services are running
4. Check the troubleshooting section above
5. Review the health check endpoints

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy Deploying! 🇺🇬🚀**