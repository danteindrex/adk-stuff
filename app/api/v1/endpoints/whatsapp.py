from fastapi import APIRouter, Depends, HTTPException, Request, status, Header, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union, Literal
import hmac
import hashlib
import logging
import json
import time
import asyncio
from datetime import datetime

from app.services.whatsapp_client import WhatsAppClient, create_whatsapp_client
from app.core.config import settings
from app.core.logging_config import StructuredLogger

# Import AI client
from whatsapp_production_ai import get_production_ai_client, ProductionAIWhatsAppClient

# Initialize logger
logger = StructuredLogger(__name__)

# Message type definitions
MessageType = Literal[
    'text', 'image', 'document', 'audio', 'video', 'sticker',
    'location', 'contacts', 'interactive', 'button', 'order', 'system'
]

router = APIRouter()
logger = logging.getLogger(__name__)

class WhatsAppWebhook(BaseModel):
    """Model for WhatsApp webhook payload"""
    object: str
    entry: List[Dict[str, Any]]

class WhatsAppMessage(BaseModel):
    """Model for incoming WhatsApp message"""
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]

class WebhookEntry(BaseModel):
    """Model for webhook entry"""
    id: str
    changes: List[Dict[str, Any]]

class WebhookPayload(BaseModel):
    """Complete webhook payload model"""
    object: str
    entry: List[WebhookEntry]

class MessageContext(BaseModel):
    """Message context for processing"""
    from_number: str
    message_id: str
    timestamp: datetime
    message_type: MessageType
    raw_message: Dict[str, Any]
    session_id: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None

