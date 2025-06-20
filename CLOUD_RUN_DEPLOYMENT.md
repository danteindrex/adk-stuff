# Google Cloud Run Deployment Guide
## Uganda E-Gov WhatsApp Helpdesk

## 🚀 Quick Deployment

### Option 1: Automated Deployment (Recommended)
```bash
./deploy-to-cloudrun.sh
```

### Option 2: Manual Step-by-Step
```bash
./manual-deploy.sh
```

### Option 3: Cloud Build (CI/CD)
```bash
gcloud builds submit --config cloudbuild.yaml .
```

## 📋 Prerequisites

### 1. Install Google Cloud SDK
```bash
# Ubuntu/Debian
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# macOS
brew install google-cloud-sdk

# Windows
# Download from: https://cloud.google.com/sdk/docs/install
```

### 2. Authenticate and Setup
```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

### 3. Enable Required APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    redis.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com
```

## 🔧 Configuration

### 1. Environment Variables
Update `.env.production` with your production values:

```bash
# Copy and edit production environment
cp .env.production.template .env.production
nano .env.production
```

### 2. Create Secrets
```bash
# Create secret in Secret Manager
gcloud secrets create uganda-egov-secrets --data-file=.env.production

# Update existing secret
gcloud secrets versions add uganda-egov-secrets --data-file=.env.production
```

### 3. Configure Redis (Optional)
```bash
# Create Redis instance for session storage
gcloud redis instances create uganda-egov-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x
```

## 🏗️ Build and Deploy

### Method 1: Using Cloud Build (Recommended)
```bash
# Submit build to Cloud Build
gcloud builds submit --config cloudbuild.yaml .

# Monitor build progress
gcloud builds log --stream
```

### Method 2: Local Build + Deploy
```bash
# Build Docker image
docker build -f Dockerfile.cloudrun -t gcr.io/$GOOGLE_CLOUD_PROJECT/uganda-egov-whatsapp .

# Push to Container Registry
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/uganda-egov-whatsapp

# Deploy to Cloud Run
gcloud run deploy uganda-egov-whatsapp \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT/uganda-egov-whatsapp \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --concurrency 100 \
    --max-instances 10 \
    --min-instances 1 \
    --timeout 300 \
    --port 8080 \
    --set-env-vars ENVIRONMENT=production \
    --update-secrets /app/.env=uganda-egov-secrets:latest
```

### Method 3: Using Service YAML
```bash
# Deploy using service configuration
gcloud run services replace service.yaml --region us-central1
```

## 🔍 Monitoring and Management

### View Service Status
```bash
# Get service details
gcloud run services describe uganda-egov-whatsapp --region us-central1

# List all services
gcloud run services list
```

### View Logs
```bash
# Tail logs in real-time
gcloud run services logs tail uganda-egov-whatsapp --region us-central1

# View recent logs
gcloud run services logs read uganda-egov-whatsapp --region us-central1 --limit 100
```

### Update Service
```bash
# Update with new image
gcloud run services update uganda-egov-whatsapp \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT/uganda-egov-whatsapp:latest \
    --region us-central1

# Update environment variables
gcloud run services update uganda-egov-whatsapp \
    --set-env-vars NEW_VAR=value \
    --region us-central1

# Update resource allocation
gcloud run services update uganda-egov-whatsapp \
    --memory 4Gi \
    --cpu 4 \
    --region us-central1
```

## 🌐 Custom Domain Setup

### 1. Map Custom Domain
```bash
# Map domain to service
gcloud run domain-mappings create \
    --service uganda-egov-whatsapp \
    --domain your-domain.com \
    --region us-central1
```

### 2. Configure DNS
Add the following DNS records:
```
Type: CNAME
Name: your-domain.com
Value: ghs.googlehosted.com
```

### 3. SSL Certificate
Cloud Run automatically provisions SSL certificates for custom domains.

## 📊 Performance Optimization

### Resource Configuration
```yaml
# Optimal settings for production
resources:
  limits:
    memory: "2Gi"
    cpu: "2000m"
  requests:
    memory: "1Gi"
    cpu: "1000m"

# Scaling configuration
autoscaling.knative.dev/maxScale: "10"
autoscaling.knative.dev/minScale: "1"
```

### Concurrency Settings
```bash
# Set concurrency per instance
gcloud run services update uganda-egov-whatsapp \
    --concurrency 100 \
    --region us-central1
```

## 🔐 Security Best Practices

### 1. IAM Permissions
```bash
# Create service account for Cloud Run
gcloud iam service-accounts create uganda-egov-sa \
    --display-name "Uganda E-Gov Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member serviceAccount:uganda-egov-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
    --role roles/secretmanager.secretAccessor
```

### 2. VPC Configuration
```bash
# Create VPC connector for private resources
gcloud compute networks vpc-access connectors create uganda-egov-connector \
    --region us-central1 \
    --subnet default \
    --subnet-project $GOOGLE_CLOUD_PROJECT \
    --min-instances 2 \
    --max-instances 3
```

