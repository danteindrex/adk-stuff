#!/bin/bash

# Manual deployment script for Uganda E-Gov WhatsApp Helpdesk
# Step-by-step deployment to Google Cloud Run

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"uganda-egov-whatsapp"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="uganda-egov-whatsapp"

echo -e "${BLUE}🇺🇬 Manual Deployment Guide for Uganda E-Gov WhatsApp Helpdesk${NC}"
echo "=============================================================="

# Step 1: Prerequisites
echo -e "${BLUE}Step 1: Prerequisites${NC}"
echo "✅ Ensure you have gcloud CLI installed"
echo "✅ Authenticate with: gcloud auth login"
echo "✅ Set project: gcloud config set project $PROJECT_ID"
echo ""
read -p "Press Enter to continue..."

# Step 2: Enable APIs
echo -e "${BLUE}Step 2: Enable Required APIs${NC}"
echo "Enabling Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    redis.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com
echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Step 3: Create secrets
echo -e "${BLUE}Step 3: Create Secrets${NC}"
echo "Creating secrets in Secret Manager..."
if ! gcloud secrets describe uganda-egov-secrets &>/dev/null; then
    gcloud secrets create uganda-egov-secrets --data-file=.env.production
    echo -e "${GREEN}✅ Created uganda-egov-secrets${NC}"
else
    echo -e "${YELLOW}⚠️  Secret already exists. Updating...${NC}"
    gcloud secrets versions add uganda-egov-secrets --data-file=.env.production
    echo -e "${GREEN}✅ Updated uganda-egov-secrets${NC}"
fi
echo ""

# Step 4: Build Docker image
echo -e "${BLUE}Step 4: Build Docker Image${NC}"
echo "Building optimized Docker image..."
docker build -f Dockerfile.optimized -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
echo -e "${GREEN}✅ Docker image built${NC}"
echo ""

# Step 5: Push to Container Registry
echo -e "${BLUE}Step 5: Push to Container Registry${NC}"
echo "Pushing image to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest
echo -e "${GREEN}✅ Image pushed to registry${NC}"
echo ""

# Step 6: Deploy to Cloud Run
echo -e "${BLUE}Step 6: Deploy to Cloud Run${NC}"
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --concurrency 100 \
    --max-instances 10 \
    --min-instances 1 \
    --timeout 300 \
    --port 8080 \
    --set-env-vars ENVIRONMENT=production,PORT_NO=8080,GOOGLE_GENAI_USE_VERTEXAI=TRUE \
    --update-secrets /app/.env=uganda-egov-secrets:latest

echo -e "${GREEN}✅ Deployed to Cloud Run${NC}"
echo ""

# Step 7: Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo -e "${GREEN}📱 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}🔧 Admin Dashboard: ${SERVICE_URL}/admin${NC}"
echo ""

# Step 8: Test deployment
echo -e "${BLUE}Step 8: Testing Deployment${NC}"
echo "Testing health endpoint..."
if curl -f "${SERVICE_URL}/health" &>/dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed. Service might still be starting up.${NC}"
fi
echo ""

# Step 9: Configure Twilio
echo -e "${BLUE}Step 9: Configure Twilio Webhook${NC}"
echo "Configure your Twilio WhatsApp webhook:"
echo "1. Go to Twilio Console > Messaging > Settings > WhatsApp sandbox"
echo "2. Set webhook URL: ${SERVICE_URL}/whatsapp/webhook"
echo "3. Set HTTP method: POST"
echo "4. Save configuration"
echo ""

echo -e "${GREEN}🇺🇬 Uganda E-Gov WhatsApp Helpdesk is now live!${NC}"
echo "Ready to serve 45+ million Ugandan citizens with government services."