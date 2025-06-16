#!/usr/bin/env python3
"""
WhatsApp Intelligent Agent
Combines Browser-Use automation with ADK agent system for maximum intelligence
"""

import asyncio
import sys
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from browser_use import Agent
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class WhatsAppIntelligentAgent:
    """Intelligent WhatsApp agent combining Browser-Use with ADK agents"""
    
    def __init__(self, phone_number: str = "+256726294861"):
        self.phone_number = phone_number
        self.browser_agent = None
        self.adk_agent = None
        self.is_authenticated = False
        self.processed_messages = set()
        self.session_dir = "whatsapp_intelligent_session"
        
        # Create session directory
        os.makedirs(self.session_dir, exist_ok=True)
        
        logger.info(f"WhatsApp Intelligent Agent initialized for {self.phone_number}")
    
    async def initialize(self):
        """Initialize both Browser-Use and ADK agents"""
        try:
            print("🧠 Initializing WhatsApp Intelligent Agent")
            print("=" * 50)
            print("📱 Phone Number: +256726294861")
            print("🤖 Browser-Use + ADK Agent System")
            print("🇺🇬 Uganda E-Gov WhatsApp Helpdesk")
            print("=" * 50)
            
            # Initialize Browser-Use agent for WhatsApp automation
            print("\n🌐 Step 1: Initializing Browser-Use agent...")
            self.browser_agent = Agent(
                task="Automate WhatsApp Web for Uganda E-Gov Helpdesk with intelligent message handling",
                llm_model="gpt-4o-mini",
                browser_config={
                    "headless": False,  # Start visible for QR code
                    "user_data_dir": self.session_dir,
                    "viewport": {"width": 1366, "height": 768}
                }
            )
            print("✅ Browser-Use agent initialized")
            
            # Initialize ADK agent system for intelligent responses
            print("\n🤖 Step 2: Initializing ADK agent system...")
            try:
                from app.agents.adk_agents_modular import create_root_agent
                self.adk_agent = await create_root_agent()
                print("✅ ADK agent system initialized")
            except Exception as e:
                print(f"⚠️  ADK agent failed to initialize: {e}")
                print("📝 Will use built-in intelligent responses")
                self.adk_agent = None
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize intelligent agent: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def authenticate(self):
        """Authenticate with WhatsApp Web using Browser-Use"""
        try:
            print("\n🔐 Authenticating with WhatsApp Web...")
            
            auth_task = """
            Navigate to WhatsApp Web and handle authentication:
            
            1. Go to https://web.whatsapp.com
            2. Check if already authenticated by looking for:
               - Chat list on the left side
               - Message conversations
               - Contact names
            3. If not authenticated:
               - Wait for QR code to appear
               - Tell user to scan QR code with their phone
               - Wait for authentication to complete
            4. Once authenticated, confirm the main interface is loaded
            5. Return 'AUTHENTICATED' when you can see the chat interface
            
            Be patient and wait for elements to load properly.
            """
            
            print("🌐 Opening WhatsApp Web...")
            print("📱 If QR code appears, scan it with your phone (+256726294861)")
            
            result = await self.browser_agent.run(auth_task)
            
            if "authenticated" in str(result).lower():
                print("✅ Authentication successful!")
                self.is_authenticated = True
                return True
            else:
                print("❌ Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            print(f"❌ Authentication error: {e}")
            return False
    
    async def send_intelligent_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send message using Browser-Use with intelligent error handling"""
        try:
            print(f"📤 Sending intelligent message to {to_number}")
            
            clean_number = to_number.replace("+", "").replace(" ", "").replace("-", "")
            
            send_task = f"""
            Send a WhatsApp message intelligently:
            
            1. Look for the search box (usually at top with "Search or start new chat")
            2. Click on the search box and clear any existing text
            3. Type the phone number: {clean_number}
            4. Wait 2-3 seconds for search results
            5. Look for the contact or number in the results
            6. Click on the contact when it appears
            7. Wait for the chat to open (you should see message history or empty chat)
            8. Find the message input area at the bottom
            9. Click in the message input box
            10. Type this message exactly: {message}
            11. Press Enter or click the send button (arrow icon)
            12. Wait to confirm the message appears in the chat
            13. Return 'MESSAGE_SENT_SUCCESS' when you see the message in the conversation
            
            If any step fails, try alternative approaches:
            - If contact not found, try starting a new chat
            - If message box not found, look for different selectors
            - Be patient and wait for elements to load
            """
            
            result = await self.browser_agent.run(send_task)
            
            if "success" in str(result).lower() or "sent" in str(result).lower():
                print(f"✅ Intelligent message sent to {to_number}")
                return {
                    "status": "success",
                    "message_id": f"intelligent_{int(datetime.now().timestamp())}",
                    "to_number": to_number,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ Failed to send intelligent message")
                return {"status": "error", "error": "Intelligent message sending failed"}
                
        except Exception as e:
            logger.error(f"Failed to send intelligent message: {e}")
            return {"status": "error", "error": str(e)}
    
    async def monitor_messages(self) -> List[Dict[str, Any]]:
        """Monitor for new messages using Browser-Use intelligence"""
        try:
            monitor_task = """
            Monitor WhatsApp for new unread messages:
            
            1. Look at the chat list on the left side
            2. Identify chats with unread indicators:
               - Green notification dots
               - Unread message count badges
               - Bold chat names (indicating unread)
            3. For each unread chat found:
               - Note the contact name or phone number
               - Click on the chat to open it
               - Scroll to the bottom to see latest messages
               - Identify which messages are new (usually at the bottom)
               - Read the message text content
               - Note the sender information
               - Go back to the chat list
            4. Format findings as: "NEW_MESSAGE|FROM:{contact}|TEXT:{message_text}"
            5. If no new messages found, return "NO_NEW_MESSAGES"
            
            Be thorough and check all chats with unread indicators.
            """
            
            result = await self.browser_agent.run(monitor_task)
            
            messages = []
            result_str = str(result)
            
            if "NEW_MESSAGE|" in result_str:
                lines = result_str.split('\n')
                for line in lines:
                    if "NEW_MESSAGE|" in line:
                        try:
                            # Parse: NEW_MESSAGE|FROM:contact|TEXT:message
                            parts = line.split('|')
                            if len(parts) >= 3:
                                from_part = parts[1].replace("FROM:", "").strip()
                                text_part = parts[2].replace("TEXT:", "").strip()
                                
                                message_id = f"intelligent_{len(messages)}_{int(datetime.now().timestamp())}"
                                
                                if message_id not in self.processed_messages:
                                    messages.append({
                                        "from": from_part,
                                        "text": text_part,
                                        "message_id": message_id,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    self.processed_messages.add(message_id)
                        except Exception as e:
                            logger.warning(f"Error parsing intelligent message: {e}")
            
            return messages
            
        except Exception as e:
            logger.error(f"Error monitoring messages: {e}")
            return []
    
    async def generate_intelligent_response(self, message_text: str, user_id: str) -> str:
        """Generate intelligent response using ADK agents or fallback"""
        try:
            # Try ADK agent system first for maximum intelligence
            if self.adk_agent:
                print("🧠 Generating response with ADK agent system...")
                
                from google.adk.events import Event
                from google.genai.types import Content, Part
                
                # Create event for ADK processing
                event = Event(
                    content=Content(parts=[Part(text=message_text)]),
                    metadata={
                        "user_id": user_id.replace("+", "").replace("whatsapp:", ""),
                        "source": "whatsapp_intelligent",
                        "timestamp": datetime.now().isoformat(),
                        "session_type": "whatsapp_conversation"
                    }
                )
                
                # Process with ADK agent
                from google.adk import Runner
                from google.adk.sessions import InMemorySessionService
                
                session_service = InMemorySessionService()
                runner = Runner(
                    app_name="uganda_egov_whatsapp_intelligent",
                    agent=self.adk_agent,
                    session_service=session_service
                )
                
                response = await runner.run(
                    session_id=user_id.replace("+", ""),
                    event=event
                )
                
                if response and hasattr(response, 'content') and response.content:
                    if hasattr(response.content, 'parts') and response.content.parts:
                        response_text = response.content.parts[0].text
                        print("✅ ADK agent response generated")
                        return response_text
            
            # Fallback to built-in intelligent responses
            print("📝 Using built-in intelligent responses...")
            return self._generate_fallback_response(message_text)
            
        except Exception as e:
            logger.error(f"Error generating intelligent response: {e}")
            return self._generate_fallback_response(message_text)
    
    def _generate_fallback_response(self, message_text: str) -> str:
        """Generate fallback intelligent response"""
        message_lower = message_text.lower().strip()
        
        # Enhanced intelligent responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start', 'hola', 'ola', 'good morning', 'good afternoon']):
            return """🇺🇬 Hello! Welcome to Uganda E-Gov WhatsApp Helpdesk!

I'm your intelligent AI assistant powered by advanced automation. I can help you with:

📋 **Birth Certificate (NIRA)**
• Check application status instantly
• Get requirements for new applications
• Find nearest NIRA offices
• Track processing timeline

💰 **Tax Services (URA)**  
• Check tax balance in real-time
• Validate TIN numbers
• Get tax clearance status
• Calculate tax obligations

🏦 **NSSF Services**
• Check contribution balance
• Generate statements
• View contribution history
• Member support services

🏡 **Land Verification**
• Verify ownership instantly
• Check title status
• Get plot information
• Land registry searches

🤖 **Powered by AI** - I understand natural language, so just tell me what you need!

What government service can I help you with today?"""
        
        elif any(word in message_lower for word in ['birth', 'certificate', 'nira', 'born', 'registration']):
            return """📋 **Birth Certificate Services (NIRA)**

I can intelligently assist you with:

✅ **Status Checking**
• Instant status lookup with reference number
• Processing timeline updates
• Application progress tracking

📝 **New Applications**
• Complete requirements checklist
• Document preparation guide
• Fee information and payment methods

🏢 **Office Locations**
• Find nearest NIRA office
• Operating hours and contact details
• Appointment booking assistance

📞 **Support Services**
• Direct contact information
• Complaint resolution
• Emergency certificate services

**How to proceed:**
• Provide your NIRA reference number for status check
• Or tell me what specific help you need

**Example:** "Check status NIRA/2023/123456"
**Example:** "I need a new birth certificate for my child"

What birth certificate service do you need?"""
        
        elif any(word in message_lower for word in ['tax', 'ura', 'tin', 'revenue', 'payment']):
            return """💰 **Tax Services (URA)**

Your intelligent tax assistant can help with:

💳 **Balance & Payments**
• Real-time tax balance checking
• Payment history and receipts
• Outstanding obligations
• Payment plan options

🆔 **TIN Services**
• TIN number validation
• Registration for new TIN
• TIN certificate download
• Update TIN information

📄 **Clearance & Compliance**
• Tax clearance certificate status
• Compliance verification
• Filing deadline reminders
• Penalty calculations

🏢 **URA Services**
• Find nearest URA office
• Online services access
• Contact information
• Appointment scheduling

**To get started:**
• Provide your TIN number for balance check
• Or describe what tax service you need

**Example:** "My TIN is 1234567890, check balance"
**Example:** "I need tax clearance certificate"

What tax service can I assist you with?"""
        
        elif any(word in message_lower for word in ['nssf', 'social security', 'pension', 'contribution', 'retirement']):
            return """🏦 **NSSF Services**

Your intelligent NSSF assistant provides:

💰 **Contribution Services**
• Real-time balance checking
• Contribution history analysis
• Monthly statement generation
• Projection calculations

📊 **Member Benefits**
• Benefit eligibility checking
• Claim status tracking
• Retirement planning
• Loan application status

📈 **Account Management**
• Update personal information
• Beneficiary management
• Contact details update
• Statement delivery preferences

📞 **Support Services**
• Member helpline access
• Office locations
• Online services guide
• Complaint resolution

**To proceed:**
• Provide your NSSF membership number
• Or tell me what you need help with

**Example:** "Check balance for member 123456789"
**Example:** "I want to update my beneficiaries"

How can I help with your NSSF needs?"""
        
        elif any(word in message_lower for word in ['land', 'title', 'property', 'plot', 'ownership', 'certificate']):
            return """🏡 **Land Verification Services**

Your intelligent land assistant offers:

✅ **Ownership Verification**
• Instant ownership verification
• Title authenticity checking
• Ownership history tracking
• Dispute resolution support

📋 **Title Services**
• Certificate of title status
• Title transfer processing
• Duplicate title applications
• Title correction services

🗺️ **Land Information**
• Plot details and boundaries
• Land use classifications
• Zoning information
• Development restrictions

📍 **Registry Services**
• Land registry searches
• Registration procedures
• Fee calculations
• Document requirements

**To get started:**
• Provide plot number and location
• Or describe what you need to verify

**Example:** "Verify plot 123 in Kampala Central"
**Example:** "Check title for Block 45 Plot 67 Entebbe"

What land verification do you need?"""
        
        else:
            return f"""🇺🇬 **Uganda E-Gov Intelligent Assistant**

I'm an AI-powered assistant that understands natural language and can help with:

📋 **Birth Certificate** - Say "birth certificate" or "NIRA"
💰 **Tax Services** - Say "tax" or "URA" or "TIN"  
🏦 **NSSF Services** - Say "NSSF" or "pension"
🏡 **Land Verification** - Say "land" or "property"

🤖 **I understand natural language!** 
Just tell me what you need in your own words:
• "I need to check my tax balance"
• "How do I get a birth certificate?"
• "What's my NSSF contribution?"
• "Verify my land ownership"

🌍 Available in: English, Luganda, Luo, Runyoro
⏰ Available 24/7 with intelligent automation
🇺🇬 Serving all Ugandan citizens

What government service can I help you with today?"""
    
    async def start_intelligent_monitoring(self):
        """Start intelligent message monitoring and response system"""
        print("\n🧠 Starting Intelligent Auto Responder...")
        print("📱 AI-powered WhatsApp monitoring active")
        print("🔄 Intelligent responses with Browser-Use + ADK")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        try:
            while True:
                # Monitor for new messages
                new_messages = await self.monitor_messages()
                
                for message in new_messages:
                    await self.handle_intelligent_message(message)
                
                # Wait before next check
                await asyncio.sleep(3)
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping intelligent responder...")
        except Exception as e:
            logger.error(f"Intelligent monitoring error: {e}")
            print(f"❌ Monitoring error: {e}")
    
    async def handle_intelligent_message(self, message_data: Dict[str, Any]):
        """Handle message with full intelligence"""
        try:
            from_contact = message_data.get('from', 'Unknown')
            message_text = message_data.get('text', '')
            
            print(f"\n📨 Intelligent message from {from_contact}:")
            print(f"   📝 Text: {message_text[:100]}...")
            
            # Extract phone number
            phone_number = self._extract_phone_number(from_contact)
            
            # Generate intelligent response
            response_text = await self.generate_intelligent_response(message_text, phone_number)
            
            # Send intelligent response
            print(f"📤 Sending intelligent response...")
            result = await self.send_intelligent_message(phone_number, response_text)
            
            if result.get("status") == "success":
                print("✅ Intelligent response sent!")
            else:
                print(f"❌ Response failed: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error handling intelligent message: {e}")
            print(f"❌ Error: {e}")
    
    def _extract_phone_number(self, contact_name: str) -> str:
        """Extract phone number intelligently"""
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
    
    async def cleanup(self):
        """Cleanup all resources"""
        print("🧹 Cleaning up intelligent agent...")
        if self.browser_agent:
            try:
                await self.browser_agent.close()
            except:
                pass
        print("✅ Intelligent cleanup complete")

async def main():
    """Main intelligent agent function"""
    agent = WhatsAppIntelligentAgent()
    
    try:
        # Initialize intelligent systems
        success = await agent.initialize()
        if not success:
            return
        
        # Authenticate
        success = await agent.authenticate()
        if not success:
            return
        
        # Send startup message
        print("\n📧 Sending intelligent startup message...")
        await agent.send_intelligent_message(
            "+256726294861",
            "🧠 Uganda E-Gov Intelligent WhatsApp Assistant is now online! Powered by Browser-Use + ADK agents for maximum intelligence. Ready to serve citizens!"
        )
        
        # Start intelligent monitoring
        await agent.start_intelligent_monitoring()
        
    except KeyboardInterrupt:
        print("\n👋 Intelligent agent stopped!")
    except Exception as e:
        logger.error(f"Intelligent agent error: {e}")
        print(f"❌ Error: {e}")
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())