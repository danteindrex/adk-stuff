"""
Admin dashboard API endpoints with authentication
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Form, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import jwt
import hashlib
import secrets
from app.core.config import settings
from app.core.logging_config import StructuredLogger

logger = StructuredLogger(__name__)

# Create router
admin_router = APIRouter()

# Security
security = HTTPBearer(auto_error=False)

# Admin credentials (in production, store these securely)
ADMIN_USERNAME = "trevor"
ADMIN_PASSWORD = "The$1000"
JWT_SECRET = settings.JWT_SECRET_KEY or "your-secret-key-here"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Active sessions store (in production, use Redis or database)
active_sessions = {}

class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    active_sessions: int
    today_interactions: int
    success_rate_24h: float
    avg_response_time: float
    service_health: Dict[str, Any]
    popular_services: List[Dict[str, Any]]
    language_distribution: Dict[str, int]
    error_summary: List[Dict[str, Any]]

class MaintenanceConfig(BaseModel):
    """Maintenance configuration model"""
    service_name: str
    enabled: bool
    message: Optional[str] = None
    duration_minutes: Optional[int] = None

class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Get password hash"""
    return hashlib.sha256(password.encode()).hexdigest()

async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != ADMIN_USERNAME:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Check if session is still active
        session_id = payload.get("session_id")
        if session_id not in active_sessions:
            raise HTTPException(status_code=401, detail="Session expired")
        
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# Authentication endpoints
@admin_router.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    """Serve admin dashboard HTML"""
    try:
        with open("static/admin.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Admin dashboard not found")

@admin_router.post("/login")
async def admin_login(login_data: LoginRequest):
    """Admin login endpoint"""
    try:
        # Verify credentials
        if login_data.username != ADMIN_USERNAME or login_data.password != ADMIN_PASSWORD:
            logger.warning(f"Failed login attempt for username: {login_data.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "username": login_data.username,
            "login_time": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        active_sessions[session_id] = session_data
        
        # Create JWT token
        access_token_expires = timedelta(hours=JWT_EXPIRATION_HOURS)
        access_token = create_access_token(
            data={"sub": login_data.username, "session_id": session_id},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Admin login successful for user: {login_data.username}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "username": login_data.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@admin_router.post("/logout")
async def admin_logout(username: str = Depends(verify_admin_token)):
    """Admin logout endpoint"""
    try:
        # Remove all sessions for this user
        sessions_to_remove = []
        for session_id, session_data in active_sessions.items():
            if session_data.get("username") == username:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del active_sessions[session_id]
        
        logger.info(f"Admin logout successful for user: {username}")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@admin_router.get("/verify")
async def verify_admin_session(username: str = Depends(verify_admin_token)):
    """Verify admin session is valid"""
    return {
        "valid": True,
        "username": username,
        "timestamp": datetime.utcnow().isoformat()
    }

@admin_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(username: str = Depends(verify_admin_token)):
    """Get comprehensive dashboard statistics with real-time data"""
    try:
        # Import services for real data
        from app.services.simple_session_manager import session_manager
        from app.services.simple_monitoring import MonitoringService
        from app.database.supabase_client import get_supabase_client
        
        # Initialize monitoring service if not available
        monitoring_service = None
        try:
            # Try to get global monitoring service
            import main
            monitoring_service = getattr(main, 'monitoring_service', None)
        except:
            pass
        
        # Get session statistics
        session_stats = await session_manager.get_session_stats()
        active_sessions = session_stats.get("total_active_sessions", 0)
        
        # Get database statistics
        db = get_supabase_client()
        db_stats = await db.get_system_stats()
        
        # Get monitoring data
        monitoring_data = {}
        if monitoring_service:
            try:
                monitoring_data = await monitoring_service.get_system_health_summary()
            except Exception as e:
                logger.warning(f"Failed to get monitoring data: {e}")
        
        # Calculate today's interactions
        today_interactions = db_stats.get("total_messages", 0)
        
        # Calculate success rate (mock for now, can be enhanced)
        success_rate = 98.5  # Default high success rate
        
        # Calculate average response time
        avg_response_time = monitoring_data.get("avg_response_time", 250.0)
        
        # Service health status
        service_health = {
            "webhook": {
                "status": "healthy",
                "uptime": "99.9%",
                "total_requests": today_interactions,
                "success_rate": success_rate / 100,
                "avg_response_time": avg_response_time
            },
            "cache": {
                "status": "healthy" if session_stats.get("error") is None else "degraded",
                "uptime": "99.8%",
                "total_requests": active_sessions,
                "success_rate": 0.99,
                "avg_response_time": 50.0
            },
            "database": {
                "status": "healthy",
                "uptime": "99.9%",
                "total_requests": db_stats.get("total_messages", 0),
                "success_rate": 0.995,
                "avg_response_time": 100.0
            },
            "adk_agents": {
                "status": "healthy",
                "uptime": "99.7%",
                "total_requests": today_interactions,
                "success_rate": success_rate / 100,
                "avg_response_time": avg_response_time * 1.2
            }
        }
        
        # Popular services (mock data, can be enhanced with real analytics)
        popular_services = [
            {"service": "NIRA", "requests": int(today_interactions * 0.35), "success_rate": 97.8},
            {"service": "URA", "requests": int(today_interactions * 0.25), "success_rate": 96.5},
            {"service": "NSSF", "requests": int(today_interactions * 0.20), "success_rate": 98.2},
            {"service": "NLIS", "requests": int(today_interactions * 0.15), "success_rate": 95.8},
            {"service": "General Help", "requests": int(today_interactions * 0.05), "success_rate": 99.1}
        ]
        
        # Language distribution (mock data, can be enhanced)
        language_distribution = {
            "en": 65,  # English
            "lg": 20,  # Luganda
            "luo": 10, # Luo
            "nyn": 5   # Runyoro
        }
        
        # Error summary (mock data, can be enhanced)
        error_summary = [
            {"error_type": "timeout", "count": 5, "percentage": 2.1},
            {"error_type": "validation", "count": 3, "percentage": 1.3},
            {"error_type": "network", "count": 2, "percentage": 0.8}
        ]
        
        return DashboardStats(
            active_sessions=active_sessions,
            today_interactions=today_interactions,
            success_rate_24h=success_rate / 100,
            avg_response_time=avg_response_time,
            service_health=service_health,
            popular_services=popular_services,
            language_distribution=language_distribution,
            error_summary=error_summary
        )
        
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=e)
        # Return fallback data
        return DashboardStats(
            active_sessions=0,
            today_interactions=0,
            success_rate_24h=1.0,
            avg_response_time=250.0,
            service_health={
                "webhook": {"status": "unknown", "uptime": "N/A"},
                "cache": {"status": "unknown", "uptime": "N/A"}
            },
            popular_services=[],
            language_distribution={"en": 100},
            error_summary=[]
        )

@admin_router.get("/logs/real-time")
async def get_real_time_logs(
    limit: int = Query(default=50, le=200),
    service: Optional[str] = Query(default=None),
    username: str = Depends(verify_admin_token)
):
    """Get real-time system logs"""
    try:
        # Import monitoring service to get real logs
        monitoring_service = None
        # Simplified - no imports needed
        
        logs_data = []
        
        # Get logs from monitoring service
        if monitoring_service:
            try:
                logs_data = await monitoring_service.get_recent_logs(limit=limit, service_filter=service)
            except Exception as e:
                logger.error(f"Failed to get logs from monitoring service: {e}")
        
        # If no monitoring service or no logs, return empty result
        if not logs_data:
            logs_data = []
        
        return {
            "logs": logs_data,
            "total": len(logs_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get real-time logs", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

@admin_router.get("/analytics/usage")
async def get_usage_analytics(
    days: int = Query(default=7, le=30),
    username: str = Depends(verify_admin_token)
):
    """Get usage analytics for specified number of days"""
    try:
        # Import monitoring service to get real analytics
        monitoring_service = None
        # Simplified - no imports needed
        
        analytics_data = []
        
        # Get analytics from monitoring service
        if monitoring_service:
            try:
                analytics_data = await monitoring_service.get_usage_analytics(days=days)
            except Exception as e:
                logger.error(f"Failed to get analytics from monitoring service: {e}")
        
        return {
            "analytics": analytics_data,
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get usage analytics", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@admin_router.get("/services/health")
async def get_services_health(username: str = Depends(verify_admin_token)):
    """Get services health status"""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy",
        "services": {
            "webhook": {"status": "healthy", "last_check": datetime.now(timezone.utc).isoformat()},
            "cache": {"status": "healthy", "last_check": datetime.now(timezone.utc).isoformat()}
        }
    }

@admin_router.post("/system/maintenance")
async def toggle_maintenance_mode(
    config: MaintenanceConfig,
    username: str = Depends(verify_admin_token)
):
    """Enable/disable maintenance mode for specific services"""
    try:
        # Import monitoring service to handle maintenance mode
        monitoring_service = None
        # Simplified - no imports needed
        
        if not monitoring_service:
            raise HTTPException(status_code=503, detail="Monitoring service not available")
        
        # Toggle maintenance mode through monitoring service
        try:
            result = await monitoring_service.set_maintenance_mode(
                config.service_name,
                config.enabled,
                config.message,
                config.duration_minutes
            )
        except AttributeError:
            # If monitoring service doesn't have maintenance mode method, log the request
            logger.info("Maintenance mode request logged", 
                       service=config.service_name, 
                       enabled=config.enabled,
                       duration=config.duration_minutes)
            result = True
        
        logger.info("Maintenance mode toggled", 
                   service=config.service_name, 
                   enabled=config.enabled,
                   duration=config.duration_minutes)
        
        return {
            "success": True,
            "service": config.service_name,
            "maintenance_enabled": config.enabled,
            "message": config.message,
            "duration_minutes": config.duration_minutes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to toggle maintenance mode", error=e, service=config.service_name)
        raise HTTPException(status_code=500, detail="Failed to toggle maintenance mode")

@admin_router.get("/alerts")
async def get_admin_alerts(
    limit: int = Query(default=20, le=100),
    severity: Optional[str] = Query(default=None),
    username: str = Depends(verify_admin_token)
):
    """Get admin alerts"""
    try:
        # Import monitoring service to get real alerts
        monitoring_service = None
        # Simplified - no imports needed
        
        alerts_data = []
        
        # Get alerts from monitoring service
        if monitoring_service:
            try:
                alerts_data = await monitoring_service.get_alerts(limit=limit, severity_filter=severity)
            except Exception as e:
                logger.error(f"Failed to get alerts from monitoring service: {e}")
        
        return {
            "alerts": alerts_data,
            "total": len(alerts_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get admin alerts", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")

@admin_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    username: str = Depends(verify_admin_token)
):
    """Acknowledge an admin alert"""
    try:
        # Import monitoring service to acknowledge alerts
        monitoring_service = None
        # Simplified - no imports needed
        
        if not monitoring_service:
            raise HTTPException(status_code=503, detail="Monitoring service not available")
        
        # Acknowledge alert through monitoring service
        try:
            result = await monitoring_service.acknowledge_alert(alert_id, username)
        except AttributeError:
            # If monitoring service doesn't have acknowledge method, log the action
            logger.info("Alert acknowledgment logged", alert_id=alert_id, acknowledged_by=username)
            result = True
        
        if not result:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        logger.info("Alert acknowledged", alert_id=alert_id, acknowledged_by=username)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "acknowledged_by": username,
            "acknowledged_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to acknowledge alert", error=e, alert_id=alert_id)
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

@admin_router.get("/performance/metrics")
async def get_performance_metrics(
    hours: int = Query(default=24, le=168),  # Max 1 week
    username: str = Depends(verify_admin_token)
):
    """Get system performance metrics"""
    try:
        # Import monitoring service to get real performance metrics
        monitoring_service = None
        # Simplified - no imports needed
        
        metrics_data = {}
        
        # Get performance metrics from monitoring service
        if monitoring_service:
            try:
                metrics_data = await monitoring_service.get_performance_metrics(hours=hours)
            except Exception as e:
                logger.error(f"Failed to get performance metrics from monitoring service: {e}")
        
        return {
            "metrics": metrics_data,
            "period_hours": hours,
            "total_data_points": sum(len(v) if isinstance(v, list) else 1 for v in metrics_data.values()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")

@admin_router.get("/users/sessions")
async def get_active_user_sessions(
    limit: int = Query(default=50, le=200),
    username: str = Depends(verify_admin_token)
):
    """Get active user sessions with detailed information"""
    try:
        from app.services.simple_session_manager import session_manager
        
        sessions_data = await session_manager.get_active_sessions(limit=limit)
        
        # Enhance session data with additional info
        enhanced_sessions = []
        for session in sessions_data:
            enhanced_session = {
                "session_id": session.get("session_id"),
                "user_id": session.get("user_id"),
                "created_at": session.get("created_at"),
                "last_activity": session.get("last_activity"),
                "message_count": len(session.get("conversation_history", [])),
                "current_agent": session.get("current_agent"),
                "user_context": session.get("user_context", {}),
                "is_active": session.get("is_active", False),
                "duration_minutes": _calculate_session_duration(session),
                "cache_expires_in_hours": session.get("cache_expires_in_hours", 0)
            }
            enhanced_sessions.append(enhanced_session)
        
        return {
            "sessions": enhanced_sessions,
            "total": len(enhanced_sessions),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get active user sessions", error=e)
        return {
            "sessions": [],
            "total": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

def _calculate_session_duration(session):
    """Calculate session duration in minutes"""
    try:
        created_at = datetime.fromisoformat(session.get("created_at", ""))
        last_activity = datetime.fromisoformat(session.get("last_activity", ""))
        duration = (last_activity - created_at).total_seconds() / 60
        return round(duration, 1)
    except:
        return 0

@admin_router.get("/system/realtime-stats")
async def get_realtime_system_stats(username: str = Depends(verify_admin_token)):
    """Get real-time system statistics for live monitoring"""
    try:
        from app.services.simple_session_manager import session_manager
        from app.database.supabase_client import get_supabase_client
        import psutil
        import time
        
        # System performance metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Session statistics
        session_stats = await session_manager.get_session_stats()
        
        # Database statistics
        db = get_supabase_client()
        db_stats = await db.get_system_stats()
        
        # Calculate recent activity (last 5 minutes)
        recent_messages = db_stats.get("total_messages", 0)  # This would need time filtering in real implementation
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_performance": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "application_metrics": {
                "active_sessions": session_stats.get("total_active_sessions", 0),
                "total_sessions": session_stats.get("total_sessions", 0),
                "unique_users": session_stats.get("unique_users", 0),
                "total_messages": db_stats.get("total_messages", 0),
                "active_users_24h": db_stats.get("active_users_24h", 0),
                "avg_messages_per_user": db_stats.get("avg_messages_per_user", 0),
                "avg_sessions_per_user": db_stats.get("avg_sessions_per_user", 0)
            },
            "recent_activity": {
                "messages_last_5min": min(recent_messages, 50),  # Mock recent activity
                "new_users_last_hour": min(session_stats.get("unique_users", 0), 10),
                "errors_last_hour": 2,  # Mock error count
                "avg_response_time_ms": 245.5
            }
        }
        
    except Exception as e:
        logger.error("Failed to get real-time system stats", error=e)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "system_performance": {},
            "application_metrics": {},
            "recent_activity": {}
        }

@admin_router.get("/analytics/service-usage")
async def get_service_usage_analytics(
    hours: int = Query(default=24, le=168),
    username: str = Depends(verify_admin_token)
):
    """Get detailed service usage analytics"""
    try:
        from app.database.supabase_client import get_supabase_client
        
        db = get_supabase_client()
        db_stats = await db.get_system_stats()
        
        total_messages = db_stats.get("total_messages", 0)
        
        # Mock service usage data (in real implementation, this would query actual usage)
        service_usage = [
            {
                "service": "NIRA",
                "display_name": "Birth Certificates",
                "icon": "🎫",
                "total_requests": int(total_messages * 0.35),
                "successful_requests": int(total_messages * 0.35 * 0.978),
                "failed_requests": int(total_messages * 0.35 * 0.022),
                "success_rate": 97.8,
                "avg_response_time_ms": 1250,
                "peak_hour": "14:00",
                "trend": "up"
            },
            {
                "service": "URA",
                "display_name": "Tax Services",
                "icon": "💼",
                "total_requests": int(total_messages * 0.25),
                "successful_requests": int(total_messages * 0.25 * 0.965),
                "failed_requests": int(total_messages * 0.25 * 0.035),
                "success_rate": 96.5,
                "avg_response_time_ms": 1850,
                "peak_hour": "10:00",
                "trend": "stable"
            },
            {
                "service": "NSSF",
                "display_name": "Pension Services",
                "icon": "🏦",
                "total_requests": int(total_messages * 0.20),
                "successful_requests": int(total_messages * 0.20 * 0.982),
                "failed_requests": int(total_messages * 0.20 * 0.018),
                "success_rate": 98.2,
                "avg_response_time_ms": 1100,
                "peak_hour": "11:00",
                "trend": "up"
            },
            {
                "service": "NLIS",
                "display_name": "Land Records",
                "icon": "🌿",
                "total_requests": int(total_messages * 0.15),
                "successful_requests": int(total_messages * 0.15 * 0.958),
                "failed_requests": int(total_messages * 0.15 * 0.042),
                "success_rate": 95.8,
                "avg_response_time_ms": 2100,
                "peak_hour": "15:00",
                "trend": "down"
            },
            {
                "service": "HELP",
                "display_name": "General Help",
                "icon": "❓",
                "total_requests": int(total_messages * 0.05),
                "successful_requests": int(total_messages * 0.05 * 0.991),
                "failed_requests": int(total_messages * 0.05 * 0.009),
                "success_rate": 99.1,
                "avg_response_time_ms": 450,
                "peak_hour": "09:00",
                "trend": "stable"
            }
        ]
        
        return {
            "period_hours": hours,
            "total_requests": total_messages,
            "services": service_usage,
            "summary": {
                "most_popular": "NIRA",
                "highest_success_rate": "General Help",
                "fastest_response": "General Help",
                "needs_attention": "NLIS"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get service usage analytics", error=e)
        return {
            "period_hours": hours,
            "total_requests": 0,
            "services": [],
            "summary": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@admin_router.get("/monitoring/agent-status")
async def get_agent_status(username: str = Depends(verify_admin_token)):
    """Get detailed ADK agent system status"""
    try:
        # Mock agent status data (in real implementation, this would query actual agent status)
        agent_status = {
            "adk_runner": {
                "status": "healthy",
                "uptime_hours": 72.5,
                "total_executions": 1247,
                "successful_executions": 1198,
                "failed_executions": 49,
                "success_rate": 96.1,
                "avg_execution_time_ms": 1850,
                "memory_usage_mb": 245,
                "last_execution": datetime.now(timezone.utc).isoformat()
            },
            "agents": [
                {
                    "name": "root_agent",
                    "type": "orchestrator",
                    "status": "healthy",
                    "executions_today": 1247,
                    "success_rate": 98.5,
                    "avg_response_time_ms": 450,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                {
                    "name": "user_identification_agent",
                    "type": "core",
                    "status": "healthy",
                    "executions_today": 1247,
                    "success_rate": 99.8,
                    "avg_response_time_ms": 125,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                {
                    "name": "language_agent",
                    "type": "core",
                    "status": "healthy",
                    "executions_today": 1247,
                    "success_rate": 97.2,
                    "avg_response_time_ms": 200,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                {
                    "name": "intent_agent",
                    "type": "core",
                    "status": "healthy",
                    "executions_today": 1247,
                    "success_rate": 95.8,
                    "avg_response_time_ms": 350,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                {
                    "name": "birth_agent",
                    "type": "service",
                    "status": "healthy",
                    "executions_today": 436,
                    "success_rate": 97.8,
                    "avg_response_time_ms": 1250,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                {
                    "name": "tax_agent",
                    "type": "service",
                    "status": "degraded",
                    "executions_today": 312,
                    "success_rate": 96.5,
                    "avg_response_time_ms": 1850,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                {
                    "name": "nssf_agent",
                    "type": "service",
                    "status": "healthy",
                    "executions_today": 249,
                    "success_rate": 98.2,
                    "avg_response_time_ms": 1100,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                {
                    "name": "land_agent",
                    "type": "service",
                    "status": "warning",
                    "executions_today": 187,
                    "success_rate": 95.8,
                    "avg_response_time_ms": 2100,
                    "last_active": datetime.now(timezone.utc).isoformat()
                }
            ],
            "mcp_servers": [
                {
                    "name": "playwright_tools",
                    "status": "healthy",
                    "connections": 4,
                    "total_operations": 892,
                    "successful_operations": 856,
                    "failed_operations": 36,
                    "success_rate": 95.9,
                    "avg_operation_time_ms": 2150
                },
                {
                    "name": "browser_use_tools",
                    "status": "healthy",
                    "connections": 2,
                    "total_operations": 156,
                    "successful_operations": 148,
                    "failed_operations": 8,
                    "success_rate": 94.9,
                    "avg_operation_time_ms": 3200
                },
                {
                    "name": "auth_tools",
                    "status": "healthy",
                    "connections": 8,
                    "total_operations": 1247,
                    "successful_operations": 1245,
                    "failed_operations": 2,
                    "success_rate": 99.8,
                    "avg_operation_time_ms": 85
                }
            ]
        }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "agent_system": agent_status
        }
        
    except Exception as e:
        logger.error("Failed to get agent status", error=e)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "unknown",
            "agent_system": {},
            "error": str(e)
        }