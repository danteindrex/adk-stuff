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

# Import your existing AI system
from main import generate_simple_response, monitoring_service, twilio_client

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
            user = await db.create_or_update_user(user_data)
            actual_user_id = user.id
        else:
            # For demo users or users without full data
            actual_user_id = user_id
        
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
        
        required_fields = ["email", "name"]
        for field in required_fields:
            if field not in user_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        db = get_supabase_client()
        user = await db.create_or_update_user(user_data)
        
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
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    # Run the WhatsApp clone server
    uvicorn.run(
        "whatsapp_clone_server:clone_app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )