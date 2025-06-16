#!/usr/bin/env python3
"""
Start WhatsApp Web with visible browser for QR code scanning
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def start_whatsapp_web_visible():
    """Start WhatsApp Web with visible browser"""
    print("🚀 Starting WhatsApp Web with visible browser")
    print("=" * 50)
    print("📱 Phone Number: +256726294861")
    print("🔐 You'll need to scan QR code with your phone")
    print("=" * 50)
    
    try:
        from app.services.whatsapp_web_client import WhatsAppWebClient
        
        # Create client
        client = WhatsAppWebClient("+256726294861")
        
        print("🌐 Opening browser...")
        print("📋 Steps to follow:")
        print("1. Browser window will open")
        print("2. WhatsApp Web will load")
        print("3. Open WhatsApp on your phone (+256726294861)")
        print("4. Go to Settings > Linked Devices")
        print("5. Tap 'Link a Device'")
        print("6. Scan the QR code in the browser")
        print()
        
        # Start the client (browser will be visible)
        success = await client.start()
        
        if success:
            if client.is_authenticated:
                print("✅ Authentication successful!")
                
                # Test sending a message
                print("🧪 Testing message sending...")
                test_result = await client.send_message(
                    "+256726294861", 
                    "🤖 WhatsApp Web setup complete! Uganda E-Gov Helpdesk is ready."
                )
                
                if test_result.get("status") == "success":
                    print("✅ Test message sent successfully!")
                else:
                    print(f"⚠️  Test message failed: {test_result.get('error')}")
                
                print("\n🎉 Setup complete!")
                print("📱 WhatsApp Web is now connected and ready")
                print("\n🔄 Keeping browser open for 30 seconds...")
                await asyncio.sleep(30)
                
            else:
                print("❌ Authentication failed or timed out")
                print("💡 Make sure to scan the QR code within the time limit")
        else:
            print("❌ Failed to start WhatsApp Web client")
        
        # Clean up
        await client.stop()
        print("🛑 Browser closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    try:
        asyncio.run(start_whatsapp_web_visible())
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()