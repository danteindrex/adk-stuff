# 🇺🇬 Uganda E-Gov WhatsApp Helpdesk

A simplified, production-ready multi-agent AI system that enables 45+ million Ugandans to access critical government services entirely through WhatsApp messages, eliminating digital divide barriers and website navigation complexity.

## 🌟 Project Vision

Enable citizens to access government services without ever leaving WhatsApp, supporting multiple local languages and providing autonomous service delivery through intelligent agent collaboration.

## 🚀 Core Innovation

- **Zero Website Interaction**: Citizens never leave WhatsApp
- **Simple Phone-Based Authentication**: Users identified by phone numbers (WhatsApp verified)
- **Multi-Language Support**: English, Luganda, Luo, Runyoro with automatic detection
- **Autonomous Service Delivery**: Agents collaborate to complete complex government processes
- **Real-World Impact**: Addresses genuine infrastructure and accessibility challenges in Uganda

## 🏗️ Technical Architecture

### Technology Stack

- **Frontend**: WhatsApp Business API (Cloud API)
- **Backend**: FastAPI (Python) for webhook handling and API management
- **Multi-Agent Orchestration**: Google Agent Development Kit (ADK) patterns
- **Session Management**: Redis for lightweight session storage
- **Browser Automation**: Playwright MCP + Browser-Use AI agent fallback
- **Infrastructure**: Docker, Kubernetes, Google Cloud Run ready
- **Monitoring**: Simple monitoring with structured logging

### Simplified Multi-Agent System Design

#### Core Agents (`app/agents/core_agents/`)
1. **UserIdentificationAgent** - Simple phone-based user identification
2. **LanguageDetectionAgent** - Seamless multilingual experience with automatic translation
3. **IntentClassificationAgent** - Intelligent routing to appropriate service agents
4. **HelpSystemAgent** - Contextual assistance and guidance

#### Service Agents (`app/agents/service_agents/`)
1. **BirthCertificateAgent** - NIRA birth certificate automation
2. **TaxStatusAgent** - URA tax services automation
3. **NSSFBalanceAgent** - NSSF pension services automation
4. **LandVerificationAgent** - NLIS land records automation
5. **FormProcessingAgent** - Government form assistance and submission

#### MCP Servers (`app/agents/mcp_servers/`)
1. **User Identification Tools** - Phone-based user identification
2. **Playwright Tools** - Enhanced browser automation with intelligent fallback
3. **Browser-Use Tools** - AI-powered browser automation for complex scenarios
4. **WhatsApp Tools** - WhatsApp Business API integration

## 🎯 Supported Government Services

### 🎫 Birth Certificates (NIRA)
- Check application status
- Get collection information
- Verify payment status
- Format: NIRA/YYYY/NNNNNN

### 💼 Tax Status (URA)
- Check tax balance and payment history
- View compliance status
- Get payment due dates
- Requires: 10-digit TIN number

### 🏦 NSSF Balance
- Check pension contributions
- View account balance and history
- Get membership details
- Requires: 8-12 digit membership number

### 🌿 Land Records (NLIS)
- Verify land ownership
- Check title status and encumbrances
- Get property details
- Requires: Plot/Block numbers or GPS coordinates

## 🌍 Multi-Language Support

### Supported Languages
- **English** (en) - Primary language
- **Luganda** (lg) - Central Uganda
- **Luo** (luo) - Northern Uganda  
- **Runyoro** (nyn) - Western Uganda

### Language Features
- Automatic language detection from user messages
- Real-time translation for processing
- Localized responses and error messages
- Language preference persistence across sessions

## 📱 Universal Commands

Available in any conversation state:
- `cancel` - Cancel current operation and return to main menu
- `help` - Show contextual help and guidance
- `status` - Display current session status
- `language` - Change language preference
- `admin` - Emergency admin contact information

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Redis** server (for session management)
- **WhatsApp Business API** account and credentials

### 1. Clone and Setup
```bash
git clone <repository-url>
cd adk-stuff

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Setup MCP Servers
```bash
# Run the automated setup script
chmod +x scripts/setup_mcp_servers.sh
./scripts/setup_mcp_servers.sh

# Or install manually:
npm install -g @playwright/mcp@latest
npm install -g @lharries/whatsapp-mcp@latest
pip install browser-use
npx playwright install
```

### 3. Environment Configuration
```bash
# Copy the production template
cp .env.production.template .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**

