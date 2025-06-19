"""
Uganda E-Gov WhatsApp Helpdesk
Multi-Agent AI System for Government Service Access
Production-Optimized Version with Modular Architecture and Enhanced Browser Automation
"""

import os
import asyncio
import logging
import time
import json
"""
Uganda E-Gov WhatsApp Helpdesk
Multi-Agent AI System for Government Service Access
Production-Optimized Version with Modular Architecture and Enhanced Browser Automation

Key Components:
1. FastAPI Web Framework
2. Twilio Integration for WhatsApp
3. OpenTelemetry for Monitoring
4. ADK Agent System with Browser Automation
5. Session Management
6. Rate Limiting
7. Caching Service
8. Monitoring Service

Architecture:
- API Routes:
  - WhatsApp Webhooks (/webhooks)
  - Admin Interface (/admin)
- Services:
  - Session Management
  - Cache Service
  - Monitoring Service
  - Twilio Client
- Agent System:
  - Root Agent Creation
  - MCP Connection Management
  - Browser Automation
  
Dependencies:
- FastAPI
- Twilio
- OpenTelemetry
- Google ADK
- SlowAPI
- Uvicorn
- Python-dotenv

Environment Configuration:
- Uses .env for configuration
- Structured logging setup
- CORS and GZip middleware
- Rate limiting implementation
"""
from app.services import twilio_client
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from dotenv import load_dotenv

# OpenTelemetry instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Import our custom modules
from app.agents.mcp_servers import cleanup_mcp_connections
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.webhooks import whatsapp_router
from app.api.admin import admin_router
# ADK agent system - using modular architecture with enhanced browser automation
from app.agents.agent import create_root_agent, cleanup_mcp_connections

from app.services.simple_session_manager import session_manager
from app.services.server_cache_service import cache_service
from app.services.simple_monitoring import MonitoringService

# ADK imports for proper agent execution
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event
from google.genai.types import Content, Part
from google.genai import types 
# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
"""
WhatsApp Clone Server Integration
Serves the WhatsApp clone interface and handles web-based messaging
"""

import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn



# Import Supabase client
from app.database.supabase_client import get_supabase_client, User, Message, ChatSession

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app for WhatsApp clone
clone_app = FastAPI(
    title="WhatsApp Clone - Uganda E-Gov Assistant",
    description="Web-based WhatsApp clone with AI integration",
    version="1.0.0"
)

# Add CORS middleware
clone_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
clone_app.mount("/static", StaticFiles(directory="whatsapp_clone"), name="static")

@clone_app.get("/", response_class=HTMLResponse)
async def serve_whatsapp_clone():
    """Serve the main WhatsApp clone interface"""
    try:
        with open("whatsapp_clone/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Replace placeholder with actual Google Client ID if available
        google_client_id = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
        html_content = html_content.replace("YOUR_GOOGLE_CLIENT_ID", google_client_id)
        
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="WhatsApp clone files not found")

@clone_app.get("/styles.css")
async def serve_css():
    """Serve CSS file"""
    return FileResponse("whatsapp_clone/styles.css", media_type="text/css")

@clone_app.get("/script.js")
async def serve_js():
    """Serve JavaScript file"""
    return FileResponse("whatsapp_clone/script.js", media_type="application/javascript")

