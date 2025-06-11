import os
import logging
from twilio.rest import Client
from app.core.config import settings

logger = logging.getLogger(__name__)

class TwilioClient:
    """Twilio WhatsApp client for sending messages"""
    
    def __init__(self):
        """Initialize Twilio client with credentials from settings"""
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER
        self.api_key_sid = settings.TWILIO_API_KEY_SID
        
        # Initialize Twilio client
        if self.api_key_sid:
            # Use API Key authentication if available (more secure)
            self.client = Client(self.api_key_sid, self.auth_token, self.account_sid)
            logger.info("Twilio WhatsApp client initialized with API Key")
        else:
            # Fall back to Account SID + Auth Token
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio WhatsApp client initialized")
    
    async def send_text_message(self, to_number: str, message: str) -> dict:
        """Send a text message via Twilio WhatsApp"""
        try:
            # Format WhatsApp number if needed
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Format from number if needed
            from_number = self.from_number
            if not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            
            # Send message
            message = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"Sent Twilio WhatsApp message to {to_number}, SID: {message.sid}")
            return {"status": "success", "message_id": message.sid}
            
        except Exception as e:
            logger.error(f"Failed to send Twilio WhatsApp message: {e}")
            return {"status": "error", "error": str(e)}
    
    async def send_template_message(self, to_number: str, template_name: str, 
                                  template_params: list = None) -> dict:
        """Send a template message via Twilio WhatsApp"""
        try:
            # Format WhatsApp number if needed
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Format from number if needed
            from_number = self.from_number
            if not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            
            # Construct message body with template
            # Note: Twilio doesn't support WhatsApp templates directly like Meta API
            # We'll need to format the message manually
            message_body = self._format_template(template_name, template_params)
            
            # Send message
            message = self.client.messages.create(
                body=message_body,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"Sent Twilio WhatsApp template message to {to_number}, SID: {message.sid}")
            return {"status": "success", "message_id": message.sid}
            
        except Exception as e:
            logger.error(f"Failed to send Twilio WhatsApp template message: {e}")
            return {"status": "error", "error": str(e)}
    
    def _format_template(self, template_name: str, template_params: list = None) -> str:
        """Format a template message for Twilio WhatsApp"""
        # This is a simplified implementation
        # You'll need to create a proper template system based on your needs
        templates = {
            "welcome": "Welcome to Uganda E-Gov WhatsApp Helpdesk! How can I help you today?",
            "error": "Sorry, we encountered an error: {0}",
            "confirmation": "Your request has been confirmed. Reference number: {0}"
        }
        
        template = templates.get(template_name, "")
        if template and template_params:
            try:
                template = template.format(*template_params)
            except Exception as e:
                logger.error(f"Error formatting template: {e}")
        
        return template