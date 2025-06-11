"""
FAQ Cache MCP Tools
Tools for managing FAQ cache operations in the agent system
"""

import logging
from typing import Dict, Any, Optional, List
from google.adk.tools import FunctionTool
from app.services.faq_cache_service import faq_service

logger = logging.getLogger(__name__)

async def get_faq_cache_tools():
    """Get FAQ cache management tools"""
    
    def check_faq_cache(
        question: str,
        language: str = "en",
        service_type: str = "general",
        tool_context=None
    ) -> dict:
        """
        Check if there's a cached answer for a question
        
        Args:
            question: User's question
            language: Language code (en, lg, luo, nyn)
            service_type: Service type (nira, ura, nssf, nlis, general)
        """
        try:
            import asyncio
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cached_response = loop.run_until_complete(
                    faq_service.get_cached_response(question, language, service_type)
                )
            finally:
                loop.close()
            
            if cached_response:
                return {
                    "status": "cache_hit",
                    "cached": True,
                    "answer": cached_response["answer"],
                    "original_question": cached_response["original_question"],
                    "similarity_score": cached_response.get("similarity_score", 1.0),
                    "language": cached_response["language"],
                    "service_type": cached_response["service_type"],
                    "access_count": cached_response.get("access_count", 0)
                }
            else:
                return {
                    "status": "cache_miss",
                    "cached": False,
                    "message": "No cached answer found for this question"
                }
                
        except Exception as e:
            logger.error(f"Error checking FAQ cache: {e}")
            return {
                "status": "error",
                "cached": False,
                "error": str(e)
            }
    
    def cache_faq_response(
        question: str,
        answer: str,
        language: str = "en",
        service_type: str = "general",
        tool_context=None
    ) -> dict:
        """
        Cache a question-answer pair for future use
        
        Args:
            question: User's question
            answer: Agent's response
            language: Language code
            service_type: Service type
        """
        try:
            import asyncio
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                success = loop.run_until_complete(
                    faq_service.cache_response(question, answer, language, service_type)
                )
            finally:
                loop.close()
            
            if success:
                return {
                    "status": "success",
                    "cached": True,
                    "message": f"Successfully cached answer for {service_type} service in {language}"
                }
            else:
                return {
                    "status": "skipped",
                    "cached": False,
                    "message": "Response not suitable for caching (too short, error, or personal info)"
                }
                
        except Exception as e:
            logger.error(f"Error caching FAQ response: {e}")
            return {
                "status": "error",
                "cached": False,
                "error": str(e)
            }
    
    def get_cache_statistics(tool_context=None) -> dict:
        """Get FAQ cache statistics and health information"""
        try:
            import asyncio
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                stats = loop.run_until_complete(faq_service.get_cache_statistics())
            finally:
                loop.close()
            
            return {
                "status": "success",
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def clear_service_cache(
        service_type: str,
        tool_context=None
    ) -> dict:
        """
        Clear cache entries for a specific service
        
        Args:
            service_type: Service to clear cache for (nira, ura, nssf, nlis, general)
        """
        try:
            import asyncio
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cleared_count = loop.run_until_complete(
                    faq_service.clear_service_cache(service_type)
                )
            finally:
                loop.close()
            
            return {
                "status": "success",
                "cleared_entries": cleared_count,
                "service_type": service_type,
                "message": f"Cleared {cleared_count} cache entries for {service_type} service"
            }
            
        except Exception as e:
            logger.error(f"Error clearing service cache: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def clear_language_cache(
        language: str,
        tool_context=None
    ) -> dict:
        """
        Clear cache entries for a specific language
        
        Args:
            language: Language to clear cache for (en, lg, luo, nyn)
        """
        try:
            import asyncio
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cleared_count = loop.run_until_complete(
                    faq_service.clear_language_cache(language)
                )
            finally:
                loop.close()
            
            return {
                "status": "success",
                "cleared_entries": cleared_count,
                "language": language,
                "message": f"Cleared {cleared_count} cache entries for {language} language"
            }
            
        except Exception as e:
            logger.error(f"Error clearing language cache: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def health_check_cache(tool_context=None) -> dict:
        """Perform health check on FAQ cache system"""
        try:
            import asyncio
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                health_status = loop.run_until_complete(faq_service.health_check())
            finally:
                loop.close()
            
            return {
                "status": "success",
                "health_check": health_status
            }
            
        except Exception as e:
            logger.error(f"Error performing cache health check: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_popular_questions(
        language: str = "en",
        service_type: str = None,
        limit: int = 10,
        tool_context=None
    ) -> dict:
        """
        Get popular questions from cache
        
        Args:
            language: Language code
            service_type: Optional service type filter
            limit: Maximum number of questions
        """
        try:
            import asyncio
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                popular_questions = loop.run_until_complete(
                    faq_service.get_popular_questions(language, service_type, limit)
                )
            finally:
                loop.close()
            
            return {
                "status": "success",
                "popular_questions": popular_questions,
                "language": language,
                "service_type": service_type,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting popular questions: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create FAQ cache tools
    faq_tools = [
        FunctionTool(check_faq_cache),
        FunctionTool(cache_faq_response),
        FunctionTool(get_cache_statistics),
        FunctionTool(clear_service_cache),
        FunctionTool(clear_language_cache),
        FunctionTool(health_check_cache),
        FunctionTool(get_popular_questions)
    ]
    
    logger.info(f"Created {len(faq_tools)} FAQ cache tools")
    return faq_tools