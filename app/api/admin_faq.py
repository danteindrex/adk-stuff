"""
FAQ Cache Admin Endpoints
Admin endpoints for managing FAQ cache
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.api.admin import verify_admin_token
from app.core.logging_config import StructuredLogger

logger = StructuredLogger(__name__)

# Create FAQ admin router
faq_admin_router = APIRouter()

@faq_admin_router.get("/cache/stats")
async def get_faq_cache_stats(token: str = Depends(verify_admin_token)):
    """Get FAQ cache statistics"""
    try:
        from app.services.faq_cache_service import faq_service
        
        stats = await faq_service.get_cache_statistics()
        
        return {
            "success": True,
            "cache_stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get FAQ cache stats", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve FAQ cache statistics")

@faq_admin_router.post("/cache/clear")
async def clear_faq_cache(
    service_type: Optional[str] = None,
    language: Optional[str] = None,
    token: str = Depends(verify_admin_token)
):
    """Clear FAQ cache with optional filters"""
    try:
        from app.services.faq_cache_service import faq_service
        
        if service_type:
            cleared_count = await faq_service.clear_service_cache(service_type)
            message = f"Cleared {cleared_count} cache entries for service: {service_type}"
        elif language:
            cleared_count = await faq_service.clear_language_cache(language)
            message = f"Cleared {cleared_count} cache entries for language: {language}"
        else:
            cleared_count = 0
            message = "Specify service_type or language parameter to clear cache"
        
        return {
            "success": True,
            "cleared_entries": cleared_count,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to clear FAQ cache", error=e)
        raise HTTPException(status_code=500, detail="Failed to clear FAQ cache")

@faq_admin_router.get("/popular")
async def get_popular_questions(
    language: str = "en",
    service_type: Optional[str] = None,
    limit: int = 20,
    token: str = Depends(verify_admin_token)
):
    """Get popular questions from FAQ cache"""
    try:
        from app.services.faq_cache_service import faq_service
        
        popular_questions = await faq_service.get_popular_questions(
            language=language,
            service_type=service_type,
            limit=limit
        )
        
        return {
            "success": True,
            "popular_questions": popular_questions,
            "language": language,
            "service_type": service_type,
            "limit": limit,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get popular questions", error=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve popular questions")

@faq_admin_router.get("/cache/health")
async def check_faq_cache_health(token: str = Depends(verify_admin_token)):
    """Check FAQ cache system health"""
    try:
        from app.services.faq_cache_service import faq_service
        
        health_status = await faq_service.health_check()
        
        return {
            "success": True,
            "health_status": health_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to check FAQ cache health", error=e)
        raise HTTPException(status_code=500, detail="Failed to check FAQ cache health")