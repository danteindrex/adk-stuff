#!/usr/bin/env python3
"""
WhatsApp Web Setup and Startup Script
Helps set up and start the WhatsApp Web automation system
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.whatsapp_web_client import WhatsAppWebClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_whatsapp_web():
    """Set up WhatsApp Web client and authenticate"""
    print("🚀 WhatsApp Web Setup for Uganda E-Gov Helpdesk")
    print("=" * 60)
    print(f"📱 Phone Number: +256726294861")
    print("=" * 60)
    
    try:
        # Create WhatsApp Web client
        client = WhatsAppWebClient("+256726294861")
        
        print("\n📋 Setup Steps:")
        print("1. Starting browser automation...")
        
        # Start the client
        success = await client.start()
        
        if success:
            print("✅ WhatsApp Web client started successfully!")
            
            if client.is_authenticated:
                print("✅ Already authenticated!")
                print("\n🎉 Setup complete! You can now start the main application.")
            else:
                print("\n📱 Authentication required:")
                print("1. Open WhatsApp on your phone")
                print("2. Go to Settings > Linked Devices")
                print("3. Tap 'Link a Device'")
                print("4. Scan the QR code that appears in the browser")
                print("\n⏳ Waiting for authentication...")
                
                # Wait for authentication
                authenticated = await client._wait_for_authentication(timeout=120)
                
                if authenticated:
                    print("✅ Authentication successful!")
                    print("\n🎉 Setup complete! You can now start the main application.")
                else:
                    print("❌ Authentication timeout. Please try again.")
                    return False
        else:
            print("❌ Failed to start WhatsApp Web client")
            return False
        
        # Test sending a message to yourself
        print("\n🧪 Testing message sending...")
        test_result = await client.send_message("+256726294861", "🤖 WhatsApp Web automation test - setup complete!")
        
        if test_result.get("status") == "success":
            print("✅ Test message sent successfully!")
        else:
            print(f"⚠️  Test message failed: {test_result.get('error')}")
        
        # Keep client running for a bit to ensure session is saved
        print("\n💾 Saving session...")
        await asyncio.sleep(5)
        
        await client.stop()
        print("✅ Setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"❌ Setup failed: {e}")
        return False

async def test_whatsapp_web():
    """Test existing WhatsApp Web setup"""
    print("🧪 Testing WhatsApp Web Setup")
    print("=" * 40)
    
    try:
        client = WhatsAppWebClient("+256726294861")
        success = await client.start()
        
        if success and client.is_authenticated:
            print("✅ WhatsApp Web is working!")
            
            # Test message
            result = await client.send_message("+256726294861", "🧪 Test message from Uganda E-Gov Helpdesk")
            
            if result.get("status") == "success":
                print("�� Test message sent successfully!")
            else:
                print(f"❌ Test message failed: {result.get('error')}")
            
            await client.stop()
            return True
        else:
            print("❌ WhatsApp Web not authenticated")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        success = asyncio.run(test_whatsapp_web())
    else:
        # Setup mode
        success = asyncio.run(setup_whatsapp_web())
    
    if success:
        print("\n🚀 Ready to start the main application:")
        print("   python main.py")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()