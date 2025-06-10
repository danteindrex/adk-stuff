# 🇺🇬 Uganda E-Gov WhatsApp Helpdesk

A multi-agent AI system that enables 45+ million Ugandans to access critical government services entirely through WhatsApp messages, eliminating digital divide barriers and website navigation complexity.

## 🌟 Project Vision

Build a hackathon-winning multi-agent AI system that enables citizens to access government services without ever leaving WhatsApp, supporting multiple local languages and providing autonomous service delivery through intelligent agent collaboration.

## 🚀 Core Innovation

- **Zero Website Interaction**: Citizens never leave WhatsApp
- **Multi-Language Support**: English, Luganda, Luo, Runyoro with automatic detection
- **Autonomous Service Delivery**: Agents collaborate to complete complex government processes
- **Real-World Impact**: Addresses genuine infrastructure and accessibility challenges in Uganda

## 🏗️ Technical Architecture

### Technology Stack

- **Frontend**: WhatsApp Business API (Cloud API)
- **Backend**: FastAPI (Python) for webhook handling and API management
- **Multi-Agent Orchestration**: Google Agent Development Kit (ADK) patterns
- **Database**: Google Cloud Firestore (with Firebase Authentication)
- **Browser Automation**: Microsoft MCP Server with Playwright + Browser-Use agent fallback
- **Infrastructure**: Google Cloud Run + Google Cloud Functions
- **Monitoring**: Google Cloud Monitoring + Custom Dashboard

### Modular Multi-Agent System Design

The system uses a modular architecture with specialized components:

#### Core Agents (`app/agents/core_agents/`)
1. **AuthenticationAgent** - Firebase-based secure user verification and session management
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
1. **Playwright Tools** - Enhanced browser automation with intelligent fallback
2. **WhatsApp Tools** - WhatsApp Business API integration
3. **Auth Tools** - Google Firebase authentication and user management

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
- `logout` - End session securely
- `admin` - Emergency admin contact information

## 🚀 Quick Start

### Prerequisites
- Google Cloud Project with billing enabled
- WhatsApp Business API access
- Firebase project setup
- Docker installed locally

### 1. Clone and Setup
```bash
git clone <repository-url>
cd adk-stuff
cp .env.example .env
# Edit .env with your configuration
```

### 2. Google Cloud Setup
```bash
# Enable required APIs
gcloud services enable identitytoolkit.googleapis.com
gcloud services enable firebase.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com

# Create service account
gcloud iam service-accounts create uganda-egov-service \
    --display-name="Uganda E-Gov Service Account"

# Download service account key
gcloud iam service-accounts keys create service-account.json \
    --iam-account=uganda-egov-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3. Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create project or import Google Cloud project
3. Enable Authentication and configure providers
4. Enable Firestore Database

### 4. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
export FIREBASE_PROJECT_ID=your-firebase-project-id
export GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Run locally
python main.py
```

### 5. Deploy to Google Cloud Run
```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy to Cloud Run
./deploy.sh
```

### 6. Configure WhatsApp Webhook
Set your WhatsApp Business API webhook URL to:
```
https://your-service-url.run.app/whatsapp/webhook
```

## 🔧 Configuration

### Required Environment Variables

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# Google Cloud Authentication
GOOGLE_OAUTH_CLIENT_ID=your_oauth_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_oauth_client_secret
FIREBASE_PROJECT_ID=your_firebase_project_id
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key
ENCRYPTION_KEY=your-32-character-encryption-key
ADMIN_WHATSAPP_GROUP=admin_group_id

# Optional
REDIS_URL=redis://localhost:6379
MCP_SERVER_URLS=http://mcp-server-1:8000
```

## 📊 Admin Dashboard

Access the real-time admin dashboard at:
```
https://your-service-url.run.app/static/admin.html
```

### Dashboard Features
- Real-time system statistics
- Service health monitoring
- Language usage analytics
- Recent system logs
- Performance metrics
- Error tracking and alerts

## 🔒 Security Features

- **Session Management**: Secure Firebase-based sessions with automatic expiry
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

### Alerting
- High error rates
- Service degradation
- Performance issues
- Security events
- System health status

## 🧪 Testing

### Test User Accounts
```
Username: john_doe, Password: password123, Phone: +256700000001
Username: mary_nakato, Password: password123, Phone: +256700000002
Username: peter_okello, Password: password123, Phone: +256700000003
Username: sarah_tumusiime, Password: password123, Phone: +256700000004
```

### Sample Interactions
```
User: login john_doe password123
Bot: ✅ Welcome back, John! You're now logged in.

User: birth certificate
Bot: Please provide your NIRA reference number...

User: NIRA/2025/001234
Bot: 🎉 Your birth certificate is ready for collection at Kampala URSB!
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_agents.py
python -m pytest tests/test_integration.py
python -m pytest tests/test_performance.py

# Run with coverage
python -m pytest --cov=app tests/
```

## 🚀 Enhanced Browser Automation

The system features intelligent browser automation with multiple fallback mechanisms:

### Automation Flow
1. **Primary**: Playwright MCP tools for fast, reliable automation
2. **Fallback**: Browser-Use agent for AI-powered automation
3. **Manual**: Step-by-step user guidance when automation fails

### Smart Features
- Retry logic with exponential backoff
- Automatic error detection and recovery
- Screenshot verification of operations
- Data validation and sanitization
- Graceful timeout handling

## 🏆 Hackathon Success Strategy

### Technical Excellence (50%)
- ✅ Clean multi-agent architecture with modular design
- ✅ Robust error handling and graceful failures
- ✅ Scalable cloud-native design
- ✅ Security best practices with Firebase integration
- ✅ Performance optimization with intelligent caching

### Innovation & Creativity (30%)
- ✅ Social impact addressing real infrastructure challenges
- ✅ Sophisticated multi-agent collaboration
- ✅ Cultural localization beyond simple translation
- ✅ Zero-digital-divide design
- ✅ Novel government integration approach

### Demo & Documentation (20%)
- ✅ Compelling demo showcasing real service completion
- ✅ Clear architecture visualization
- ✅ Comprehensive documentation
- ✅ Production-ready deployment

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
│   ├── core_agents/          # Authentication, Language, Intent, Help
│   ├── service_agents/       # Government service automation
│   ├── mcp_servers/          # MCP tool integrations
│   └── adk_agents_modular.py # Main agent orchestration
├── api/                      # FastAPI endpoints
├── core/                     # Configuration and logging
├── database/                 # Firestore client
├── models/                   # Data models
└── services/                 # Supporting services
```

### Key Features
- **Intelligent Routing**: Intent classification routes to appropriate agents
- **Session Persistence**: Firebase-based session management
- **Error Recovery**: Multiple fallback mechanisms for reliability
- **Real-time Monitoring**: Comprehensive logging and metrics
- **Scalable Design**: Cloud-native architecture for high availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Emergency**: Contact admin through the WhatsApp bot using 'admin' command

## 🎉 Acknowledgments

- Uganda Government for digital transformation initiatives
- WhatsApp Business API for messaging platform
- Google Cloud for infrastructure and ADK framework
- Firebase for authentication services
- The open-source community for tools and libraries

---

**Built with ❤️ for Uganda's digital future**

*This system demonstrates how AI can bridge the digital divide and make government services accessible to all citizens, regardless of their technical literacy or internet access.*