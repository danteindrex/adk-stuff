# Uganda E-Gov WhatsApp Helpdesk - Google Cloud Run Deployment Script (PowerShell)
# This script deploys the application to Google Cloud Run

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = $env:PROJECT_ID,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "uganda-egov-whatsapp"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🚀 Uganda E-Gov WhatsApp Helpdesk - Cloud Run Deployment" -ForegroundColor $Blue
Write-Host "==================================================" -ForegroundColor $Blue

# Check if PROJECT_ID is set
if ([string]::IsNullOrEmpty($ProjectId)) {
    Write-Host "❌ Error: PROJECT_ID is not set" -ForegroundColor $Red
    Write-Host "Please set your Google Cloud Project ID:" -ForegroundColor $Yellow
    Write-Host "`$env:PROJECT_ID = 'your-project-id'" -ForegroundColor $Yellow
    Write-Host "Or run: .\deploy-to-cloudrun.ps1 -ProjectId 'your-project-id'" -ForegroundColor $Yellow
    exit 1
}

$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-Host "📋 Configuration:" -ForegroundColor $Blue
Write-Host "  Project ID: $ProjectId"
Write-Host "  Region: $Region"
Write-Host "  Service Name: $ServiceName"
Write-Host "  Image: $ImageName"
Write-Host ""

# Check if gcloud is installed
Write-Host "🔍 Checking Google Cloud SDK..." -ForegroundColor $Yellow
try {
    $gcloudVersion = gcloud version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud not found"
    }
} catch {
    Write-Host "❌ Error: Google Cloud SDK is not installed" -ForegroundColor $Red
    Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install" -ForegroundColor $Yellow
    exit 1
}

# Check authentication
Write-Host "🔍 Checking authentication..." -ForegroundColor $Yellow
$authList = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if ([string]::IsNullOrEmpty($authList)) {
    Write-Host "❌ Error: Not authenticated with Google Cloud" -ForegroundColor $Red
    Write-Host "Please run: gcloud auth login" -ForegroundColor $Yellow
    exit 1
}

# Set the project
Write-Host "🔧 Setting up Google Cloud project..." -ForegroundColor $Yellow
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "🔧 Enabling required Google Cloud APIs..." -ForegroundColor $Yellow
$apis = @(
    "cloudbuild.googleapis.com",
    "run.googleapis.com", 
    "containerregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Enabling $api..."
    gcloud services enable $api
}

# Function to create secret if it doesn't exist
function Create-SecretIfNotExists {
    param(
        [string]$SecretName,
        [string]$Description
    )
    
    $secretExists = gcloud secrets describe $SecretName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Creating secret: $SecretName" -ForegroundColor $Yellow
        "PLACEHOLDER_VALUE" | gcloud secrets create $SecretName --replication-policy="automatic" --data-file=-
        Write-Host "⚠️  Please update the secret '$SecretName' with the actual value:" -ForegroundColor $Yellow
        Write-Host "   echo 'actual-value' | gcloud secrets versions add $SecretName --data-file=-" -ForegroundColor $Yellow
    } else {
        Write-Host "Secret $SecretName already exists" -ForegroundColor $Green
    }
}

# Create secrets in Secret Manager
Write-Host "🔐 Setting up secrets in Secret Manager..." -ForegroundColor $Yellow

$secrets = @{
    "twilio-account-sid" = "Twilio Account SID"
    "twilio-auth-token" = "Twilio Auth Token"
    "twilio-whatsapp-number" = "Twilio WhatsApp Number"
    "twilio-webhook-verify-token" = "Twilio Webhook Verify Token"
    "jwt-secret-key" = "JWT Secret Key"
    "encryption-key" = "Encryption Key"
    "google-api-key" = "Google API Key"
    "admin-whatsapp-group" = "Admin WhatsApp Group ID"
}

foreach ($secret in $secrets.GetEnumerator()) {
    Create-SecretIfNotExists -SecretName $secret.Key -Description $secret.Value
}

Write-Host ""

# Build and deploy using Cloud Build
Write-Host "🏗️  Building and deploying with Cloud Build..." -ForegroundColor $Yellow
gcloud builds submit --config cloudbuild.yaml --substitutions="_REGION=$Region,_SERVICE_NAME=$ServiceName" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor $Red
    exit 1
}

# Get the service URL
Write-Host "🔍 Getting service URL..." -ForegroundColor $Yellow
$ServiceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"

Write-Host ""
Write-Host "✅ Deployment completed successfully!" -ForegroundColor $Green
Write-Host "==================================================" -ForegroundColor $Green
Write-Host "🌐 Service URL: $ServiceUrl" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor $Blue
Write-Host "1. Update your Twilio webhook URL to: $ServiceUrl/whatsapp/webhook"
Write-Host "2. Test the health endpoint: $ServiceUrl/health"
Write-Host "3. Check the admin dashboard: $ServiceUrl/admin/dashboard"
Write-Host "4. Monitor logs: gcloud logs tail --service=$ServiceName"
Write-Host ""
Write-Host "🔐 Don't forget to update the secrets with actual values:" -ForegroundColor $Yellow
Write-Host "   echo 'actual-value' | gcloud secrets versions add twilio-account-sid --data-file=-"
Write-Host "   echo 'actual-value' | gcloud secrets versions add twilio-auth-token --data-file=-"
Write-Host "   echo 'actual-value' | gcloud secrets versions add google-api-key --data-file=-"
Write-Host "   # ... and other secrets"
Write-Host ""
Write-Host "📊 Useful commands:" -ForegroundColor $Blue
Write-Host "   View logs: gcloud logs tail --service=$ServiceName"
Write-Host "   Update service: gcloud run deploy $ServiceName --image=$ImageName`:latest --region=$Region"
Write-Host "   Delete service: gcloud run services delete $ServiceName --region=$Region"
Write-Host ""
Write-Host "🎉 Your Uganda E-Gov WhatsApp Helpdesk is now running on Cloud Run!" -ForegroundColor $Green