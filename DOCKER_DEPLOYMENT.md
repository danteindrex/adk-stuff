# 🐳 Docker Hub Deployment - Uganda E-Gov WhatsApp Helpdesk

## 📦 **Docker Hub Repository**

**🔗 Docker Hub URL:** https://hub.docker.com/r/danteindrex/uganda-egov-whatsapp

**📥 Pull Command:**
```bash
docker pull danteindrex/uganda-egov-whatsapp:latest
```

**🏷️ Available Tags:**
- `latest` - Latest stable version
- `v2.0.0` - Version 2.0.0 with WhatsApp Business API integration

## 🚀 **Quick Start**

### **1. Pull and Run (Basic)**
```bash
# Pull the image
docker pull danteindrex/uganda-egov-whatsapp:latest

# Run with basic configuration
docker run -d \
  --name uganda-egov-app \
  -p 8080:8080 \
  -e WHATSAPP_ACCESS_TOKEN=your_access_token \
  -e WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id \
  -e WHATSAPP_VERIFY_TOKEN=your_verify_token \
  -e JWT_SECRET_KEY=your_jwt_secret_key \
  -e ENCRYPTION_KEY=your_encryption_key \
  danteindrex/uganda-egov-whatsapp:latest
```

### **2. Run with Environment File**
```bash
# Create .env file with your configuration
cat > .env << EOF
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters
ENCRYPTION_KEY=your_encryption_key_exactly_32_chars
ADMIN_WHATSAPP_GROUP=your_admin_group_id
EOF

# Run with environment file
docker run -d \
  --name uganda-egov-app \
  -p 8080:8080 \
  --env-file .env \
  danteindrex/uganda-egov-whatsapp:latest
```

### **3. Run with Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    image: danteindrex/uganda-egov-whatsapp:latest
    container_name: uganda-egov-app
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - WHATSAPP_ACCESS_TOKEN=${WHATSAPP_ACCESS_TOKEN}
      - WHATSAPP_PHONE_NUMBER_ID=${WHATSAPP_PHONE_NUMBER_ID}
      - WHATSAPP_VERIFY_TOKEN=${WHATSAPP_VERIFY_TOKEN}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:7-alpine
    container_name: uganda-egov-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
```

```bash
# Start with Docker Compose
docker-compose up -d
```

## 🔧 **Configuration**

### **Required Environment Variables**
```bash
# WhatsApp Business API (Required)
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_verify_token

# Security (Required)
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters
ENCRYPTION_KEY=your_encryption_key_exactly_32_characters
```

### **Optional Environment Variables**
```bash
# WhatsApp Business API (Optional)
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_APP_ID=your_app_id
WHATSAPP_APP_SECRET=your_app_secret
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT_NO=8080

# Admin Configuration
ADMIN_WHATSAPP_GROUP=your_admin_group_id

# Redis (if using external Redis)
REDIS_URL=redis://redis:6379

# Google Services (Optional)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CLIENT_ID=your_google_client_id
```

## 🌐 **Access Points**

After deployment, your application will be available at:

- **🏠 Main Application:** http://localhost:8080
- **📱 WhatsApp Clone:** http://localhost:8080/whatsapp-clone
- **🔧 Admin Dashboard:** http://localhost:8080/admin
- **📚 API Documentation:** http://localhost:8080/docs
- **❤️ Health Check:** http://localhost:8080/health

## 🔗 **Webhook Configuration**

### **WhatsApp Business API Webhook**
Configure your webhook URL in Meta Developer Console:

**Webhook URL:** `https://your-domain.com/whatsapp/webhook`
**Verify Token:** Use your `WHATSAPP_VERIFY_TOKEN`

### **Webhook Verification**
```bash
# Test webhook verification
curl "https://your-domain.com/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=test123"
```

## 🧪 **Testing**

### **Health Check**
```bash
curl http://localhost:8080/health
```

