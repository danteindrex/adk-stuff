#!/usr/bin/env python3
"""
Dynamic AI WhatsApp Client - Uses Gemini LLM for diverse, contextual responses
No more template messages - AI generates unique responses every time
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

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class DynamicAIWhatsAppClient:
    """Dynamic AI WhatsApp client using Gemini for contextual responses"""
    
    def __init__(self, phone_number: str = "+256726294861"):
        self.phone_number = phone_number
        self.gemini_llm = None
        self.is_initialized = False
        self.conversation_history = {}  # Store conversation context per user
        self.demo_mode = True  # Set to False when Twilio is ready
        
        logger.info(f"Dynamic AI WhatsApp client initialized for {self.phone_number}")
    
    async def initialize(self):
        """Initialize the Gemini LLM for dynamic responses"""
        try:
            print("🤖 Initializing Dynamic AI WhatsApp Client")
            print("=" * 60)
            print(f"📱 Phone Number: {self.phone_number}")
            print("🧠 Using Gemini AI for dynamic, contextual responses")
            print("🎭 Demo Mode - No actual messages sent")
            print("=" * 60)
            
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
                temperature=0.7,  # Higher temperature for more diverse responses
                max_tokens=1000,
                timeout=30,
                max_retries=2,
                google_api_key=google_api_key
            )
            
            print("✅ Gemini LLM initialized successfully")
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Uganda E-Gov assistant"""
        return """You are an AI assistant for the Uganda E-Government WhatsApp Helpdesk. Your role is to help Ugandan citizens access government services through WhatsApp.

IMPORTANT GUIDELINES:
- Be helpful, friendly, and professional
- Use emojis appropriately (🇺🇬 for Uganda, 📋 for documents, etc.)
- Keep responses concise but informative
- Always offer specific next steps
- Be culturally sensitive to Ugandan context
- Support multiple languages when possible (English, Luganda, Luo, Runyoro)

SERVICES YOU HELP WITH:
1. Birth Certificate (NIRA) - Application status, requirements, office locations
2. Tax Services (URA) - TIN validation, tax balance, clearance certificates
3. NSSF Services - Contribution balance, statements, member services
4. Land Verification (NLIS) - Ownership verification, title checks, plot information

RESPONSE STYLE:
- Generate unique, contextual responses (no templates)
- Vary your language and approach based on the user's tone
- Ask clarifying questions when needed
- Provide examples relevant to the user's request
- Include relevant contact information or next steps

Remember: You're representing the Uganda government, so maintain professionalism while being approachable."""

    async def _generate_ai_response(self, user_message: str, user_id: str) -> str:
        """Generate dynamic AI response using Gemini"""
        try:
            # Get conversation history for context
            history = self.conversation_history.get(user_id, [])
            
            # Create messages for the LLM
            messages = [
                SystemMessage(content=self._get_system_prompt())
            ]
            
            # Add conversation history for context (last 3 exchanges)
            for msg in history[-6:]:  # Last 3 user-assistant pairs
                messages.append(msg)
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            print(f"🧠 Generating AI response for: '{user_message[:50]}...'")
            
            # Generate response using Gemini
            response = await asyncio.to_thread(self.gemini_llm.invoke, messages)
            
            ai_response = response.content.strip()
            
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
        """Simulate sending a message (demo mode)"""
        try:
            if not self.is_initialized:
                return {"status": "error", "error": "Client not initialized"}
            
            if self.demo_mode:
                print(f"📤 [DEMO] Would send to {to_number}")
                print(f"📊 Message length: {len(message)} characters")
                
                # Simulate API delay
                await asyncio.sleep(0.3)
                
                demo_message_id = f"demo_ai_{int(datetime.now().timestamp())}"
                
                return {
                    "status": "success",
                    "message_id": demo_message_id,
                    "to_number": to_number,
                    "timestamp": datetime.now().isoformat(),
                    "method": "demo_ai_mode"
                }
            else:
                # TODO: Integrate with Twilio when ready
                # return await self.twilio_client.send_text_message(to_number, message)
                pass
                
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def handle_incoming_message(self, from_number: str, message_text: str) -> Dict[str, Any]:
        """Handle incoming message with dynamic AI response"""
        try:
            print(f"\n📨 Incoming message from {from_number}:")
            print(f"   📝 Text: {message_text}")
            
            # Generate dynamic AI response
            ai_response = await self._generate_ai_response(message_text, from_number)
            
            print(f"\n🤖 AI Generated Response:")
            print("=" * 60)
            print(ai_response)
            print("=" * 60)
            
            # Send response
            result = await self.send_message(from_number, ai_response)
            
            if result.get("status") == "success":
                print("✅ AI response would be sent successfully!")
                logger.info(f"AI response generated for {from_number}: {len(ai_response)} chars")
                return {
                    "status": "success",
                    "response_sent": True,
                    "message_id": result.get("message_id"),
                    "ai_generated": True,
                    "response_length": len(ai_response)
                }
            else:
                print(f"❌ Response sending failed: {result.get('error')}")
                return {
                    "status": "error",
                    "response_sent": False,
                    "error": result.get("error"),
                    "ai_generated": True
                }
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            print(f"❌ Message handling error: {e}")
            return {
                "status": "error",
                "response_sent": False,
                "error": str(e)
            }
    
    async def interactive_demo(self):
        """Interactive demo mode for testing AI responses"""
        print("\n🎭 Interactive AI Demo Mode")
        print("=" * 50)
        print("🧠 Each response is generated dynamically by Gemini AI")
        print("💬 Type messages to see diverse, contextual responses")
        print("🔄 Try the same question multiple times for variety")
        print("Type 'quit' to exit")
        print("=" * 50)
        
        user_id = "+256726294861"  # Demo user
        
        while True:
            try:
                user_input = input("\n💬 Your message: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Exiting AI demo mode...")
                    break
                
                if not user_input:
                    continue
                
                # Process the message with AI
                result = await self.handle_incoming_message(user_id, user_input)
                
                print(f"\n📊 Result: {result.get('status')}")
                if result.get('ai_generated'):
                    print(f"🧠 AI Response Length: {result.get('response_length', 0)} chars")
                
            except KeyboardInterrupt:
                print("\n👋 Demo interrupted by user")
                break
            except Exception as e:
                print(f"❌ Demo error: {e}")
    
    async def test_response_diversity(self):
        """Test how diverse the AI responses are for the same input"""
        print("\n🔬 Testing Response Diversity")
        print("=" * 40)
        
        test_message = "I need help with birth certificate"
        user_id = "+256726294861"
        
        print(f"Testing message: '{test_message}'")
        print("Generating 3 different responses...\n")
        
        for i in range(3):
            print(f"🧪 Response {i+1}:")
            print("-" * 30)
            
            # Clear history to get fresh responses
            if user_id in self.conversation_history:
                del self.conversation_history[user_id]
            
            response = await self._generate_ai_response(test_message, user_id)
            print(response)
            print()
            
            await asyncio.sleep(1)  # Brief pause between generations

