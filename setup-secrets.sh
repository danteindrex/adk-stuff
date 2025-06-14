#!/bin/bash

# Setup Google Cloud Secrets for Uganda E-Gov WhatsApp Helpdesk
# This script helps you set up all required secrets in Google Cloud Secret Manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ID=${PROJECT_ID:-""}

echo -e "${BLUE}🔐 Setting up Google Cloud Secrets${NC}"
echo "=================================="

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: PROJECT_ID environment variable is not set${NC}"
    echo "Please set your Google Cloud Project ID:"
    echo "export PROJECT_ID=your-project-id"
    exit 1
fi

echo -e "${BLUE}Project ID: $PROJECT_ID${NC}"
echo ""

# Function to create or update a secret
setup_secret() {
    local secret_name=$1
    local description=$2
    local prompt_message=$3
    
    echo -e "${YELLOW}🔑 Setting up: $secret_name${NC}"
    echo "Description: $description"
    
    # Check if secret exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &> /dev/null; then
        echo "Secret $secret_name already exists."
        read -p "Do you want to update it? (y/N): " update_secret
        if [[ $update_secret =~ ^[Yy]$ ]]; then
            echo "$prompt_message"
            read -s secret_value
            echo "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID
            echo -e "${GREEN}✅ Secret $secret_name updated${NC}"
        else
            echo "Skipping $secret_name"
        fi
    else
        echo "Creating new secret: $secret_name"
        gcloud secrets create $secret_name --replication-policy="automatic" --project=$PROJECT_ID
        echo "$prompt_message"
        read -s secret_value
        echo "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID
        echo -e "${GREEN}✅ Secret $secret_name created${NC}"
    fi
    echo ""
}

# Enable Secret Manager API
echo -e "${YELLOW}🔧 Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

echo ""
echo -e "${BLUE}📋 We'll now set up all required secrets.${NC}"
echo "You can find these values in your .env file or service provider dashboards."
echo ""

# Setup all required secrets
setup_secret "twilio-account-sid" \
    "Twilio Account SID for WhatsApp messaging" \
    "Enter your Twilio Account SID:"

setup_secret "twilio-auth-token" \
    "Twilio Auth Token for API authentication" \
    "Enter your Twilio Auth Token:"

setup_secret "twilio-whatsapp-number" \
    "Twilio WhatsApp phone number (format: +1234567890)" \
    "Enter your Twilio WhatsApp number:"

setup_secret "twilio-webhook-verify-token" \
    "Token for verifying Twilio webhook requests" \
    "Enter your Twilio webhook verify token:"

setup_secret "jwt-secret-key" \
    "Secret key for JWT token generation" \
    "Enter a secure JWT secret key (32+ characters):"

setup_secret "encryption-key" \
    "Key for encrypting sensitive data" \
    "Enter a secure encryption key (32+ characters):"

setup_secret "google-api-key" \
    "Google AI API key for language model functionality" \
    "Enter your Google AI API key:"

setup_secret "admin-whatsapp-group" \
    "WhatsApp group ID for admin notifications" \
    "Enter your admin WhatsApp group ID:"

# Optional secrets
echo -e "${BLUE}🔧 Optional Secrets${NC}"
echo "The following secrets are optional but recommended for enhanced functionality:"
echo ""

read -p "Do you want to set up optional secrets? (y/N): " setup_optional
if [[ $setup_optional =~ ^[Yy]$ ]]; then
    
    setup_secret "twilio-api-key-sid" \
        "Twilio API Key SID for enhanced features" \
        "Enter your Twilio API Key SID (optional):"
    
    setup_secret "google-cloud-project" \
        "Google Cloud Project ID for advanced features" \
        "Enter your Google Cloud Project ID:"
    
    setup_secret "firebase-project-id" \
        "Firebase Project ID for advanced caching" \
        "Enter your Firebase Project ID (optional):"
fi

echo ""
echo -e "${GREEN}✅ All secrets have been set up successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Summary of created secrets:${NC}"
gcloud secrets list --project=$PROJECT_ID --filter="name:twilio* OR name:jwt* OR name:encryption* OR name:google* OR name:admin*" --format="table(name,createTime)"

echo ""
echo -e "${BLUE}🔍 To verify a secret value:${NC}"
echo "gcloud secrets versions access latest --secret=SECRET_NAME --project=$PROJECT_ID"
echo ""
echo -e "${BLUE}🔄 To update a secret:${NC}"
echo "echo 'NEW_VALUE' | gcloud secrets versions add SECRET_NAME --data-file=- --project=$PROJECT_ID"
echo ""
echo -e "${GREEN}🎉 Your secrets are ready for Cloud Run deployment!${NC}"