### **WhatsApp API Test**
```bash
# Test WhatsApp API integration
docker exec uganda-egov-app python test_whatsapp_api.py
```

### **Admin Dashboard**
1. Navigate to http://localhost:8080/admin
2. Login with credentials:
   - Username: `trevor`
   - Password: `The$1000`

## 📊 **Monitoring**

### **Container Logs**
```bash
# View application logs
docker logs -f uganda-egov-app

# View last 100 lines
docker logs --tail 100 uganda-egov-app
```

### **Container Stats**
```bash
# Monitor resource usage
docker stats uganda-egov-app
```

### **Health Monitoring**
```bash
# Check container health
docker inspect uganda-egov-app | grep Health -A 10
```

## 🔄 **Updates**

### **Update to Latest Version**
```bash
# Pull latest image
docker pull danteindrex/uganda-egov-whatsapp:latest

# Stop current container
docker stop uganda-egov-app
docker rm uganda-egov-app

# Run new version
docker run -d \
  --name uganda-egov-app \
  -p 8080:8080 \
  --env-file .env \
  danteindrex/uganda-egov-whatsapp:latest
```

### **Rollback to Previous Version**
```bash
# Run specific version
docker run -d \
  --name uganda-egov-app \
  -p 8080:8080 \
  --env-file .env \
  danteindrex/uganda-egov-whatsapp:v2.0.0
```

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Container Won't Start**
   ```bash
   # Check logs for errors
   docker logs uganda-egov-app
   
   # Verify environment variables
   docker exec uganda-egov-app env | grep WHATSAPP
   ```

2. **WhatsApp API Connection Issues**
   ```bash
   # Test API connectivity
   docker exec uganda-egov-app python test_whatsapp_api.py
   ```

3. **Port Already in Use**
   ```bash
   # Use different port
   docker run -p 8081:8080 danteindrex/uganda-egov-whatsapp:latest
   ```

### **Debug Mode**
```bash
# Run in debug mode
docker run -d \
  --name uganda-egov-app \
  -p 8080:8080 \
  -e DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  --env-file .env \
  danteindrex/uganda-egov-whatsapp:latest
```

## 🔒 **Security**

### **Production Deployment**
- Use strong, unique values for `JWT_SECRET_KEY` and `ENCRYPTION_KEY`
- Set up HTTPS with SSL certificates
- Configure firewall rules
- Use Docker secrets for sensitive data
- Regular security updates

### **Environment Security**
```bash
# Generate secure keys
openssl rand -hex 32  # For ENCRYPTION_KEY
openssl rand -base64 48  # For JWT_SECRET_KEY
```

## 📈 **Scaling**

### **Horizontal Scaling**
```bash
# Run multiple instances with load balancer
docker run -d --name uganda-egov-app-1 -p 8080:8080 --env-file .env danteindrex/uganda-egov-whatsapp:latest
docker run -d --name uganda-egov-app-2 -p 8081:8080 --env-file .env danteindrex/uganda-egov-whatsapp:latest
```

### **Resource Limits**
```bash
# Run with resource limits
docker run -d \
  --name uganda-egov-app \
  --memory=2g \
  --cpus=1.5 \
  -p 8080:8080 \
  --env-file .env \
  danteindrex/uganda-egov-whatsapp:latest
```

## 🎯 **Production Checklist**

- [ ] Configure all required environment variables
- [ ] Set up WhatsApp Business API webhook
- [ ] Configure HTTPS/SSL
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Test all endpoints
- [ ] Set up health checks
- [ ] Configure auto-restart policies
- [ ] Set up log rotation
- [ ] Configure security headers

---

## 📞 **Support**

For issues or questions:
- **GitHub Issues:** [Report bugs and request features]
- **Docker Hub:** https://hub.docker.com/r/danteindrex/uganda-egov-whatsapp
- **Documentation:** Check the README.md in the repository

---

**🇺🇬 Built for Uganda's digital transformation with ❤️**