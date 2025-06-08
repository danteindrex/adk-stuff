# Migration from Supabase to Google Cloud Authentication

## Overview

This document outlines the migration from Supabase authentication to Google Cloud's native authentication services using Google ADK's built-in tools. The migration leverages:

- **Google Identity Platform** for user authentication
- **Firebase Authentication** for user management
- **Google Cloud Firestore** for session storage
- **Google ADK built-in authentication tools** for seamless integration

## Benefits of Using Google Cloud Authentication

### 1. **Native ADK Integration**
- Google ADK has built-in support for Google Cloud services
- No need for external MCP servers for authentication
- Seamless OAuth 2.0 flow handling
- Automatic token management and refresh

### 2. **Enterprise-Grade Security**
- Google-grade authentication infrastructure
- Multi-factor authentication support
- Advanced threat detection
- Compliance with industry standards (SOC 2, ISO 27001)

### 3. **Scalability and Reliability**
- 99.95% uptime SLA
- Global infrastructure
- Automatic scaling
- Built-in monitoring and alerting

### 4. **Cost Effectiveness**
- Pay-per-use pricing model
- Free tier for development and small applications
- No infrastructure maintenance costs

## Architecture Changes

### Before (Supabase)
```
WhatsApp User → FastAPI → Supabase MCP Server → Supabase Auth → PostgreSQL
```

### After (Google Cloud)
```
WhatsApp User → FastAPI → Google ADK Auth Tools → Identity Platform → Firestore
```

## Key Components

### 1. Google Identity Platform
- Handles user authentication flows
- Supports multiple providers (Google, Facebook, Twitter, etc.)
- Manages OAuth 2.0 flows
- Issues JWT tokens

### 2. Firebase Authentication
- User management and profiles
- Custom claims and roles
- Session management
- Token verification

### 3. Google Cloud Firestore
- Session storage
- User data persistence
- Real-time synchronization
- Automatic scaling

### 4. Google ADK Authentication Tools
- Built-in OAuth 2.0 support
- Automatic token handling
- Interactive authentication flows
- Session state management

## Implementation Details

### 1. Authentication Agent

The authentication agent now uses Google ADK's built-in Identity Platform tools:

```python
async def get_google_auth_tools():
    """Get Google Cloud authentication tools using ADK built-in tools"""
    from google.adk.tools.google_api_tool import identity_platform_tool_set
    
    # Configure OAuth2 for Google Identity Platform
    auth_scheme = OAuth2(
        flows=OAuthFlows(
            authorizationCode=OAuthFlowAuthorizationCode(
                authorizationUrl="https://accounts.google.com/o/oauth2/auth",
                tokenUrl="https://oauth2.googleapis.com/token",
                scopes={
                    "https://www.googleapis.com/auth/userinfo.email": "email scope",
                    "https://www.googleapis.com/auth/userinfo.profile": "profile scope",
                    "openid": "openid scope"
                }
            )
        )
    )
    
    # Configure the Google Identity Platform toolset
    identity_platform_tool_set.configure_auth(
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    )
    
    return identity_platform_tool_set.get_tools()
```

### 2. Session Management

The new `GoogleSessionManager` uses Firebase and Firestore:

```python
class GoogleSessionManager:
    def __init__(self):
        self._initialize_firebase()
        self._initialize_firestore()
    
    async def authenticate_user_with_token(self, id_token: str):
        """Authenticate user using Firebase ID token"""
        decoded_token = auth.verify_id_token(id_token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            # ... other user info
        }
```

### 3. Monitoring and Logging

Integrated with Google Cloud services:

```python
class MonitoringService:
    def __init__(self):
        self.logging_client = cloud_logging.Client()
        self.monitoring_client = monitoring_v3.MetricServiceClient()
```

## Environment Variables

### Required Environment Variables

```bash
# Google Cloud Authentication
GOOGLE_OAUTH_CLIENT_ID=your_oauth_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_oauth_client_secret
FIREBASE_PROJECT_ID=your_firebase_project_id
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# WhatsApp Business API (unchanged)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# Application Settings
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO
```

### Removed Environment Variables

```bash
# No longer needed
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_MCP_PAT
```

## Setup Instructions

### 1. Google Cloud Project Setup

