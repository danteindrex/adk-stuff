#!/usr/bin/env python3
"""
WhatsApp Web Message Listener
Standalone script to listen for incoming WhatsApp messages and process them
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.whatsapp_web_client import WhatsAppWebClient
from app.agents.agent import create_root_agent
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class WhatsAppMessageListener:
    """Listen for and process WhatsApp messages"""
    
    def __init__(self):
        self.client = None
        self.agent = None
        self.running = False
    
    async def initialize(self):
        """Initialize the listener"""
        try:
            print("🚀 Initializing WhatsApp Web Message Listener")
            print("=" * 50)
            
            # Initialize WhatsApp Web client
            print("📱 Starting WhatsApp Web client...")
            self.client = WhatsAppWebClient("+256726294861")
            success = await self.client.start()
            
            if not success or not self.client.is_authenticated:
                print("❌ WhatsApp Web client not authenticated")
                print("💡 Run: python start_whatsapp_web.py")
                return False
            
            print("✅ WhatsApp Web client ready")
            
            # Initialize agent system
            print("🤖 Initializing AI agent...")
            try:
                self.agent = await create_root_agent()
                print("✅ AI agent ready")
            except Exception as e:
                print(f"⚠️  AI agent failed to initialize: {e}")
                print("📝 Will use simple responses")
                self.agent = None
            
            # Add message handler
            await self.client.add_message_handler(self.handle_message)
            
            print("🎉 Message listener initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize listener: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def handle_message(self, message):
        """Handle incoming WhatsApp message"""
        try:
            from_contact = message.get('from', 'Unknown')
            message_text = message.get('text', '')
            
            print(f"\n📨 New message from {from_contact}:")
            print(f"   Message: {message_text[:100]}...")
            
            # Extract phone number
            phone_number = self._extract_phone_number(from_contact)
            
            if not phone_number:
                print(f"⚠️  Could not extract phone number from: {from_contact}")
                return
            
            # Generate response
            response_text = await self._generate_response(message_text, phone_number)
            
            # Send response
            if response_text:
                print(f"📤 Sending response to {phone_number}...")
                result = await self.client.send_message(phone_number, response_text)
                
                if result.get("status") == "success":
                    print("✅ Response sent successfully!")
                else:
                    print(f"❌ Failed to send response: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            print(f"❌ Error handling message: {e}")
    
    def _extract_phone_number(self, contact_name):
        """Extract phone number from contact name"""
        try:
            # If contact name is already a phone number
            if contact_name.replace('+', '').replace(' ', '').replace('-', '').isdigit():
                return contact_name
            
            # Look for phone number patterns
            import re
            phone_pattern = r'(\+?256\d{9}|\+?\d{10,15})'
            match = re.search(phone_pattern, contact_name)
            
            if match:
                return match.group(1)
            
            # Return as-is if no pattern found
            return contact_name
            
        except Exception as e:
            logger.error(f"Error extracting phone number: {e}")
            return contact_name
    
    async def _generate_response(self, message_text, phone_number):
        """Generate response to message"""
        try:
            if self.agent:
                # Use AI agent for intelligent response
                from google.adk.events import Event
                from google.genai.types import Content, Part
                
                event = Event(
                    content=Content(parts=[Part(text=message_text)]),
                    metadata={
                        "user_id": phone_number.replace("+", "").replace("whatsapp:", ""),
                        "source": "whatsapp_web",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Process with agent (simplified - you might need to set up ADK runner)
                # For now, use a simple response
                response = await self._simple_response(message_text)
                return response
            else:
                # Use simple response
                return await self._simple_response(message_text)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Hello! I'm the Uganda E-Gov assistant. How can I help you today?"
    
    async def _simple_response(self, message_text):
        """Generate simple response"""
        message_lower = message_text.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return """🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk!

I can help you with:
• Birth Certificate (NIRA) - Check status
• Tax Services (URA) - Check balance  
• NSSF Balance - Check contributions
• Land Verification - Verify ownership

What would you like help with today?"""
        
        elif any(word in message_lower for word in ['birth', 'certificate', 'nira']):
            return """📋 Birth Certificate Services (NIRA)

I can help you:
• Check application status
• Get requirements for new application
• Find nearest NIRA office

Please provide your reference number or tell me what you need help with."""
        
        elif any(word in message_lower for word in ['tax', 'ura', 'tin']):
            return """💰 Tax Services (URA)

I can help you:
• Check tax balance
• Get tax clearance status
• Find tax obligations

Please provide your TIN number or tell me what you need."""
        
        elif any(word in message_lower for word in ['nssf', 'social security']):
            return """🏦 NSSF Services

I can help you:
• Check contribution balance
• Get statement
• Find contribution history

Please provide your NSSF number or tell me what you need."""
        
        elif any(word in message_lower for word in ['land', 'title', 'property']):
            return """🏡 Land Verification Services

I can help you:
• Verify land ownership
• Check title status
• Get land information

Please provide plot details or tell me what you need."""
        
        else:
            return """🇺🇬 Uganda E-Gov WhatsApp Helpdesk

I can help you with:
• Birth Certificate (NIRA)
• Tax Services (URA)
• NSSF Balance
• Land Verification

Please tell me which service you need, or type 'help' for more information."""
    
    async def start_listening(self):
        """Start listening for messages"""
        if not self.client or not self.client.is_authenticated:
            print("❌ Client not ready")
            return
        
        print("\n🔄 Starting message listener...")
        print("📱 Listening for WhatsApp messages...")
        print("⏹️  Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            # Start message polling
            await self.client.start_message_polling(interval=3)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping message listener...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
            print(f"❌ Listener error: {e}")
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
    listener = WhatsAppMessageListener()
    
    # Initialize
    success = await listener.initialize()
    if not success:
        print("❌ Failed to initialize listener")
        return
    
    # Start listening
    await listener.start_listening()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)