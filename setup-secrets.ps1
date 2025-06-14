# Setup Google Cloud Secrets for Uganda E-Gov WhatsApp Helpdesk (PowerShell)
# This script helps you set up all required secrets in Google Cloud Secret Manager

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = $env:PROJECT_ID
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🔐 Setting up Google Cloud Secrets" -ForegroundColor $Blue
Write-Host "==================================" -ForegroundColor $Blue

# Check if PROJECT_ID is set
if ([string]::IsNullOrEmpty($ProjectId)) {
    Write-Host "❌ Error: PROJECT_ID is not set" -ForegroundColor $Red
    Write-Host "Please set your Google Cloud Project ID:" -ForegroundColor $Yellow
    Write-Host "`$env:PROJECT_ID = 'your-project-id'" -ForegroundColor $Yellow
    Write-Host "Or run: .\setup-secrets.ps1 -ProjectId 'your-project-id'" -ForegroundColor $Yellow
    exit 1
}

Write-Host "Project ID: $ProjectId" -ForegroundColor $Blue
Write-Host ""

# Function to create or update a secret
function Setup-Secret {
    param(
        [string]$SecretName,
        [string]$Description,
        [string]$PromptMessage
    )
    
    Write-Host "🔑 Setting up: $SecretName" -ForegroundColor $Yellow
    Write-Host "Description: $Description"
    
    # Check if secret exists
    $secretExists = gcloud secrets describe $SecretName --project=$ProjectId 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Secret $SecretName already exists."
        $updateSecret = Read-Host "Do you want to update it? (y/N)"
        if ($updateSecret -eq "y" -or $updateSecret -eq "Y") {
            $secretValue = Read-Host -Prompt $PromptMessage -AsSecureString
            $secretValuePlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretValue))
            $secretValuePlain | gcloud secrets versions add $SecretName --data-file=- --project=$ProjectId
            Write-Host "✅ Secret $SecretName updated" -ForegroundColor $Green
        } else {
            Write-Host "Skipping $SecretName"
        }
    } else {
        Write-Host "Creating new secret: $SecretName"
        gcloud secrets create $SecretName --replication-policy="automatic" --project=$ProjectId
        $secretValue = Read-Host -Prompt $PromptMessage -AsSecureString
        $secretValuePlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretValue))
        $secretValuePlain | gcloud secrets versions add $SecretName --data-file=- --project=$ProjectId
        Write-Host "✅ Secret $SecretName created" -ForegroundColor $Green
    }
    Write-Host ""
}

# Enable Secret Manager API
Write-Host "🔧 Enabling Secret Manager API..." -ForegroundColor $Yellow
gcloud services enable secretmanager.googleapis.com --project=$ProjectId

Write-Host ""
Write-Host "📋 We'll now set up all required secrets." -ForegroundColor $Blue
Write-Host "You can find these values in your .env file or service provider dashboards."
Write-Host ""

# Setup all required secrets
$secrets = @(
    @{
        Name = "twilio-account-sid"
        Description = "Twilio Account SID for WhatsApp messaging"
        Prompt = "Enter your Twilio Account SID"
    },
    @{
        Name = "twilio-auth-token"
        Description = "Twilio Auth Token for API authentication"
        Prompt = "Enter your Twilio Auth Token"
    },
    @{
        Name = "twilio-whatsapp-number"
        Description = "Twilio WhatsApp phone number (format: +1234567890)"
        Prompt = "Enter your Twilio WhatsApp number"
    },
    @{
        Name = "twilio-webhook-verify-token"
        Description = "Token for verifying Twilio webhook requests"
        Prompt = "Enter your Twilio webhook verify token"
    },
    @{
        Name = "jwt-secret-key"
        Description = "Secret key for JWT token generation"
        Prompt = "Enter a secure JWT secret key (32+ characters)"
    },
    @{
        Name = "encryption-key"
        Description = "Key for encrypting sensitive data"
        Prompt = "Enter a secure encryption key (32+ characters)"
    },
    @{
        Name = "google-api-key"
        Description = "Google AI API key for language model functionality"
        Prompt = "Enter your Google AI API key"
    },
    @{
        Name = "admin-whatsapp-group"
        Description = "WhatsApp group ID for admin notifications"
        Prompt = "Enter your admin WhatsApp group ID"
    }
)

foreach ($secret in $secrets) {
    Setup-Secret -SecretName $secret.Name -Description $secret.Description -PromptMessage $secret.Prompt
}

# Optional secrets
Write-Host "🔧 Optional Secrets" -ForegroundColor $Blue
Write-Host "The following secrets are optional but recommended for enhanced functionality:"
Write-Host ""

$setupOptional = Read-Host "Do you want to set up optional secrets? (y/N)"
if ($setupOptional -eq "y" -or $setupOptional -eq "Y") {
    
    $optionalSecrets = @(
        @{
            Name = "twilio-api-key-sid"
            Description = "Twilio API Key SID for enhanced features"
            Prompt = "Enter your Twilio API Key SID (optional)"
        },
        @{
            Name = "google-cloud-project"
            Description = "Google Cloud Project ID for advanced features"
            Prompt = "Enter your Google Cloud Project ID"
        },
        @{
            Name = "firebase-project-id"
            Description = "Firebase Project ID for advanced caching"
            Prompt = "Enter your Firebase Project ID (optional)"
        }
    )
    
    foreach ($secret in $optionalSecrets) {
        Setup-Secret -SecretName $secret.Name -Description $secret.Description -PromptMessage $secret.Prompt
    }
}

Write-Host ""
Write-Host "✅ All secrets have been set up successfully!" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Summary of created secrets:" -ForegroundColor $Blue
gcloud secrets list --project=$ProjectId --filter="name:twilio* OR name:jwt* OR name:encryption* OR name:google* OR name:admin*" --format="table(name,createTime)"

Write-Host ""
Write-Host "🔍 To verify a secret value:" -ForegroundColor $Blue
Write-Host "gcloud secrets versions access latest --secret=SECRET_NAME --project=$ProjectId"
Write-Host ""
Write-Host "🔄 To update a secret:" -ForegroundColor $Blue
Write-Host "echo 'NEW_VALUE' | gcloud secrets versions add SECRET_NAME --data-file=- --project=$ProjectId"
Write-Host ""
Write-Host "🎉 Your secrets are ready for Cloud Run deployment!" -ForegroundColor $Green