async def verify_webhook_signature(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="x-hub-signature-256")
) -> bool:
    """
    Verify the webhook signature from WhatsApp with enhanced security and logging
    """
    if not settings.WHATSAPP_WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured, skipping signature verification")
        return True
        
    if not x_hub_signature_256:
        logger.error("Missing X-Hub-Signature-256 header")
        return False
        
    try:
        # Store the request body for verification
        body = await request.body()
        
        # Create HMAC signature
        signature = hmac.new(
            key=settings.WHATSAPP_WEBHOOK_SECRET.encode('utf-8'),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Format expected signature
        expected_signature = f"sha256={signature}"
        
        # Secure comparison to prevent timing attacks
        is_valid = hmac.compare_digest(
            x_hub_signature_256.encode('utf-8'),
            expected_signature.encode('utf-8')
        )
        
        if not is_valid:
            logger.warning("Invalid webhook signature")
            
        return is_valid
        
    except Exception as e:
        logger.error(f"Signature verification error: {str(e)}", exc_info=True)
        return False

@router.get("/webhook")
async def verify_webhook(
    mode: str,
    token: str,
    challenge: str,
    request: Request
):
    """
    WhatsApp webhook verification endpoint
    
    This endpoint is called by WhatsApp during the webhook setup process
    to verify the webhook URL.
    """
    logger.info(f"Webhook verification request from {request.client.host if request.client else 'unknown'}")
    
    # Verify the verification token
    if not all([mode, token, challenge]):
        logger.error("Missing required parameters for webhook verification")
        raise HTTPException(status_code=400, detail="Missing parameters")
    
    if mode != "subscribe":
        logger.error(f"Invalid mode: {mode}")
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if token != settings.WHATSAPP_VERIFY_TOKEN:
        logger.error("Invalid verification token")
        raise HTTPException(status_code=403, detail="Invalid token")
    
    logger.info("Webhook verified successfully")
    return PlainTextResponse(challenge, media_type="text/plain")

@router.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    verified: bool = Depends(verify_webhook_signature)
):
    """
    Primary webhook endpoint for processing WhatsApp messages and events
    
    This is the main entry point for all WhatsApp interactions.
    It handles message processing asynchronously for better performance.
    """
    start_time = time.time()
    request_id = f"webhook-{int(start_time * 1000)}"
    
    logger.info(f"[{request_id}] New webhook request from {request.client.host if request.client else 'unknown'}")
    
    if not verified:
        logger.error(f"[{request_id}] Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        # Parse the request body
        try:
            body = await request.json()
            logger.debug(f"[{request_id}] Webhook payload: {json.dumps(body, indent=2, default=str)}")
        except json.JSONDecodeError:
            logger.error(f"[{request_id}] Invalid JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process the webhook asynchronously
        background_tasks.add_task(process_webhook, body, request_id)
        
        # Always return 200 OK to acknowledge receipt
        process_time = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] Webhook processed in {process_time:.2f}ms")
        
        return {"status": "accepted"}
        
    except Exception as e:
        logger.error(f"[{request_id}] Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )

async def process_webhook(webhook_data: dict, request_id: str):
    """
    Process incoming webhook payload asynchronously
    
    This function handles the actual processing of webhook data
    in the background to ensure fast response times.
    """
    try:
        logger.info(f"[{request_id}] Processing webhook payload")
        
        # Parse the webhook data
        try:
            webhook_payload = WhatsAppWebhook(**webhook_data)
        except Exception as e:
            logger.error(f"[{request_id}] Invalid webhook payload: {str(e)}")
            return
        
        # Process each entry in the webhook
        for entry in webhook_payload.entry:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Handle messages
                if "messages" in value:
                    await process_messages(value, request_id)
                # Handle message status updates
                elif "statuses" in value:
                    await process_status_updates(value, request_id)
                else:
                    logger.warning(f"[{request_id}] Unhandled webhook change type")
        
        logger.info(f"[{request_id}] Webhook processing completed successfully")
        
    except Exception as e:
        logger.error(f"[{request_id}] Error in background webhook processing: {str(e)}", exc_info=True)

async def process_messages(webhook_data: dict, request_id: str):
    """Process incoming messages from the webhook"""
    try:
        message_data = WhatsAppMessage(**webhook_data)
        
        for message in message_data.messages:
            try:
                # Extract basic message info
                from_number = message.get("from")
                message_id = message.get("id")
                timestamp = datetime.fromtimestamp(int(message.get("timestamp")))
                message_type = message.get("type")
                
                if not all([from_number, message_id, message_type]):
                    logger.warning(f"[{request_id}] Missing required message fields")
                    continue
                
                # Create message context
                context = MessageContext(
                    from_number=from_number,
                    message_id=message_id,
                    timestamp=timestamp,
                    message_type=message_type,
                    raw_message=message
                )
                
                logger.info(
                    f"[{request_id}] Processing {message_type} message "
                    f"from {from_number} (ID: {message_id})"
                )
                
                # Route to appropriate handler based on message type
                handler = MESSAGE_HANDLERS.get(message_type, handle_unknown_message)
                await handler(context, request_id)
                
            except Exception as e:
                logger.error(f"[{request_id}] Error processing message: {str(e)}", exc_info=True)
                
    except Exception as e:
        logger.error(f"[{request_id}] Error in message processing: {str(e)}", exc_info=True)
        raise

async def handle_text_message(context: MessageContext, request_id: str):
    """Handle incoming text messages with AI processing"""
    try:
        text = context.raw_message.get("text", {}).get("body", "")
        from_number = context.from_number
        
        logger.info(f"[{request_id}] Processing text from {from_number}: {text[:100]}...")
        
        # Get the AI client
        try:
            ai_client = await get_production_ai_client()
            logger.info(f"[{request_id}] AI client initialized successfully")
            
            # Process the message with AI
            result = await ai_client.handle_incoming_message(from_number, text)
            
            if result.get("status") != "success":
                error_msg = result.get("error", "Unknown error")
                logger.error(f"[{request_id}] AI processing failed: {error_msg}")
                
                # Send error message to user
                error_response = "I'm sorry, I encountered an error processing your message. Please try again later."
                async with create_whatsapp_client() as client:
                    await client.send_text_message(
                        to=from_number,
                        text=error_response
                    )
            
            logger.info(f"[{request_id}] AI processing completed successfully")
            
        except Exception as ai_error:
            logger.error(f"[{request_id}] Error in AI processing: {str(ai_error)}", exc_info=True)
            
            # Fallback response if AI fails
            fallback_response = "Thank you for your message. Our system is currently busy. Please try again in a moment."
            async with create_whatsapp_client() as client:
                await client.send_text_message(
                    to=from_number,
                    text=fallback_response
                )
            
    except Exception as e:
        logger.error(f"[{request_id}] Error in text message handler: {str(e)}", exc_info=True)
        
        # Final fallback in case of complete failure
        try:
            async with create_whatsapp_client() as client:
                await client.send_text_message(
                    to=from_number,
                    text="We're experiencing technical difficulties. Please try again later."
                )
        except Exception as send_error:
            logger.critical(f"[{request_id}] Failed to send error message: {str(send_error)}")
        
        raise

# Handler registry with AI integration
MESSAGE_HANDLERS = {
    "text": handle_text_message,  # Handled by AI
    "image": lambda c, r: handle_ai_media(c, r, "image"),
    "document": lambda c, r: handle_ai_media(c, r, "document"),
    "audio": lambda c, r: handle_ai_media(c, r, "audio"),
    "video": lambda c, r: handle_ai_media(c, r, "video"),
    "sticker": lambda c, r: handle_ai_media(c, r, "sticker"),
    "location": handle_ai_location,
    "button": handle_ai_interactive,
    "interactive": handle_ai_interactive
}

async def handle_ai_media(context: MessageContext, request_id: str, media_type: str):
    """Handle media messages with AI processing"""
    try:
        media_id = context.raw_message.get(media_type, {}).get("id")
        caption = context.raw_message.get(media_type, {}).get("caption", "")
        
        logger.info(
            f"[{request_id}] Processing {media_type} message from {context.from_number} "
            f"(ID: {media_id}, Caption: {caption[:50]}...)"
        )
        
        # Get the AI client
        ai_client = await get_production_ai_client()
        
        # Create a prompt that includes the media context
        prompt = f"User sent a {media_type}. "
        if caption:
            prompt += f"Caption: {caption}"
        else:
            prompt += "No caption provided."
        
        # Process with AI
        result = await ai_client.handle_incoming_message(context.from_number, prompt)
        
        if result.get("status") != "success":
            logger.error(f"[{request_id}] Failed to process {media_type} with AI")
            await _send_fallback_response(context.from_number, "I couldn't process that media. Please try sending it again or describe what you need help with.")
            
    except Exception as e:
        logger.error(f"[{request_id}] Error processing {media_type} message: {str(e)}", exc_info=True)
        await _send_fallback_response(context.from_number, "I had trouble processing that media. Could you describe what you need help with?")

async def handle_ai_location(context: MessageContext, request_id: str):
    """Handle location messages with AI processing"""
    try:
        location = context.raw_message.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        name = location.get("name", "")
        address = location.get("address", "")
        
        logger.info(
            f"[{request_id}] Processing location from {context.from_number}: "
            f"{latitude},{longitude} - {name or 'No name'} - {address or 'No address'}"
        )
        
        # Get the AI client
        ai_client = await get_production_ai_client()
        
        # Create a prompt that includes the location context
        prompt = f"User shared location - "
        if name:
            prompt += f"Place: {name}. "
        if address:
            prompt += f"Address: {address}. "
        prompt += f"Coordinates: {latitude},{longitude}. "
        prompt += "What government services are available near this location?"
        
        # Process with AI
        result = await ai_client.handle_incoming_message(context.from_number, prompt)
        
        if result.get("status") != "success":
            logger.error(f"[{request_id}] Failed to process location with AI")
            await _send_fallback_response(
                context.from_number,
                "Thanks for sharing your location. How can I assist you with government services in this area?"
            )
            
    except Exception as e:
        logger.error(f"[{request_id}] Error processing location message: {str(e)}", exc_info=True)
        await _send_fallback_response(
            context.from_number,
            "I received your location but had trouble processing it. How can I help you with government services?"
        )

async def handle_ai_interactive(context: MessageContext, request_id: str):
    """Handle interactive messages (buttons, lists, etc.) with AI processing"""
    try:
        interactive = context.raw_message.get("interactive", {})
        interactive_type = interactive.get("type")
        
        logger.info(
            f"[{request_id}] Processing {interactive_type} interactive message from {context.from_number}"
        )
        
        # Get the AI client
        ai_client = await get_production_ai_client()
        
        # Create a prompt based on the interactive type
        if interactive_type == "button_reply":
            button_text = interactive.get("button_reply", {}).get("title", "")
            prompt = f"User clicked button: {button_text}"
        elif interactive_type == "list_reply":
            list_item = interactive.get("list_reply", {})
            list_title = list_item.get("title", "")
            list_id = list_item.get("id", "")
            prompt = f"User selected from list - Title: {list_title}, ID: {list_id}"
        else:
            prompt = f"User interacted with {interactive_type}: {interactive}"
        
        # Process with AI
        result = await ai_client.handle_incoming_message(context.from_number, prompt)
        
        if result.get("status") != "success":
            logger.error(f"[{request_id}] Failed to process interactive message with AI")
            await _send_fallback_response(
                context.from_number,
                "I had trouble processing that selection. Please try again or type your request."
            )
            
    except Exception as e:
        logger.error(f"[{request_id}] Error processing interactive message: {str(e)}", exc_info=True)
        await _send_fallback_response(
            context.from_number,
            "I encountered an error processing your selection. Please try again or type your request."
        )

async def handle_unknown_message(context: MessageContext, request_id: str):
    """Handle unknown message types"""
    logger.warning(
        f"[{request_id}] Received unsupported message type: "
        f"{context.message_type} from {context.from_number}"
    )
    
    # Try to process with AI anyway, in case it can handle it
    try:
        ai_client = await get_production_ai_client()
        await ai_client.handle_incoming_message(
            context.from_number,
            f"[System: Received unsupported message type: {context.message_type}]"
        )
    except Exception as e:
        logger.error(f"[{request_id}] Error processing unknown message type: {str(e)}")
        await _send_fallback_response(
            context.from_number,
            "I'm not able to process this type of message. Please try text or a supported media type."
        )

async def _send_fallback_response(to_number: str, message: str):
    """Helper to send fallback responses with error handling"""
    try:
        async with create_whatsapp_client() as client:
            await client.send_text_message(
                to=to_number,
                text=message
            )
    except Exception as e:
        logger.error(f"Failed to send fallback response to {to_number}: {str(e)}")

async def process_status_updates(webhook_data: dict, request_id: str):
    """Process message status updates"""
    try:
        for status_update in webhook_data.get("statuses", []):
            message_id = status_update.get("id")
            status = status_update.get("status", {})
            timestamp = status_update.get("timestamp")
            recipient_id = status_update.get("recipient_id")
            
            logger.info(
                f"[{request_id}] Message {message_id} status update: "
                f"{status} (recipient: {recipient_id}, ts: {timestamp})"
            )
            
            # Here you would update your database with the message status
            # For example:
            # await update_message_status(message_id, status, timestamp)
            
    except Exception as e:
        logger.error(f"[{request_id}] Error processing status update: {str(e)}", exc_info=True)
        raise

async def process_media_message(from_number: str, message: dict, media_type: str):
    """Process a media message (image, document, audio, video, sticker)"""
    try:
        logger.info(f"Processing {media_type} message from {from_number}")
        
        # Get the media ID and other metadata
        media_id = message.get(media_type, {}).get("id")
        caption = message.get(media_type, {}).get("caption")
        
        # Here you would typically process the media
        # For now, we'll just send an acknowledgment
        async with create_whatsapp_client() as client:
            await client.send_text_message(
                to=from_number,
                text=f"Received your {media_type} message. Thanks!"
            )
            
    except Exception as e:
        logger.exception(f"Error processing {media_type} message: {e}")

async def process_location_message(from_number: str, location: dict):
    """Process a location message"""
    try:
        logger.info(f"Processing location message from {from_number}")
        
        # Get the location coordinates
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        
        # Here you would typically process the location
        # For now, we'll just send an acknowledgment
        async with create_whatsapp_client() as client:
            await client.send_text_message(
                to=from_number,
                text=f"Received your location: {latitude}, {longitude}"
            )
            
    except Exception as e:
        logger.exception(f"Error processing location message: {e}")

async def process_button_message(from_number: str, message: dict):
    """Process a button message"""
    try:
        logger.info(f"Processing button message from {from_number}")
        
        # Get the button payload
        button_id = message.get("button", {}).get("payload")
        button_text = message.get("button", {}).get("text")
        
        # Here you would typically handle the button press
        # For now, we'll just send an acknowledgment
        async with create_whatsapp_client() as client:
            await client.send_text_message(
                to=from_number,
                text=f"You pressed button: {button_text} (ID: {button_id})"
            )
            
    except Exception as e:
        logger.exception(f"Error processing button message: {e}")

async def process_interactive_message(from_number: str, interactive: dict):
    """Process an interactive message (e.g., list, button reply)"""
    try:
        logger.info(f"Processing interactive message from {from_number}")
        
        # Handle different types of interactive messages
        if "button_reply" in interactive:
            # Button reply
            button_id = interactive["button_reply"]["id"]
            button_title = interactive["button_reply"]["title"]
            
            response_text = f"You selected: {button_title} (ID: {button_id})"
            
        elif "list_reply" in interactive:
            # List reply
            list_id = interactive["list_reply"]["id"]
            list_title = interactive["list_reply"]["title"]
            
            response_text = f"You selected from list: {list_title} (ID: {list_id})"
            
        else:
            response_text = "Thanks for your response!"
        
        # Send the response
        async with create_whatsapp_client() as client:
            await client.send_text_message(
                to=from_number,
                text=response_text
            )
            
    except Exception as e:
        logger.exception(f"Error processing interactive message: {e}")

async def process_status_update(webhook_data: dict):
    """Process a message status update"""
    try:
        for status_update in webhook_data.get("statuses", []):
            message_id = status_update.get("id")
            recipient_id = status_update.get("recipient_id")
            status_value = status_update.get("status")
            timestamp = status_update.get("timestamp")
            
            # Log the status update
            logger.info(
                f"Message {message_id} to {recipient_id} is now {status_value} "
                f"(Timestamp: {timestamp})"
            )
            
            # Here you would typically update your database with the new status
            # For example:
            # await update_message_status(message_id, status_value, timestamp)
            
    except Exception as e:
        logger.exception(f"Error processing status update: {e}")
