"""
FAQ Cache Service
Server-side FAQ caching with 2-day expiration
"""

import logging
import asyncio
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.server_cache_service import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class FAQCacheService:
    """Service for managing FAQ cache operations using server-side cache"""
    
    def __init__(self):
        self.cache = cache_service
        self.enabled = getattr(settings, 'FAQ_CACHE_ENABLED', True)
        self.namespace = "faq"
        self.stats_namespace = "faq_stats"
    
    def _create_question_key(self, user_question: str, language: str, service_type: str) -> str:
        """Create a unique key for a question"""
        # Normalize the question for better cache hits
        normalized_question = user_question.lower().strip()
        key_string = f"{normalized_question}:{language}:{service_type}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _create_stats_key(self, service_type: str, language: str) -> str:
        """Create a key for statistics tracking"""
        return f"stats:{service_type}:{language}"
    
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
            question_key = self._create_question_key(user_question, language, service_type)
            cached_entry = await self.cache.get(question_key, self.namespace)
            
            if cached_entry:
                # Update access statistics
                await self._update_access_stats(service_type, language)
                
                # Update access count for this specific entry
                cached_entry["access_count"] = cached_entry.get("access_count", 0) + 1
                cached_entry["last_accessed"] = datetime.utcnow().isoformat()
                
                # Re-cache with updated stats
                await self.cache.set(question_key, cached_entry, self.namespace)
                
                return {
                    "answer": cached_entry["answer"],
                    "original_question": cached_entry["question"],
                    "language": cached_entry["language"],
                    "service_type": cached_entry["service_type"],
                    "similarity_score": 1.0,  # Exact match
                    "cache_hit": True,
                    "access_count": cached_entry["access_count"],
                    "last_updated": cached_entry["created_at"],
                    "last_accessed": cached_entry["last_accessed"]
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
                question_key = self._create_question_key(user_question, language, service_type)
                
                cache_entry = {
                    "question": user_question,
                    "answer": agent_response,
                    "language": language,
                    "service_type": service_type,
                    "created_at": datetime.utcnow().isoformat(),
                    "access_count": 0,
                    "last_accessed": None
                }
                
                success = await self.cache.set(question_key, cache_entry, self.namespace)
                
                if success:
                    # Update cache statistics
                    await self._update_cache_stats(service_type, language)
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
    
    async def _update_access_stats(self, service_type: str, language: str):
        """Update access statistics"""
        try:
            stats_key = self._create_stats_key(service_type, language)
            current_stats = await self.cache.get(stats_key, self.stats_namespace) or {
                "cache_hits": 0,
                "last_hit": None
            }
            
            current_stats["cache_hits"] += 1
            current_stats["last_hit"] = datetime.utcnow().isoformat()
            
            await self.cache.set(stats_key, current_stats, self.stats_namespace)
        except Exception as e:
            logger.error(f"Error updating access stats: {e}")
    
    async def _update_cache_stats(self, service_type: str, language: str):
        """Update cache creation statistics"""
        try:
            stats_key = self._create_stats_key(service_type, language)
            current_stats = await self.cache.get(stats_key, self.stats_namespace) or {
                "cache_hits": 0,
                "cached_responses": 0,
                "last_hit": None,
                "last_cache": None
            }
            
            current_stats["cached_responses"] = current_stats.get("cached_responses", 0) + 1
            current_stats["last_cache"] = datetime.utcnow().isoformat()
            
            await self.cache.set(stats_key, current_stats, self.stats_namespace)
        except Exception as e:
            logger.error(f"Error updating cache stats: {e}")
    
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
            # Get all FAQ entries
            faq_entries = await self.cache.get_entries_by_namespace(self.namespace)
            
            # Filter and sort by access count
            filtered_entries = []
            for entry_info in faq_entries:
                try:
                    # Get the actual entry data
                    entry_data = await self.cache.get(entry_info["key"], self.namespace)
                    if entry_data:
                        # Apply filters
                        if language and entry_data.get("language") != language:
                            continue
                        if service_type and entry_data.get("service_type") != service_type:
                            continue
                        
                        filtered_entries.append({
                            "question": entry_data["question"],
                            "answer": entry_data["answer"],
                            "language": entry_data["language"],
                            "service_type": entry_data["service_type"],
                            "access_count": entry_data.get("access_count", 0),
                            "created_at": entry_data["created_at"],
                            "last_accessed": entry_data.get("last_accessed")
                        })
                except Exception as e:
                    logger.error(f"Error processing entry {entry_info['key']}: {e}")
                    continue
            
            # Sort by access count and return top entries
            filtered_entries.sort(key=lambda x: x["access_count"], reverse=True)
            return filtered_entries[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular questions: {e}")
            return []
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            # Get overall cache stats
            cache_stats = await self.cache.get_stats()
            
            # Get FAQ-specific stats
            faq_entries = await self.cache.get_entries_by_namespace(self.namespace)
            stats_entries = await self.cache.get_entries_by_namespace(self.stats_namespace)
            
            # Calculate FAQ-specific metrics
            total_faq_entries = len(faq_entries)
            total_access_count = 0
            languages = set()
            service_types = set()
            
            for entry_info in faq_entries:
                try:
                    entry_data = await self.cache.get(entry_info["key"], self.namespace)
                    if entry_data:
                        total_access_count += entry_data.get("access_count", 0)
                        languages.add(entry_data.get("language", "unknown"))
                        service_types.add(entry_data.get("service_type", "unknown"))
                except:
                    continue
            
            return {
                "enabled": self.enabled,
                "service_name": "FAQ Cache Service",
                "last_check": datetime.utcnow().isoformat(),
                "faq_entries": total_faq_entries,
                "total_access_count": total_access_count,
                "languages": list(languages),
                "service_types": list(service_types),
                "cache_stats": cache_stats,
                "stats_entries": len(stats_entries)
            }
            
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
            cleared_count = 0
            faq_entries = await self.cache.get_entries_by_namespace(self.namespace)
            
            for entry_info in faq_entries:
                try:
                    entry_data = await self.cache.get(entry_info["key"], self.namespace)
                    if entry_data and entry_data.get("service_type") == service_type:
                        await self.cache.delete(entry_info["key"], self.namespace)
                        cleared_count += 1
                except:
                    continue
            
            logger.info(f"Cleared {cleared_count} cache entries for service: {service_type}")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing service cache: {e}")
            return 0
    
    async def clear_language_cache(self, language: str) -> int:
        """Clear cache for a specific language"""
        try:
            cleared_count = 0
            faq_entries = await self.cache.get_entries_by_namespace(self.namespace)
            
            for entry_info in faq_entries:
                try:
                    entry_data = await self.cache.get(entry_info["key"], self.namespace)
                    if entry_data and entry_data.get("language") == language:
                        await self.cache.delete(entry_info["key"], self.namespace)
                        cleared_count += 1
                except:
                    continue
            
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
                await self.clear_service_cache("test")
                
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