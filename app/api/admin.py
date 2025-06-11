"""
Admin dashboard API endpoints
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging_config import StructuredLogger

logger = StructuredLogger(__name__)

# Create router
admin_router = APIRouter()

# Security
security = HTTPBearer()

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

async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token"""
    # In production, implement proper JWT token verification
    # For now, use a simple token check
    if credentials.credentials != settings.JWT_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials

@admin_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(token: str = Depends(verify_admin_token)):
    """Get real-time dashboard statistics"""
    try:
        from main import supabase_client, monitoring_service
        
        if not supabase_client or not monitoring_service:
            raise HTTPException(status_code=503, detail="Services not available")
        
        # Get active sessions count
        active_sessions = await supabase_client.get_active_sessions_count()
        
        # Get today's usage stats
        today = datetime.now(timezone.utc).date().isoformat()
        daily_stats = await supabase_client.get_daily_usage_stats(today)
        
        # Get service health status
        service_health = await supabase_client.get_service_health_status()
        
        # Get error summary
        error_summary = await supabase_client.get_recent_error_summary(24)
        
        # Get popular services from actual monitoring data
        try:
            metrics_summary = await monitoring_service.get_metrics_summary()
            service_metrics = metrics_summary.get("services", {})
            
            popular_services = []
            for service, data in service_metrics.items():
                if isinstance(data, dict):
                    popular_services.append({
                        "service": service,
                        "requests": data.get("requests", 0),
                        "success_rate": data.get("success_rate", 0.0)
                    })
                else:
                    popular_services.append({
                        "service": service,
                        "requests": data if isinstance(data, int) else 0,
                        "success_rate": 0.0
                    })
            
            # Sort by requests count
            popular_services.sort(key=lambda x: x["requests"], reverse=True)
            
            # If no data available, show empty state
            if not popular_services:
                popular_services = [
                    {"service": "no_data", "requests": 0, "success_rate": 0.0}
                ]
                
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            popular_services = [
                {"service": "error_loading", "requests": 0, "success_rate": 0.0}
            ]
        
        # Get language distribution from actual usage data
        try:
            language_metrics = metrics_summary.get("languages", {})
            
            # Convert to expected format
            language_distribution = {}
            for lang, count in language_metrics.items():
                language_distribution[lang] = count if isinstance(count, int) else 0
            
            # If no data available, show empty state
            if not language_distribution:
                language_distribution = {"no_data": 0}
                
        except Exception as e:
            logger.error(f"Failed to get language metrics: {e}")
            language_distribution = {"error_loading": 0}
        
        return DashboardStats(
            active_sessions=active_sessions,
            today_interactions=daily_stats.get('total_interactions', 0),
            success_rate_24h=daily_stats.get('success_rate', 0.0),
            avg_response_time=daily_stats.get('avg_response_time', 0.0),
            service_health=service_health,
            popular_services=popular_services,
            language_distribution=language_distribution,
            error_summary=error_summary
        )
        
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard statistics")

@admin_router.get("/logs/real-time")
async def get_real_time_logs(
    limit: int = Query(default=50, le=200),
    service: Optional[str] = Query(default=None),
    token: str = Depends(verify_admin_token)
):
    """Get real-time system logs"""
    try:
        from main import supabase_client
        
        if not supabase_client:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Build query
        query = supabase_client.client.table('conversation_logs').select('*').order('timestamp', desc=True).limit(limit)
        
        if service:
            query = query.eq('agent_involved', service)
        
        result = query.execute()
        
        return {
            "logs": result.data,
            "total": len(result.data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get real-time logs", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

@admin_router.get("/analytics/usage")
async def get_usage_analytics(
    days: int = Query(default=7, le=30),
    token: str = Depends(verify_admin_token)
):
    """Get usage analytics for specified number of days"""
    try:
        from main import supabase_client
        
        if not supabase_client:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get daily stats for the specified period
        analytics_data = []
        for i in range(days):
            date = (datetime.now(timezone.utc).date() - datetime.timedelta(days=i)).isoformat()
            daily_stats = await supabase_client.get_daily_usage_stats(date)
            if daily_stats:
                analytics_data.append(daily_stats)
        
        return {
            "analytics": analytics_data,
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get usage analytics", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@admin_router.get("/services/health")
async def get_services_health(token: str = Depends(verify_admin_token)):
    """Get detailed health status of all services"""
    try:
        from main import supabase_client, agent_orchestrator
        
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "services": {}
        }
        
        # Check database
        if supabase_client:
            db_healthy = await supabase_client.health_check()
            health_status["services"]["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "last_check": datetime.now(timezone.utc).isoformat()
            }
        
        # Check agent orchestrator
        if agent_orchestrator:
            orchestrator_healthy = await agent_orchestrator.health_check()
            health_status["services"]["agent_orchestrator"] = {
                "status": "healthy" if orchestrator_healthy else "unhealthy",
                "last_check": datetime.now(timezone.utc).isoformat()
            }
        
        # Check government services
        if supabase_client:
            service_health = await supabase_client.get_service_health_status()
            health_status["services"]["government_portals"] = service_health
        
        # Determine overall status
        unhealthy_services = [
            name for name, status in health_status["services"].items()
            if isinstance(status, dict) and status.get("status") == "unhealthy"
        ]
        
        if unhealthy_services:
            health_status["overall_status"] = "degraded"
            health_status["unhealthy_services"] = unhealthy_services
        
        return health_status
        
    except Exception as e:
        logger.error("Failed to get services health", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve service health")

@admin_router.post("/system/maintenance")
async def toggle_maintenance_mode(
    config: MaintenanceConfig,
    token: str = Depends(verify_admin_token)
):
    """Enable/disable maintenance mode for specific services"""
    try:
        from main import agent_orchestrator
        
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="Agent orchestrator not available")
        
        # Toggle maintenance mode
        result = await agent_orchestrator.set_maintenance_mode(
            config.service_name,
            config.enabled,
            config.message,
            config.duration_minutes
        )
        
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
    token: str = Depends(verify_admin_token)
):
    """Get admin alerts"""
    try:
        from main import supabase_client
        
        if not supabase_client:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Build query
        query = supabase_client.client.table('admin_alerts').select('*').order('timestamp', desc=True).limit(limit)
        
        if severity:
            query = query.eq('severity', severity)
        
        result = query.execute()
        
        return {
            "alerts": result.data,
            "total": len(result.data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get admin alerts", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")

@admin_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    token: str = Depends(verify_admin_token)
):
    """Acknowledge an admin alert"""
    try:
        from main import supabase_client
        
        if not supabase_client:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Update alert as acknowledged
        result = supabase_client.client.table('admin_alerts').update({
            'acknowledged': True,
            'acknowledged_by': 'admin',  # In production, use actual admin user
            'acknowledged_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', alert_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        logger.info("Alert acknowledged", alert_id=alert_id)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "acknowledged_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to acknowledge alert", error=e, alert_id=alert_id)
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

@admin_router.get("/performance/metrics")
async def get_performance_metrics(
    hours: int = Query(default=24, le=168),  # Max 1 week
    token: str = Depends(verify_admin_token)
):
    """Get system performance metrics"""
    try:
        from main import supabase_client
        
        if not supabase_client:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get performance metrics for the specified period
        cutoff_time = datetime.now(timezone.utc).replace(hour=datetime.now().hour-hours).isoformat()
        
        result = supabase_client.client.table('system_performance').select('*').gte('timestamp', cutoff_time).order('timestamp', desc=True).execute()
        
        # Group metrics by name
        metrics_by_name = {}
        for metric in result.data:
            name = metric['metric_name']
            if name not in metrics_by_name:
                metrics_by_name[name] = []
            metrics_by_name[name].append(metric)
        
        return {
            "metrics": metrics_by_name,
            "period_hours": hours,
            "total_data_points": len(result.data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")

@admin_router.get("/users/sessions")
async def get_active_user_sessions(
    limit: int = Query(default=50, le=200),
    token: str = Depends(verify_admin_token)
):
    """Get active user sessions"""
    try:
        from main import supabase_client
        
        if not supabase_client:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get active sessions (last 30 minutes)
        cutoff_time = datetime.now(timezone.utc).replace(minute=datetime.now().minute-30).isoformat()
        
        result = supabase_client.client.table('user_sessions').select('*').gte('last_activity', cutoff_time).order('last_activity', desc=True).limit(limit).execute()
        
        return {
            "sessions": result.data,
            "total": len(result.data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get active user sessions", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user sessions")