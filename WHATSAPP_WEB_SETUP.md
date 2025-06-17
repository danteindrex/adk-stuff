# WhatsApp Web Automation Setup

This guide will help you set up WhatsApp Web automation for the Uganda E-Gov Helpdesk instead of using Twilio.

## Overview

The system now uses headless browser automation to interact with WhatsApp Web directly, eliminating the need for Twilio API credentials and costs.

**Phone Number**: +256726294861

## Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Chrome/Chromium browser (installed automatically)
- WhatsApp account with the phone number +256726294861

## Installation

### 1. Install Dependencies

```bash
# Run the installation script
python install_whatsapp_web.py
```

Or manually:

```bash
# Install Playwright
pip install playwright

# Install browser
playwright install chromium

# Install additional dependencies
pip install python-json-logger
```

### 2. Set Up WhatsApp Web Authentication

```bash
# First-time setup (will open browser for QR code scanning)
python start_whatsapp_web.py
```

**Steps:**
1. The script will open a browser window
2. Navigate to WhatsApp Web
3. Open WhatsApp on your phone (+256726294861)
4. Go to Settings > Linked Devices
5. Tap "Link a Device"
6. Scan the QR code displayed in the browser
7. Wait for authentication confirmation

### 3. Test the Setup

```bash
# Test if WhatsApp Web is working
python start_whatsapp_web.py test
```

## Usage Options

### Option 1: Standalone Message Listener

Run a dedicated message listener that processes incoming WhatsApp messages:

```bash
python whatsapp_web_listener.py
```

This will:
- Listen for incoming WhatsApp messages
- Process them with AI agents
- Send automated responses
- Run continuously until stopped (Ctrl+C)

### Option 2: Full Application Server

Run the complete FastAPI server with WhatsApp Web integration:

```bash
python main.py
```

This includes:
- WhatsApp Web automation
- Web API endpoints
- Admin dashboard
- Full agent system

## Features

### Automated Message Processing

- **Incoming Messages**: Automatically detected and processed
- **AI Responses**: Intelligent responses using ADK agents
- **Service Integration**: Direct integration with Uganda government services
- **Multi-language**: Support for English, Luganda, Luo, and Runyoro

### Supported Services

1. **Birth Certificate (NIRA)**
   - Status checking
   - Application guidance
   - Office locations

2. **Tax Services (URA)**
   - Balance inquiries
   - TIN validation
   - Tax obligations

3. **NSSF Services**
   - Contribution balance
   - Statement requests
   - History lookup

4. **Land Verification**
   - Ownership verification
   - Title status
   - Property information

### Message Examples

**User**: "Hello"
**Bot**: "🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk! I can help you with Birth Certificate, Tax Services, NSSF Balance, and Land Verification. What would you like help with today?"

**User**: "Check my birth certificate NIRA/2023/123456"
**Bot**: *Processes request and provides status update*

**User**: "My TIN is 1234567890"
**Bot**: *Checks tax balance and provides information*

## API Endpoints

When running the full server, these endpoints are available:

- `GET /api/whatsapp-web/status` - Check WhatsApp Web connection status
- `POST /api/whatsapp-web/send` - Send message via WhatsApp Web
- `POST /api/whatsapp-web/restart` - Restart WhatsApp Web client
- `GET /health` - System health check

## Configuration

### Environment Variables

The system uses these environment variables (optional for WhatsApp Web):

```bash
# Optional - for fallback or hybrid mode
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+256726294861

# Required for other services
JWT_SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key
```

### Session Persistence

WhatsApp Web sessions are saved in the `whatsapp_session/` directory to avoid re-authentication on restart.

## Troubleshooting

### Common Issues

1. **QR Code Not Appearing**
   ```bash
   # Try running with visible browser
   # Edit whatsapp_web_client.py and set headless=False
   ```

2. **Authentication Timeout**
   ```bash
   # Increase timeout or try again
   python start_whatsapp_web.py
   ```

3. **Browser Not Found**
   ```bash
   # Reinstall browser
   playwright install chromium
   ```

4. **Permission Errors**
   ```bash
   # Check file permissions
   chmod +x *.py
   ```

### Logs and Debugging

- Logs are saved to `logs/app.log`
- Enable debug mode by setting `DEBUG=true`
- Check browser console for JavaScript errors

### Performance Tips

1. **Resource Usage**: Browser automation uses more resources than API calls
2. **Session Management**: Keep sessions active to avoid re-authentication
3. **Message Polling**: Adjust polling interval based on message volume
4. **Concurrent Users**: System handles multiple conversations simultaneously

## Security Considerations

1. **Session Security**: WhatsApp Web sessions are stored locally
2. **Phone Number**: Only use with authorized phone numbers
3. **Data Privacy**: Messages are processed locally, not sent to third parties
4. **Access Control**: Secure the server environment

## Migration from Twilio

If migrating from Twilio:

1. **Backup**: Save existing Twilio configuration
2. **Test**: Run both systems in parallel initially
3. **Switch**: Update webhook URLs to use WhatsApp Web endpoints
4. **Monitor**: Check message delivery and response times

## Support

For issues or questions:

1. Check logs in `logs/app.log`
2. Run diagnostic: `python start_whatsapp_web.py test`
3. Restart services: `python main.py`
4. Review this documentation

## Advantages over Twilio

1. **Cost**: No API fees or usage charges
2. **Features**: Full WhatsApp feature support
3. **Control**: Direct control over messaging
4. **Flexibility**: Custom automation possibilities
5. **Independence**: No dependency on third-party APIs

## Limitations

1. **Reliability**: Depends on WhatsApp Web stability
2. **Resources**: Higher server resource usage
3. **Maintenance**: Requires session management
4. **Scale**: May need optimization for high volume

---

**Phone Number**: +256726294861  
**System**: Uganda E-Gov WhatsApp Helpdesk  
**Technology**: Playwright + WhatsApp Web Automation