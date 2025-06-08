"""
WhatsApp Business API webhook handlers
"""

import json
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging_config import StructuredLogger
from app.services.whatsapp_client import WhatsAppClient
from app.models.whatsapp_models import WhatsAppWebhook, WhatsAppMessage

logger = StructuredLogger(__name__)

# Create router
whatsapp_router = APIRouter()

# Global WhatsApp client (will be initialized in main.py)
whatsapp_client = None

class WebhookVerification(BaseModel):
    """Model for webhook verification"""
    mode: str = Field(..., alias="hub.mode")
    token: str = Field(..., alias="hub.verify_token")
    challenge: str = Field(..., alias="hub.challenge")

@whatsapp_router.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Verify WhatsApp webhook endpoint
    This is called by WhatsApp to verify the webhook URL
    """
    logger.info("Webhook verification request received", mode=mode, token=token[:10] + "...")
    
    if mode == "subscribe" and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verification successful")
        return PlainTextResponse(challenge)
    else:
        logger.warning("Webhook verification failed", mode=mode, token_match=token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN)
        raise HTTPException(status_code=403, detail="Verification failed")

@whatsapp_router.post("/webhook")
async def handle_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming WhatsApp messages
    This endpoint receives all WhatsApp events (messages, status updates, etc.)
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature (optional but recommended for production)
        if not await verify_webhook_signature(request, body):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = json.loads(body.decode())
        logger.debug("Webhook data received", data_keys=list(webhook_data.keys()))
        
        # Process webhook in background to return 200 quickly
        background_tasks.add_task(process_webhook_data, webhook_data)
        
        return {"status": "received"}
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in webhook", error=e)
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error("Webhook processing error", error=e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def verify_webhook_signature(request: Request, body: bytes) -> bool:
    """
    Verify webhook signature from WhatsApp
    This ensures the webhook is actually from WhatsApp
    """
    try:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature:
            return True  # Skip verification if no signature (for development)
        
        # Remove 'sha256=' prefix
        signature = signature.replace("sha256=", "")
        
        # Calculate expected signature
        expected_signature = hmac.new(
            settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error("Signature verification error", error=e)
        return False

async def process_webhook_data(webhook_data: Dict[str, Any]):
    """
    Process WhatsApp webhook data
    This function handles the actual message processing
    """
    try:
        # Parse webhook structure
        if "entry" not in webhook_data:
            logger.debug("No entry in webhook data")
            return
        
        for entry in webhook_data["entry"]:
            if "changes" not in entry:
                continue
                
            for change in entry["changes"]:
                if change.get("field") != "messages":
                    continue
                
                value = change.get("value", {})
                
                # Process incoming messages
                if "messages" in value:
                    for message_data in value["messages"]:
                        await process_incoming_message(message_data, value.get("metadata", {}))
                
                # Process message status updates
                if "statuses" in value:
                    for status_data in value["statuses"]:
                        await process_message_status(status_data)
                        
    except Exception as e:
        logger.error("Error processing webhook data", error=e, webhook_data=webhook_data)

async def process_incoming_message(message_data: Dict[str, Any], metadata: Dict[str, Any]):
    """
    Process an incoming WhatsApp message
    """
    try:
        # Extract message details
        from_number = message_data.get("from")
        message_id = message_data.get("id")
        timestamp = message_data.get("timestamp")
        message_type = message_data.get("type")
        
        logger.info("Processing incoming message", 
                   from_number=from_number, 
                   message_id=message_id, 
                   message_type=message_type)
        
        # Extract message content based on type
        message_text = ""
        if message_type == "text":
            message_text = message_data.get("text", {}).get("body", "")
        elif message_type == "button":
            message_text = message_data.get("button", {}).get("text", "")
        elif message_type == "interactive":
            interactive = message_data.get("interactive", {})
            if interactive.get("type") == "button_reply":
                message_text = interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                message_text = interactive.get("list_reply", {}).get("title", "")
        else:
            logger.info("Unsupported message type", message_type=message_type)
            await send_unsupported_message_response(from_number)
            return
        
        # Create message object
        whatsapp_message = WhatsAppMessage(
            id=message_id,
            from_number=from_number,
            timestamp=timestamp,
            type=message_type,
            text=message_text,
            metadata=metadata
        )
        
        # Get agent orchestrator from main app
        from main import agent_orchestrator
        if agent_orchestrator:
            await agent_orchestrator.process_message(whatsapp_message)
        else:
            logger.error("Agent orchestrator not available")
            await send_error_response(from_number, "System temporarily unavailable")
            
    except Exception as e:
        logger.error("Error processing incoming message", error=e, message_data=message_data)
        if message_data.get("from"):
            await send_error_response(message_data["from"], "Sorry, I encountered an error processing your message.")

async def process_message_status(status_data: Dict[str, Any]):
    """
    Process WhatsApp message status updates (delivered, read, etc.)
    """
    try:
        message_id = status_data.get("id")
        status = status_data.get("status")
        timestamp = status_data.get("timestamp")
        
        logger.debug("Message status update", 
                    message_id=message_id, 
                    status=status, 
                    timestamp=timestamp)
        
        # Log status for monitoring
        from main import monitoring_service
        if monitoring_service:
            await monitoring_service.log_message_status(message_id, status, timestamp)
            
    except Exception as e:
        logger.error("Error processing message status", error=e, status_data=status_data)

async def send_unsupported_message_response(to_number: str):
    """Send response for unsupported message types"""
    try:
        global whatsapp_client
        if not whatsapp_client:
            whatsapp_client = WhatsAppClient()
        
        message = "I can only process text messages at the moment. Please send your request as text."
        await whatsapp_client.send_text_message(to_number, message)
        
    except Exception as e:
        logger.error("Error sending unsupported message response", error=e, to_number=to_number)

async def send_error_response(to_number: str, error_message: str):
    """Send error response to user"""
    try:
        global whatsapp_client
        if not whatsapp_client:
            whatsapp_client = WhatsAppClient()
        
        await whatsapp_client.send_text_message(to_number, f"❌ {error_message}")
        
    except Exception as e:
        logger.error("Error sending error response", error=e, to_number=to_number)

# Health check for webhook
@whatsapp_router.get("/webhook/health")
async def webhook_health():
    """Health check for webhook endpoint"""
    return {
        "status": "healthy",
        "webhook_url": "/whatsapp/webhook",
        "verification_url": "/whatsapp/webhook"
    }