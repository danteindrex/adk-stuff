# WhatsApp Clone - Uganda E-Gov Assistant

A pixel-perfect WhatsApp clone with Google OAuth authentication and AI-powered government services assistant.

## Features

- 🎨 **Identical WhatsApp UI** - Pixel-perfect recreation of WhatsApp Web interface
- 🔐 **Google OAuth Login** - Secure authentication with Google accounts
- 🤖 **AI Assistant Integration** - Connected to Uganda E-Gov AI backend
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
- 📞 **Twilio Integration** - Optional real WhatsApp message sending
- 💾 **Local Storage** - Saves chat history and user preferences
- 🌐 **PWA Ready** - Can be installed as a Progressive Web App

## Setup Instructions

### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized origins:
   - `http://localhost:8081`
   - `http://localhost:8080`
   - Your production domain
7. Copy the Client ID and add it to your environment variables

### 2. Environment Variables

Add these to your `.env` file:

```bash
# Google OAuth


# Twilio (already configured in your main app)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 3. Running the Application

#### Option 1: Standalone Server
```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the WhatsApp clone server
python whatsapp_clone_server.py
```

The app will be available at: `http://localhost:8081`

#### Option 2: Integrated with Main App
Add these routes to your main FastAPI app:

```python
# Add to main.py
from whatsapp_clone_server import clone_app

# Mount the WhatsApp clone
app.mount("/whatsapp-clone", clone_app)
```

Then access at: `http://localhost:8080/whatsapp-clone`

### 4. Demo Mode

If you don't want to set up Google OAuth immediately, you can use the demo mode:

1. Click "Try Demo (No Login Required)" on the login screen
2. This creates a demo user and lets you test all features
3. Perfect for development and demonstrations

## Usage

### Login Options

1. **Google OAuth**: Click the Google sign-in button
2. **Demo Mode**: Click "Try Demo" for immediate access

### Messaging

1. Type your message in the input field at the bottom
2. Press Enter or click the send button
3. The AI will respond with government service information
4. All messages are saved locally in your browser

### Twilio Integration

1. Click the menu (three dots) in the top right
2. Select "Twilio Settings"
3. Enter your WhatsApp number
4. Enable "Send messages to actual WhatsApp"
5. Now messages will be sent to both the web interface and real WhatsApp

### Features Available

The AI assistant can help with:

- **Birth Certificate (NIRA)** - Check status with reference number
- **Tax Status (URA)** - Check balance with TIN number
- **NSSF Balance** - Check contributions with membership number
- **Land Verification (NLIS)** - Verify ownership with plot details
- **Multi-language support** - English, Luganda, Luo, and Runyoro

## File Structure

```
whatsapp_clone/
├── index.html          # Main HTML file
├── styles.css          # WhatsApp-identical styling
├── script.js           # JavaScript functionality
└── README.md           # This file

whatsapp_clone_server.py # FastAPI server integration
```

## API Endpoints

- `GET /` - Serve the WhatsApp clone interface
- `POST /whatsapp/webhook` - Handle web messages (connects to AI)
- `POST /api/twilio/send` - Send messages via Twilio
- `GET /api/health` - Health check
- `GET /manifest.json` - PWA manifest
- `GET /sw.js` - Service worker for PWA

## Customization

### Changing Colors
Edit `styles.css` and modify these CSS variables:
- `#25d366` - WhatsApp green
- `#111b21` - Dark background
- `#202c33` - Chat background

### Adding Features
1. Add new functions to `script.js`
2. Add corresponding HTML elements to `index.html`
3. Style with CSS in `styles.css`

### Backend Integration
The clone connects to your existing AI backend via:
- `/whatsapp/webhook` endpoint
- Uses the same `generate_simple_response` function
- Integrates with monitoring and Twilio services

## Security Notes

- Google OAuth tokens are handled securely
- User data is stored locally (not on server)
- HTTPS recommended for production
- Environment variables for sensitive data

## Troubleshooting

### Google OAuth Issues
1. Check that your domain is in authorized origins
2. Verify the Client ID is correct
3. Make sure Google+ API is enabled

### Twilio Issues
1. Verify your Twilio credentials in `.env`
2. Check that your WhatsApp number is verified
3. Ensure Twilio sandbox is configured

### AI Backend Issues
1. Make sure your main AI server is running
2. Check that `/whatsapp/webhook` endpoint is accessible
3. Verify environment variables are loaded

## Production Deployment

1. Set up HTTPS (required for Google OAuth)
2. Configure proper CORS origins
3. Set production Google OAuth origins
4. Use environment variables for all secrets
5. Consider using a reverse proxy (nginx)

## Browser Support

- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## PWA Installation

Users can install the app on their devices:
1. Visit the site in a supported browser
2. Look for "Install" prompt or menu option
3. The app will work offline with cached content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for demonstration purposes. WhatsApp is a trademark of Meta Platforms, Inc.