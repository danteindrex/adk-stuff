# 🚀 Deployment and Testing Guide

This guide covers how to deploy the Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run and test it thoroughly.

## 📋 Prerequisites

### Required Accounts and Services
- Google Cloud Platform account with billing enabled
- WhatsApp Business API access (Meta Business account)
- Firebase project
- Domain name (optional, for custom webhook URLs)

### Local Development Environment
- Python 3.9 or higher
- Docker and Docker Compose
- Google Cloud SDK (`gcloud` CLI)
- Git

## 🔧 Initial Setup

### 1. Google Cloud Project Setup

```bash
# Create a new project (or use existing)
gcloud projects create uganda-egov-helpdesk --name="Uganda E-Gov Helpdesk"

# Set the project as default
gcloud config set project uganda-egov-helpdesk

# Enable billing (required for Cloud Run)
gcloud billing projects link uganda-egov-helpdesk --billing-account=YOUR_BILLING_ACCOUNT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    identitytoolkit.googleapis.com \
    firebase.googleapis.com \
    firestore.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    translate.googleapis.com
```

### 2. Firebase Project Setup

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in your project directory
firebase init

# Select the following features:
# - Firestore
# - Authentication
# - Hosting (optional)

# Choose your Google Cloud project
# Accept default Firestore rules and indexes
# Choose default authentication settings
```

### 3. Service Account Creation

```bash
# Create service account
gcloud iam service-accounts create uganda-egov-service \
    --display-name="Uganda E-Gov Service Account" \
    --description="Service account for Uganda E-Gov WhatsApp Helpdesk"

# Assign necessary roles
gcloud projects add-iam-policy-binding uganda-egov-helpdesk \
    --member="serviceAccount:uganda-egov-service@uganda-egov-helpdesk.iam.gserviceaccount.com" \
    --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding uganda-egov-helpdesk \
    --member="serviceAccount:uganda-egov-service@uganda-egov-helpdesk.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding uganda-egov-helpdesk \
    --member="serviceAccount:uganda-egov-service@uganda-egov-helpdesk.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding uganda-egov-helpdesk \
    --member="serviceAccount:uganda-egov-service@uganda-egov-helpdesk.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"

# Create and download service account key
gcloud iam service-accounts keys create service-account.json \
    --iam-account=uganda-egov-service@uganda-egov-helpdesk.iam.gserviceaccount.com
```

### 4. WhatsApp Business API Setup

1. **Create Meta Business Account**:
   - Go to [Meta Business](https://business.facebook.com/)
   - Create a business account
   - Verify your business

2. **Set up WhatsApp Business API**:
   - Go to [Meta for Developers](https://developers.facebook.com/)
   - Create a new app
   - Add WhatsApp product
   - Get your access token and phone number ID

3. **Configure Webhook** (will be done after deployment):
   - Webhook URL: `https://your-service-url.run.app/whatsapp/webhook`
   - Verify token: Generate a secure random string

## 🏗️ Local Development

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# Google Cloud Authentication
GOOGLE_OAUTH_CLIENT_ID=your_oauth_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_oauth_client_secret
FIREBASE_PROJECT_ID=uganda-egov-helpdesk
GOOGLE_CLOUD_PROJECT=uganda-egov-helpdesk
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters
ENCRYPTION_KEY=your-32-character-encryption-key-here
ADMIN_WHATSAPP_GROUP=your_admin_group_id

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
PORT=8080

# Optional Services
REDIS_URL=redis://localhost:6379
```

### 2. Local Installation and Testing

```bash
# Clone the repository
git clone <your-repository-url>
cd adk-stuff

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### 3. Local Testing

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test system info
curl http://localhost:8080/system/info

# Test WhatsApp webhook verification
curl -X GET "http://localhost:8080/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=your_webhook_verify_token"
```

## 🚀 Cloud Deployment

### 1. Prepare for Deployment

Update the `deploy.sh` script with your project details:

```bash
#!/bin/bash

# Configuration
PROJECT_ID="uganda-egov-helpdesk"
SERVICE_NAME="uganda-egov-helpdesk"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run..."

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to Google Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 100 \
    --max-instances 10 \
    --set-env-vars "ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --service-account "uganda-egov-service@$PROJECT_ID.iam.gserviceaccount.com"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Admin Dashboard: $SERVICE_URL/static/admin.html"
echo "🔗 Health Check: $SERVICE_URL/health"

echo "📝 Next steps:"
echo "1. Configure WhatsApp webhook URL: $SERVICE_URL/whatsapp/webhook"
echo "2. Test the deployment with the health check"
echo "3. Send a test WhatsApp message"
```

### 2. Deploy to Cloud Run

```bash
# Make the deploy script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

### 3. Configure Environment Variables in Cloud Run

```bash
# Set environment variables for the Cloud Run service
gcloud run services update uganda-egov-helpdesk \
    --region us-central1 \
    --set-env-vars \
    "WHATSAPP_ACCESS_TOKEN=your_token,\
    WHATSAPP_PHONE_NUMBER_ID=your_phone_id,\
    WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token,\
    WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_id,\
    FIREBASE_PROJECT_ID=uganda-egov-helpdesk,\
    JWT_SECRET_KEY=your_jwt_secret,\
    ENCRYPTION_KEY=your_encryption_key,\
    ADMIN_WHATSAPP_GROUP=your_admin_group"
```

## 🧪 Testing Guide

### 1. Automated Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_agents.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_integration.py -v

# Run tests with coverage
python -m pytest --cov=app tests/ --cov-report=html

