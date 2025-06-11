"""
FAQ Cache Service
Integrates Firebase FAQ caching with the agent system
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.database.firebase_client import faq_cache, FAQEntry
from app.core.config import settings

logger = logging.getLogger(__name__)

class FAQCacheService:
    """Service for managing FAQ cache operations"""
    
    def __init__(self):
        self.cache = faq_cache
        self.enabled = settings.FAQ_CACHE_ENABLED
    
    async def get_cached_response(
        self, 
        user_question: str, 
        language: str = "en", 
        service_type: str = "general"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a user question
        
        Args:
            user_question: The user's question
            language: Language code (en, lg, luo, nyn)
            service_type: Type of service (nira, ura, nssf, nlis, general)
            
        Returns:
            Dictionary with cached response or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            faq_entry = await self.cache.get_cached_answer(
                question=user_question,
                language=language,
                service_type=service_type
            )
            
            if faq_entry:
                return {
                    "answer": faq_entry.answer,
                    "original_question": faq_entry.question,
                    "language": faq_entry.language,
                    "service_type": faq_entry.service_type,
                    "similarity_score": getattr(faq_entry, 'similarity_score', 1.0),
                    "cache_hit": True,
                    "access_count": faq_entry.access_count,
                    "last_updated": faq_entry.updated_at.isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")
            return None
    
    async def cache_response(
        self,
        user_question: str,
        agent_response: str,
        language: str = "en",
        service_type: str = "general"
    ) -> bool:
        """
        Cache a question-response pair
        
        Args:
            user_question: The user's question
            agent_response: The agent's response
            language: Language code
            service_type: Type of service
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Only cache successful, informative responses
            if self._should_cache_response(agent_response):
                success = await self.cache.cache_answer(
                    question=user_question,
                    answer=agent_response,
                    language=language,
                    service_type=service_type
                )
                
                if success:
                    logger.info(f"Cached response for service: {service_type}, language: {language}")
                
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
            return False
    
    def _should_cache_response(self, response: str) -> bool:
        """
        Determine if a response should be cached
        
        Args:
            response: The agent response to evaluate
            
        Returns:
            True if response should be cached
        """
        # Don't cache very short responses
        if len(response.strip()) < 20:
            return False
        
        # Don't cache error messages
        error_indicators = [
            "error", "failed", "unable to", "sorry", "apologize",
            "try again", "not available", "system error"
        ]
        
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in error_indicators):
            return False
        
        # Don't cache responses with personal information
        personal_indicators = [
            "your account", "your balance", "your status",
            "your application", "your payment"
        ]
        
        if any(indicator in response_lower for indicator in personal_indicators):
            return False
        
        return True
    
    async def get_popular_questions(
        self, 
        language: str = "en", 
        service_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get popular questions from cache
        
        Args:
            language: Language code
            service_type: Optional service type filter
            limit: Maximum number of questions to return
            
        Returns:
            List of popular questions with metadata
        """
        try:
            # This would require additional Firestore queries
            # For now, return empty list - can be enhanced later
            return []
            
        except Exception as e:
            logger.error(f"Error getting popular questions: {e}")
            return []
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            stats = await self.cache.get_cache_stats()
            
            # Add service-level statistics
            stats.update({
                "enabled": self.enabled,
                "service_name": "FAQ Cache Service",
                "last_check": datetime.utcnow().isoformat()
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {
                "enabled": self.enabled,
                "status": "error",
                "error": str(e)
            }
    
    async def clear_service_cache(self, service_type: str) -> int:
        """Clear cache for a specific service"""
        try:
            cleared_count = await self.cache.clear_cache(service_type=service_type)
            logger.info(f"Cleared {cleared_count} cache entries for service: {service_type}")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing service cache: {e}")
            return 0
    
    async def clear_language_cache(self, language: str) -> int:
        """Clear cache for a specific language"""
        try:
            cleared_count = await self.cache.clear_cache(language=language)
            logger.info(f"Cleared {cleared_count} cache entries for language: {language}")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing language cache: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the FAQ cache service"""
        try:
            if not self.enabled:
                return {
                    "status": "disabled",
                    "healthy": True,
                    "message": "FAQ caching is disabled"
                }
            
            # Test basic cache operations
            test_question = "test_health_check_question"
            test_answer = "test_health_check_answer"
            
            # Try to cache and retrieve
            cache_success = await self.cache_response(
                test_question, test_answer, "en", "test"
            )
            
            if cache_success:
                cached_response = await self.get_cached_response(
                    test_question, "en", "test"
                )
                
                # Clean up test entry
                await self.cache.clear_cache(service_type="test")
                
                return {
                    "status": "healthy",
                    "healthy": True,
                    "cache_write": cache_success,
                    "cache_read": cached_response is not None,
                    "message": "FAQ cache service is operational"
                }
            else:
                return {
                    "status": "degraded",
                    "healthy": False,
                    "message": "Cache write operation failed"
                }
                
        except Exception as e:
            logger.error(f"FAQ cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e),
                "message": "FAQ cache service health check failed"
            }

# Global FAQ cache service instance
faq_service = FAQCacheService()