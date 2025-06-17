#!/usr/bin/env python3
"""
Smart WhatsApp Web Client
Automatically handles authentication and switches between headless/visible modes
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

class SmartWhatsAppClient:
    """Smart WhatsApp client that handles authentication automatically"""
    
    def __init__(self):
        self.client = None
        self.is_ready = False
    
    async def initialize_and_authenticate(self):
        """Initialize client and ensure authentication"""
        try:
            print("🤖 Smart WhatsApp Client Initialization")
            print("=" * 50)
            print("📱 Phone Number: +256726294861")
            print("🧠 Auto-detecting best authentication method...")
            print("=" * 50)
            
            # Step 1: Try headless mode first (if session exists)
            print("\n🔍 Step 1: Trying headless mode with existing session...")
            self.client = WhatsAppWebClient("+256726294861", headless=True)
            
            success = await self.client.start()
            
            if success and self.client.is_authenticated:
                print("✅ Headless authentication successful!")
                self.is_ready = True
                return True
            
            # Step 2: Session expired or invalid, switch to visible mode
            print("\n🔄 Step 2: Session expired, switching to visible mode...")
            await self.client.stop()
            
            # Create new client in visible mode
            self.client = WhatsAppWebClient("+256726294861", headless=False)
            
            print("🖥️  Opening browser for QR code authentication...")
            print("\n📋 PLEASE FOLLOW THESE STEPS:")
            print("1. ✅ Browser window will open")
            print("2. 📱 On your phone (+256726294861):")
            print("   - Open WhatsApp")
            print("   - Go to Settings > Linked Devices")
            print("   - Tap 'Link a Device'")
            print("   - Scan the QR code in browser")
            print("3. ⏰ You have 5 minutes")
            print()
            
            success = await self.client.start()
            
            if success and self.client.is_authenticated:
                print("✅ Visual authentication successful!")
                
                # Step 3: Test the connection
                print("\n🧪 Step 3: Testing connection...")
                test_result = await self.client.send_message(
                    "+256726294861",
                    "🎉 WhatsApp Web authentication successful! Uganda E-Gov Helpdesk is ready."
                )
                
                if test_result.get("status") == "success":
                    print("✅ Test message sent successfully!")
                
                # Step 4: Switch back to headless for production use
                print("\n🔄 Step 4: Switching to headless mode for production...")
                await self.client.stop()
                
                # Wait a moment for session to save
                await asyncio.sleep(3)
                
                # Create new headless client
                self.client = WhatsAppWebClient("+256726294861", headless=True)
                success = await self.client.start()
                
                if success and self.client.is_authenticated:
                    print("✅ Successfully switched to headless mode!")
                    self.is_ready = True
                    return True
                else:
                    print("⚠️  Headless switch failed, keeping visible mode")
                    # Go back to visible mode
                    await self.client.stop()
                    self.client = WhatsAppWebClient("+256726294861", headless=False)
                    await self.client.start()
                    self.is_ready = True
                    return True
            else:
                print("❌ Visual authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Smart client initialization failed: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def send_message(self, to_number: str, message: str):
        """Send message through the client"""
        if not self.is_ready or not self.client:
            return {"status": "error", "error": "Client not ready"}
        
        return await self.client.send_message(to_number, message)
    
    async def start_auto_responder(self):
        """Start the auto responder"""
        if not self.is_ready:
            print("❌ Client not ready for auto responding")
            return
        
        print("\n🤖 Starting Smart Auto Responder...")
        print("📱 Monitoring WhatsApp messages...")
        print("🔄 Will automatically respond to incoming messages")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        # Add message handler
        await self.client.add_message_handler(self.handle_message)
        
        try:
            # Start message polling
            await self.client.start_message_polling(interval=2)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping auto responder...")
        except Exception as e:
            logger.error(f"Auto responder error: {e}")
            print(f"❌ Auto responder error: {e}")
        finally:
            await self.cleanup()
    
    async def handle_message(self, message_data: dict):
        """Handle incoming message and send response"""
        try:
            from_contact = message_data.get('from', 'Unknown')
            message_text = message_data.get('text', '')
            message_id = message_data.get('message_id', '')
            
            print(f"\n📨 New message from {from_contact}:")
            print(f"   📝 Text: {message_text[:100]}...")
            
            # Extract phone number
            phone_number = self._extract_phone_number(from_contact)
            
            if not phone_number:
                print(f"⚠️  Could not extract phone number from: {from_contact}")
                return
            
            # Generate response
            response_text = self._generate_response(message_text)
            
            # Send response
            print(f"📤 Sending response to {phone_number}...")
            result = await self.send_message(phone_number, response_text)
            
            if result.get("status") == "success":
                print("✅ Response sent successfully!")
            else:
                print(f"❌ Failed to send response: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            print(f"❌ Error handling message: {e}")
    
    def _extract_phone_number(self, contact_name: str) -> str:
        """Extract phone number from contact name"""
        try:
            clean_contact = contact_name.strip()
            
            if clean_contact.replace('+', '').replace(' ', '').replace('-', '').isdigit():
                return clean_contact
            
            import re
            phone_patterns = [
                r'(\+256\d{9})',
                r'(\+\d{10,15})',
                r'(256\d{9})',
                r'(\d{10,15})'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, clean_contact)
                if match:
                    return match.group(1)
            
            return clean_contact
            
        except Exception as e:
            logger.error(f"Error extracting phone number: {e}")
            return contact_name
    
    def _generate_response(self, message_text: str) -> str:
        """Generate response to message"""
        message_lower = message_text.lower().strip()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return """🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk!

