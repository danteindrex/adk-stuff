# Quick Start: Deploy to Google Cloud Run

This is a quick guide to get your Uganda E-Gov WhatsApp Helpdesk running on Google Cloud Run in minutes.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed ([Download here](https://cloud.google.com/sdk/docs/install))
3. **A Google Cloud Project** created

## 🚀 Quick Deployment (5 minutes)

### Step 1: Set up your environment

```powershell
# Windows PowerShell
$env:PROJECT_ID = "your-project-id-here"

# Or Linux/Mac Bash
export PROJECT_ID=your-project-id-here
```

### Step 2: Authenticate with Google Cloud

```bash
gcloud auth login
gcloud config set project $PROJECT_ID
```

### Step 3: Run the deployment script

**Windows:**
```powershell
.\deploy-to-cloudrun.ps1 -ProjectId "your-project-id"
```

**Linux/Mac:**
```bash
chmod +x deploy-to-cloudrun.sh
./deploy-to-cloudrun.sh
```

### Step 4: Set up secrets (when prompted)

The script will create placeholder secrets. Update them with real values:

```bash
# Update secrets with actual values
echo "your-actual-twilio-account-sid" | gcloud secrets versions add twilio-account-sid --data-file=-
echo "your-actual-twilio-auth-token" | gcloud secrets versions add twilio-auth-token --data-file=-
echo "your-actual-google-api-key" | gcloud secrets versions add google-api-key --data-file=-
```

### Step 5: Configure Twilio Webhook

1. Get your service URL from the deployment output
2. In Twilio Console, set webhook URL to: `https://your-service-url/whatsapp/webhook`

## 🔧 Alternative: Manual Setup

If you prefer to set up secrets interactively:

**Windows:**
```powershell
.\setup-secrets.ps1 -ProjectId "your-project-id"
```

**Linux/Mac:**
```bash
chmod +x setup-secrets.sh
./setup-secrets.sh
```

Then deploy:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## 📋 Required Information

You'll need these values (from your .env file):

| Secret | Description | Example |
|--------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | From Twilio Console | `AC1234567890abcdef...` |
| `TWILIO_AUTH_TOKEN` | From Twilio Console | `1234567890abcdef...` |
| `TWILIO_WHATSAPP_NUMBER` | Your Twilio WhatsApp number | `+14155238886` |
| `GOOGLE_API_KEY` | From Google AI Studio | `AIzaSy...` |
| `JWT_SECRET_KEY` | Random 32+ character string | `your-secure-jwt-secret` |
| `ENCRYPTION_KEY` | Random 32+ character string | `your-secure-encryption-key` |
| `ADMIN_WHATSAPP_GROUP` | WhatsApp group ID for admins | `120363...@g.us` |

## ✅ Verification

After deployment:

1. **Health Check**: Visit `https://your-service-url/health`
2. **System Info**: Visit `https://your-service-url/system/info`
3. **Test WhatsApp**: Send a message to your Twilio WhatsApp number

## 📊 Monitoring

```bash
# View logs
gcloud logs tail --service=uganda-egov-whatsapp

# Check service status
gcloud run services describe uganda-egov-whatsapp --region=us-central1
```

## 🔄 Updates

To update your deployment:

```bash
# Rebuild and redeploy
gcloud builds submit --config cloudbuild.yaml
```

## 💰 Cost Estimate

**Typical monthly costs for moderate usage:**
- Cloud Run: $10-50/month (depending on traffic)
- Secret Manager: $1-5/month
- Container Registry: $1-10/month
- Logging/Monitoring: $5-20/month

**Total estimated cost: $17-85/month**

## 🆘 Troubleshooting

### Common Issues:

1. **Build fails**: Check `gcloud builds log`
2. **Service won't start**: Check `gcloud logs read --service=uganda-egov-whatsapp`
3. **Secrets not found**: Verify with `gcloud secrets list`

### Quick Fixes:

```bash
# Restart service
gcloud run services update uganda-egov-whatsapp --region=us-central1

# Check service configuration
gcloud run services describe uganda-egov-whatsapp --region=us-central1 --format=yaml
```

## 🎯 Next Steps

1. **Custom Domain**: Set up a custom domain for your service
2. **Monitoring**: Set up alerts and dashboards
3. **Backup**: Configure automated backups
4. **CI/CD**: Set up automated deployments

## 📞 Support

- Check logs: `gcloud logs tail --service=uganda-egov-whatsapp`
- Health endpoint: `https://your-service-url/health`
- Admin dashboard: `https://your-service-url/admin/dashboard`

---

**🎉 That's it! Your Uganda E-Gov WhatsApp Helpdesk is now running on Google Cloud Run!**