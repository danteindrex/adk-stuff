"""
Uganda E-Gov WhatsApp Helpdesk
Multi-Agent AI System for Government Service Access
Production-Optimized Version with Modular Architecture and Enhanced Browser Automation
"""

import os
import asyncio
import logging
import time
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
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.webhooks import whatsapp_router
from app.api.admin import admin_router
# ADK agent system - using modular architecture with enhanced browser automation
from app.agents.adk_agents_modular import create_root_agent, cleanup_mcp_connections
from app.services.google_session_manager import GoogleSessionManager
from app.services.simple_monitoring import MonitoringService

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global services
session_manager = None
monitoring_service = None
root_agent = None

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
    global root_agent, session_manager, monitoring_service
    
    logger.info("Starting Uganda E-Gov WhatsApp Helpdesk (Modular Production Mode)...")
    
    try:
        # Initialize simple monitoring first
        monitoring_service = MonitoringService()
        await monitoring_service.start_monitoring()
        logger.info("Simple monitoring service started")
        
        # Initialize session manager
        session_manager = GoogleSessionManager()
        await session_manager.start_cleanup_task()
        logger.info("Session manager initialized")
        
        # Initialize modular ADK agent system
        logger.info("Initializing modular ADK agent system with enhanced browser automation...")
        start_time = time.time()
        root_agent = await create_root_agent()
        init_time = time.time() - start_time
        await monitoring_service.log_conversation_event({"event": "agent_initialization", "duration": init_time, "status": "success"})
        logger.info(f"Modular ADK agent system initialized successfully in {init_time:.2f}s")
        
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

# Production-optimized WhatsApp webhook endpoint with enhanced automation
@app.post("/whatsapp/webhook")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """WhatsApp webhook endpoint with enhanced browser automation and comprehensive error handling"""
    start_time = time.time()
    
    try:
        body = await request.json()
        
        # Validate webhook structure
        if "entry" not in body:
            await monitoring_service.log_error_event("webhook_validation", "Missing entry field", {"body_keys": list(body.keys())})
            return {"status": "invalid_webhook"}
        
        entry = body.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return {"status": "no_message"}
        
        message = messages[0]
        user_text = message.get("text", {}).get("body", "")
        user_id = message.get("from")
        message_id = message.get("id")
        
        # Log incoming message
        logger.info(f"Processing WhatsApp message from {user_id}: {user_text[:100]}...")
        
        # Route to modular ADK agent with timeout
        try:
            adk_response = await asyncio.wait_for(
                root_agent.run_async({
                    "user_id": user_id,
                    "text": user_text,
                    "raw": message,
                    "automation_enabled": True,  # Enable enhanced automation
                    "fallback_enabled": True     # Enable browser-use fallback
                }),
                timeout=settings.REQUEST_TIMEOUT_SECONDS
            )
            
            # Process agent response
            final_response = None
            async for event in adk_response:
                if getattr(event, "is_final_response", False):
                    final_response = event
                    break
            
            if final_response:
                response_text = getattr(final_response, "content", "")
                processing_time = time.time() - start_time
                
                # Log successful operation
                await monitoring_service.log_conversation_event({
                    "event": "whatsapp_message_processed",
                    "user_id": user_id,
                    "processing_time": processing_time,
                    "status": "success"
                })
                
                logger.info(f"Processed message with modular system in {processing_time:.2f}s")
                return JSONResponse({"reply": response_text})
            else:
                await monitoring_service.log_error_event("agent_response", "No final response from agent", {
                    "user_id": user_id,
                    "message_id": message_id
                })
                return {"status": "processed", "warning": "no_final_response"}
                
        except asyncio.TimeoutError:
            await monitoring_service.log_error_event("timeout", "Agent processing timeout", {
                "user_id": user_id,
                "timeout": settings.REQUEST_TIMEOUT_SECONDS
            })
            return JSONResponse(
                {"error": "Processing timeout", "retry": True},
                status_code=408
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        await monitoring_service.log_error_event("webhook_error", str(e), {
            "processing_time": processing_time,
            "user_id": locals().get("user_id"),
            "message_id": locals().get("message_id")
        })
        
        logger.error(f"WhatsApp webhook error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Uganda E-Gov WhatsApp Helpdesk API",
        "version": "2.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "architecture": "modular",
        "features": [
            "Enhanced browser automation with Playwright + Browser-Use fallback",
            "Modular agent architecture",
            "Multi-language support",
            "Comprehensive monitoring",
            "Production-optimized performance"
        ],
        "services": {
            "whatsapp_webhook": "/whatsapp/webhook",
            "admin_dashboard": "/admin/dashboard",
            "health_check": "/health",
            "metrics": "/metrics",
            "ready": "/ready"
        }
    }

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

if __name__ == "__main__":
    # Production-optimized server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.ENVIRONMENT == "development" else 4,
        access_log=settings.ENVIRONMENT == "development",
        server_header=False,
        date_header=False
    )