1. Create a new Google Cloud Project or use existing one
2. Enable the following APIs:
   - Identity Platform API
   - Firebase Authentication API
   - Cloud Firestore API
   - Cloud Logging API
   - Cloud Monitoring API

```bash
gcloud services enable identitytoolkit.googleapis.com
gcloud services enable firebase.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
```

### 2. Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or import your Google Cloud project
3. Enable Authentication
4. Configure sign-in providers (Google, Email/Password, etc.)
5. Enable Firestore Database

### 3. Identity Platform Setup

1. Go to [Identity Platform Console](https://console.cloud.google.com/customer-identity)
2. Enable Identity Platform
3. Configure OAuth consent screen
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs

### 4. Service Account Setup

1. Create a service account with the following roles:
   - Firebase Authentication Admin
   - Cloud Datastore User
   - Logging Writer
   - Monitoring Metric Writer

```bash
gcloud iam service-accounts create uganda-egov-service \
    --display-name="Uganda E-Gov Service Account"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:uganda-egov-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:uganda-egov-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
```

2. Download the service account key and set `GOOGLE_APPLICATION_CREDENTIALS`

## Authentication Flow

### 1. User Authentication
```
1. User sends WhatsApp message
2. System checks for existing session
3. If no session, initiate OAuth flow
4. User authenticates via Google Identity Platform
5. System receives ID token
6. Token is verified using Firebase Admin SDK
7. User session is created in Firestore
8. Subsequent requests use cached session
```

### 2. Token Management
```
1. ADK handles token refresh automatically
2. Expired tokens trigger re-authentication
3. Session state is maintained in Firestore
4. Cleanup tasks remove expired sessions
```

## Security Features

### 1. Token Security
- JWT tokens with short expiration times
- Automatic token refresh
- Secure token storage in session state
- Token validation on every request

### 2. Session Security
- Session timeout (30 minutes default)
- Automatic cleanup of expired sessions
- Secure session storage in Firestore
- Session invalidation on logout

### 3. Infrastructure Security
- Google Cloud's security infrastructure
- Encrypted data in transit and at rest
- IAM-based access controls
- Audit logging

## Monitoring and Observability

### 1. Google Cloud Logging
- Structured logging for all authentication events
- Centralized log aggregation
- Real-time log streaming
- Log-based alerting

### 2. Google Cloud Monitoring
- Custom metrics for authentication success/failure rates
- Session duration and count metrics
- Error rate monitoring
- Performance monitoring

### 3. Health Checks
- Firestore connectivity checks
- Authentication service health
- Session manager status
- Agent system health

## Migration Checklist

- [ ] Set up Google Cloud Project
- [ ] Enable required APIs
- [ ] Configure Firebase Authentication
- [ ] Set up Identity Platform
- [ ] Create service account and download key
- [ ] Update environment variables
- [ ] Install new dependencies
- [ ] Test authentication flow
- [ ] Verify session management
- [ ] Test monitoring and logging
- [ ] Update deployment configuration
- [ ] Migrate existing user data (if needed)

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check OAuth client configuration
   - Verify redirect URIs
   - Ensure service account has correct permissions

2. **Firestore Connection Issues**
   - Verify service account credentials
   - Check Firestore API is enabled
   - Ensure proper IAM roles

3. **Token Validation Errors**
   - Check Firebase project configuration
   - Verify token expiration settings
   - Ensure clock synchronization

### Debug Commands

```bash
# Test Firestore connection
gcloud firestore databases list

# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Test authentication
gcloud auth application-default login
```

## Performance Considerations

### 1. Caching Strategy
- In-memory session caching
- Firestore read optimization
- Token caching with TTL

### 2. Scaling
- Firestore automatic scaling
- Connection pooling
- Async operations

### 3. Cost Optimization
- Efficient Firestore queries
- Session cleanup to reduce storage
- Monitoring usage patterns

## Conclusion

The migration to Google Cloud authentication provides:

1. **Better Integration**: Native ADK support eliminates external dependencies
2. **Enhanced Security**: Enterprise-grade authentication infrastructure
3. **Improved Scalability**: Google Cloud's global infrastructure
4. **Cost Efficiency**: Pay-per-use model with generous free tiers
5. **Better Monitoring**: Integrated observability tools

The new architecture is more maintainable, secure, and scalable while providing the same functionality as the previous Supabase implementation.