#!/usr/bin/env python3
"""
WhatsApp Web Automation using Browser-Use with Gemini
Working implementation for Uganda E-Gov Helpdesk
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

from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppBrowserUseClient:
    """Intelligent WhatsApp Web client using Browser-Use with Gemini"""
    
    def __init__(self, phone_number: str = "+256726294861"):
        self.phone_number = phone_number
        self.agent = None
        self.is_authenticated = False
        self.processed_messages = set()
        
        logger.info(f"WhatsApp Browser-Use client initialized for {self.phone_number}")
    
    async def initialize(self):
        """Initialize the Browser-Use agent with Gemini LLM"""
        try:
            print("🤖 Initializing WhatsApp Browser-Use Agent with Gemini")
            print("=" * 60)
            print(f"📱 Phone Number: {self.phone_number}")
            print("🧠 Using Gemini AI-powered browser automation")
            print("=" * 60)
            
            # Initialize Gemini LLM
            print("🔧 Setting up Gemini LLM...")
            
            # Get Google API key
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("⚠️  GOOGLE_API_KEY not found in environment variables")
                print("💡 Please set GOOGLE_API_KEY in your .env file")
                return False
            
            # Create Gemini LLM
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.1,
                max_tokens=2048,
                timeout=60,
                max_retries=2,
                google_api_key=google_api_key
            )
            print("✅ Gemini LLM initialized successfully")
            
            # Create Browser-Use agent
            print("🤖 Creating Browser-Use agent...")
            self.agent = Agent(
                task="Manage WhatsApp Web for Uganda E-Gov Helpdesk",
                llm=gemini_llm,
                use_vision=True
            )
            
            print("✅ Browser-Use agent created successfully with Gemini")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Browser-Use agent: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def authenticate(self):
        """Authenticate with WhatsApp Web"""
        try:
            print("\n🔐 Step 1: Authenticating with WhatsApp Web...")
            
            auth_task = """
Navigate to https://web.whatsapp.com and handle authentication:

1. Go to WhatsApp Web
2. Check if already authenticated (look for chat list)
3. If QR code appears, wait for user to scan it
4. Wait for successful authentication (chat interface appears)
5. Return 'authenticated' when main WhatsApp interface is visible

