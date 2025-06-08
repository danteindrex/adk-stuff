#!/bin/bash

# Uganda E-Gov WhatsApp Helpdesk Deployment Script
# This script deploys the application to Google Cloud Run

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="uganda-egov-whatsapp"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
echo "📋 Setting project to $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push the container image
echo "🏗️ Building container image..."
docker build -t $IMAGE_NAME:latest .

echo "📤 Pushing image to Container Registry..."
docker push $IMAGE_NAME:latest

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 100 \
    --set-env-vars ENVIRONMENT=production \
    --set-env-vars LOG_LEVEL=INFO

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔗 Webhook URL: $SERVICE_URL/whatsapp/webhook"
echo "📊 Admin Dashboard: $SERVICE_URL/admin/dashboard/stats"
echo "❤️ Health Check: $SERVICE_URL/health"

echo ""
echo "📋 Next Steps:"
echo "1. Configure your WhatsApp Business API webhook URL: $SERVICE_URL/whatsapp/webhook"
echo "2. Set up your environment variables in Cloud Run console"
echo "3. Configure your Supabase database with the provided schema"
echo "4. Test the webhook with a WhatsApp message"

echo ""
echo "🔧 Environment Variables to Set:"
echo "- WHATSAPP_ACCESS_TOKEN"
echo "- WHATSAPP_PHONE_NUMBER_ID"
echo "- WHATSAPP_WEBHOOK_VERIFY_TOKEN"
echo "- SUPABASE_URL"
echo "- SUPABASE_SERVICE_ROLE_KEY"
echo "- JWT_SECRET_KEY"
echo "- ENCRYPTION_KEY"

echo ""
echo "🎉 Uganda E-Gov WhatsApp Helpdesk is now live!"