```env
# WhatsApp Business API (Required)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# Security (Required)
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters_long
ENCRYPTION_KEY=your_encryption_key_exactly_32_characters
ADMIN_WHATSAPP_GROUP=your_admin_whatsapp_group_id

# Redis (Required for session management)
REDIS_URL=redis://localhost:6379

# MCP Servers (Required for browser automation)
MCP_SERVER_URLS=http://localhost:8001
```

### 4. Start the Application
```bash
# Start Redis server
redis-server &

# Start the application
python main.py
```

The application will be available at `http://localhost:8080`

### 5. Configure WhatsApp Webhook
Set your WhatsApp Business API webhook URL to:
```
https://your-service-url/whatsapp/webhook
```

## 🔧 Production Deployment

### Docker Deployment
```bash
# Build production image
docker build -f Dockerfile.prod -t uganda-egov-helpdesk .

# Run with environment file
docker run -d \
  --name uganda-egov-helpdesk \
  --env-file .env \
  -p 8080:8080 \
  uganda-egov-helpdesk
```

### Docker Compose
```bash
# Start all services including Redis
docker-compose up -d

# View logs
docker-compose logs -f
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
```

## 📊 Admin Dashboard

Access the real-time admin dashboard at:
```
https://your-service-url/admin/dashboard
```

### Dashboard Features
- Real-time system statistics
- Service health monitoring
- Language usage analytics
- Recent system logs
- Performance metrics
- Error tracking and alerts

## 🔒 Simplified Security Model

### Phone-Based Authentication
- **No complex login required** - users identified by WhatsApp phone numbers
- **WhatsApp verification** - phone ownership already verified by WhatsApp Business API
- **Automatic normalization** - phone numbers formatted to Uganda standard (+256)
- **Session management** - lightweight Redis-based sessions
- **Audit logging** - all interactions logged for compliance

### Security Features
- **Rate Limiting**: Protection against abuse and spam
- **Input Validation**: Comprehensive sanitization of user inputs
- **Data Encryption**: Sensitive data encrypted at rest
- **Audit Logging**: Complete audit trail of all interactions
- **Access Control**: Role-based access for admin functions

## 📈 Monitoring & Analytics

### Real-time Metrics
- Active user sessions
- Message processing times
- Service success rates
- Error rates and types
- Language distribution
- Popular services

### Health Check Endpoints
- **Basic Health**: `GET /health`
- **Readiness**: `GET /ready`
- **Metrics**: `GET /metrics`
- **System Info**: `GET /system/info`

## 🚀 Enhanced Browser Automation

The system features intelligent browser automation with multiple fallback mechanisms:

### Automation Strategy
1. **Primary**: Playwright MCP tools for fast, reliable automation
2. **Secondary**: Browser-Use AI agent for complex scenarios
3. **Smart**: Combined approach with automatic fallbacks
4. **Manual**: Step-by-step instructions when automation fails

### Smart Features
- AI-powered browser automation with natural language tasks
- Retry logic with exponential backoff
- Automatic error detection and recovery
- Screenshot verification of operations
- Data validation and sanitization
- Graceful timeout handling

## 🧪 Testing

### Sample User Interactions
```
User: Hello
Bot: 🇺🇬 Welcome to Uganda E-Gov Services! I can help you with:
     1. Birth Certificate (NIRA)
     2. Tax Status (URA)
     3. NSSF Balance
     4. Land Verification (NLIS)

User: birth certificate
Bot: Please provide your NIRA reference number (format: NIRA/YYYY/NNNNNN)

User: NIRA/2025/001234
Bot: 🎉 Your birth certificate is ready for collection at Kampala URSB!
     Collection hours: Monday-Friday, 8:00 AM - 5:00 PM
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=app tests/
```