Complete this task step by step.
"""
            
            print("🌐 Opening WhatsApp Web...")
            print("📱 If QR code appears, please scan it with your phone")
            
            # Run authentication task without max_steps parameter
            result = await self.agent.run(auth_task)
            
            result_str = str(result).lower()
            if "authenticated" in result_str or "chat" in result_str or "success" in result_str:
                print("✅ Authentication successful!")
                self.is_authenticated = True
                return True
            else:
                print("❌ Authentication failed or incomplete")
                print(f"Result: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            print(f"❌ Authentication error: {e}")
            return False
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a message using Browser-Use"""
        try:
            if not self.is_authenticated:
                return {"status": "error", "error": "Not authenticated"}
            
            print(f"📤 Sending message to {to_number}")
            
            # Clean phone number
            clean_number = to_number.replace("+", "").replace(" ", "").replace("-", "")
            
            send_task = f"""
Send a WhatsApp message to {clean_number}:

1. Find and click the search box at the top
2. Type the phone number: {clean_number}
3. Wait for contact to appear and click it
4. Wait for chat to open
5. Find the message input box at the bottom
6. Type this message: {message}
7. Press Enter or click send button
8. Confirm message was sent
9. Return 'message_sent' when complete

Complete this task step by step.
"""
            
            result = await self.agent.run(send_task)
            
            result_str = str(result).lower()
            if "message_sent" in result_str or "sent" in result_str or "success" in result_str:
                print(f"✅ Message sent to {to_number}")
                return {
                    "status": "success",
                    "message_id": f"browser_use_{int(datetime.now().timestamp())}",
                    "to_number": to_number,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ Failed to send message")
                print(f"Result: {result}")
                return {"status": "error", "error": "Message sending failed"}
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            print(f"❌ Send message error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def check_new_messages(self) -> List[Dict[str, Any]]:
        """Check for new messages"""
        try:
            if not self.is_authenticated:
                return []
            
            check_task = """
Check for new unread WhatsApp messages:

1. Look at the chat list on the left side
2. Find chats with unread indicators (green dots, badges)
3. For each unread chat:
   - Note the contact name/number
   - Click on the chat
   - Read the latest messages
   - Note the message text
4. Return format: "NEW_MESSAGE: from [contact] message [text]"
5. If no new messages, return "NO_NEW_MESSAGES"

Complete this task step by step.
"""
            
            result = await self.agent.run(check_task)
            
            messages = []
            result_str = str(result)
            
            if "NEW_MESSAGE:" in result_str:
                lines = result_str.split('\n')
                for line in lines:
                    if "NEW_MESSAGE:" in line:
                        try:
                            parts = line.split("message")
                            if len(parts) >= 2:
                                contact = parts[0].replace("NEW_MESSAGE:", "").replace("from", "").strip()
                                text = parts[1].strip()
                                
                                message_id = f"browser_use_{len(messages)}_{int(datetime.now().timestamp())}"
                                
                                if message_id not in self.processed_messages:
                                    messages.append({
                                        "from": contact,
                                        "text": text,
                                        "message_id": message_id,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    self.processed_messages.add(message_id)
                        except Exception as e:
                            logger.warning(f"Error parsing message: {e}")
            
            return messages
            
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
            return []
    
    def _generate_response(self, message_text: str) -> str:
        """Generate intelligent response to message"""
        message_lower = message_text.lower().strip()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return """🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk!

I'm your AI assistant for government services:

📋 Birth Certificate (NIRA) - Type "birth certificate"
💰 Tax Services (URA) - Type "tax services"  
���� NSSF Services - Type "nssf"
🏡 Land Verification - Type "land"

What would you like help with today?"""
        
        elif any(word in message_lower for word in ['birth', 'certificate', 'nira']):
            return """📋 Birth Certificate Services (NIRA)

I can help you with:
✅ Check application status with reference number
📝 New application requirements
🏢 Find NIRA offices

Please provide your NIRA reference number or tell me what you need help with.

Example: "Check status NIRA/2023/123456"

How can I help with your birth certificate?"""
        
        elif any(word in message_lower for word in ['tax', 'ura', 'tin']):
            return """💰 Tax Services (URA)

I can help you with:
💳 Check tax balance with TIN number
🆔 TIN validation
📄 Tax clearance certificate

Please provide your TIN number or describe what you need.

Example: "My TIN is 1234567890"

What tax service do you need?"""
        
        elif any(word in message_lower for word in ['nssf', 'pension', 'contribution']):
            return """🏦 NSSF Services

I can help you with:
💰 Check contribution balance
📊 Request statements
📈 View contribution history

Please provide your NSSF membership number.

Example: "Check balance for member 123456789"

How can I help with NSSF?"""
        
        elif any(word in message_lower for word in ['land', 'title', 'property']):
            return """🏡 Land Verification Services

I can help you with:
✅ Verify land ownership
📋 Check title status
🗺️ Get plot information

Please provide plot number and location.

Example: "Verify plot 123 in Kampala"

What land verification do you need?"""
        
        else:
            return """🇺🇬 Hello! I'm your Uganda E-Gov AI assistant.

I can help with:
📋 Birth Certificate - Type "birth certificate"
💰 Tax Services - Type "tax services"  
🏦 NSSF Balance - Type "nssf"
🏡 Land Verification - Type "land"

Available 24/7 to serve Ugandan citizens! 🇺🇬

What can I help you with today?"""
    
    async def handle_message(self, message_data: Dict[str, Any]):
        """Handle incoming message and send response"""
        try:
            from_contact = message_data.get('from', 'Unknown')
            message_text = message_data.get('text', '')
            
            print(f"\n📨 New message from {from_contact}:")
            print(f"   📝 Text: {message_text[:100]}...")
            
            # Generate response
            response_text = self._generate_response(message_text)
            
            # Extract phone number for response
            phone_number = from_contact
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            
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
    
    async def start_auto_responder(self):
        """Start the auto responder loop"""
        print("\n🤖 Starting Auto Responder...")
        print("📱 Monitoring for new WhatsApp messages...")
        print("🔄 Will automatically respond to incoming messages")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        try:
            while True:
                # Check for new messages
                new_messages = await self.check_new_messages()
                
                for message in new_messages:
                    await self.handle_message(message)
                
                # Wait before checking again
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping auto responder...")
        except Exception as e:
            logger.error(f"Auto responder error: {e}")
            print(f"❌ Auto responder error: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up Browser-Use agent...")
        if self.agent:
            try:
                # Browser-Use cleanup
                pass
            except:
                pass
        print("✅ Cleanup complete")

async def main():
    """Main function"""
    client = WhatsAppBrowserUseClient()
    
    try:
        # Initialize Browser-Use agent with Gemini
        success = await client.initialize()
        if not success:
            print("❌ Failed to initialize Browser-Use agent")
            return
        
        # Authenticate with WhatsApp Web
        success = await client.authenticate()
        if not success:
            print("❌ Failed to authenticate with WhatsApp Web")
            print("💡 Make sure to scan the QR code when it appears")
            return
        
        # Send initial test message
        print("\n📧 Sending startup message...")
        test_result = await client.send_message(
            "+256726294861",
            "🤖 Uganda E-Gov WhatsApp Helpdesk is now online with Gemini AI! Ready to help citizens with government services."
        )
        
        if test_result.get("status") == "success":
            print("✅ Startup message sent!")
        else:
            print("⚠️  Startup message failed, but continuing...")
        
        # Start auto responder
        await client.start_auto_responder()
        
    except KeyboardInterrupt:
        print("\n👋 WhatsApp Browser-Use client stopped!")
    except Exception as e:
        logger.error(f"Main error: {e}")
        print(f"❌ Error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    print("🚀 Starting Uganda E-Gov WhatsApp Browser-Use Automation")
    print("🧠 Powered by Gemini AI and Browser-Use")
    print("=" * 60)
    asyncio.run(main())