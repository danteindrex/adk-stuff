"""Twilio WhatsApp webhook handlers"""

import json
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Query, Form, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging_config import StructuredLogger
from app.services.twilio_client import TwilioClient
from app.models.whatsapp_models import WhatsAppMessage

logger = StructuredLogger(__name__)

# Create router
whatsapp_router = APIRouter()

# Global Twilio client (will be initialized in main.py)
twilio_client = None

@whatsapp_router.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode", default=None),
    token: str = Query(alias="hub.verify_token", default=None),
    challenge: str = Query(alias="hub.challenge", default=None)
):
    """
    Verify webhook endpoint - supports both Meta and Twilio verification
    This maintains backward compatibility with Meta WhatsApp verification
    """
    logger.info("Webhook verification request received")
    
    # Handle Meta WhatsApp verification (legacy support)
    if mode and token and challenge:
        if mode == "subscribe" and token == settings.TWILIO_WEBHOOK_VERIFY_TOKEN:
            logger.info("Meta webhook verification successful")
            return PlainTextResponse(challenge)
    
    # For Twilio, just return a 200 OK response
    return {"status": "ok"}

@whatsapp_router.post("/webhook")
async def handle_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    # Twilio form fields
    message_sid: str = Form(None),
    body: str = Form(None),
    from_: str = Form(None, alias="From"),
    to: str = Form(None, alias="To"),
):
    """
    Handle incoming Twilio WhatsApp messages
    This endpoint receives all Twilio WhatsApp events
    """
    try:
        # Get raw body for potential signature verification
        raw_body = await request.body()
        
        # Verify Twilio webhook signature (optional but recommended)
        # if not await verify_twilio_signature(request, raw_body):
        #     logger.warning("Invalid Twilio signature")
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process form data for Twilio
        if from_ and body:
            logger.info(f"Received Twilio WhatsApp message: {message_sid}")
            
            # Process webhook in background to return 200 quickly
            background_tasks.add_task(process_twilio_message, message_sid, from_, to, body)
            
            return {"status": "received"}
        else:
            # Handle other Twilio webhook types (status updates, etc.)
            form_data = await request.form()
            logger.debug(f"Received other Twilio webhook: {dict(form_data)}")
            return {"status": "received"}
            
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_twilio_message(message_sid: str, from_number: str, to_number: str, message_text: str):
    """
    Process an incoming Twilio WhatsApp message
    """
    try:
        # Extract the actual phone number from Twilio's WhatsApp format
        # Twilio format: "whatsapp:+1234567890"
        user_phone = from_number.replace("whatsapp:", "")
        
        # Create a WhatsApp message object (using existing model for compatibility)
        whatsapp_message = WhatsAppMessage(
            message_id=message_sid,
            from_number=user_phone,
            to_number=to_number.replace("whatsapp:", ""),
            text=message_text,
            timestamp=None,  # Twilio doesn't provide this directly
            type="text"
        )
        
        # Get the agent orchestrator from main.py
        from main import agent_orchestrator
        
        # Process the message with the agent system
        await agent_orchestrator.process_message(whatsapp_message)
        
    except Exception as e:
        logger.error(f"Error processing Twilio message: {e}")

async def send_whatsapp_message(to_number: str, message: str):
    """Send a WhatsApp message using Twilio"""
    global twilio_client
    if not twilio_client:
        twilio_client = TwilioClient()
    
    return await twilio_client.send_text_message(to_number, message)

async def send_error_message(to_number: str, error_message: str):
    """Send an error message via WhatsApp using Twilio"""
    global twilio_client
    if not twilio_client:
        twilio_client = TwilioClient()
    
    return await twilio_client.send_text_message(to_number, f"❌ {error_message}")