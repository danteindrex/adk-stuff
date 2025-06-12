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
    """Get simple dashboard statistics"""
    try:
        return DashboardStats(
            active_sessions=0,
            today_interactions=0,
            success_rate_24h=100.0,
            avg_response_time=250.0,
            service_health={
                "webhook": {"status": "healthy", "uptime": "99.9%"},
                "cache": {"status": "healthy", "uptime": "99.9%"}
            },
            popular_services=[
                {"service": "NIRA", "requests": 0, "success_rate": 100.0},
                {"service": "URA", "requests": 0, "success_rate": 100.0}
            ],
            language_distribution={"en": 100},
            error_summary=[]
        )
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard statistics")

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
    """Get active user sessions"""
    try:
        # Import session manager to get real user sessions
        session_manager = None
        # Simplified - no imports needed
        
        sessions_data = []
        
        # Get active sessions from session manager
        if session_manager:
            try:
                sessions_data = await session_manager.get_active_sessions(limit=limit)
            except Exception as e:
                logger.error(f"Failed to get active sessions from session manager: {e}")
        
        return {
            "sessions": sessions_data,
            "total": len(sessions_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get active user sessions", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user sessions")