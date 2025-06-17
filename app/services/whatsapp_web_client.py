"""
WhatsApp Web Automation Client
Headless browser automation for sending and receiving WhatsApp messages
"""

import os
import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhatsAppWebClient:
    """WhatsApp Web automation client using Playwright"""
    
    def __init__(self, phone_number: str = "+256726294861", headless: bool = None):
        """Initialize WhatsApp Web client"""
        self.phone_number = phone_number
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_authenticated = False
        self.session_dir = "whatsapp_session"
        self.last_message_check = datetime.now()
        self.message_handlers = []
        
        # Auto-detect headless mode based on session existence
        if headless is None:
            self.headless = self._should_run_headless()
        else:
            self.headless = headless
        
        # Create session directory
        os.makedirs(self.session_dir, exist_ok=True)
        
        logger.info(f"WhatsApp Web client initialized for {self.phone_number} (headless: {self.headless})")
    
    def _should_run_headless(self) -> bool:
        """Determine if we should run in headless mode based on existing session"""
        try:
            # Check if session directory has authentication data
            default_dir = os.path.join(self.session_dir, "Default")
            if os.path.exists(default_dir):
                # Look for WhatsApp-related files that indicate successful authentication
                local_storage = os.path.join(default_dir, "Local Storage")
                session_storage = os.path.join(default_dir, "Session Storage")
                
                if os.path.exists(local_storage) or os.path.exists(session_storage):
                    print("🔍 Found existing session - running in headless mode")
                    return True
            
            print("🔍 No existing session found - running with visible browser for QR code")
            return False
        except Exception as e:
            logger.warning(f"Error checking session: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the WhatsApp Web client"""
        try:
            print("🚀 Starting WhatsApp Web client...")
            
            # Launch browser with persistent context
            playwright = await async_playwright().start()
            
            # Use persistent context for session storage
            self.context = await playwright.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                headless=self.headless,  # Auto-detect based on existing session
                viewport={'width': 1366, 'height': 768},
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            if self.headless:
                print("🔇 Running in headless mode (background)")
            else:
                print("🖥️  Running with visible browser (for QR code)")
            
            # Browser is not needed when using persistent context
            self.browser = None
            
            # Create page
            self.page = await self.context.new_page()
            
            # Navigate to WhatsApp Web
            print("📱 Navigating to WhatsApp Web...")
            await self.page.goto('https://web.whatsapp.com', wait_until='networkidle')
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Check if already authenticated
            if await self._check_authentication():
                print("✅ Already authenticated with WhatsApp Web")
                self.is_authenticated = True
                return True
            else:
                print("🔐 Authentication required - please scan QR code")
                await self._wait_for_authentication()
                return self.is_authenticated
                
        except Exception as e:
            logger.error(f"Failed to start WhatsApp Web client: {e}")
            print(f"❌ Failed to start WhatsApp Web client: {e}")
            return False
    
    async def _check_authentication(self) -> bool:
        """Check if user is authenticated"""
        try:
            # Wait a bit for page to load
            await asyncio.sleep(3)
            
            # Look for the main chat interface (indicates authenticated)
            try:
                await self.page.wait_for_selector('[data-testid="chat-list"]', timeout=10000)
                print("✅ Found chat list - authenticated!")
                return True
            except:
                pass
            
            # Alternative selectors for authenticated state
            auth_selectors = [
                '[data-testid="conversation-panel-wrapper"]',
                '[data-testid="side"]',
                '.two',  # WhatsApp Web main container
                '#app .two'  # Alternative main container
            ]
            
            for selector in auth_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    print(f"✅ Found authenticated element: {selector}")
                    return True
                except:
                    continue
            
            # Look for QR code (indicates not authenticated)
            try:
                await self.page.wait_for_selector('[data-testid="qr-code"]', timeout=3000)
                print("🔐 Found QR code - not authenticated")
                return False
            except:
                pass
            
            # Check page content for authentication indicators
            try:
                page_content = await self.page.content()
                if 'chat-list' in page_content or 'conversation' in page_content:
                    print("✅ Found chat content - authenticated!")
                    return True
                elif 'qr-code' in page_content or 'scan' in page_content.lower():
                    print("🔐 Found QR content - not authenticated")
                    return False
            except:
                pass
            
            print("❓ Authentication status unclear - assuming not authenticated")
            return False
            
        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            return False
    
    async def _wait_for_authentication(self, timeout: int = 60) -> bool:
        """Wait for user to scan QR code and authenticate"""
        print("📱 Please scan the QR code with your WhatsApp mobile app...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if chat list is available (indicates successful auth)
                await self.page.wait_for_selector('[data-testid="chat-list"]', timeout=2000)
                print("✅ Authentication successful!")
                self.is_authenticated = True
                return True
            except:
                # Still waiting for authentication
                await asyncio.sleep(2)
                print("⏳ Waiting for QR code scan...")
        
        print("❌ Authentication timeout")
        return False
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a message to a WhatsApp contact"""
        try:
            if not self.is_authenticated:
                return {"status": "error", "error": "Not authenticated"}
            
            print(f"📤 Sending message to {to_number}")
            
            # Format phone number (remove + and spaces)
            clean_number = to_number.replace("+", "").replace(" ", "").replace("-", "")
            
            # Search for contact
            search_box = await self.page.wait_for_selector('[data-testid="chat-list-search"]')
            await search_box.click()
            await search_box.fill(clean_number)
            await asyncio.sleep(2)
            
            # Click on the contact
            try:
                contact_selector = f'[title*="{clean_number}"], [data-testid="cell-frame-title"]:has-text("{clean_number}")'
                await self.page.wait_for_selector(contact_selector, timeout=5000)
                await self.page.click(contact_selector)
            except:
                # If contact not found, try to start new chat
                print(f"Contact {clean_number} not found, starting new chat...")
                await self._start_new_chat(clean_number)
            
            # Wait for chat to load
            await asyncio.sleep(2)
            
            # Find message input box
            message_box = await self.page.wait_for_selector('[data-testid="conversation-compose-box-input"]')
            
            # Type and send message
            await message_box.click()
            await message_box.fill(message)
            
            # Send message (Enter key or send button)
            send_button = await self.page.wait_for_selector('[data-testid="send"]')
            await send_button.click()
            
            print(f"✅ Message sent to {to_number}")
            logger.info(f"Sent WhatsApp message to {to_number}")
            
            return {
                "status": "success",
                "message_id": f"wa_web_{int(time.time())}",
                "to_number": to_number,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            print(f"❌ Failed to send message: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _start_new_chat(self, phone_number: str):
        """Start a new chat with a phone number"""
        try:
            # Click on new chat button
            new_chat_button = await self.page.wait_for_selector('[data-testid="new-chat-btn"]')
            await new_chat_button.click()
            
            # Wait for new chat dialog
            await asyncio.sleep(1)
            
            # Enter phone number
            search_input = await self.page.wait_for_selector('[data-testid="new-chat-search"]')
            await search_input.fill(phone_number)
            await asyncio.sleep(2)
            
            # Click on the phone number option
            phone_option = await self.page.wait_for_selector(f'[title*="{phone_number}"]')
            await phone_option.click()
            
        except Exception as e:
            logger.error(f"Failed to start new chat: {e}")
            raise
    
    async def get_new_messages(self) -> List[Dict[str, Any]]:
        """Get new messages since last check"""
        try:
            if not self.is_authenticated:
                return []
            
            messages = []
            
            # Get all chat items
            chat_items = await self.page.query_selector_all('[data-testid="chat-list"] [data-testid="cell-frame-container"]')
            
            for chat_item in chat_items:
                try:
                    # Check if chat has unread messages
                    unread_indicator = await chat_item.query_selector('[data-testid="unread-count"]')
                    if unread_indicator:
                        # Click on the chat
                        await chat_item.click()
                        await asyncio.sleep(1)
                        
                        # Get contact name/number
                        contact_name = await self.page.text_content('[data-testid="conversation-header"] [data-testid="conversation-info-header-chat-title"]')
                        
                        # Get recent messages
                        message_elements = await self.page.query_selector_all('[data-testid="msg-container"]')
                        
                        # Get the last few messages
                        for msg_element in message_elements[-5:]:  # Last 5 messages
                            try:
                                # Check if it's an incoming message
                                is_incoming = await msg_element.query_selector('[data-testid="msg-container-incoming"]')
                                if is_incoming:
                                    message_text = await msg_element.text_content('[data-testid="conversation-text"]')
                                    timestamp = await msg_element.get_attribute('data-pre-plain-text')
                                    
                                    if message_text and self._is_new_message(timestamp):
                                        messages.append({
                                            "from": contact_name,
                                            "text": message_text.strip(),
                                            "timestamp": timestamp,
                                            "message_id": f"wa_web_{int(time.time())}_{len(messages)}"
                                        })
                            except:
                                continue
                        
                        # Go back to chat list
                        await self.page.click('[data-testid="back"]')
                        await asyncio.sleep(1)
                        
                except:
                    continue
            
            self.last_message_check = datetime.now()
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get new messages: {e}")
            return []
    
    def _is_new_message(self, timestamp_str: str) -> bool:
        """Check if message is newer than last check"""
        try:
            # This is a simplified check - you might need to parse the actual timestamp
            # WhatsApp Web timestamps can be in various formats
            return True  # For now, consider all messages as potentially new
        except:
            return True
    
    async def add_message_handler(self, handler):
        """Add a message handler function"""
        self.message_handlers.append(handler)
    
    async def start_message_polling(self, interval: int = 5):
        """Start polling for new messages"""
        print(f"🔄 Starting message polling (every {interval} seconds)...")
        
        while self.is_authenticated:
            try:
                new_messages = await self.get_new_messages()
                
                for message in new_messages:
                    print(f"📨 New message from {message['from']}: {message['text'][:50]}...")
                    
                    # Call all message handlers
                    for handler in self.message_handlers:
                        try:
                            await handler(message)
                        except Exception as e:
                            logger.error(f"Message handler error: {e}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Message polling error: {e}")
                await asyncio.sleep(interval)
    
    async def stop(self):
        """Stop the WhatsApp Web client"""
        try:
            if self.context:
                await self.context.close()
                print("🛑 WhatsApp Web client stopped")
        except Exception as e:
            logger.error(f"Error stopping WhatsApp Web client: {e}")
    
    async def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Alias for send_message to maintain compatibility"""
        return await self.send_message(to_number, message)
    
    async def send_template_message(self, to_number: str, template_name: str, 
                                  template_params: List[str] = None) -> Dict[str, Any]:
        """Send a template message"""
        # Format template message
        message = self._format_template(template_name, template_params)
        return await self.send_message(to_number, message)
    
    def _format_template(self, template_name: str, template_params: List[str] = None) -> str:
        """Format a template message"""
        templates = {
            "welcome": "🇺🇬 Welcome to Uganda E-Gov WhatsApp Helpdesk! How can I help you today?",
            "error": "❌ Sorry, we encountered an error: {0}",
            "confirmation": "✅ Your request has been confirmed. Reference number: {0}",
            "help": "ℹ️ Available services:\n1. Birth Certificate\n2. Tax Services\n3. Land Records\n4. NSSF Services\n\nType the service name or number to get started."
        }
        
        template = templates.get(template_name, template_name)
        if template and template_params:
            try:
                template = template.format(*template_params)
            except Exception as e:
                logger.error(f"Error formatting template: {e}")
        
        return template


# Global WhatsApp Web client instance
_whatsapp_client = None

async def get_whatsapp_client() -> WhatsAppWebClient:
    """Get or create WhatsApp Web client instance"""
    global _whatsapp_client
    
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppWebClient("+256726294861")
        
        # Start the client
        success = await _whatsapp_client.start()
        if not success:
            logger.error("Failed to start WhatsApp Web client")
            raise Exception("Failed to start WhatsApp Web client")
    
    return _whatsapp_client

async def cleanup_whatsapp_client():
    """Cleanup WhatsApp Web client"""
    global _whatsapp_client
    
    if _whatsapp_client:
        await _whatsapp_client.stop()
        _whatsapp_client = None