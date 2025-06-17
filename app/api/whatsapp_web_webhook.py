"""
WhatsApp Web Webhook Handler
Handles incoming messages from WhatsApp Web automation
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.whatsapp_web_client import get_whatsapp_client
from app.core.logging_config import StructuredLogger

logger = StructuredLogger(__name__)
whatsapp_web_router = APIRouter()

# Global message processing queue
message_queue = asyncio.Queue()
processing_active = False

class WhatsAppWebMessageProcessor:
    """Process incoming WhatsApp Web messages"""
    
    def __init__(self):
        self.client = None
        self.agent_orchestrator = None
    
    async def initialize(self):
        """Initialize the message processor"""
        try:
            # Get WhatsApp Web client
            self.client = await get_whatsapp_client()
            
            # Import agent orchestrator (avoid circular imports)
            from app.agents.adk_agents_modular import get_root_agent
            self.agent_orchestrator = await get_root_agent()
            
            # Add message handler to client
            await self.client.add_message_handler(self.handle_incoming_message)
            
            logger.info("WhatsApp Web message processor initialized")
            
        except Exception as e:
            logger.error("Failed to initialize WhatsApp Web message processor", error=e)
            raise
    
    async def handle_incoming_message(self, message: Dict[str, Any]):
        """Handle incoming WhatsApp message"""
        try:
            logger.info(f"Processing WhatsApp Web message from {message.get('from')}")
            
            # Extract message details
            from_contact = message.get('from', '')
            message_text = message.get('text', '')
            message_id = message.get('message_id', '')
            
            # Extract phone number from contact name if possible
            # This is a simplified approach - you might need more sophisticated contact resolution
            phone_number = self._extract_phone_number(from_contact)
            
            if not phone_number:
                logger.warning(f"Could not extract phone number from contact: {from_contact}")
                return
            
            # Create message object for processing
            whatsapp_message = {
                "message_id": message_id,
                "from_number": phone_number,
                "to_number": "+256726294861",  # Your WhatsApp number
                "text": message_text,
                "timestamp": message.get('timestamp'),
                "type": "text"
            }
            
            # Process with agent system
            if self.agent_orchestrator:
                response = await self.agent_orchestrator.process_message(whatsapp_message)
                
                # Send response back
                if response and response.get('response'):
                    await self.client.send_message(phone_number, response['response'])
                    logger.info(f"Sent response to {phone_number}")
            
        except Exception as e:
            logger.error("Error processing WhatsApp Web message", error=e)
    
    def _extract_phone_number(self, contact_name: str) -> str:
        """Extract phone number from contact name"""
        try:
            # If contact name is already a phone number
            if contact_name.replace('+', '').replace(' ', '').replace('-', '').isdigit():
                return contact_name
            
            # Look for phone number patterns in contact name
            import re
            phone_pattern = r'(\+?256\d{9}|\+?\d{10,15})'
            match = re.search(phone_pattern, contact_name)
            
            if match:
                return match.group(1)
            
            # If no phone number found, return the contact name as-is
            # The system will need to handle contact name to phone number mapping
            return contact_name
            
        except Exception as e:
            logger.error(f"Error extracting phone number from {contact_name}", error=e)
            return contact_name

# Global processor instance
message_processor = WhatsAppWebMessageProcessor()

@whatsapp_web_router.on_event("startup")
async def startup_whatsapp_web():
    """Initialize WhatsApp Web on startup"""
    global processing_active
    
    try:
        logger.info("Starting WhatsApp Web integration...")
        
        # Initialize message processor
        await message_processor.initialize()
        
        # Start message polling in background
        processing_active = True
        asyncio.create_task(start_message_polling())
        
        logger.info("WhatsApp Web integration started successfully")
        
    except Exception as e:
        logger.error("Failed to start WhatsApp Web integration", error=e)

async def start_message_polling():
    """Start polling for messages in background"""
    global processing_active
    
    try:
        if message_processor.client:
            await message_processor.client.start_message_polling(interval=5)
    except Exception as e:
        logger.error("Message polling error", error=e)
    finally:
        processing_active = False

@whatsapp_web_router.get("/whatsapp-web/status")
async def get_whatsapp_web_status():
    """Get WhatsApp Web client status"""
    try:
        client = await get_whatsapp_client()
        return {
            "status": "connected" if client.is_authenticated else "disconnected",
            "phone_number": client.phone_number,
            "processing_active": processing_active
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@whatsapp_web_router.post("/whatsapp-web/send")
async def send_whatsapp_web_message(
    to_number: str,
    message: str,
    background_tasks: BackgroundTasks
):
    """Send a message via WhatsApp Web"""
    try:
        client = await get_whatsapp_client()
        
        if not client.is_authenticated:
            raise HTTPException(status_code=400, detail="WhatsApp Web not authenticated")
        
        # Send message in background
        background_tasks.add_task(client.send_message, to_number, message)
        
        return {
            "status": "queued",
            "to_number": to_number,
            "message_length": len(message)
        }
        
    except Exception as e:
        logger.error("Failed to send WhatsApp Web message", error=e)
        raise HTTPException(status_code=500, detail=str(e))

@whatsapp_web_router.post("/whatsapp-web/restart")
async def restart_whatsapp_web():
    """Restart WhatsApp Web client"""
    try:
        global processing_active
        
        # Stop current client
        processing_active = False
        
        from app.services.whatsapp_web_client import cleanup_whatsapp_client
        await cleanup_whatsapp_client()
        
        # Restart
        await startup_whatsapp_web()
        
        return {"status": "restarted"}
        
    except Exception as e:
        logger.error("Failed to restart WhatsApp Web", error=e)
        raise HTTPException(status_code=500, detail=str(e))

@whatsapp_web_router.on_event("shutdown")
async def shutdown_whatsapp_web():
    """Cleanup WhatsApp Web on shutdown"""
    global processing_active
    processing_active = False
    
    try:
        from app.services.whatsapp_web_client import cleanup_whatsapp_client
        await cleanup_whatsapp_client()
        logger.info("WhatsApp Web integration stopped")
    except Exception as e:
        logger.error("Error stopping WhatsApp Web integration", error=e)