@clone_app.post("/whatsapp/webhook")
async def web_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle messages from the web WhatsApp clone with Supabase storage"""
    start_time = datetime.now()
    processing_time_ms = None
    
    try:
        # Parse request body
        body = await request.json()
        
        user_text = body.get("Body", "")
        user_id = body.get("From", "web_user")
        session_id = body.get("session_id")
        source = body.get("source", "web_clone")
        user_data = body.get("user_data", {})
        
        logger.info(f"Web WhatsApp message from {user_id}: {user_text[:100]}")
        
        # Get Supabase client
        db = get_supabase_client()
        
        # Create or update user if user_data is provided
        if user_data and user_data.get("email"):
            try:
                logger.info(f"Attempting to create/update user with data: {user_data}")
                user = await db.create_or_update_user(user_data)
                actual_user_id = user.id
                logger.info(f"Successfully created/updated user: {user.email} with ID: {actual_user_id}")
            except Exception as user_error:
                logger.error(f"Failed to create/update user: {str(user_error)}")
                logger.error(f"User data that failed: {user_data}")
                # Fall back to using the provided user_id
                actual_user_id = user_id
                logger.info(f"Falling back to user_id: {actual_user_id}")
        else:
            # For demo users or users without full data
            actual_user_id = user_id
            logger.info(f"No user_data provided, using user_id: {actual_user_id}")
        
        # Get or create session
        if not session_id:
            # Create new session
            session = await db.create_chat_session(actual_user_id, "New Chat")
            session_id = session.id
        
        # Save user message to database
        user_message = await db.save_message(
            user_id=actual_user_id,
            session_id=session_id,
            content=user_text,
            message_type="user",
            metadata={
                "source": source,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Generate AI response using your existing system
        ai_start_time = datetime.now()
        response_text = await generate_simple_response(user_text, f"web:{user_id}")
        processing_time_ms = int((datetime.now() - ai_start_time).total_seconds() * 1000)
        
        # Save AI response to database
        ai_message = await db.save_message(
            user_id=actual_user_id,
            session_id=session_id,
            content=response_text,
            message_type="ai",
            processing_time_ms=processing_time_ms,
            ai_model="uganda_egov_assistant",
            metadata={
                "source": source,
                "response_to": user_message.id
            }
        )
        
        # Log the interaction
        if monitoring_service:
            await monitoring_service.log_conversation_event({
                "event": "web_whatsapp_message",
                "user_id": actual_user_id,
                "session_id": session_id,
                "source": source,
                "input_length": len(user_text),
                "output_length": len(response_text),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "message_id": ai_message.id
            })
        
        return JSONResponse({
            "reply": response_text,
            "status": "success",
            "source": "web_clone",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "message_id": ai_message.id,
            "processing_time_ms": processing_time_ms
        })
        
    except Exception as e:
        logger.error(f"Web WhatsApp webhook error: {e}")
        
        if monitoring_service:
            await monitoring_service.log_error_event("web_whatsapp_error", str(e), {
                "source": "web_clone",
                "user_id": user_id if 'user_id' in locals() else None,
                "processing_time_ms": processing_time_ms
            })
        
        # Return fallback response
        return JSONResponse({
            "reply": "Hello! I'm the Uganda E-Gov assistant. How can I help you with government services today?",
            "status": "error_fallback",
            "error": str(e),
            "session_id": session_id if 'session_id' in locals() else None
        })

@clone_app.post("/api/twilio/send")
async def send_via_twilio(request: Request):
    """Send message via Twilio WhatsApp API"""
    try:
        body = await request.json()
        
        to_number = body.get("to", "")
        message = body.get("message", "")
        from_web = body.get("from_web", False)
        
        if not to_number or not message:
            raise HTTPException(status_code=400, detail="Missing 'to' or 'message' parameter")
        
        # Ensure phone number format
        if not to_number.startswith("+"):
            to_number = f"+{to_number}"
        
        # Send via your existing Twilio client
        result = await twilio_client.send_text_message(to_number, message)
        
        if result.get("status") == "success":
            logger.info(f"Twilio message sent successfully to {to_number}")
            return JSONResponse({
                "status": "success",
                "message_id": result.get("message_id"),
                "to": to_number
            })
        else:
            logger.error(f"Twilio send failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to send message"))
            
    except Exception as e:
        logger.error(f"Twilio API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.get("/api/health")
async def health_check():
    """Health check for the web clone"""
    return {
        "status": "healthy",
        "service": "whatsapp_clone",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "google_oauth": bool(os.getenv("GOOGLE_CLIENT_ID")),
            "twilio_integration": bool(os.getenv("TWILIO_ACCOUNT_SID")),
            "ai_backend": True
        }
    }

@clone_app.get("/api/user/{user_id}/sessions")
async def get_user_sessions(user_id: str, limit: int = 50):
    """Get all chat sessions for a user"""
    try:
        db = get_supabase_client()
        sessions = await db.get_user_sessions(user_id, limit)
        
        return {
            "user_id": user_id,
            "sessions": [
                {
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "message_count": session.message_count,
                    "is_active": session.is_active
                }
                for session in sessions
            ],
            "total": len(sessions)
        }
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = 100, offset: int = 0):
    """Get all messages for a chat session"""
    try:
        db = get_supabase_client()
        messages = await db.get_session_messages(session_id, limit, offset)
        
        return {
            "session_id": session_id,
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "timestamp": msg.timestamp.isoformat(),
                    "processing_time_ms": msg.processing_time_ms,
                    "ai_model": msg.ai_model,
                    "intent_classification": msg.intent_classification,
                    "metadata": msg.metadata
                }
                for msg in messages
            ],
            "total": len(messages),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.get("/api/user/{user_id}/messages")
async def get_user_messages(user_id: str, limit: int = 1000, offset: int = 0):
    """Get all messages for a user across all sessions"""
    try:
        db = get_supabase_client()
        messages = await db.get_user_messages(user_id, limit, offset)
        
        return {
            "user_id": user_id,
            "messages": [
                {
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "timestamp": msg.timestamp.isoformat(),
                    "processing_time_ms": msg.processing_time_ms,
                    "ai_model": msg.ai_model,
                    "intent_classification": msg.intent_classification,
                    "metadata": msg.metadata
                }
                for msg in messages
            ],
            "total": len(messages),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting user messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.post("/api/user/create")
async def create_user(request: Request):
    """Create or update a user"""
    try:
        user_data = await request.json()
        logger.info(f"Received user creation request: {user_data}")
        
        required_fields = ["email", "name"]
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                logger.error(f"Missing or empty required field: {field}")
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate email format
        email = user_data["email"]
        if "@" not in email or "." not in email:
            logger.error(f"Invalid email format: {email}")
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        db = get_supabase_client()
        logger.info(f"Attempting to create/update user: {email}")
        
        user = await db.create_or_update_user(user_data)
        
        logger.info(f"Successfully created/updated user: {user.email}")
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "phone": user.phone,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_method": user.login_method
            },
            "status": "success"
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        logger.error(f"User data: {user_data if 'user_data' in locals() else 'N/A'}")
        
        # Return more specific error information
        error_detail = str(e)
        if "duplicate key" in error_detail.lower():
            error_detail = "User with this email already exists"
        elif "violates not-null constraint" in error_detail.lower():
            error_detail = "Missing required user information"
        elif "connection" in error_detail.lower():
            error_detail = "Database connection error"
        
        raise HTTPException(status_code=500, detail=f"Failed to create user: {error_detail}")

@clone_app.post("/api/session/create")
async def create_session(request: Request):
    """Create a new chat session"""
    try:
        data = await request.json()
        
        user_id = data.get("user_id")
        title = data.get("title", "New Chat")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        db = get_supabase_client()
        session = await db.create_chat_session(user_id, title)
        
        return {
            "session": {
                "id": session.id,
                "user_id": session.user_id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count,
                "is_active": session.is_active
            },
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.delete("/api/session/{session_id}")
async def delete_session(session_id: str, user_id: str):
    """Delete a chat session and all its messages"""
    try:
        db = get_supabase_client()
        success = await db.delete_session(session_id, user_id)
        
        if success:
            return {"status": "success", "message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.get("/api/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get user statistics"""
    try:
        db = get_supabase_client()
        stats = await db.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "stats": stats,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.get("/api/search/messages")
