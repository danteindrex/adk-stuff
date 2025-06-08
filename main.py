"""
Uganda E-Gov WhatsApp Helpdesk
Multi-Agent AI System for Government Service Access
"""

import os
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Import our custom modules
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.webhooks import whatsapp_router
from app.api.admin import admin_router
# ADK agent system
from app.agents.adk_agents import create_root_agent, cleanup_mcp_connections
from app.services.google_session_manager import GoogleSessionManager
from app.services.simple_monitoring import MonitoringService

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global services
session_manager = None
monitoring_service = None
root_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global root_agent, session_manager, monitoring_service
    
    logger.info("Starting Uganda E-Gov WhatsApp Helpdesk...")
    
    try:
        # Initialize core services
        session_manager = GoogleSessionManager()
        monitoring_service = MonitoringService()
        
        # Initialize ADK agent system
        logger.info("Initializing ADK agent system...")
        root_agent = await create_root_agent()
        logger.info("ADK agent system initialized successfully")
        
        # Start background session cleanup
        await session_manager.start_cleanup_task()
        
        # Start background monitoring
        asyncio.create_task(monitoring_service.start_monitoring())
        logger.info("All services initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        logger.info("Shutting down services...")
        if monitoring_service:
            await monitoring_service.stop_monitoring()
        # Cleanup MCP connections
        await cleanup_mcp_connections()

# Create FastAPI application
app = FastAPI(
    title="Uganda E-Gov WhatsApp Helpdesk",
    description="Multi-Agent AI System for Government Service Access",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

# WhatsApp webhook endpoint using ADK agent
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    # Extract WhatsApp message (simplified, real implementation should parse all types)
    try:
        entry = body.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "no_message"}
        message = messages[0]
        user_text = message.get("text", {}).get("body", "")
        user_id = message.get("from")
        # Route to ADK agent
        adk_response = await root_agent.run_async({
            "user_id": user_id,
            "text": user_text,
            "raw": message
        })
        # ADK returns an async generator of events; get the final response
        final_response = None
        async for event in adk_response:
            if getattr(event, "is_final_response", False):
                final_response = event
        if final_response:
            return JSONResponse({"reply": getattr(final_response, "content", "")})
        return {"status": "processed"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Uganda E-Gov WhatsApp Helpdesk API",
        "version": "1.0.0",
        "status": "operational",
        "services": {
            "whatsapp_webhook": "/whatsapp/webhook",
            "admin_dashboard": "/admin/dashboard",
            "health_check": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Check Google Cloud services
        google_services_health = False
        if session_manager:
            try:
                # Test Firestore connection by getting session stats
                stats = await session_manager.get_session_stats()
                google_services_health = True
            except:
                google_services_health = False
        
        # Check root agent
        agent_health = root_agent is not None
            
        return {
            "status": "healthy" if (google_services_health and agent_health) else "degraded",
            "timestamp": datetime.now().isoformat() if monitoring_service else None,
            "services": {
                "google_cloud": "healthy" if google_services_health else "unhealthy",
                "root_agent": "healthy" if agent_health else "unhealthy",
                "session_manager": "healthy" if session_manager else "unhealthy",
                "monitoring": "healthy" if monitoring_service else "unhealthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if monitoring_service:
        await monitoring_service.log_error("global_exception", str(exc), {
            "path": str(request.url.path),
            "method": request.method
        })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Our team has been notified."
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )