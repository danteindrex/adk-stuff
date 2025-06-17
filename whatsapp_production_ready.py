#!/usr/bin/env python3
"""
Production-Ready WhatsApp Automation for Google Cloud Run
Uses Twilio WhatsApp API instead of web automation for cloud deployment
"""

import asyncio
import sys
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.twilio_client import TwilioClient
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class ProductionWhatsAppClient:
    """Production-ready WhatsApp client using Twilio API for Cloud Run deployment"""
    
    def __init__(self, phone_number: str = "+256726294861"):
        self.phone_number = phone_number
        self.twilio_client = None
        self.is_initialized = False
        self.processed_messages = set()
        
        logger.info(f"Production WhatsApp client initialized for {self.phone_number}")
    
    async def initialize(self):
        """Initialize the Twilio WhatsApp client"""
        try:
            print("🤖 Initializing Production WhatsApp Client")
            print("=" * 60)
            print(f"📱 Phone Number: {self.phone_number}")
            print("🌐 Using Twilio WhatsApp API (Cloud Run Ready)")
            print("=" * 60)
            
            # Initialize Twilio client
            print("🔧 Setting up Twilio WhatsApp client...")
            self.twilio_client = TwilioClient()
            print("✅ Twilio WhatsApp client initialized successfully")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a message using Twilio WhatsApp API"""
        try:
            if not self.is_initialized:
                return {"status": "error", "error": "Client not initialized"}
            
            print(f"📤 Sending message to {to_number}")
            print(f"📝 Message: {message[:100]}...")
            
            # Send via Twilio
            result = await self.twilio_client.send_text_message(to_number, message)
            
            if result.get("status") == "success":
                print(f"✅ Message sent to {to_number}")
                print(f"📧 Twilio SID: {result.get('message_id')}")
                return {
                    "status": "success",
                    "message_id": result.get("message_id"),
                    "to_number": to_number,
                    "timestamp": datetime.now().isoformat(),
                    "method": "twilio_api"
                }
            else:
                print(f"❌ Failed to send message: {result.get('error')}")
                return {"status": "error", "error": result.get("error")}
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            print(f"❌ Send message error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_response(self, message_text: str) -> str:
        """Generate intelligent response to message"""
        message_lower = message_text.lower().strip()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start', 'hola', 'ola']):
            return """🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk!

I'm your AI assistant for government services. I can help you with:

📋 Birth Certificate (NIRA)
• Check application status
• New application requirements
• Find NIRA offices

💰 Tax Services (URA)  
• Check tax balance
• TIN validation
• Tax clearance

🏦 NSSF Services
• Contribution balance
• Statements & history
• Member services

🏡 Land Verification
• Ownership verification
• Title status checks
• Land information

What would you like help with today?
Type the service name or describe your need."""
        
        elif any(word in message_lower for word in ['birth', 'certificate', 'nira']):
            return """📋 Birth Certificate Services (NIRA)

I can assist you with:
✅ Check application status with reference number
📝 Requirements for new applications
🏢 Locate nearest NIRA office
📞 Contact information & support

Please provide:
• Your NIRA reference number (if checking status)
• Or tell me what specific help you need

Example: "Check status NIRA/2023/123456"
Example: "I need a new birth certificate"

How can I help with your birth certificate needs?"""
        
        elif any(word in message_lower for word in ['tax', 'ura', 'tin']):
            return """💰 Tax Services (URA)

I can help you with:
💳 Check current tax balance
🆔 TIN number validation
📄 Tax clearance certificate status
📋 Outstanding tax obligations
🏢 Find URA offices

Please provide:
• Your TIN number for balance check
• Or describe what you need help with

Example: "My TIN is 1234567890"
Example: "I need tax clearance certificate"

What tax service do you need assistance with?"""
        
        elif any(word in message_lower for word in ['nssf', 'social security', 'pension', 'contribution']):
            return """🏦 NSSF Services

I can assist with:
💰 Check contribution balance
📊 Request contribution statements
📈 View contribution history
📞 Member support services
🏢 Find NSSF offices

Please provide:
• Your NSSF membership number
• Or tell me what you need help with

Example: "Check balance for member 123456789"
Example: "I need my contribution statement"

How can I help with your NSSF needs?"""
        
        elif any(word in message_lower for word in ['land', 'title', 'property', 'plot', 'ownership']):
            return """🏡 Land Verification Services

I can help you with:
✅ Verify land ownership
📋 Check certificate of title status
🗺️  Get land/plot information
📍 Land registry searches
🏢 Find land offices

Please provide:
• Plot number and location/district
• Or describe what you need to verify

Example: "Verify plot 123 in Kampala"
Example: "Check title for Block 45 Plot 67 Entebbe"

What land verification do you need?"""
        
        elif any(word in message_lower for word in ['help', 'menu', 'services', 'what', 'options']):
            return """ℹ️ Uganda E-Gov WhatsApp Helpdesk

🔹 Birth Certificate (NIRA)
   Type: "birth certificate" or "nira"

