#!/usr/bin/env python3
"""
WhatsApp Auto Responder
Automatically detects and responds to incoming WhatsApp messages
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.whatsapp_web_client import WhatsAppWebClient
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class WhatsAppAutoResponder:
    """Automatically respond to WhatsApp messages"""
    
    def __init__(self):
        self.client = None
        self.running = False
        self.processed_messages = set()  # Track processed messages to avoid duplicates
    
    async def initialize(self):
        """Initialize the auto responder"""
        try:
            print("🤖 Initializing WhatsApp Auto Responder")
            print("=" * 50)
            print("📱 Phone Number: +256726294861")
            print("🇺🇬 Uganda E-Gov WhatsApp Helpdesk")
            print("=" * 50)
            
            # Initialize WhatsApp Web client (will auto-detect headless mode)
            self.client = WhatsAppWebClient("+256726294861")
            
            print("🚀 Starting WhatsApp Web client...")
            success = await self.client.start()
            
            if not success:
                print("❌ Failed to start WhatsApp Web client")
                return False
            
            if not self.client.is_authenticated:
                print("❌ WhatsApp Web not authenticated")
                if not self.client.headless:
                    print("📱 Please scan the QR code in the browser window")
                    print("⏰ Waiting for authentication...")
                    # Wait for authentication
                    authenticated = await self.client._wait_for_authentication(timeout=300)  # 5 minutes
                    if not authenticated:
                        print("❌ Authentication timeout")
                        return False
                else:
                    print("💡 Session expired. Please run setup again:")
                    print("   python start_with_browser.py")
                    return False
            
            print("✅ WhatsApp Web authenticated and ready!")
            print(f"🔇 Running in {'headless' if self.client.headless else 'visible'} mode")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize auto responder: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def generate_response(self, message_text: str, from_contact: str) -> str:
        """Generate intelligent response to message"""
        try:
            message_lower = message_text.lower().strip()
            
            # Greeting responses
            if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start', 'hola', 'ola']):
                return """🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk!

I can help you with:
• 📋 Birth Certificate (NIRA) - Check status & applications
• 💰 Tax Services (URA) - Check balance & TIN validation  
• 🏦 NSSF Balance - Check contributions & statements
• 🏡 Land Verification - Verify ownership & title status

What would you like help with today?

Type the service name or describe what you need."""
            
            # Birth certificate services
            elif any(word in message_lower for word in ['birth', 'certificate', 'nira']):
                return """📋 Birth Certificate Services (NIRA)

I can help you with:
• ✅ Check application status
• 📝 New application requirements
• 🏢 Find nearest NIRA office
• 📞 Contact information

Please provide:
- Your reference number (if checking status)
- Or tell me what specific help you need

Example: "Check status NIRA/2023/123456" """
            
            # Tax services
            elif any(word in message_lower for word in ['tax', 'ura', 'tin']):
                return """💰 Tax Services (URA)

I can help you with:
• 💳 Check tax balance
• 🆔 TIN validation
• 📄 Tax clearance status
• 📋 Tax obligations

Please provide:
- Your TIN number
- Or tell me what you need help with

Example: "My TIN is 1234567890" """
            
            # NSSF services
            elif any(word in message_lower for word in ['nssf', 'social security', 'pension']):
                return """🏦 NSSF Services

I can help you with:
• 💰 Check contribution balance
• 📊 Get contribution statement
• 📈 View contribution history
• 📞 Contact NSSF

Please provide:
- Your NSSF membership number
- Or tell me what you need

Example: "Check my NSSF balance 123456789" """
            
            # Land services
            elif any(word in message_lower for word in ['land', 'title', 'property', 'plot']):
                return """🏡 Land Verification Services

I can help you with:
• ✅ Verify land ownership
• 📋 Check title status
• 🗺️  Get land information
• 🏢 Find land offices

Please provide:
- Plot number and location
- Or describe what you need

Example: "Verify plot 123 in Kampala" """
            
            # Help and menu
            elif any(word in message_lower for word in ['help', 'menu', 'services', 'what']):
                return """ℹ️ Uganda E-Gov WhatsApp Helpdesk Services

🔹 Birth Certificate (NIRA)
   Type: "birth certificate" or "nira"

🔹 Tax Services (URA)  
   Type: "tax" or "ura"