async def main():
    """Main function for AI demo testing"""
    client = DynamicAIWhatsAppClient()
    
    try:
        # Initialize client
        success = await client.initialize()
        if not success:
            print("❌ Failed to initialize AI client")
            return
        
        print("\n🎯 AI Demo Options:")
        print("1. Interactive chat mode")
        print("2. Test response diversity")
        print("3. Automated test suite")
        
        choice = input("\nSelect option (1, 2, or 3): ").strip()
        
        if choice == "1":
            # Interactive mode
            await client.interactive_demo()
        elif choice == "2":
            # Diversity test
            await client.test_response_diversity()
        else:
            # Automated test suite with AI responses
            print("\n🧪 Running AI test suite...")
            test_messages = [
                "Hello, I need help",
                "I want to check my birth certificate status",
                "How do I pay my taxes?", 
                "What is my NSSF balance?",
                "I need to verify land ownership",
                "Can you help me with government services?",
                "Webale nyo! (Thank you in Luganda)"
            ]
            
            user_id = "+256726294861"
            
            for i, test_msg in enumerate(test_messages, 1):
                print(f"\n🧪 AI Test {i}/{len(test_messages)}: '{test_msg}'")
                result = await client.handle_incoming_message(user_id, test_msg)
                print(f"✅ Test {i} completed: {result.get('status')}")
                await asyncio.sleep(2)  # Pause between tests
            
            print("\n✅ All AI tests completed!")
        
    except KeyboardInterrupt:
        print("\n👋 AI demo stopped!")
    except Exception as e:
        logger.error(f"AI demo error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧠 Uganda E-Gov Dynamic AI WhatsApp Client")
    print("🚀 Powered by Gemini AI for diverse responses")
    print("🎭 No more templates - every response is unique!")
    print("=" * 60)
    asyncio.run(main())