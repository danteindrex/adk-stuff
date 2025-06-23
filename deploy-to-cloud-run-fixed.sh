#!/bin/bash

# Deploy Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run
# Fixed version with proper Pydantic settings

set -e

echo "🇺🇬 Deploying Uganda E-Gov WhatsApp Helpdesk to Google Cloud Run"
echo "=================================================================="

# Configuration
SERVICE_NAME="uganda-egov-whatsapp"
REGION="us-central1"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}"
IMAGE_URL="danteindrex/uganda-egov-fixed-v2:v2.1"

echo "📋 Configuration:"
echo "   Service Name: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Project ID: $PROJECT_ID"
echo "   Image: $IMAGE_URL"
echo ""

# Check if required environment variables are set
echo "🔍 Checking required environment variables..."
REQUIRED_VARS=(
    "WHATSAPP_ACCESS_TOKEN"
    "WHATSAPP_PHONE_NUMBER_ID"
    "WHATSAPP_VERIFY_TOKEN"
    "JWT_SECRET_KEY"
    "ENCRYPTION_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf "   - %s\n" "${MISSING_VARS[@]}"
    echo ""
    echo "Please set these variables before running this script:"
    echo "export WHATSAPP_ACCESS_TOKEN='your_token'"
    echo "export WHATSAPP_PHONE_NUMBER_ID='your_phone_id'"
    echo "export WHATSAPP_VERIFY_TOKEN='your_verify_token'"
    echo "export JWT_SECRET_KEY='your_jwt_secret'"
    echo "export ENCRYPTION_KEY='your_encryption_key'"
    exit 1
fi

echo "✅ All required environment variables are set"
echo ""

# Deploy to Cloud Run
echo "🚀 Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_URL \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8080 \
    --memory=2Gi \
    --cpu=1 \
    --timeout=300 \
    --concurrency=80 \
    --max-instances=10 \
    --set-env-vars="ENVIRONMENT=production" \
    --set-env-vars="LOG_LEVEL=INFO" \
    --set-env-vars="WHATSAPP_ACCESS_TOKEN=$WHATSAPP_ACCESS_TOKEN" \
    --set-env-vars="WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_NUMBER_ID" \
    --set-env-vars="WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN" \
    --set-env-vars="JWT_SECRET_KEY=$JWT_SECRET_KEY" \
    --set-env-vars="ENCRYPTION_KEY=$ENCRYPTION_KEY" \
    --set-env-vars="REDIS_URL=redis://localhost:6379" \
    --set-env-vars="FRONTEND_URL=https://$SERVICE_NAME-$PROJECT_ID.a.run.app"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment successful!"
    echo "=================================================================="
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    echo "📱 Service URL: $SERVICE_URL"
    echo "🔗 Health Check: $SERVICE_URL/health"
    echo "📊 Metrics: $SERVICE_URL/metrics"
    echo "🔧 Admin: $SERVICE_URL/admin"
    echo ""
    echo "📋 WhatsApp Webhook URL for Facebook Developer Console:"
    echo "   $SERVICE_URL/whatsapp/webhook"
    echo ""
    echo "🧪 Test the deployment:"
    echo "   curl $SERVICE_URL/health"
    echo ""
else
    echo "❌ Deployment failed!"
    exit 1
fi