I can help you with:
• 📋 Birth Certificate (NIRA) - Check status & applications
• 💰 Tax Services (URA) - Check balance & TIN validation  
• 🏦 NSSF Balance - Check contributions & statements
• 🏡 Land Verification - Verify ownership & title status

What would you like help with today?"""
        
        elif any(word in message_lower for word in ['birth', 'certificate', 'nira']):
            return """📋 Birth Certificate Services (NIRA)

I can help you:
• ✅ Check application status
• 📝 New application requirements
• 🏢 Find nearest NIRA office

Please provide your reference number or tell me what you need help with."""
        
        elif any(word in message_lower for word in ['tax', 'ura', 'tin']):
            return """💰 Tax Services (URA)

I can help you:
• 💳 Check tax balance
• 🆔 TIN validation
• 📄 Tax clearance status

Please provide your TIN number or tell me what you need."""
        
        elif any(word in message_lower for word in ['nssf', 'social security']):
            return """🏦 NSSF Services

I can help you:
• 💰 Check contribution balance
• 📊 Get contribution statement
• 📈 View contribution history

Please provide your NSSF number or tell me what you need."""
        
        elif any(word in message_lower for word in ['land', 'title', 'property']):
            return """🏡 Land Verification Services

I can help you:
• ✅ Verify land ownership
• 📋 Check title status
• 🗺️  Get land information

Please provide plot details or tell me what you need."""
        
        else:
            return """🇺🇬 Uganda E-Gov WhatsApp Helpdesk

I can help you with:
📋 Birth Certificate - Type "birth certificate"
💰 Tax Services - Type "tax"
🏦 NSSF - Type "nssf"
🏡 Land - Type "land"

Or describe what you need help with.
Available 24/7! 🇺🇬"""
    
    async def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up...")
        if self.client:
            await self.client.stop()
        print("✅ Cleanup complete")

async def main():
    """Main function"""
    smart_client = SmartWhatsAppClient()
    
    # Initialize and authenticate
    success = await smart_client.initialize_and_authenticate()
    
    if not success:
        print("❌ Failed to initialize smart client")
        return
    
    print("\n🎉 Smart WhatsApp Client ready!")
    print("🤖 Starting auto responder...")
    
    # Start auto responding
    await smart_client.start_auto_responder()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Smart client stopped!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)