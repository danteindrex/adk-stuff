#!/bin/bash

# Deploy Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run
# This script handles the complete deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"g-govt-helpdesk"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="uganda-egov-whatsapp"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}🇺🇬 Deploying Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run${NC}"
echo "=================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  Not authenticated with gcloud. Please run:${NC}"
    echo "gcloud auth login"
    exit 1
fi

# Set the project
echo -e "${BLUE}📋 Setting up Google Cloud project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    redis.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com

# Create secrets for environment variables
echo -e "${BLUE}🔐 Creating secrets in Secret Manager...${NC}"
if ! gcloud secrets describe uganda-egov-secrets &>/dev/null; then
    gcloud secrets create uganda-egov-secrets --data-file=.env.production
    echo -e "${GREEN}✅ Created uganda-egov-secrets${NC}"
else
    gcloud secrets versions add uganda-egov-secrets --data-file=.env.production
    echo -e "${GREEN}✅ Updated uganda-egov-secrets${NC}"
fi

# Build and deploy using Cloud Build
echo -e "${BLUE}🏗️  Building and deploying with Cloud Build...${NC}"
gcloud builds submit --config cloudbuild.yaml .

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================================="
echo -e "${GREEN}📱 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}🔧 Admin Dashboard: ${SERVICE_URL}/admin${NC}"
echo -e "${GREEN}📊 Health Check: ${SERVICE_URL}/health${NC}"
echo -e "${GREEN}📖 API Docs: ${SERVICE_URL}/docs${NC}"
echo ""

# Test the deployment
echo -e "${BLUE}🧪 Testing the deployment...${NC}"
if curl -f "${SERVICE_URL}/health" &>/dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed. Service might still be starting up.${NC}"
fi

# Display useful commands
echo ""
echo -e "${BLUE}📋 Useful commands:${NC}"
echo "View logs:     gcloud run services logs tail $SERVICE_NAME --region=$REGION"
echo "Update service: gcloud run services update $SERVICE_NAME --region=$REGION"
echo "Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo ""

# Setup webhook URL for Twilio
echo -e "${YELLOW}📞 Next Steps for Twilio Configuration:${NC}"
echo "1. Go to your Twilio Console"
echo "2. Navigate to Messaging > Settings > WhatsApp sandbox settings"
echo "3. Set webhook URL to: ${SERVICE_URL}/whatsapp/webhook"
echo "4. Set HTTP method to: POST"
echo "5. Save the configuration"
echo ""

echo -e "${GREEN}🇺🇬 Uganda E-Gov WhatsApp Helpdesk is now live and ready to serve 45+ million citizens!${NC}"