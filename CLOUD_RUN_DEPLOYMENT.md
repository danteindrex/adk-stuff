# Google Cloud Run Deployment Guide

This guide will help you deploy the Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: You need a Google Cloud account with billing enabled
2. **Google Cloud SDK**: Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install [Docker](https://docs.docker.com/get-docker/) (optional, Cloud Build will handle this)
4. **Project Setup**: Create a Google Cloud project

## Quick Deployment

### Step 1: Set up your environment

```bash
# Set your Google Cloud Project ID
export PROJECT_ID=your-project-id-here

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $PROJECT_ID
```

### Step 2: Set up secrets

Run the secrets setup script to configure all required environment variables:

```bash
# Make the script executable (Linux/Mac)
chmod +x setup-secrets.sh

# Run the setup script
./setup-secrets.sh
```

This will prompt you to enter all required values:
- Twilio Account SID
- Twilio Auth Token  
- Twilio WhatsApp Number
- JWT Secret Key
- Encryption Key
- Google API Key
- Admin WhatsApp Group ID

### Step 3: Deploy to Cloud Run

```bash
# Make the deployment script executable (Linux/Mac)
chmod +x deploy-to-cloudrun.sh

# Run the deployment
./deploy-to-cloudrun.sh
```

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Enable Required APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com
```

### 2. Create Secrets

```bash
# Create secrets in Secret Manager
echo "your-twilio-account-sid" | gcloud secrets create twilio-account-sid --data-file=-
echo "your-twilio-auth-token" | gcloud secrets create twilio-auth-token --data-file=-
echo "your-jwt-secret" | gcloud secrets create jwt-secret-key --data-file=-
# ... repeat for other secrets
```

### 3. Build and Deploy

```bash
# Build using Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Or build and deploy in one step
gcloud run deploy uganda-egov-whatsapp \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-secrets="TWILIO_ACCOUNT_SID=twilio-account-sid:latest,TWILIO_AUTH_TOKEN=twilio-auth-token:latest"
```

## Configuration

### Environment Variables

The following environment variables are automatically set in production:

- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `PORT=8080`
- `FAQ_CACHE_ENABLED=true`
- `SESSION_TIMEOUT_MINUTES=30`

### Secrets

All sensitive data is stored in Google Cloud Secret Manager:

| Secret Name | Description |
|-------------|-------------|
| `twilio-account-sid` | Twilio Account SID |
| `twilio-auth-token` | Twilio Auth Token |
| `twilio-whatsapp-number` | Twilio WhatsApp Number |
| `twilio-webhook-verify-token` | Webhook verification token |
| `jwt-secret-key` | JWT signing key |
| `encryption-key` | Data encryption key |
| `google-api-key` | Google AI API key |
| `admin-whatsapp-group` | Admin group ID |

### Resource Allocation

- **Memory**: 2GB
- **CPU**: 2 vCPUs
- **Timeout**: 300 seconds
- **Concurrency**: 100 requests per instance
- **Max Instances**: 10
- **Min Instances**: 1

## Post-Deployment

### 1. Get Service URL

```bash
gcloud run services describe uganda-egov-whatsapp \
    --region us-central1 \
    --format "value(status.url)"
```

### 2. Configure Twilio Webhook

Update your Twilio WhatsApp webhook URL to:
```
https://your-service-url/whatsapp/webhook
```

### 3. Test the Deployment

```bash
# Health check
curl https://your-service-url/health

# System info
curl https://your-service-url/system/info
```

## Monitoring and Logging

### View Logs

```bash
# Tail logs in real-time
gcloud logs tail --service=uganda-egov-whatsapp

# View recent logs
gcloud logs read --service=uganda-egov-whatsapp --limit=50
```

### Monitoring

The application includes built-in monitoring endpoints:

- `/health` - Health check
- `/ready` - Readiness probe
- `/metrics` - Basic metrics
- `/admin/metrics` - Detailed admin metrics

## Scaling and Performance

### Auto-scaling Configuration

The service is configured to:
- Scale from 1 to 10 instances
- Handle 100 concurrent requests per instance
- Scale based on CPU and request metrics

### Performance Optimization

- Uses production-optimized Docker image
- Implements connection pooling
- Includes response caching
- Uses async/await for non-blocking operations

## Security

### Network Security

- Service runs on Google Cloud's secure infrastructure
- HTTPS enforced by default
- Private container registry

### Data Security

- All secrets stored in Secret Manager
- Encryption at rest and in transit
- Non-root container user
- Regular security updates

## Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs
   gcloud builds log --region=us-central1
   ```

2. **Service Not Starting**
   ```bash
   # Check service logs
   gcloud logs read --service=uganda-egov-whatsapp --limit=20
   ```

3. **Secret Access Issues**
   ```bash
   # Verify secret exists
   gcloud secrets describe twilio-account-sid
   
   # Check IAM permissions
   gcloud projects get-iam-policy $PROJECT_ID
   ```

### Debug Commands

```bash
# Service status
gcloud run services describe uganda-egov-whatsapp --region=us-central1

# Recent deployments
gcloud run revisions list --service=uganda-egov-whatsapp --region=us-central1

# Service configuration
gcloud run services describe uganda-egov-whatsapp --region=us-central1 --format=yaml
```

## Cost Optimization

### Pricing Factors

- **CPU allocation**: 2 vCPUs
- **Memory allocation**: 2GB
- **Request volume**: Pay per request
- **Idle time**: Minimal cost when not serving requests

### Cost Reduction Tips

1. **Optimize min instances**: Set to 0 for development
2. **Monitor usage**: Use Cloud Monitoring to track usage
3. **Right-size resources**: Adjust CPU/memory based on actual usage

## Updates and Maintenance

### Updating the Service

```bash
# Redeploy with latest code
gcloud builds submit --config cloudbuild.yaml

# Or deploy specific image
gcloud run deploy uganda-egov-whatsapp \
    --image gcr.io/$PROJECT_ID/uganda-egov-whatsapp:latest \
    --region us-central1
```

### Rolling Back

```bash
# List revisions
gcloud run revisions list --service=uganda-egov-whatsapp --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic uganda-egov-whatsapp \
    --to-revisions=REVISION_NAME=100 \
    --region=us-central1
```

## Support

For issues and questions:

1. Check the application logs
2. Review the health endpoints
3. Verify secret configuration
4. Check Google Cloud status page

## Next Steps

After successful deployment:

1. Set up monitoring alerts
2. Configure backup strategies
3. Implement CI/CD pipeline
4. Set up staging environment
5. Configure custom domain (optional)

---

**Note**: This deployment uses Google Cloud's managed services for maximum reliability and minimal maintenance overhead.