🔹 NSSF Services
   Type: "nssf" or "pension"

🔹 Land Verification
   Type: "land" or "property"

🔹 General Help
   Type: "help" for this menu

Available in: English, Luganda, Luo, Runyoro

How can I assist you today?"""
            
            # Thank you responses
            elif any(word in message_lower for word in ['thank', 'thanks', 'asante']):
                return """🙏 You're welcome! 

I'm here to help with Uganda government services anytime.

Need anything else? Just ask!

🇺🇬 Uganda E-Gov WhatsApp Helpdesk"""
            
            # Default response for unrecognized messages
            else:
                return f"""🇺🇬 Hello! I'm the Uganda E-Gov assistant.

I can help you with government services:

📋 Birth Certificate - Type "birth certificate"
💰 Tax Services - Type "tax services"  
🏦 NSSF Balance - Type "nssf"
🏡 Land Verification - Type "land"

Or describe what you need help with.

Available 24/7 to serve Ugandan citizens! 🇺🇬"""
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Hello! I'm the Uganda E-Gov assistant. How can I help you with government services today?"
    
    async def process_message(self, message_data: dict):
        """Process an incoming message and send response"""
        try:
            from_contact = message_data.get('from', 'Unknown')
            message_text = message_data.get('text', '')
            message_id = message_data.get('message_id', '')
            
            # Skip if already processed
            if message_id in self.processed_messages:
                return
            
            # Add to processed set
            self.processed_messages.add(message_id)
            
            print(f"\n📨 New message from {from_contact}:")
            print(f"   📝 Text: {message_text[:100]}...")
            print(f"   🆔 ID: {message_id}")
            
            # Extract phone number
            phone_number = self._extract_phone_number(from_contact)
            
            if not phone_number:
                print(f"⚠️  Could not extract phone number from: {from_contact}")
                return
            
            # Generate response
            print("🤖 Generating response...")
            response_text = await self.generate_response(message_text, from_contact)
            
            # Send response
            print(f"📤 Sending response to {phone_number}...")
            result = await self.client.send_message(phone_number, response_text)
            
            if result.get("status") == "success":
                print("✅ Response sent successfully!")
                logger.info(f"Sent response to {phone_number}: {len(response_text)} chars")
            else:
                print(f"❌ Failed to send response: {result.get('error')}")
                logger.error(f"Failed to send response to {phone_number}: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            print(f"❌ Error processing message: {e}")
    
    def _extract_phone_number(self, contact_name: str) -> str:
        """Extract phone number from contact name"""
        try:
            # Clean the contact name
            clean_contact = contact_name.strip()
            
            # If it's already a phone number format
            if clean_contact.replace('+', '').replace(' ', '').replace('-', '').isdigit():
                return clean_contact
            
            # Look for phone number patterns
            import re
            phone_patterns = [
                r'(\+256\d{9})',  # Uganda format
                r'(\+\d{10,15})', # International format
                r'(256\d{9})',    # Uganda without +
                r'(\d{10,15})'    # Generic long number
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, clean_contact)
                if match:
                    return match.group(1)
            
            # If no phone number found, return as-is
            return clean_contact
            
        except Exception as e:
            logger.error(f"Error extracting phone number: {e}")
            return contact_name
    
    async def start_auto_responding(self):
        """Start the auto responder"""
        if not self.client or not self.client.is_authenticated:
            print("❌ Client not ready")
            return
        
        print("\n🤖 Starting Auto Responder...")
        print("📱 Monitoring WhatsApp messages...")
        print("🔄 Will automatically respond to incoming messages")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        self.running = True
        
        try:
            # Add message handler
            await self.client.add_message_handler(self.process_message)
            
            # Start message polling with faster interval for responsiveness
            await self.client.start_message_polling(interval=2)
            
        except KeyboardInterrupt:
            print("\n⏹️  Stopping auto responder...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in auto responder: {e}")
            print(f"❌ Auto responder error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up...")
        if self.client:
            await self.client.stop()
        print("✅ Cleanup complete")

async def main():
    """Main function"""
    responder = WhatsAppAutoResponder()
    
    # Initialize
    success = await responder.initialize()
    if not success:
        print("❌ Failed to initialize auto responder")
        return
    
    # Start auto responding
    await responder.start_auto_responding()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Auto responder stopped!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)