## 🛠️ Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   ```bash
   # Check if MCP servers are installed
   npx @playwright/mcp@latest --help
   npx @lharries/whatsapp-mcp@latest --help
   
   # Reinstall if needed
   npm install -g @playwright/mcp@latest
   ```

2. **Browser-Use Import Error**
   ```bash
   # Install browser-use
   pip install browser-use
   
   # Test import
   python -c "import browser_use; print('OK')"
   ```

3. **WhatsApp API Errors**
   - Verify your access token is valid
   - Check phone number ID is correct
   - Ensure webhook verify token matches

4. **Redis Connection Issues**
   ```bash
   # Start Redis
   redis-server
   
   # Test connection
   redis-cli ping
   ```

### Debug Mode

Enable debug mode for detailed logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🎯 Key Improvements Made

### ✅ Simplified Authentication
- **Removed complex Google OAuth/Firebase** authentication
- **Phone-based identification** - users identified by WhatsApp phone numbers
- **No registration required** - immediate service access
- **Automatic phone formatting** to Uganda standard (+256)

### ✅ Complete MCP Server Setup
- **Playwright MCP Server** for reliable browser automation
- **WhatsApp MCP Server** for Business API integration
- **Browser-Use Tools** for AI-powered automation fallback
- **Automated setup script** for easy deployment

### ✅ Production Ready
- **No demo/mock data** - all metrics from real usage
- **Simplified dependencies** - removed unnecessary Google Cloud services
- **Production environment template** with all required variables
- **Comprehensive setup documentation**

### ✅ Enhanced Automation
- **Smart fallback mechanisms** - Playwright → Browser-Use → Manual
- **Government portal integration** for all major Uganda services
- **AI-powered automation** for complex scenarios
- **Error recovery and retry logic**

## 📋 Production Checklist

Before deploying to production:

- [ ] **MCP Servers installed** (run `./scripts/setup_mcp_servers.sh`)
- [ ] **Environment configured** (copy and edit `.env.production.template`)
- [ ] **WhatsApp Business API** credentials configured
- [ ] **Redis server** running and accessible
- [ ] **Security keys** generated (JWT_SECRET_KEY, ENCRYPTION_KEY)
- [ ] **Webhook URL** configured in Meta Developer Console
- [ ] **Health checks** passing (`/health`, `/ready`)
- [ ] **Admin dashboard** accessible and showing real data

## 🎯 Success Metrics

### Technical Metrics
- **Response Time**: < 5 seconds for simple queries, < 30 seconds for portal automation
- **Success Rate**: > 95% for service completions
- **Language Accuracy**: > 98% translation accuracy
- **Uptime**: 99.9% availability

### Impact Metrics
- **Accessibility**: Zero digital literacy required
- **Language Inclusion**: Support for 80%+ of Uganda's population
- **Service Coverage**: 4+ major government services automated
- **User Experience**: Single WhatsApp conversation completes entire process

## 🔧 System Architecture

### Modular Components
```
/app
├── agents/
│   ├── core_agents/          # User ID, Language, Intent, Help
│   ├── service_agents/       # Government service automation
│   ├── mcp_servers/          # MCP tool integrations
│   └── adk_agents_modular.py # Main agent orchestration
├── api/                      # FastAPI endpoints
├── core/                     # Configuration and logging
├── models/                   # Data models
└── services/                 # Supporting services
```

### Key Features
- **Simplified user identification** by phone number
- **Intelligent routing** with intent classification
- **Lightweight session management** with Redis
- **Multi-level automation** with smart fallbacks
- **Real-time monitoring** with simple logging
- **Production-ready** deployment options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Setup Guide**: See `PRODUCTION_CHECKLIST.md` for deployment verification
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Emergency**: Contact admin through the WhatsApp bot using 'admin' command

## 🎉 Acknowledgments

- Uganda Government for digital transformation initiatives
- WhatsApp Business API for messaging platform
- Google ADK framework for multi-agent orchestration
- Microsoft Playwright for browser automation
- Browser-Use project for AI-powered automation
- The open-source community for tools and libraries

---

**Built with ❤️ for Uganda's digital future**

*This system demonstrates how AI can bridge the digital divide and make government services accessible to all citizens, regardless of their technical literacy or internet access - now production-ready with simplified authentication and comprehensive automation capabilities.*

## 🚀 Ready to Deploy!

The Uganda E-Gov WhatsApp Helpdesk is now **production-ready** with:

- ✅ **Simplified phone-based authentication**
- ✅ **Complete MCP server setup and automation**
- ✅ **Zero demo/mock data - all real metrics**
- ✅ **Comprehensive documentation and setup guides**
- ✅ **Multi-language support for Uganda**
- ✅ **Government service integration ready**

**Start serving citizens through WhatsApp today!** 🇺🇬