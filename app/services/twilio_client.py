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
        
        print(f"🔧 TWILIO CLIENT INITIALIZATION:")
        print(f"   Account SID: {self.account_sid}")
        print(f"   Auth Token: {'SET' if self.auth_token else 'NOT SET'}")
        print(f"   WhatsApp Number: {self.from_number}")
        print(f"   API Key SID: {self.api_key_sid}")
        
        # Initialize Twilio client - Use Account SID + Auth Token (standard method)
        try:
            self.client = Client(self.account_sid, self.auth_token)
            print(f"   ✅ Twilio client initialized with Account SID + Auth Token")
            logger.info("Twilio WhatsApp client initialized with Account SID + Auth Token")
        except Exception as e:
            print(f"   ❌ Twilio client initialization failed: {e}")
            logger.error(f"Twilio client initialization failed: {e}")
            raise
    
    async def send_text_message(self, to_number: str, message: str) -> dict:
        """Send a text message via Twilio WhatsApp"""
        try:
            print(f"🔧 TWILIO CLIENT - SENDING MESSAGE:")
            print(f"   To: {to_number}")
            print(f"   From: {self.from_number}")
            print(f"   Message length: {len(message)} chars")
            
            # Format WhatsApp number if needed
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Format from number if needed
            from_number = self.from_number
            if not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            
            print(f"   Formatted To: {to_number}")
            print(f"   Formatted From: {from_number}")
            
            # Send message using Twilio client
            print(f"   📞 Calling Twilio API...")
            
            # Run the synchronous Twilio call in a thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            
            def send_message():
                return self.client.messages.create(
                    body=message,
                    from_=from_number,
                    to=to_number
                )
            
            # Execute in thread pool to avoid blocking
            twilio_message = await loop.run_in_executor(None, send_message)
            
            print(f"   ✅ Twilio API call successful!")
            print(f"   📧 Message SID: {twilio_message.sid}")
            print(f"   📊 Message status: {twilio_message.status}")
            
            logger.info(f"Sent Twilio WhatsApp message to {to_number}, SID: {twilio_message.sid}")
            return {
                "status": "success", 
                "message_id": twilio_message.sid,
                "twilio_status": twilio_message.status
            }
            
        except Exception as e:
            print(f"   ❌ Twilio API error:")
            print(f"   Error: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
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