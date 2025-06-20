#!/bin/bash

# Quick deployment script for immediate deployment
# Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"uganda-egov-whatsapp-$(date +%s)"}
REGION="us-central1"
SERVICE_NAME="uganda-egov-whatsapp"

echo -e "${BLUE}🚀 Quick Deploy to Google Cloud Run${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project $PROJECT_ID 2>/dev/null || {
    echo "Creating new project: $PROJECT_ID"
    gcloud projects create $PROJECT_ID
    gcloud config set project $PROJECT_ID
}

# Enable APIs quickly
echo "Enabling APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --quiet

# Create secret
echo "Creating secrets..."
gcloud secrets create uganda-egov-secrets --data-file=.env.production --quiet 2>/dev/null || \
gcloud secrets versions add uganda-egov-secrets --data-file=.env.production --quiet

# Build and deploy in one command
echo "Building and deploying..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --set-env-vars ENVIRONMENT=production,PORT_NO=8080 \
    --update-secrets /app/.env=uganda-egov-secrets:latest \
    --quiet

# Get URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ Deployed successfully!${NC}"
echo -e "${GREEN}🌐 URL: $SERVICE_URL${NC}"
echo -e "${GREEN}🔧 Admin: $SERVICE_URL/admin${NC}"
echo ""
echo "Configure Twilio webhook: $SERVICE_URL/whatsapp/webhook"