async def search_messages(user_id: str, query: str, limit: int = 50):
    """Search messages by content"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        db = get_supabase_client()
        messages = await db.search_messages(user_id, query, limit)
        
        return {
            "user_id": user_id,
            "query": query,
            "messages": [
                {
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in messages
            ],
            "total": len(messages)
        }
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@clone_app.get("/api/admin/stats")
async def get_system_stats():
    """Get system-wide statistics (admin only)"""
    try:
        db = get_supabase_client()
        stats = await db.get_system_stats()
        
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Service Worker for PWA
@clone_app.get("/sw.js")
async def service_worker():
    """Serve service worker for PWA functionality"""
    sw_content = """
// Service Worker for WhatsApp Clone PWA
const CACHE_NAME = 'whatsapp-clone-v1';
const urlsToCache = [
    '/',
    '/styles.css',
    '/script.js',
    'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});
"""
    return Response(sw_content, media_type="application/javascript")

# Manifest for PWA
@clone_app.get("/manifest.json")
async def app_manifest():
    """Serve PWA manifest"""
    manifest = {
        "name": "WhatsApp Clone - Uganda E-Gov Assistant",
        "short_name": "WhatsApp Clone",
        "description": "Web-based WhatsApp clone with AI government assistant",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#111b21",
        "theme_color": "#25d366",
        "icons": [
            {
                "src": "https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg",
                "sizes": "192x192",
                "type": "image/svg+xml"
            }
        ]
    }
    return JSONResponse(manifest)

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global services
monitoring_service = None
root_agent = None
adk_runner = None

import logging
from typing import Any, Dict, Optional
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService # Assuming this or similar is used
 # For message formatting

# Assume these are defined globally or passed in during initialization
# For demonstration, we'll mock them if they're not provided.
# You should ensure 'adk_runner', 'root_agent', and 'monitoring_service'
# are properly initialized where this function is called from.
adk_runner: Optional[Runner] = None
root_agent: Optional[Agent] = None
monitoring_service: Any = None # Replace 'Any' with the actual type if known

# Configure basic logging for better output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def generate_simple_response(user_text: str, user_id: str) -> str:
    """Generate response using the ADK agent system with intelligent fallback"""

    print(f"\n🔄 GENERATE_SIMPLE_RESPONSE CALLED:")
    print(f"   Input text: '{user_text}'")
    print(f"   User ID: '{user_id}'")

    # Normalize user ID (phone number)
    normalized_user_id = user_id.strip()
    if not normalized_user_id.startswith("256"):
        normalized_user_id = f"256{normalized_user_id.lstrip('0')}"

    print(f"   Normalized user ID: '{normalized_user_id}'")
    logger.info(f"Processing message from {normalized_user_id}: {user_text[:100]}")

    try:
        # --- ENSURE SESSION EXISTS FOR USER ---
        print(f"\n🔧 ENSURING SESSION EXISTS FOR USER:")
        try:
            # Check if user has an active session in our session manager
            existing_session = await session_manager.get_user_active_session(normalized_user_id)
            
            if not existing_session:
                print(f"   📝 No active session found - creating new session for user")
                # Create new session for the user
                session_id = await session_manager.create_session(
                    user_id=normalized_user_id,
                    initial_data={
                        "first_message": user_text,
                        "created_via": "whatsapp_webhook",
                        "user_phone": normalized_user_id
                    }
                )
                print(f"   ✅ Created new session: {session_id}")
                
                # Log session creation
                if monitoring_service:
                    await monitoring_service.log_conversation_event({
                        "event": "new_session_created",
                        "user_id": normalized_user_id,
                        "session_id": session_id,
                        "trigger": "new_user_message"
                    })
            else:
                print(f"   ✅ Found existing active session: {existing_session['session_id']}")
                # Update session activity
                await session_manager.add_message(
                    existing_session['session_id'], 
                    "user", 
                    user_text,
                    {"timestamp": datetime.now().isoformat()}
                )
                
        except Exception as session_mgr_error:
            print(f"   ⚠️  Session manager error: {session_mgr_error}")
            logger.warning(f"Session manager error, continuing with ADK session handling: {session_mgr_error}")
        # --- End Session Management ---

        # Check if ADK components are available
        print(f"\n🔍 CHECKING ADK SYSTEM AVAILABILITY:")
        print(f"   adk_runner available: {adk_runner is not None}")
        print(f"   root_agent available: {root_agent is not None}")

        # Primary: Use ADK agent system for intelligent responses
        if adk_runner and root_agent:
            try:
                print(f"✅ ADK system available - routing to intelligent agent")
                logger.info("Routing to ADK agent system for intelligent processing")

                # The session_id for a conversation. Often, user_id is sufficient for 1:1 user-session.
                session_id_to_use = normalized_user_id
                
                # --- IMPROVED ADK SESSION HANDLING ---
                # Always create new session for each interaction to avoid threading issues
                print(f"   🔧 Creating fresh ADK session for user...")
                try:
                    # Create a unique session ID for this interaction
                    unique_session_id = f"{normalized_user_id}_{int(time.time())}"
                    
                    # Create new ADK session
                    session = await adk_runner.session_service.create_session(
                        app_name=adk_runner.app_name,
                        user_id=normalized_user_id,
                        session_id=unique_session_id,
                        state={
                            "username": normalized_user_id, 
                            "created_at": time.time(),
                            "interaction_type": "whatsapp_message"
                        }
                    )
                    session_id_to_use = unique_session_id
                    print(f"   ✅ Created fresh ADK session: {session_id_to_use}")
                        
                except Exception as session_error:
                    print(f"   ❌ ADK session creation failed: {session_error}")
                    # Try with timestamp-based unique session ID as fallback
                    fallback_session_id = f"fallback_{normalized_user_id}_{int(time.time() * 1000)}"
                    print(f"   🔄 Trying with fallback session ID: {fallback_session_id}")
                    try:
                        session = await adk_runner.session_service.create_session(
                            app_name=adk_runner.app_name,
                            user_id=normalized_user_id,
                            session_id=fallback_session_id,
                            state={"username": normalized_user_id, "created_at": time.time()}
                        )
                        session_id_to_use = fallback_session_id
                        print(f"   ✅ Fallback session created: {session_id_to_use}")
                    except Exception as final_error:
                        print(f"   ❌ Final session creation failed: {final_error}")
                        raise final_error
                
                # Verify session was created
                if session is None:
                    raise ValueError(f"Failed to create ADK session: {session_id_to_use}")
                # --- End Improved ADK Session Handling ---


                print(f"🚀 CALLING ADK RUNNER:")
                print(f"   User ID: {normalized_user_id}")
                print(f"   Session ID for run: {session_id_to_use}")
                print(f"   Session object: {session}")
                print(f"   ADK Runner app_name: {adk_runner.app_name}")

                # Create the message in a format ADK expects (google.generativeai.types.Content)
                new_message_content = types.Content(
                    role='user', parts=[types.Part(text=user_text)]
                )
                print(f"   Message content created: {new_message_content}")

                final_response_text = None
                event_count = 0
                try:
                    async for event in adk_runner.run_async(
                        user_id=normalized_user_id,
                        session_id=session_id_to_use,
                        new_message=new_message_content,
                    ):
                        event_count += 1
                        print(f"   Event #{event_count}: {event.__class__.__name__}")
                        if hasattr(event, 'content') and event.content:
                            print(f"   Event content: {str(event.content)[:100]}...")
                        
                        if event.is_final_response():
                            if event.content and event.content.parts:
                                final_response_text = event.content.parts[0].text
                                print(f"   ✅ Extracted final response text from event #{event_count}")
                                break
                            else:
                                print(f"   ⚠️  Final response event has no content or parts")
                    
                    print(f"   📊 Total events processed: {event_count}")
                except Exception as run_error:
                    print(f"   ❌ Error during ADK runner execution:")
                    print(f"   Error: {str(run_error)}")
                    print(f"   Error type: {type(run_error).__name__}")
                    
                    # If it's a session not found error, try the synchronous approach
                    if "Session not found" in str(run_error):
                        print(f"   🔄 Trying synchronous runner as fallback...")
                        try:
                            # Use the synchronous run method which doesn't have thread issues
                            events = adk_runner.run(
                                user_id=normalized_user_id,
                                session_id=session_id_to_use,
                                new_message=new_message_content,
                            )
                            
                            # Process events from synchronous run
                            for event in events:
                                event_count += 1
                                print(f"   Sync Event #{event_count}: {event.__class__.__name__}")
                                if hasattr(event, 'content') and event.content:
                                    print(f"   Event content: {str(event.content)[:100]}...")
                                
                                if event.is_final_response():
                                    if event.content and event.content.parts:
                                        final_response_text = event.content.parts[0].text
                                        print(f"   ✅ Extracted final response text from sync event #{event_count}")
                                        break
                                    else:
                                        print(f"   ⚠️  Final response event has no content or parts")
                            
                            print(f"   📊 Total sync events processed: {event_count}")
                            
                        except Exception as sync_error:
                            print(f"   ❌ Synchronous fallback also failed: {sync_error}")
                            raise run_error  # Raise the original error
                    else:
                        raise run_error

                if final_response_text:
                    print(f"✅ ADK AGENT RESPONSE EXTRACTED:")
                    print(f"   Response length: {len(final_response_text)} characters")
                    print(f"   Response preview: {final_response_text[:200]}...")

                    logger.info(
                        f"ADK agent response generated successfully: {len(final_response_text)} chars"
                    )

                    if monitoring_service:
                        await monitoring_service.log_conversation_event(
                            {
                                "event": "adk_agent_response",
                                "user_id": normalized_user_id,
                                "input_length": len(user_text),
                                "output_length": len(final_response_text),
                                "processing_method": "adk_agents",
                            }
                        )
                    return final_response_text
                else:
                    print(f"⚠️  ADK agent returned no final response with content.")
                    logger.warning("ADK agent returned empty response, using fallback")

            except Exception as e:
                print(f"❌ ADK AGENT ERROR:")
                print(f"   Error: {str(e)}")
                print(f"   Error type: {type(e).__name__}")

                import traceback
                print(f"   Traceback: {traceback.format_exc()}")

                logger.error(f"ADK agent processing failed: {e}")
                if monitoring_service:
                    await monitoring_service.log_error_event(
                        "adk_agent_error",
                        str(e),
                        {"user_id": normalized_user_id, "input_text": user_text[:100]},
                    )
                # Continue to fallback

        else:
            print(f"⚠️  ADK system not available:")
            if not adk_runner:
                print(f"   - adk_runner is None")
            if not root_agent:
                print(f"   - root_agent is None")
            logger.warning("ADK agent system not available, using fallback responses")

        print(f"\n🔄 USING FALLBACK RESPONSE SYSTEM")
        logger.info("Using minimal fallback response system")

        if monitoring_service:
            await monitoring_service.log_conversation_event(
                {
                    "event": "fallback_response_used",
                    "user_id": normalized_user_id,
                    "input_text": user_text[:100],
                    "processing_method": "fallback",
                }
            )

        fallback_response = """🇺🇬 Hello! I'm the Uganda E-Gov assistant.

I can help you with:
• Birth Certificate (NIRA) - Check status with reference number
• Tax Status (URA) - Check balance with TIN number
• NSSF Balance - Check contributions with membership number
• Land Verification (NLIS) - Verify ownership with plot details

Just tell me what you need help with, or provide your reference numbers directly.

Examples:
• "Check my birth certificate NIRA/2023/123456"
• "My TIN is 1234567890, what's my tax status?"
• "I need help with land verification"

Available in English, Luganda, Luo, and Runyoro.

How can I assist you today?"""

        print(f"📤 FALLBACK RESPONSE GENERATED:")
        print(f"   Length: {len(fallback_response)} characters")
        print(f"   Preview: {fallback_response[:200]}...")

        return fallback_response

    except Exception as e:
        print(f"\n❌ GENERATE_SIMPLE_RESPONSE TOP-LEVEL ERROR:")
        print(f"   Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

        logger.error(f"Top-level error generating response: {e}")

        error_response = """Hello! I'm the Uganda E-Gov assistant.

I can help you with government services like birth certificates, tax status, NSSF balance, and land verification.

How can I assist you today?"""

        print(f"📤 FINAL ERROR RESPONSE GENERATED:")
        print(f"   Length: {len(error_response)} characters")

        return error_response

async def _validate_services():
    """Validate all services are working correctly"""
    try:
        # Test session manager
        stats = await session_manager.get_session_stats()
        logger.info(f"Session manager validation: {stats}")
        
        # Test monitoring service
        summary = await monitoring_service.get_system_health_summary()
        logger.info("Monitoring service validation: OK")
        
        # Log validation success
        await monitoring_service.log_conversation_event({"event": "validation", "status": "success"})
        
    except Exception as e:
        logger.error(f"Service validation failed: {e}")
        await monitoring_service.log_error_event("validation_error", str(e), {})
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with comprehensive initialization"""
    global root_agent, session_manager, monitoring_service, adk_runner
    
    logger.info("Starting Uganda E-Gov WhatsApp Helpdesk (Modular Production Mode)...")
    
    try:
        # Initialize simple monitoring first
        monitoring_service = MonitoringService()
        await monitoring_service.start_monitoring()
        logger.info("Simple monitoring service started")
        
        # Initialize server cache service
        await cache_service.start_cleanup_task()
        logger.info("Server cache service started")
        
        # Initialize session manager
        await session_manager.start_cleanup_task()
        logger.info("Session manager initialized")
        
        # Initialize WhatsApp Web client
  
        # Initialize modular ADK agent system
        print("\n🤖 INITIALIZING ADK AGENT SYSTEM:")
        logger.info("Initializing modular ADK agent system with enhanced browser automation...")
        start_time = time.time()
        
        try:
            print("   Creating root agent...")
            root_agent = await create_root_agent()
            print(f"   ✅ Root agent created: {root_agent}")
            print(f"   Root agent type: {type(root_agent)}")
            
            if root_agent:
                print(f"   Root agent name: {root_agent.name}")
                print(f"   Root agent tools: {len(root_agent.tools) if hasattr(root_agent, 'tools') else 'N/A'}")
            
            # Create ADK runner with session service
            print("   Creating ADK session service...")
            adk_session_service = InMemorySessionService()
            print(f"   ✅ Session service created: {adk_session_service}")
            print(f"   Session service type: {type(adk_session_service)}")
            
            print("   Creating ADK runner...")
            adk_runner = Runner(
                app_name="uganda_egov_whatsapp",
                agent=root_agent,
                session_service=adk_session_service
            )
            print(f"   ✅ ADK runner created: {adk_runner}")
            print(f"   ADK runner app_name: {adk_runner.app_name}")
            print(f"   ADK runner session_service: {adk_runner.session_service}")
            print(f"   ADK runner agent: {adk_runner.agent}")
            
            # Test session service functionality
            print("   🧪 Testing session service...")
            try:
                test_session_id = "test_session_123"
                test_user_id = "test_user_123"
                
                # Try to create a test session
                test_session = await adk_runner.session_service.create_session(
                    app_name=adk_runner.app_name,
                    user_id=test_user_id,
                    session_id=test_session_id,
                    state={"test": True}
                )
                print(f"   ✅ Test session created successfully: {test_session}")
                
                # Try to get the test session
                retrieved_session = await adk_runner.session_service.get_session(
                    app_name=adk_runner.app_name,
                    user_id=test_user_id,
                    session_id=test_session_id
                )
                print(f"   ✅ Test session retrieved successfully: {retrieved_session}")
                
                print("   ✅ Session service test passed!")
                
            except Exception as test_error:
                print(f"   ❌ Session service test failed: {test_error}")
                print(f"   This may cause issues with ADK runner execution")
            
            init_time = time.time() - start_time
            await monitoring_service.log_conversation_event({"event": "agent_initialization", "duration": init_time, "status": "success"})
            
            print(f"   🎉 ADK system initialized successfully in {init_time:.2f}s")
            logger.info(f"Modular ADK agent system and runner initialized successfully in {init_time:.2f}s")
            
        except Exception as agent_error:
            print(f"   ❌ ADK agent initialization failed:")
            print(f"      Error: {str(agent_error)}")
            print(f"      Error type: {type(agent_error).__name__}")
            
            import traceback
            print(f"      Traceback: {traceback.format_exc()}")
            
            logger.error(f"ADK agent initialization failed: {agent_error}")
            
            # Set to None so fallback will be used
            root_agent = None
            adk_runner = None
            
            print("   ⚠️  Continuing with fallback responses only")
        
        # Validate all services
        await _validate_services()
        
        logger.info("All services initialized successfully - Modular system ready")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        if monitoring_service:
            await monitoring_service.log_error_event("startup_error", str(e), {"phase": "initialization"})
        raise
    finally:
        logger.info("Shutting down services gracefully...")
        
        # Stop monitoring first to capture shutdown metrics
        if monitoring_service:
            await monitoring_service.log_error_event("shutdown", "System shutdown initiated", {"phase": "cleanup"})
            await monitoring_service.stop_monitoring()
        
        # Cleanup WhatsApp Web client
        if whatsapp_web_client:
            await whatsapp_web_client.stop()
        
        # Cleanup MCP connections
        await cleanup_mcp_connections()
        
        logger.info("Shutdown complete")

# Create FastAPI application with production settings
app = FastAPI(
    title="Uganda E-Gov WhatsApp Helpdesk",
    description="Multi-Agent AI System for Government Service Access with Modular Architecture",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add production middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenTelemetry instrumentation
if settings.ENVIRONMENT == "production":
    FastAPIInstrumentor.instrument_app(app)

# Middleware for request monitoring
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Monitor all HTTP requests"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log request
        if monitoring_service:
            await monitoring_service.log_conversation_event({
                "event": "http_request",
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": response.status_code,
                "duration": duration
            })
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(duration)
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        if monitoring_service:
            await monitoring_service.log_conversation_event({
                "event": "http_request",
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": 500,
                "duration": duration
            })
            await monitoring_service.log_error_event("request_error", str(e), {
                "method": request.method,
                "path": request.url.path,
                "duration": duration
            })
        
        raise

# Include routers
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

# Add static file serving for admin dashboard
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# Production-optimized WhatsApp Web automation
# Update imports


# WhatsApp Web client will be initialized in lifespan
whatsapp_web_client = None

# Update webhook endpoint
# Fixed webhook function
# Simplified webhook function
@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Enhanced WhatsApp webhook endpoint with comprehensive logging"""
    start_time = time.time()
    
    print("\n" + "="*80)
    print("🔔 WEBHOOK REQUEST RECEIVED")
    print("="*80)
    
    try:
        # Log request details
        print(f"📍 Request from: {request.client.host if request.client else 'unknown'}")
        print(f"🕐 Timestamp: {datetime.now().isoformat()}")
        print(f"📋 Headers: {dict(request.headers)}")
        
        # Try to get form data
        body = {}
        content_type = request.headers.get("content-type", "")
        print(f"📄 Content-Type: {content_type}")
        
        try:
            if "application/json" in content_type:
                body = await request.json()
                print("📦 Parsed as JSON")
            else:
                form = await request.form()
                body = dict(form)
                print("📦 Parsed as form data")
        except Exception as parse_error:
            print(f"⚠️  Parse error: {parse_error}")
            # Try raw body
            try:
                raw_body = await request.body()
                print(f"📄 Raw body: {raw_body.decode('utf-8', errors='ignore')[:500]}")
            except:
                pass
            body = {}
        
        print(f"📊 Request body: {json.dumps(body, indent=2)}")
        
        # Handle webhook verification (common for setup)
        if "hub.challenge" in body:
            challenge = body["hub.challenge"]
            print(f"✅ Webhook verification - returning challenge: {challenge}")
            return PlainTextResponse(challenge)
        
        # Extract message and sender from various formats
        user_text = "Hello"  # Default message
        user_id = "user"     # Default user
        
        print("\n🔍 EXTRACTING MESSAGE DATA:")
        
        # Try different field combinations
        if "Body" in body:
            user_text = body["Body"]
            print(f"📝 Found Body: {user_text}")
        elif "message" in body:
            user_text = body["message"]
            print(f"📝 Found message: {user_text}")
        elif "text" in body:
            user_text = body["text"]
            print(f"📝 Found text: {user_text}")
        else:
            print(f"⚠️  No message field found, using default: {user_text}")
        
        if "From" in body:
            user_id = body["From"]
            print(f"👤 Found From: {user_id}")
        elif "sender" in body:
            user_id = body["sender"]
            print(f"👤 Found sender: {user_id}")
        elif "from" in body:
            user_id = body["from"]
            print(f"👤 Found from: {user_id}")
        else:
            print(f"⚠️  No sender field found, using default: {user_id}")
        
        print(f"\n🎯 FINAL EXTRACTED DATA:")
        print(f"   Message: '{user_text}'")
        print(f"   User ID: '{user_id}'")
        
        
        # Ensure session exists for this user before generating response
        print(f"\n🔧 ENSURING USER SESSION EXISTS:")
        try:
            # Check if user has an active session
            existing_session = await session_manager.get_user_active_session(user_id)
            
            if not existing_session:
                print(f"   📝 Creating new session for WhatsApp user: {user_id}")
                session_id = await session_manager.create_session(
                    user_id=user_id,
                    initial_data={
                        "first_message": user_text,
                        "created_via": "whatsapp_webhook",
                        "source": "whatsapp_business_api",
                        "user_phone": user_id
                    }
                )
                print(f"   ✅ Created session: {session_id}")
                
                # Log new user session creation
                if monitoring_service:
                    await monitoring_service.log_conversation_event({
                        "event": "new_whatsapp_user_session",
                        "user_id": user_id,
                        "session_id": session_id,
                        "first_message": user_text[:100]
                    })
            else:
                print(f"   ✅ Using existing session: {existing_session['session_id']}")
                
        except Exception as session_error:
            print(f"   ⚠️  Session creation error: {session_error}")
            logger.warning(f"Failed to create session for user {user_id}: {session_error}")

        # Generate response with detailed logging
        print(f"\n🤖 GENERATING RESPONSE:")
        print(f"   Calling generate_simple_response...")
        
        response_text = await generate_simple_response(user_text, user_id)
        
        print(f"✅ Response generated successfully!")
        print(f"📝 Response length: {len(response_text)} characters")
        print(f"📄 Response preview: {response_text[:200]}...")
        
        # Send response back to WhatsApp via WhatsApp Web
        print(f"\n📱 SENDING WHATSAPP RESPONSE:")
        print(f"   To: {user_id}")
        print(f"   Message: {response_text[:100]}...")
        
        try:
            if whatsapp_web_client and whatsapp_web_client.is_authenticated:
                # Send the response back to WhatsApp
                send_result = await whatsapp_web_client.send_text_message(user_id, response_text)
                
                if send_result.get("status") == "success":
                    print(f"   ✅ WhatsApp message sent successfully!")
                    print(f"   📧 Message ID: {send_result.get('message_id')}")
                    whatsapp_status = "sent"
                else:
                    print(f"   ❌ Failed to send WhatsApp message:")
                    print(f"   Error: {send_result.get('error')}")
                    whatsapp_status = "failed"
            else:
                print(f"   ❌ WhatsApp Web client not available or not authenticated")
                whatsapp_status = "not_authenticated"
                
        except Exception as send_error:
            print(f"   ❌ WhatsApp sending error:")
            print(f"   Error: {str(send_error)}")
            print(f"   Error type: {type(send_error).__name__}")
            
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            
            whatsapp_status = "error"
        
        processing_time = time.time() - start_time
        
        # Log successful operation
        if monitoring_service:
            await monitoring_service.log_conversation_event({
                "event": "whatsapp_message_processed",
                "user_id": user_id,
                "processing_time": processing_time,
                "status": "success",
                "whatsapp_sent": whatsapp_status
            })
        
        print(f"⏱️  Total processing time: {processing_time:.2f}s")
        
        # Return response in multiple formats for compatibility
        response_data = {
            "reply": response_text,
            "message": response_text,
            "response": response_text,
            "status": "success",
            "processing_time": processing_time,
            "user_id": user_id,
            "whatsapp_status": whatsapp_status
        }
        
        print(f"\n📤 HTTP RESPONSE:")
        print(f"📊 Response data: {json.dumps(response_data, indent=2)}")
        print("="*80)
        
        return JSONResponse(response_data)
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        print(f"\n❌ WEBHOOK ERROR:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Processing time: {processing_time:.2f}s")
        
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        if monitoring_service:
            await monitoring_service.log_error_event("webhook_error", str(e), {
                "processing_time": processing_time,
                "error_type": type(e).__name__
            })
        
        logger.error(f"Webhook error: {e}")
        
        # Return a simple success response even on error to avoid webhook retries
        error_response = {
            "reply": "Hello! I'm the Uganda E-Gov assistant. How can I help you with government services today?",
            "status": "error_fallback",
            "error": str(e),
            "processing_time": processing_time
        }
        
        print(f"📤 Sending error response: {json.dumps(error_response, indent=2)}")
        print("="*80)
        
        return JSONResponse(error_response)

@app.post("/")
async def root_post(request: Request):
    """Handle POST requests to root endpoint - redirect to proper webhook"""
    try:
        # Log the POST request for debugging
        body = await request.body()
        logger.info(f"POST request to root endpoint from {request.client.host if request.client else 'unknown'}")
        logger.debug(f"POST body: {body.decode('utf-8', errors='ignore')[:500]}")
        
        # Check if this looks like a webhook request
        try:
            form = await request.form()
            if "Body" in form and "From" in form:
                # This looks like a WhatsApp webhook, redirect to proper endpoint
                logger.info("Redirecting WhatsApp webhook from root to /whatsapp/webhook")
                return JSONResponse({
                    "error": "Webhook endpoint moved",
                    "message": "Please send WhatsApp webhooks to /whatsapp/webhook",
                    "correct_endpoint": "/whatsapp/webhook"
                }, status_code=301)
        except:
            pass
        
        # For other POST requests, return helpful information
        return JSONResponse({
            "message": "Uganda E-Gov WhatsApp Helpdesk API",
            "error": "POST not supported on root endpoint",
            "available_endpoints": {
                "whatsapp_webhook": "POST /whatsapp/webhook",
                "health_check": "GET /health",
                "metrics": "GET /metrics",
                "system_info": "GET /system/info"
            }
        }, status_code=405)
        
    except Exception as e:
        logger.error(f"Error handling POST to root: {e}")
        return JSONResponse({
            "error": "Invalid request",
            "message": "Please check your request format and endpoint"
        }, status_code=400)

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "architecture": "modular",
            "services": {},
            "metrics": {}
        }
        
        # Check session manager
        try:
            stats = await session_manager.get_session_stats()
            health_status["services"]["session_manager"] = "healthy"
            health_status["metrics"]["active_sessions"] = stats.get("total_active_sessions", 0)
        except Exception as e:
            health_status["services"]["session_manager"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check monitoring service
        try:
            summary = await monitoring_service.get_system_health_summary()
            health_status["services"]["monitoring"] = "healthy"
            if isinstance(summary, dict):
                health_status["metrics"].update(summary)
        except Exception as e:
            health_status["services"]["monitoring"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check root agent
        health_status["services"]["root_agent"] = "healthy" if root_agent else "unhealthy"
        if not root_agent:
            health_status["status"] = "degraded"
        
        # Log session count
        if monitoring_service and "active_sessions" in health_status["metrics"]:
            await monitoring_service.log_conversation_event({
                "event": "session_count_update",
                "active_sessions": health_status["metrics"]["active_sessions"]
            })
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    if not all([session_manager, monitoring_service, root_agent]):
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready", "architecture": "modular"}

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    if not monitoring_service:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    return await monitoring_service.get_system_health_summary()

@app.get("/admin/metrics")
async def admin_metrics():
    """Admin metrics endpoint with detailed information"""
    if not monitoring_service:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    return await monitoring_service.get_system_health_summary()

@app.get("/system/info")
async def system_info():
    """System architecture information"""
    return {
        "architecture": "modular",
        "version": "2.0.0",
        "components": {
            "mcp_servers": [
                "user_identification_tools",
                "playwright_tools", 
                "browser_use_tools",
                "whatsapp_tools"
            ],
            "core_agents": [
                "user_identification_agent",
                "language_agent",
                "intent_agent", 
                "help_agent"
            ],
            "service_agents": [
                "birth_agent",
                "tax_agent",
                "nssf_agent",
                "land_agent",
                "form_agent"
            ]
        },
        "automation": {
            "primary": "Playwright MCP",
            "fallback": "Browser-Use Agent",
            "features": [
                "Smart web automation",
                "Government portal integration",
                "Screenshot capture",
                "Data extraction",
                "Error recovery"
            ]
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with comprehensive logging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if monitoring_service:
        await monitoring_service.log_error_event("global_exception", str(exc), {
            "path": str(request.url.path),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "remote_addr": get_remote_address(request)
        })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Our team has been notified.",
            "request_id": id(request),  # Simple request ID for tracking
            "architecture": "modular"
        }
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Rate limit exception handler"""
    if monitoring_service:
        await monitoring_service.log_error_event("rate_limit_exceeded", str(exc), {
            "path": str(request.url.path),
            "remote_addr": get_remote_address(request)
        })
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": 60
        }
    )
app.mount("/whatsapp-clone", clone_app)
if __name__ == "__main__":
    # Production-optimized server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT_NO", 8080)),
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.ENVIRONMENT == "development" else 4,
        access_log=settings.ENVIRONMENT == "development",
        server_header=False,
        date_header=False
    )