🔹 Tax Services (URA)  
   Type: "tax" or "ura" or "tin"

🔹 NSSF Services
   Type: "nssf" or "pension"

🔹 Land Verification
   Type: "land" or "property"

🔹 General Help
   Type: "help" for this menu

🌍 Available in: English, Luganda, Luo, Runyoro
⏰ Available 24/7 to serve Ugandan citizens

Simply type what you need help with, and I'll guide you through the process!"""
        
        elif any(word in message_lower for word in ['thank', 'thanks', 'asante', 'webale']):
            return """🙏 You're very welcome! 

I'm here to help make Uganda government services accessible to all citizens through WhatsApp.

Need help with anything else?
• Birth certificates
• Tax services  
• NSSF contributions
• Land verification

Just ask anytime! 🇺🇬

Uganda E-Gov WhatsApp Helpdesk"""
        
        else:
            return f"""🇺🇬 Hello! I'm your Uganda E-Gov AI assistant.

I can help you with government services:

📋 Birth Certificate - Type "birth certificate"
💰 Tax Services - Type "tax services"  
🏦 NSSF Balance - Type "nssf"
🏡 Land Verification - Type "land"

Or simply describe what you need help with in your own words.

Available 24/7 to serve Ugandan citizens! 🇺🇬

What can I help you with today?"""
    
    async def handle_incoming_message(self, from_number: str, message_text: str) -> Dict[str, Any]:
        """Handle incoming message and generate response"""
        try:
            print(f"\n📨 Incoming message from {from_number}:")
            print(f"   📝 Text: {message_text[:100]}...")
            
            # Generate response
            response_text = self._generate_response(message_text)
            
            # Send response
            print(f"📤 Sending response to {from_number}...")
            result = await self.send_message(from_number, response_text)
            
            if result.get("status") == "success":
                print("✅ Response sent successfully!")
                logger.info(f"Sent response to {from_number}: {len(response_text)} chars")
                return {
                    "status": "success",
                    "response_sent": True,
                    "message_id": result.get("message_id")
                }
            else:
                print(f"❌ Failed to send response: {result.get('error')}")
                logger.error(f"Failed to send response to {from_number}: {result.get('error')}")
                return {
                    "status": "error",
                    "response_sent": False,
                    "error": result.get("error")
                }
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            print(f"❌ Error handling message: {e}")
            return {
                "status": "error",
                "response_sent": False,
                "error": str(e)
            }
    
    async def send_startup_message(self):
        """Send startup notification"""
        try:
            startup_message = """🤖 Uganda E-Gov WhatsApp Helpdesk is now online!

✅ Production deployment active
🌐 Powered by Twilio WhatsApp API
🇺🇬 Ready to help Ugandan citizens with government services

Available services:
📋 Birth Certificate (NIRA)
💰 Tax Services (URA)
🏦 NSSF Services
🏡 Land Verification

Send "hello" to get started!"""
            
            result = await self.send_message(self.phone_number, startup_message)
            
            if result.get("status") == "success":
                print("✅ Startup message sent!")
                return True
            else:
                print(f"⚠️  Startup message failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")
            return False

# Global client instance for webhook usage
_production_client = None

async def get_production_client() -> ProductionWhatsAppClient:
    """Get or create production WhatsApp client"""
    global _production_client
    
    if _production_client is None:
        _production_client = ProductionWhatsAppClient("+256726294861")
        success = await _production_client.initialize()
        
        if not success:
            logger.error("Failed to initialize production WhatsApp client")
            raise Exception("Failed to initialize production WhatsApp client")
    
    return _production_client

async def handle_webhook_message(from_number: str, message_text: str) -> Dict[str, Any]:
    """Handle webhook message - main entry point for Cloud Run"""
    try:
        client = await get_production_client()
        return await client.handle_incoming_message(from_number, message_text)
    except Exception as e:
        logger.error(f"Webhook message handling failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "response_sent": False
        }

async def main():
    """Main function for testing"""
    client = ProductionWhatsAppClient()
    
    try:
        # Initialize client
        success = await client.initialize()
        if not success:
            print("❌ Failed to initialize client")
            return
        
        # Send startup message
        print("\n📧 Sending startup message...")
        await client.send_startup_message()
        
        # Test message handling
        print("\n🧪 Testing message handling...")
        test_messages = [
            "hello",
            "birth certificate",
            "tax services",
            "nssf",
            "land verification",
            "help"
        ]
        
        for test_msg in test_messages:
            print(f"\n🧪 Testing: '{test_msg}'")
            result = await client.handle_incoming_message("+256726294861", test_msg)
            print(f"Result: {result.get('status')}")
            await asyncio.sleep(2)  # Rate limiting
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n👋 Production client stopped!")
    except Exception as e:
        logger.error(f"Main error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Uganda E-Gov Production WhatsApp Client")
    print("🌐 Cloud Run Ready - Using Twilio WhatsApp API")
    print("=" * 60)
    asyncio.run(main())