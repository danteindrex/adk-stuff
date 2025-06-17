#!/usr/bin/env python3
"""
Setup and Run WhatsApp Auto Responder
Fresh setup with QR code authentication, then auto-respond to messages
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

async def setup_and_run():
    """Setup WhatsApp Web and start auto responding"""
    print("🚀 WhatsApp Web Setup & Auto Responder")
    print("=" * 50)
    print("📱 Phone Number: +256726294861")
    print("🇺🇬 Uganda E-Gov WhatsApp Helpdesk")
    print("=" * 50)
    
    try:
        # Step 1: Initial setup with visible browser
        print("\n📋 Step 1: Setting up WhatsApp Web authentication")
        print("🖥️  Opening browser for QR code scanning...")
        print("\n📱 PLEASE SCAN QR CODE:")
        print("1. Browser will open with WhatsApp Web")
        print("2. On your phone (+256726294861):")
        print("   - Open WhatsApp")
        print("   - Settings > Linked Devices")
        print("   - Link a Device")
        print("   - Scan QR code")
        print()
        
        # Create client in visible mode for initial setup
        client = WhatsAppWebClient("+256726294861", headless=False)
        
        success = await client.start()
        
        if not success or not client.is_authenticated:
            print("❌ Authentication failed")
            return False
        
        print("✅ Authentication successful!")
        
        # Step 2: Test messaging
        print("\n📧 Step 2: Testing message sending...")
        test_result = await client.send_message(
            "+256726294861",
            "🎉 WhatsApp Web setup complete! Auto-responder is starting..."
        )
        
        if test_result.get("status") == "success":
            print("✅ Test message sent successfully!")
        else:
            print(f"⚠️  Test message failed: {test_result.get('error')}")
        
        # Step 3: Start auto responding
        print("\n🤖 Step 3: Starting Auto Responder...")
        print("📱 Now monitoring for incoming messages...")
        print("���� Will automatically respond to messages")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        # Message handler
        processed_messages = set()
        
        async def handle_message(message_data):
            try:
                from_contact = message_data.get('from', 'Unknown')
                message_text = message_data.get('text', '')
                message_id = message_data.get('message_id', '')
                
                # Skip duplicates
                if message_id in processed_messages:
                    return
                processed_messages.add(message_id)
                
                print(f"\n📨 New message from {from_contact}:")
                print(f"   📝 Text: {message_text[:100]}...")
                
                # Extract phone number
                phone_number = extract_phone_number(from_contact)
                
                if not phone_number:
                    print(f"⚠️  Could not extract phone number")
                    return
                
                # Generate response
                response_text = generate_response(message_text)
                
                # Send response
                print(f"📤 Sending response...")
                result = await client.send_message(phone_number, response_text)
                
                if result.get("status") == "success":
                    print("✅ Response sent!")
                else:
                    print(f"❌ Response failed: {result.get('error')}")
                
            except Exception as e:
                print(f"❌ Error handling message: {e}")
        
        # Add message handler
        await client.add_message_handler(handle_message)
        
        # Start message polling
        await client.start_message_polling(interval=3)
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping auto responder...")
    except Exception as e:
        logger.error(f"Setup and run failed: {e}")
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            await client.stop()
            print("🛑 WhatsApp Web client stopped")
        except:
            pass
    
    return True

def extract_phone_number(contact_name: str) -> str:
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
        return contact_name

def generate_response(message_text: str) -> str:
    """Generate response to message"""
    message_lower = message_text.lower().strip()
    
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start', 'hola']):
        return """🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk!

I can help you with:
• 📋 Birth Certificate (NIRA) - Check status & applications
• 💰 Tax Services (URA) - Check balance & TIN validation  
• 🏦 NSSF Balance - Check contributions & statements
• 🏡 Land Verification - Verify ownership & title status

What would you like help with today?

Type the service name or describe what you need."""
    
    elif any(word in message_lower for word in ['birth', 'certificate', 'nira']):
        return """📋 Birth Certificate Services (NIRA)

I can help you:
• ✅ Check application status
• 📝 New application requirements  
• 🏢 Find nearest NIRA office
• 📞 Contact information

Please provide:
- Your reference number (if checking status)
- Or tell me what specific help you need

Example: "Check status NIRA/2023/123456" """
    
    elif any(word in message_lower for word in ['tax', 'ura', 'tin']):
        return """💰 Tax Services (URA)

I can help you:
• 💳 Check tax balance
• 🆔 TIN validation
• 📄 Tax clearance status
• 📋 Tax obligations

Please provide:
- Your TIN number
- Or tell me what you need help with

Example: "My TIN is 1234567890" """
    
    elif any(word in message_lower for word in ['nssf', 'social security', 'pension']):
        return """🏦 NSSF Services

I can help you:
• 💰 Check contribution balance
• 📊 Get contribution statement
• 📈 View contribution history
• 📞 Contact NSSF

Please provide:
- Your NSSF membership number
- Or tell me what you need

Example: "Check my NSSF balance 123456789" """
    
    elif any(word in message_lower for word in ['land', 'title', 'property', 'plot']):
        return """🏡 Land Verification Services

I can help you:
• ✅ Verify land ownership
• 📋 Check title status
• 🗺️  Get land information
• 🏢 Find land offices

Please provide:
- Plot number and location
- Or describe what you need

Example: "Verify plot 123 in Kampala" """
    
    elif any(word in message_lower for word in ['help', 'menu', 'services']):
        return """ℹ️ Uganda E-Gov WhatsApp Helpdesk Services

🔹 Birth Certificate (NIRA)
   Type: "birth certificate" or "nira"

🔹 Tax Services (URA)  
   Type: "tax" or "ura"

🔹 NSSF Services
   Type: "nssf" or "pension"

🔹 Land Verification
   Type: "land" or "property"

Available in: English, Luganda, Luo, Runyoro
Available 24/7 to serve Ugandan citizens! 🇺🇬"""
    
    elif any(word in message_lower for word in ['thank', 'thanks', 'asante']):
        return """🙏 You're welcome! 

I'm here to help with Uganda government services anytime.

Need anything else? Just ask!

🇺🇬 Uganda E-Gov WhatsApp Helpdesk"""
    
    else:
        return f"""🇺🇬 Hello! I'm the Uganda E-Gov assistant.

I can help you with government services:

📋 Birth Certificate - Type "birth certificate"
💰 Tax Services - Type "tax services"  
🏦 NSSF Balance - Type "nssf"
🏡 Land Verification - Type "land"

Or describe what you need help with.

Available 24/7 to serve Ugandan citizens! 🇺🇬"""

def main():
    """Main function"""
    try:
        success = asyncio.run(setup_and_run())
        if success:
            print("\n✅ Auto responder completed successfully!")
        else:
            print("\n❌ Auto responder failed")
    except KeyboardInterrupt:
        print("\n👋 Auto responder stopped by user!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()