# Performance testing
python -m pytest tests/test_performance.py -v
```

### 2. Manual Testing Checklist

#### Health Checks
- [ ] Service health endpoint responds: `GET /health`
- [ ] System info endpoint works: `GET /system/info`
- [ ] Admin dashboard loads: `GET /static/admin.html`

#### WhatsApp Integration
- [ ] Webhook verification works
- [ ] Can receive WhatsApp messages
- [ ] Can send WhatsApp messages
- [ ] Message formatting is correct

#### Authentication Flow
- [ ] User can authenticate via WhatsApp
- [ ] Sessions are created and managed properly
- [ ] Session timeout works correctly
- [ ] Logout functionality works

#### Multi-Language Support
- [ ] Language detection works for all supported languages
- [ ] Translation responses are appropriate
- [ ] Language preference is remembered

#### Government Services
- [ ] Birth certificate lookup works
- [ ] Tax status checking works
- [ ] NSSF balance inquiry works
- [ ] Land records verification works

#### Error Handling
- [ ] Invalid inputs are handled gracefully
- [ ] Service timeouts are handled properly
- [ ] Network errors trigger appropriate fallbacks
- [ ] User receives helpful error messages

### 3. Load Testing

```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load_test.py --host=https://your-service-url.run.app
```

### 4. Integration Testing with WhatsApp

Create test scenarios:

```python
# Test authentication
test_message = "login test_user password123"

# Test service requests
test_messages = [
    "birth certificate",
    "NIRA/2025/001234",
    "tax status", 
    "1234567890",
    "nssf balance",
    "123456789",
    "help",
    "cancel",
    "logout"
]
```

## 📊 Monitoring and Observability

### 1. Google Cloud Monitoring Setup

```bash
# Create custom metrics dashboard
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard.json

# Set up alerting policies
gcloud alpha monitoring policies create --policy-from-file=monitoring/alert_rules.yml
```

### 2. Log Analysis

```bash
# View application logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=uganda-egov-helpdesk" --limit=50

# Filter for errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=uganda-egov-helpdesk AND severity>=ERROR" --limit=20

# Real-time log streaming
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=uganda-egov-helpdesk"
```

### 3. Performance Monitoring

Key metrics to monitor:
- **Response Time**: Average response time for WhatsApp messages
- **Success Rate**: Percentage of successful service completions
- **Error Rate**: Rate of errors and failures
- **Active Sessions**: Number of concurrent user sessions
- **Language Distribution**: Usage patterns across languages
- **Service Usage**: Most popular government services

## 🔒 Security Considerations

### 1. Production Security Checklist

- [ ] Service account has minimal required permissions
- [ ] Environment variables are properly secured
- [ ] HTTPS is enforced for all endpoints
- [ ] Input validation is comprehensive
- [ ] Rate limiting is configured
- [ ] Audit logging is enabled
- [ ] Secrets are managed securely

### 2. WhatsApp Security

- [ ] Webhook verification is implemented
- [ ] Message signatures are validated
- [ ] User input is sanitized
- [ ] Session tokens are secure
- [ ] Personal data is encrypted

### 3. Google Cloud Security

- [ ] IAM roles follow principle of least privilege
- [ ] VPC security is configured (if applicable)
- [ ] Cloud Armor is configured for DDoS protection
- [ ] Security scanning is enabled
- [ ] Backup and disaster recovery plans are in place

## 🚨 Troubleshooting

### Common Deployment Issues

1. **Build Failures**:
   ```bash
   # Check Docker build logs
   docker build -t test-image . --no-cache
   
   # Verify dependencies
   pip install -r requirements.txt --dry-run
   ```

2. **Service Account Issues**:
   ```bash
   # Verify service account permissions
   gcloud projects get-iam-policy uganda-egov-helpdesk
   
   # Test service account authentication
   gcloud auth activate-service-account --key-file=service-account.json
   ```

3. **WhatsApp Webhook Issues**:
   ```bash
   # Test webhook endpoint
   curl -X GET "https://your-service-url.run.app/whatsapp/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=your_token"
   
   # Check webhook logs
   gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message:webhook"
   ```

### Performance Issues

1. **High Response Times**:
   - Check Cloud Run instance configuration
   - Monitor database query performance
   - Review browser automation timeouts

2. **Memory Issues**:
   - Increase Cloud Run memory allocation
   - Check for memory leaks in browser automation
   - Optimize agent initialization

3. **Rate Limiting**:
   - Implement request queuing
   - Add caching for frequent requests
   - Optimize government portal interactions

## 📈 Scaling Considerations

### Horizontal Scaling
- Configure Cloud Run autoscaling
- Implement load balancing for MCP servers
- Use Cloud SQL for high-traffic scenarios

### Performance Optimization
- Implement Redis caching
- Optimize database queries
- Use CDN for static assets
- Implement connection pooling

### Cost Optimization
- Monitor Cloud Run usage patterns
- Implement intelligent caching
- Optimize cold start times
- Use preemptible instances where appropriate

## 🎯 Production Readiness Checklist

### Before Going Live
- [ ] All tests pass
- [ ] Load testing completed
- [ ] Security review completed
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures tested
- [ ] Documentation updated
- [ ] Team training completed

### Launch Day
- [ ] Deploy to production
- [ ] Configure WhatsApp webhook
- [ ] Monitor system health
- [ ] Test with real users
- [ ] Monitor error rates and performance
- [ ] Have rollback plan ready

### Post-Launch
- [ ] Monitor user feedback
- [ ] Track success metrics
- [ ] Optimize based on usage patterns
- [ ] Plan feature enhancements
- [ ] Regular security updates

---

**This deployment guide ensures a smooth, secure, and scalable deployment of the Uganda E-Gov WhatsApp Helpdesk system.**