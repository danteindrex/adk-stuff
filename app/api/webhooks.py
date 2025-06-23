"""WhatsApp Business API webhook handlers"""

import json
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Query, Form, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging_config import StructuredLogger
from app.services.whatsapp_client import create_whatsapp_client
from app.models.whatsapp_models import WhatsAppMessage

logger = StructuredLogger(__name__)

# Create router
whatsapp_router = APIRouter()

# Global WhatsApp client
whatsapp_client = None

@whatsapp_router.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode", default=None),
    token: str = Query(alias="hub.verify_token", default=None),
    challenge: str = Query(alias="hub.challenge", default=None)
):
    """
    Verify webhook endpoint for WhatsApp Business API
    """
    logger.info("Webhook verification request received")
    
    # Handle WhatsApp Business API verification
    if mode and token and challenge:
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verification successful")
            return PlainTextResponse(challenge)
        else:
            logger.warning(f"Invalid verification token: {token}")
            raise HTTPException(status_code=403, detail="Invalid verification token")
    
    # Return error if required parameters are missing
    raise HTTPException(status_code=400, detail="Missing verification parameters")

@whatsapp_router.post("/webhook")
async def handle_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming WhatsApp Business API messages
    This endpoint receives all WhatsApp Business API events
    """
    try:
        # Get raw body for signature verification
        raw_body = await request.body()
        
        # Verify WhatsApp webhook signature
        if not await verify_whatsapp_signature(request, raw_body):
            logger.warning("Invalid WhatsApp signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON payload
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Process WhatsApp webhook payload
        if "entry" in payload:
            for entry in payload["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            value = change.get("value", {})
                            
                            # Process incoming messages
                            if "messages" in value:
                                for message in value["messages"]:
                                    background_tasks.add_task(
                                        process_whatsapp_message, 
                                        message, 
                                        value.get("metadata", {})
                                    )
                            
                            # Process message status updates
                            if "statuses" in value:
                                for status in value["statuses"]:
                                    background_tasks.add_task(
                                        process_message_status, 
                                        status
                                    )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def verify_whatsapp_signature(request: Request, raw_body: bytes) -> bool:
    """
    Verify WhatsApp webhook signature
    """
    if not settings.WHATSAPP_WEBHOOK_SECRET:
        logger.warning("WHATSAPP_WEBHOOK_SECRET not configured, skipping signature verification")
        return True
    
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        logger.warning("Missing X-Hub-Signature-256 header")
        return False
    
    # Remove 'sha256=' prefix
    if signature.startswith("sha256="):
        signature = signature[7:]
    
    # Calculate expected signature
    expected_signature = hmac.new(
        settings.WHATSAPP_WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

async def process_whatsapp_message(message: Dict[str, Any], metadata: Dict[str, Any]):
    """
    Process an incoming WhatsApp Business API message
    """
    try:
        message_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        message_type = message.get("type")
        
        # Extract message text based on type
        message_text = ""
        if message_type == "text":
            message_text = message.get("text", {}).get("body", "")
        elif message_type == "button":
            message_text = message.get("button", {}).get("text", "")
        elif message_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                message_text = interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                message_text = interactive.get("list_reply", {}).get("title", "")
        else:
            logger.info(f"Received unsupported message type: {message_type}")
            return
        
        if not message_text:
            logger.warning(f"Empty message text for message {message_id}")
            return
        
        logger.info(f"Received WhatsApp message: {message_id} from {from_number}")
        
        # Create a WhatsApp message object
        whatsapp_message = WhatsAppMessage(
            message_id=message_id,
            from_number=from_number,
            to_number=metadata.get("phone_number_id", ""),
            text=message_text,
            timestamp=timestamp,
            type=message_type
        )
        
        # Get the agent orchestrator from main.py
        from main import agent_orchestrator
        
        # Process the message with the agent system
        await agent_orchestrator.process_message(whatsapp_message)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")

async def process_message_status(status: Dict[str, Any]):
    """
    Process WhatsApp message status updates
    """
    try:
        message_id = status.get("id")
        recipient_id = status.get("recipient_id")
        status_type = status.get("status")
        timestamp = status.get("timestamp")
        
        logger.info(f"Message {message_id} status: {status_type} for {recipient_id}")
        
        # Handle different status types
        if status_type == "delivered":
            logger.debug(f"Message {message_id} delivered to {recipient_id}")
        elif status_type == "read":
            logger.debug(f"Message {message_id} read by {recipient_id}")
        elif status_type == "failed":
            error = status.get("errors", [{}])[0]
            error_code = error.get("code")
            error_title = error.get("title")
            logger.error(f"Message {message_id} failed: {error_code} - {error_title}")
        
    except Exception as e:
        logger.error(f"Error processing message status: {e}")

async def send_whatsapp_message(to_number: str, message: str):
    """Send a WhatsApp message using WhatsApp Business API"""
    try:
        async with create_whatsapp_client() as client:
            result = await client.send_text_message(to_number, message)
            return result
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return {"error": str(e)}

async def send_error_message(to_number: str, error_message: str):
    """Send an error message via WhatsApp Business API"""
    try:
        async with create_whatsapp_client() as client:
            result = await client.send_text_message(to_number, f"❌ {error_message}")
            return result
    except Exception as e:
        logger.error(f"Error sending error message: {e}")
        return {"error": str(e)}

async def send_template_message(to_number: str, template_name: str, language_code: str = "en_US", components: list = None):
    """Send a template message via WhatsApp Business API"""
    try:
        async with create_whatsapp_client() as client:
            result = await client.send_template_message(
                to=to_number,
                template_name=template_name,
                language_code=language_code,
                components=components
            )
            return result
    except Exception as e:
        logger.error(f"Error sending template message: {e}")
        return {"error": str(e)}

async def send_interactive_message(to_number: str, interactive_data: Dict[str, Any]):
    """Send an interactive message (buttons, lists) via WhatsApp Business API"""
    try:
        from app.services.whatsapp_client import WhatsAppMessageRequest
        
        message = WhatsAppMessageRequest(
            to=to_number,
            type="interactive",
            interactive=interactive_data
        )
        
        async with create_whatsapp_client() as client:
            result = await client.send_message(message)
            return result
    except Exception as e:
        logger.error(f"Error sending interactive message: {e}")
        return {"error": str(e)}