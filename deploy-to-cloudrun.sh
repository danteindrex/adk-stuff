#!/bin/bash

# Uganda E-Gov WhatsApp Helpdesk - Google Cloud Run Deployment Script
# This script deploys the application to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-""}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"uganda-egov-whatsapp"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}🚀 Uganda E-Gov WhatsApp Helpdesk - Cloud Run Deployment${NC}"
echo "=================================================="

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: PROJECT_ID environment variable is not set${NC}"
    echo "Please set your Google Cloud Project ID:"
    echo "export PROJECT_ID=your-project-id"
    exit 1
fi

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image: $IMAGE_NAME"
echo ""

# Check if gcloud is installed and authenticated
echo -e "${YELLOW}🔍 Checking Google Cloud SDK...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: Google Cloud SDK is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Error: Not authenticated with Google Cloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set the project
echo -e "${YELLOW}🔧 Setting up Google Cloud project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com

# Create secrets in Secret Manager (if they don't exist)
echo -e "${YELLOW}🔐 Setting up secrets in Secret Manager...${NC}"

create_secret_if_not_exists() {
    local secret_name=$1
    local description=$2
    
    if ! gcloud secrets describe $secret_name &> /dev/null; then
        echo "Creating secret: $secret_name"
        gcloud secrets create $secret_name --replication-policy="automatic" --data-file=- <<< "PLACEHOLDER_VALUE"
        echo -e "${YELLOW}⚠️  Please update the secret '$secret_name' with the actual value:${NC}"
        echo "   gcloud secrets versions add $secret_name --data-file=-"
    else
        echo "Secret $secret_name already exists"
    fi
}

# Create required secrets
create_secret_if_not_exists "twilio-account-sid" "Twilio Account SID"
create_secret_if_not_exists "twilio-auth-token" "Twilio Auth Token"
create_secret_if_not_exists "twilio-whatsapp-number" "Twilio WhatsApp Number"
create_secret_if_not_exists "twilio-webhook-verify-token" "Twilio Webhook Verify Token"
create_secret_if_not_exists "jwt-secret-key" "JWT Secret Key"
create_secret_if_not_exists "encryption-key" "Encryption Key"
create_secret_if_not_exists "google-api-key" "Google API Key"
create_secret_if_not_exists "admin-whatsapp-group" "Admin WhatsApp Group ID"

echo ""

# Build and deploy using Cloud Build
echo -e "${YELLOW}🏗️  Building and deploying with Cloud Build...${NC}"
gcloud builds submit --config cloudbuild.yaml --substitutions=_REGION=$REGION,_SERVICE_NAME=$SERVICE_NAME .

# Get the service URL
echo -e "${YELLOW}🔍 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo "=================================================="
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Update your Twilio webhook URL to: $SERVICE_URL/whatsapp/webhook"
echo "2. Test the health endpoint: $SERVICE_URL/health"
echo "3. Check the admin dashboard: $SERVICE_URL/admin/dashboard"
echo "4. Monitor logs: gcloud logs tail --service=$SERVICE_NAME"
echo ""
echo -e "${YELLOW}🔐 Don't forget to update the secrets with actual values:${NC}"
echo "   gcloud secrets versions add twilio-account-sid --data-file=-"
echo "   gcloud secrets versions add twilio-auth-token --data-file=-"
echo "   gcloud secrets versions add google-api-key --data-file=-"
echo "   # ... and other secrets"
echo ""
echo -e "${BLUE}📊 Useful commands:${NC}"
echo "   View logs: gcloud logs tail --service=$SERVICE_NAME"
echo "   Update service: gcloud run deploy $SERVICE_NAME --image=$IMAGE_NAME:latest --region=$REGION"
echo "   Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo ""
echo -e "${GREEN}🎉 Your Uganda E-Gov WhatsApp Helpdesk is now running on Cloud Run!${NC}"