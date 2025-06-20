# 🌐 Uganda E-Gov WhatsApp Helpdesk API Documentation

## 📋 Table of Contents
- [API Overview](#-api-overview)
- [Authentication](#-authentication)
- [Rate Limiting](#-rate-limiting)
- [Endpoints](#-endpoints)
  - [WhatsApp Webhooks](#whatsapp-webhooks)
  - [Health Checks](#health-checks)
  - [Admin Endpoints](#admin-endpoints)
  - [User Management](#user-management)
  - [Session Management](#session-management)
  - [Message Management](#message-management)
  - [System Information](#system-information)
- [Error Handling](#-error-handling)
- [WebSocket Support](#-websocket-support)
- [Monitoring & Metrics](#-monitoring--metrics)
- [Response Formats](#-response-formats)

## 🌟 API Overview

The Uganda E-Gov WhatsApp Helpdesk API provides a comprehensive interface for:
- Processing WhatsApp messages via webhooks
- Managing user sessions and conversations
- Administering the system
- Monitoring system health and performance

The API follows RESTful principles and returns JSON responses. All endpoints are prefixed with `/api/v1/`.

## 🔒 Authentication

Most endpoints require authentication using JWT tokens. Include the token in the `Authorization` header:

```http
Authorization: Bearer your-jwt-token-here
```

### Obtaining a Token

1. **Admin Dashboard Login**
   - Visit `/admin/login`
   - Use your admin credentials
   - The JWT token will be returned in the response

2. **Programmatic Access**
   ```http
   POST /api/v1/auth/login
   Content-Type: application/json
   
   {
     "username": "admin",
     "password": "your-secure-password"
   }
   ```

## ⚡ Rate Limiting

- Public endpoints: 60 requests per minute
- Authenticated endpoints: 300 requests per minute
- Admin endpoints: 1000 requests per minute

Exceeding limits returns a `429 Too Many Requests` response.

## 📡 Endpoints

### WhatsApp Webhooks

#### Receive WhatsApp Messages
```http
POST /api/v1/webhooks/whatsapp
Content-Type: application/json

{
  "From": "whatsapp:+256XXXXXXXXX",
  "Body": "Hello, I need help with my tax return"
}
```

**Response**
```json
{
  "status": "success",
  "message": "Message received and being processed"
}
```

### Health Checks

#### Service Health
```http
GET /health
```

**Response**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-06-20T13:15:30Z",
  "services": {
    "database": {
      "status": "up",
      "latency_ms": 12.5
    },
    "cache": {
      "status": "up"
    },
    "ai_service": {
      "status": "up",
      "provider": "Gemini"
    }
  }
}
```

#### Readiness Check
```http
GET /ready
```

**Response**
```json
{
  "status": "ready",
  "services": ["database", "cache", "ai_service"],
  "ready": true
}
```

### User Management

#### Create User
```http
POST /api/v1/users
Content-Type: application/json
Authorization: Bearer your-jwt-token

{
  "phone_number": "+256XXXXXXXXX",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "role": "user"
}
```

**Response**
```json
{
  "id": "user_123",
  "phone_number": "+256XXXXXXXXX",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "role": "user",
  "created_at": "2025-06-20T13:15:30Z"
}
```

### Session Management

#### Create Session
```http
POST /api/v1/sessions
Content-Type: application/json
Authorization: Bearer your-jwt-token

{
  "user_id": "user_123",
  "metadata": {
    "device_info": "iPhone 13, iOS 16",
    "location": "Kampala, Uganda"
  }
}
```

**Response**
```json
{
  "session_id": "sess_xyz",
  "user_id": "user_123",
  "status": "active",
  "created_at": "2025-06-20T13:15:30Z",
  "last_active": "2025-06-20T13:15:30Z"
}
```

### Message Management

#### Send Message
```http
POST /api/v1/messages
Content-Type: application/json
Authorization: Bearer your-jwt-token

{
  "session_id": "sess_xyz",
  "content": "Hello, how can I help you today?",
  "type": "text",
  "sender": "bot"
}
```

**Response**
```json
{
  "message_id": "msg_abc",
  "session_id": "sess_xyz",
  "content": "Hello, how can I help you today?",
  "type": "text",
  "sender": "bot",
  "timestamp": "2025-06-20T13:15:30Z",
  "status": "sent"
}
```

### System Information

#### Get System Stats
```http
GET /api/v1/system/stats
Authorization: Bearer your-admin-token
```

**Response**
```json
{
  "users": {
    "total": 1500,
    "active_today": 342,
    "new_today": 28
  },
  "messages": {
    "total": 125000,
    "today": 1245,
    "avg_response_time_ms": 1240
  },
  "system": {
    "uptime_days": 14,
    "version": "1.0.0",
    "environment": "production"
  }
}
```

## ❌ Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid request parameters",
  "status": 400,
  "error": "VALIDATION_ERROR",
  "details": [
    {
      "loc": ["body", "phone_number"],
      "msg": "Invalid phone number format",
      "type": "value_error"
    }
  ]
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials",
  "status": 401,
  "error": "UNAUTHORIZED"
}
```

#### 404 Not Found
```json
{
  "detail": "User not found",
  "status": 404,
  "error": "NOT_FOUND"
}
```

#### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded: 60 per minute",
  "status": 429,
  "error": "RATE_LIMIT_EXCEEDED",
  "retry_after_seconds": 30
}
```

## 🔌 WebSocket Support

### Real-time Updates
Connect to `wss://your-domain.com/ws` for real-time updates.

**Events**
- `message:new`: New incoming message
- `message:status`: Message status update
- `user:typing`: User is typing
- `session:update`: Session state changed

## 📊 Monitoring & Metrics

### Prometheus Metrics
Scrape metrics from `/metrics` endpoint.

### Key Metrics
- `http_requests_total`
- `http_request_duration_seconds`
- `active_sessions`
- `messages_processed_total`
- `ai_requests_total`

## 📝 Response Formats

### Standard Response
```json
{
  "status": "success",
  "data": {},
  "meta": {
    "request_id": "req_123",
    "timestamp": "2025-06-20T13:15:30Z"
  }
}
```

### Paginated Response
```json
{
  "status": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "meta": {}
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "Invalid input provided",
    "details": {}
  },
  "meta": {}
}
```

## 🔄 Webhook Payloads

### Incoming WhatsApp Message
```json
{
  "MessageSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "SmsMessageSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "From": "whatsapp:+256XXXXXXXXX",
  "To": "whatsapp:+14155238886",
  "Body": "Hello, I need help with my tax return",
  "NumMedia": "0",
  "ProfileName": "John Doe"
}
```

### Outgoing WhatsApp Message
```json
{
  "to": "whatsapp:+256XXXXXXXXX",
  "from": "whatsapp:+14155238886",
  "body": "Hello! How can I assist you with your tax return?",
  "status_callback": "https://your-domain.com/webhooks/message/status"
}
```

## 📚 Additional Resources

- [Twilio WhatsApp API Documentation](https://www.twilio.com/docs/whatsapp/api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Schema](/docs)
- [Admin Dashboard](/admin)

## 📞 Support

For support, please contact:
- Email: support@uganda-egov.ug
- Phone: +256 200 000000
- Hours: 24/7

---

*Last Updated: June 20, 2025*
