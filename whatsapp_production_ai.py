#!/usr/bin/env python3
"""
Production WhatsApp Client with Dynamic AI Responses
Uses Gemini LLM for diverse, contextual responses + Twilio for message delivery
Perfect for Cloud Run deployment
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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class ProductionAIWhatsAppClient:
    """Production WhatsApp client with dynamic AI responses using Gemini + Twilio"""
    
    def __init__(self, phone_number: str = "+256726294861"):
        self.phone_number = phone_number
        self.twilio_client = None
        self.gemini_llm = None
        self.is_initialized = False
        self.conversation_history = {}  # Store conversation context per user
        self.processed_messages = set()
        
        logger.info(f"Production AI WhatsApp client initialized for {self.phone_number}")
    
    async def initialize(self):
        """Initialize both Twilio and Gemini for production use"""
        try:
            print("🤖 Initializing Production AI WhatsApp Client")
            print("=" * 60)
            print(f"📱 Phone Number: {self.phone_number}")
            print("🧠 Using Gemini AI for dynamic responses")
            print("📡 Using Twilio API for message delivery")
            print("=" * 60)
            
            # Initialize Twilio client
            print("🔧 Setting up Twilio WhatsApp client...")
            self.twilio_client = TwilioClient()
            print("✅ Twilio WhatsApp client initialized")
            
            # Get Google API key
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("⚠️  GOOGLE_API_KEY not found in environment variables")
                print("💡 Please set GOOGLE_API_KEY in your .env file")
                return False
            
            # Initialize Gemini LLM
            print("🔧 Setting up Gemini LLM...")
            self.gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.7,  # Higher temperature for diverse responses
                max_tokens=1000,
                timeout=30,
                max_retries=2,
                google_api_key=google_api_key
            )
            print("✅ Gemini LLM initialized")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize production AI client: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Uganda E-Gov assistant"""
        return """You are an AI assistant for the Uganda E-Government WhatsApp Helpdesk. Your role is to help Ugandan citizens access government services through WhatsApp.

IMPORTANT GUIDELINES:
- Be helpful, friendly, and professional
- Use emojis appropriately (🇺🇬 for Uganda, 📋 for documents, etc.)
- Keep responses concise but informative (max 800 characters for WhatsApp)
- Always offer specific next steps
- Be culturally sensitive to Ugandan context
- Support multiple languages when possible (English, Luganda, Luo, Runyoro)
- Vary your language and tone to avoid repetitive responses

SERVICES YOU HELP WITH:
1. Birth Certificate (NIRA) - Application status, requirements, office locations
2. Tax Services (URA) - TIN validation, tax balance, clearance certificates  
3. NSSF Services - Contribution balance, statements, member services
4. Land Verification (NLIS) - Ownership verification, title checks, plot information

RESPONSE STYLE:
- Generate unique, contextual responses (no templates)
- Adapt your tone to match the user's communication style
- Ask clarifying questions when needed
- Provide examples relevant to the user's specific request
- Include relevant contact information or next steps when appropriate
- If user provides reference numbers, acknowledge them specifically

IMPORTANT: Keep responses under 800 characters for WhatsApp compatibility.

Remember: You represent the Uganda government - be professional yet approachable."""

    async def _generate_ai_response(self, user_message: str, user_id: str) -> str:
        """Generate dynamic AI response using Gemini"""
        try:
            # Get conversation history for context
            history = self.conversation_history.get(user_id, [])
            
            # Create messages for the LLM
            messages = [
                SystemMessage(content=self._get_system_prompt())
            ]
            
            # Add conversation history for context (last 4 exchanges)
            for msg in history[-8:]:  # Last 4 user-assistant pairs
                messages.append(msg)
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            print(f"🧠 Generating AI response for: '{user_message[:50]}...'")
            
            # Generate response using Gemini
            response = await asyncio.to_thread(self.gemini_llm.invoke, messages)
            
            ai_response = response.content.strip()
            
            # Ensure response is not too long for WhatsApp
            if len(ai_response) > 1000:
                ai_response = ai_response[:950] + "..."
            
            # Update conversation history
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            self.conversation_history[user_id].extend([
                HumanMessage(content=user_message),
                response
            ])
            
            # Keep only last 10 messages to avoid token limits
            if len(self.conversation_history[user_id]) > 10:
                self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
            
            print(f"✅ AI response generated ({len(ai_response)} chars)")
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            print(f"❌ AI response error: {e}")
            
            # Fallback response
            return """🇺🇬 Hello! I'm your Uganda E-Gov assistant. I'm here to help you with government services like birth certificates, tax services, NSSF, and land verification. 

How can I assist you today?"""
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a message using Twilio WhatsApp API"""
        try:
            if not self.is_initialized:
                return {"status": "error", "error": "Client not initialized"}
            
            print(f"📤 Sending AI-generated message to {to_number}")
            print(f"📝 Message preview: {message[:100]}...")
            
            # Send via Twilio
            result = await self.twilio_client.send_text_message(to_number, message)
            
            if result.get("status") == "success":
                print(f"✅ AI message sent to {to_number}")
                print(f"📧 Twilio SID: {result.get('message_id')}")
                return {
                    "status": "success",
                    "message_id": result.get("message_id"),
                    "to_number": to_number,
                    "timestamp": datetime.now().isoformat(),
                    "method": "twilio_api",
                    "ai_generated": True
                }
            else:
                print(f"❌ Failed to send AI message: {result.get('error')}")
                return {"status": "error", "error": result.get("error")}
                
        except Exception as e:
            logger.error(f"Failed to send AI message: {e}")
            print(f"❌ Send AI message error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def handle_incoming_message(self, from_number: str, message_text: str) -> Dict[str, Any]:
        """Handle incoming message with dynamic AI response"""
        try:
            print(f"\n📨 Incoming message from {from_number}:")
            print(f"   📝 Text: {message_text}")
            
            # Generate dynamic AI response
            ai_response = await self._generate_ai_response(message_text, from_number)
            
            print(f"\n🤖 AI Generated Response:")
            print("=" * 50)
            print(ai_response)
            print("=" * 50)
            
            # Send AI response via Twilio
            result = await self.send_message(from_number, ai_response)
            
            if result.get("status") == "success":
                print("✅ AI response sent successfully!")
                logger.info(f"AI response sent to {from_number}: {len(ai_response)} chars")
                return {
                    "status": "success",
                    "response_sent": True,
                    "message_id": result.get("message_id"),
                    "ai_generated": True,
                    "response_length": len(ai_response)
                }
            else:
                print(f"❌ Failed to send AI response: {result.get('error')}")
                logger.error(f"Failed to send AI response to {from_number}: {result.get('error')}")
                return {
                    "status": "error",
                    "response_sent": False,
                    "error": result.get("error"),
                    "ai_generated": True
                }
            
        except Exception as e:
            logger.error(f"Error handling message with AI: {e}")
            print(f"❌ AI message handling error: {e}")
            return {
                "status": "error",
                "response_sent": False,
                "error": str(e)
            }
    
    async def send_startup_message(self):
        """Send AI-generated startup notification"""
        try:
            startup_prompt = "Generate a brief, friendly startup message announcing that the Uganda E-Gov WhatsApp Helpdesk is now online and ready to help citizens with government services. Keep it under 300 characters."
            
            startup_message = await self._generate_ai_response(startup_prompt, "system")
            
            result = await self.send_message(self.phone_number, startup_message)
            
            if result.get("status") == "success":
                print("✅ AI startup message sent!")
                return True
            else:
                print(f"⚠️  AI startup message failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send AI startup message: {e}")
            return False

# Global client instance for webhook usage
_production_ai_client = None

async def get_production_ai_client() -> ProductionAIWhatsAppClient:
    """Get or create production AI WhatsApp client"""
    global _production_ai_client
    
    if _production_ai_client is None:
        _production_ai_client = ProductionAIWhatsAppClient("+256726294861")
        success = await _production_ai_client.initialize()
        
        if not success:
            logger.error("Failed to initialize production AI WhatsApp client")
            raise Exception("Failed to initialize production AI WhatsApp client")
    
    return _production_ai_client

async def handle_webhook_message_ai(from_number: str, message_text: str) -> Dict[str, Any]:
    """Handle webhook message with AI - main entry point for Cloud Run"""
    try:
        client = await get_production_ai_client()
        return await client.handle_incoming_message(from_number, message_text)
    except Exception as e:
        logger.error(f"AI webhook message handling failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "response_sent": False,
            "ai_generated": False
        }

async def main():
    """Main function for testing AI production client"""
    client = ProductionAIWhatsAppClient()
    
    try:
        # Initialize client
        success = await client.initialize()
        if not success:
            print("❌ Failed to initialize AI production client")
            return
        
        print("\n🎯 Production AI Testing Options:")
        print("1. Test AI response generation (no Twilio)")
        print("2. Full production test (with Twilio)")
        
        choice = input("\nSelect option (1 or 2): ").strip()
        
        if choice == "1":
            # Test AI generation only
            print("\n🧪 Testing AI response generation...")
            test_messages = [
                "Hello, I need help with government services",
                "I want to check my birth certificate application NIRA/2023/123456",
                "How can I verify my TIN number 1234567890?",
                "What documents do I need for NSSF withdrawal?",
                "I need to verify ownership of plot 45 in Kampala"
            ]
            
            for i, test_msg in enumerate(test_messages, 1):
                print(f"\n🧪 AI Test {i}/{len(test_messages)}: '{test_msg}'")
                ai_response = await client._generate_ai_response(test_msg, "+256726294861")
                print(f"🤖 AI Response: {ai_response}")
                print(f"📊 Length: {len(ai_response)} chars")
                await asyncio.sleep(1)
        
        else:
            # Full production test with Twilio
            print("\n🚀 Full production test with Twilio...")
            print("⚠️  This will use your Twilio account!")
            
            confirm = input("Continue? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Test cancelled")
                return
            
            # Send startup message
            print("\n📧 Sending AI startup message...")
            await client.send_startup_message()
            
            # Test message handling
            test_result = await client.handle_incoming_message(
                "+256726294861", 
                "Hello, I need help with birth certificate"
            )
            print(f"📊 Test result: {test_result}")
        
        print("\n✅ All AI production tests completed!")
        
    except KeyboardInterrupt:
        print("\n👋 AI production client stopped!")
    except Exception as e:
        logger.error(f"AI production error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧠 Uganda E-Gov Production AI WhatsApp Client")
    print("🚀 Dynamic AI responses + Twilio delivery")
    print("☁️  Cloud Run ready with diverse responses")
    print("=" * 60)
    asyncio.run(main())