### 3. Security Headers
The application includes security headers:
- CORS configuration
- Rate limiting
- Input validation
- JWT authentication for admin

## 🧪 Testing Deployment

### Health Checks
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe uganda-egov-whatsapp --region us-central1 --format "value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health

# Test admin dashboard
curl $SERVICE_URL/admin

# Test WhatsApp webhook
curl -X POST $SERVICE_URL/whatsapp/webhook \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "From=+1234567890&Body=Hello"
```

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 $SERVICE_URL/health
```

## 📱 Twilio Configuration

### 1. Configure Webhook URL
1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to Messaging > Settings > WhatsApp sandbox
3. Set webhook URL: `https://your-service-url/whatsapp/webhook`
4. Set HTTP method: `POST`
5. Save configuration

### 2. Test WhatsApp Integration
1. Send "join [sandbox-keyword]" to your Twilio WhatsApp number
2. Send a test message
3. Check Cloud Run logs for processing

## 💰 Cost Optimization

### Pricing Factors
- **CPU allocation**: 2 vCPU = $0.00002400/vCPU-second
- **Memory allocation**: 2 GiB = $0.00000250/GiB-second
- **Requests**: $0.40 per million requests
- **Networking**: $0.12/GB egress

### Cost Optimization Tips
1. **Right-size resources**: Start with 1 CPU, 1 GiB memory
2. **Use min instances**: Set to 0 for development, 1 for production
3. **Optimize cold starts**: Use smaller images, faster startup
4. **Monitor usage**: Use Cloud Monitoring to track resource usage

### Estimated Monthly Costs
- **Light usage** (1000 requests/day): ~$5-10/month
- **Medium usage** (10,000 requests/day): ~$20-40/month
- **Heavy usage** (100,000 requests/day): ~$100-200/month

## 🚨 Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
gcloud builds log --stream

# Common fixes:
# - Increase build timeout
# - Use smaller base image
# - Optimize Dockerfile
```

#### 2. Deployment Failures
```bash
# Check service logs
gcloud run services logs tail uganda-egov-whatsapp --region us-central1

# Common fixes:
# - Check environment variables
# - Verify secrets are accessible
# - Ensure port 8080 is exposed
```

#### 3. Runtime Errors
```bash
# View detailed logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=uganda-egov-whatsapp" --limit 50

# Common fixes:
# - Check database connectivity
# - Verify API keys
# - Monitor memory usage
```

#### 4. Performance Issues
```bash
# Monitor metrics
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"

# Solutions:
# - Increase CPU/memory allocation
# - Optimize database queries
# - Implement caching
# - Use connection pooling
```

## 📈 Monitoring and Alerting

### Cloud Monitoring Setup
```bash
# Create alerting policy for high error rate
gcloud alpha monitoring policies create --policy-from-file=alerting-policy.yaml
```

### Key Metrics to Monitor
- **Request latency**: < 2 seconds
- **Error rate**: < 1%
- **CPU utilization**: < 80%
- **Memory utilization**: < 80%
- **Instance count**: Monitor scaling

### Logging Best Practices
- Use structured logging (JSON)
- Include correlation IDs
- Log at appropriate levels
- Monitor error patterns

## 🔄 CI/CD Pipeline

### GitHub Actions Integration
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: google-github-actions/setup-gcloud@v0
    - run: gcloud builds submit --config cloudbuild.yaml .
```

### Automated Testing
```bash
# Run tests before deployment
python -m pytest tests/
```

## 🎯 Success Metrics

### Technical KPIs
- **Uptime**: > 99.9%
- **Response time**: < 2 seconds
- **Error rate**: < 1%
- **Successful deployments**: > 95%

### Business KPIs
- **User adoption**: Monthly active users
- **Service completion**: Successful government service requests
- **User satisfaction**: Response quality ratings

## 🆘 Support and Maintenance

### Regular Maintenance Tasks
1. **Update dependencies**: Monthly security updates
2. **Monitor costs**: Weekly cost analysis
3. **Review logs**: Daily error monitoring
4. **Performance tuning**: Monthly optimization
5. **Backup verification**: Weekly backup tests

### Emergency Procedures
1. **Rollback**: `gcloud run services update --image previous-version`
2. **Scale down**: `gcloud run services update --max-instances 0`
3. **Emergency contact**: Set up alerting to admin team

## 🎉 Deployment Complete!

Your Uganda E-Gov WhatsApp Helpdesk is now deployed on Google Cloud Run and ready to serve 45+ million Ugandan citizens with government services through WhatsApp!

### Next Steps:
1. Configure Twilio webhook URL
2. Test the service with sample messages
3. Monitor logs and metrics
4. Set up alerting and monitoring
5. Plan for scaling and optimization

**Service URL**: Check deployment output for your unique URL
**Admin Dashboard**: `https://your-service-url/admin`
**Health Check**: `https://your-service-url/health`