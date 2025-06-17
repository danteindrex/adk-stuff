#!/usr/bin/env python3
"""
WhatsApp Demo Mode - Works without sending actual messages
Perfect for testing and development when Twilio limits are reached
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

from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class WhatsAppDemoClient:
    """Demo WhatsApp client that simulates message sending without using Twilio API"""
    
    def __init__(self, phone_number: str = "+256726294861"):
        self.phone_number = phone_number
        self.is_initialized = False
        self.processed_messages = set()
        self.demo_mode = True
        
        logger.info(f"WhatsApp Demo client initialized for {self.phone_number}")
    
    async def initialize(self):
        """Initialize the demo client"""
        try:
            print("🤖 Initializing WhatsApp Demo Client")
            print("=" * 60)
            print(f"📱 Phone Number: {self.phone_number}")
            print("🎭 Demo Mode - No actual messages sent")
            print("💡 Perfect for testing without Twilio limits")
            print("=" * 60)
            
            self.is_initialized = True
            print("✅ Demo client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize demo client: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Simulate sending a message (demo mode)"""
        try:
            if not self.is_initialized:
                return {"status": "error", "error": "Client not initialized"}
            
            print(f"📤 [DEMO] Sending message to {to_number}")
            print(f"📝 Message preview: {message[:100]}...")
            print(f"📊 Message length: {len(message)} characters")
            
            # Simulate API delay
            await asyncio.sleep(0.5)
            
            # Generate demo message ID
            demo_message_id = f"demo_{int(datetime.now().timestamp())}"
            
            print(f"✅ [DEMO] Message would be sent successfully")
            print(f"📧 Demo Message ID: {demo_message_id}")
            
            return {
                "status": "success",
                "message_id": demo_message_id,
                "to_number": to_number,
                "timestamp": datetime.now().isoformat(),
                "method": "demo_mode",
                "note": "Message simulated - not actually sent"
            }
                
        except Exception as e:
            logger.error(f"Demo send error: {e}")
            print(f"❌ Demo send error: {e}")
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
            print(f"\n📨 [DEMO] Incoming message from {from_number}:")
            print(f"   📝 Text: {message_text}")
            
            # Generate response
            response_text = self._generate_response(message_text)
            
            print(f"\n🤖 Generated response:")
            print("=" * 50)
            print(response_text)
            print("=" * 50)
            
            # Simulate sending response
            result = await self.send_message(from_number, response_text)
            
            if result.get("status") == "success":
                print("✅ [DEMO] Response would be sent successfully!")
                logger.info(f"Demo response generated for {from_number}: {len(response_text)} chars")
                return {
                    "status": "success",
                    "response_sent": True,
                    "message_id": result.get("message_id"),
                    "demo_mode": True
                }
            else:
                print(f"❌ [DEMO] Response simulation failed: {result.get('error')}")
                return {
                    "status": "error",
                    "response_sent": False,
                    "error": result.get("error"),
                    "demo_mode": True
                }
            
        except Exception as e:
            logger.error(f"Error in demo message handling: {e}")
            print(f"❌ Demo error: {e}")
            return {
                "status": "error",
                "response_sent": False,
                "error": str(e),
                "demo_mode": True
            }
    
    async def interactive_demo(self):
        """Interactive demo mode for testing responses"""
        print("\n🎭 Interactive Demo Mode")
        print("=" * 40)
        print("Type messages to see how the system would respond")
        print("Type 'quit' to exit")
        print("=" * 40)
        
        while True:
            try:
                user_input = input("\n💬 Your message: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Exiting demo mode...")
                    break
                
                if not user_input:
                    continue
                
                # Process the message
                result = await self.handle_incoming_message("+256726294861", user_input)
                
                print(f"\n📊 Demo Result: {result.get('status')}")
                
            except KeyboardInterrupt:
                print("\n👋 Demo interrupted by user")
                break
            except Exception as e:
                print(f"❌ Demo error: {e}")

async def main():
    """Main function for demo testing"""
    client = WhatsAppDemoClient()
    
    try:
        # Initialize client
        success = await client.initialize()
        if not success:
            print("❌ Failed to initialize demo client")
            return
        
        print("\n🎯 Demo Options:")
        print("1. Automated test suite")
        print("2. Interactive demo mode")
        
        choice = input("\nSelect option (1 or 2): ").strip()
        
        if choice == "2":
            # Interactive mode
            await client.interactive_demo()
        else:
            # Automated test suite
            print("\n���� Running automated test suite...")
            test_messages = [
                "hello",
                "birth certificate", 
                "I need help with tax services",
                "nssf balance check",
                "land verification for plot 123",
                "help me with government services",
                "thank you"
            ]
            
            for i, test_msg in enumerate(test_messages, 1):
                print(f"\n🧪 Test {i}/{len(test_messages)}: '{test_msg}'")
                result = await client.handle_incoming_message("+256726294861", test_msg)
                print(f"✅ Test {i} completed: {result.get('status')}")
                await asyncio.sleep(1)  # Pause between tests
            
            print("\n✅ All automated tests completed!")
        
    except KeyboardInterrupt:
        print("\n👋 Demo stopped!")
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎭 Uganda E-Gov WhatsApp Demo Mode")
    print("🚀 Test responses without sending actual messages")
    print("💡 Perfect for development and testing")
    print("=" * 60)
    asyncio.run(main())