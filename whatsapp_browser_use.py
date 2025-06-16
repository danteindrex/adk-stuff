#!/usr/bin/env python3
"""
WhatsApp Web Automation using Browser-Use
Intelligent WhatsApp automation with AI-powered browser interaction
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
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class WhatsAppBrowserUseClient:
    """Intelligent WhatsApp Web client using Browser-Use"""
    
    def __init__(self, phone_number: str = "+256726294861"):
        self.phone_number = phone_number
        self.agent = None
        self.is_authenticated = False
        self.processed_messages = set()
        self.session_dir = "whatsapp_browser_use_session"
        
        # Create session directory
        os.makedirs(self.session_dir, exist_ok=True)
        
        logger.info(f"WhatsApp Browser-Use client initialized for {self.phone_number}")
    
    async def initialize(self):
        """Initialize the Browser-Use agent with Gemini LLM"""
        try:
            print("🤖 Initializing WhatsApp Browser-Use Agent")
            print("=" * 50)
            print("📱 Phone Number: +256726294861")
            print("🧠 Using Gemini AI-powered browser automation")
            print("=" * 50)
            
            # Initialize Gemini LLM
            print("🔧 Setting up Gemini LLM...")
            
            # Check for Google API key
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("⚠️  GOOGLE_API_KEY not found in environment variables")
                print("💡 Please set GOOGLE_API_KEY in your .env file or environment")
                # Use a placeholder for now - this will fail but show the error
                google_api_key = "your-google-api-key-here"
            
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.1,
                max_tokens=2048,
                timeout=60,
                max_retries=2,
                google_api_key=google_api_key
            )
            print("✅ Gemini LLM initialized")
            
            # Create Browser-Use agent with Gemini and WhatsApp-specific instructions
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
        """Authenticate with WhatsApp Web using Browser-Use"""
        try:
            print("\n🔐 Step 1: Authenticating with WhatsApp Web...")
            
            # Navigate to WhatsApp Web and handle authentication
            auth_task = """
            Navigate to https://web.whatsapp.com and handle the authentication process:
            
            1. Go to WhatsApp Web
            2. Check if already authenticated (look for chat list or conversations)
            3. If not authenticated, wait for QR code to appear
            4. Inform user to scan QR code with their phone
            5. Wait for successful authentication (chat interface appears)
            6. Confirm authentication is complete
            
            Return 'authenticated' when the main WhatsApp interface with chats is visible.
            """
            
            print("🌐 Opening WhatsApp Web...")
            print("📱 If QR code appears, please scan it with your phone (+256726294861)")
            
            result = await self.agent.run(auth_task)
            
            if "authenticated" in str(result).lower() or "chat" in str(result).lower():
                print("✅ Authentication successful!")
                self.is_authenticated = True
                return True
            else:
                print("❌ Authentication failed or incomplete")
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
            
            # Use Browser-Use to send message
            send_task = f"""
            Send a WhatsApp message to {clean_number}:
            
            1. Look for the search box at the top (usually has placeholder "Search or start new chat")
            2. Click on the search box
            3. Type the phone number: {clean_number}
            4. Wait for search results or contact to appear
            5. Click on the contact/number when it appears
            6. Wait for the chat to open
            7. Find the message input box at the bottom
            8. Click on the message input box
            9. Type this exact message: {message}
            10. Press Enter or click the send button to send the message
            11. Confirm the message was sent (appears in chat)
            
            Return 'message_sent' when the message appears in the chat conversation.
            """
            
            result = await self.agent.run(send_task)
            
            if "message_sent" in str(result).lower() or "sent" in str(result).lower():
                print(f"✅ Message sent to {to_number}")
                return {
                    "status": "success",
                    "message_id": f"browser_use_{int(datetime.now().timestamp())}",
                    "to_number": to_number,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ Failed to send message")
                return {"status": "error", "error": "Message sending failed"}
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            print(f"❌ Send message error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def check_new_messages(self) -> List[Dict[str, Any]]:
        """Check for new messages using Browser-Use"""
        try:
            if not self.is_authenticated:
                return []
            
            # Use Browser-Use to check for new messages
            check_task = """
            Check for new unread WhatsApp messages:
            
            1. Look at the chat list on the left side
            2. Find any chats with unread message indicators (green dots, unread count badges)
            3. For each unread chat:
               - Note the contact name/number
               - Click on the chat to open it
               - Read the latest unread messages
               - Note the message text and sender
               - Go back to chat list
            4. Return information about new messages in format:
               "NEW_MESSAGE: from [contact] message [text]"
            
            If no new messages, return "NO_NEW_MESSAGES"
            """
            
            result = await self.agent.run(check_task)
            
            messages = []
            result_str = str(result).lower()
            
            if "new_message:" in result_str:
                # Parse messages from result
                lines = str(result).split('\n')
                for line in lines:
                    if "NEW_MESSAGE:" in line.upper():
                        try:
                            # Extract contact and message
                            parts = line.split("message")
                            if len(parts) >= 2:
                                contact_part = parts[0].replace("NEW_MESSAGE:", "").replace("from", "").strip()
                                message_text = parts[1].strip()
                                
                                message_id = f"browser_use_{len(messages)}_{int(datetime.now().timestamp())}"
                                
                                if message_id not in self.processed_messages:
                                    messages.append({
                                        "from": contact_part,
                                        "text": message_text,
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
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping auto responder...")
        except Exception as e:
            logger.error(f"Auto responder error: {e}")
            print(f"❌ Auto responder error: {e}")
    
    async def handle_message(self, message_data: Dict[str, Any]):
        """Handle incoming message and send response"""
        try:
            from_contact = message_data.get('from', 'Unknown')
            message_text = message_data.get('text', '')
            
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
                logger.info(f"Sent response to {phone_number}: {len(response_text)} chars")
            else:
                print(f"❌ Failed to send response: {result.get('error')}")
                logger.error(f"Failed to send response to {phone_number}: {result.get('error')}")
            
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
            return """��� NSSF Services

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
    
    async def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up Browser-Use agent...")
        if self.agent:
            try:
                await self.agent.close()
            except:
                pass
        print("✅ Cleanup complete")

async def main():
    """Main function"""
    client = WhatsAppBrowserUseClient()
    
    try:
        # Initialize Browser-Use agent
        success = await client.initialize()
        if not success:
            print("❌ Failed to initialize Browser-Use agent")
            return
        
        # Authenticate with WhatsApp Web
        success = await client.authenticate()
        if not success:
            print("❌ Failed to authenticate with WhatsApp Web")
            return
        
        # Send initial test message
        print("\n📧 Sending startup message...")
        test_result = await client.send_message(
            "+256726294861",
            "🤖 Uganda E-Gov WhatsApp Helpdesk is now online with Browser-Use AI automation! Ready to help citizens with government services."
        )
        
        if test_result.get("status") == "success":
            print("✅ Startup message sent!")
        
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
    asyncio.run(main())