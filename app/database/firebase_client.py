"""
Firebase Client Stub
Provides a simple in-memory implementation when Firebase is not available
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FAQEntry:
    """FAQ Entry data structure"""
    question: str
    answer: str
    language: str = "en"
    service_type: str = "general"
    access_count: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    similarity_score: float = 1.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class InMemoryFAQCache:
    """In-memory FAQ cache implementation"""
    
    def __init__(self):
        self.cache: Dict[str, FAQEntry] = {}
        self.enabled = True
        logger.info("Initialized in-memory FAQ cache")
    
    def _generate_key(self, question: str, language: str, service_type: str) -> str:
        """Generate cache key"""
        return f"{service_type}:{language}:{question.lower().strip()}"
    
    async def get_cached_answer(
        self, 
        question: str, 
        language: str = "en", 
        service_type: str = "general"
    ) -> Optional[FAQEntry]:
        """Get cached answer for a question"""
        try:
            key = self._generate_key(question, language, service_type)
            
            if key in self.cache:
                entry = self.cache[key]
                entry.access_count += 1
                entry.updated_at = datetime.utcnow()
                logger.debug(f"Cache hit for question: {question[:50]}...")
                return entry
            
            # Try fuzzy matching (simple implementation)
            for cached_key, entry in self.cache.items():
                if (entry.language == language and 
                    entry.service_type == service_type and
                    self._is_similar_question(question, entry.question)):
                    entry.access_count += 1
                    entry.updated_at = datetime.utcnow()
                    entry.similarity_score = 0.8  # Approximate similarity
                    logger.debug(f"Fuzzy cache hit for question: {question[:50]}...")
                    return entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached answer: {e}")
            return None
    
    def _is_similar_question(self, q1: str, q2: str) -> bool:
        """Simple similarity check"""
        q1_words = set(q1.lower().split())
        q2_words = set(q2.lower().split())
        
        if len(q1_words) == 0 or len(q2_words) == 0:
            return False
        
        intersection = q1_words.intersection(q2_words)
        union = q1_words.union(q2_words)
        
        similarity = len(intersection) / len(union)
        return similarity > 0.6  # 60% similarity threshold
    
    async def cache_answer(
        self,
        question: str,
        answer: str,
        language: str = "en",
        service_type: str = "general"
    ) -> bool:
        """Cache a question-answer pair"""
        try:
            key = self._generate_key(question, language, service_type)
            
            if key in self.cache:
                # Update existing entry
                entry = self.cache[key]
                entry.answer = answer
                entry.updated_at = datetime.utcnow()
            else:
                # Create new entry
                entry = FAQEntry(
                    question=question,
                    answer=answer,
                    language=language,
                    service_type=service_type
                )
                self.cache[key] = entry
            
            logger.debug(f"Cached answer for question: {question[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error caching answer: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_entries = len(self.cache)
            
            # Count by service type
            service_counts = {}
            language_counts = {}
            total_access_count = 0
            
            for entry in self.cache.values():
                service_counts[entry.service_type] = service_counts.get(entry.service_type, 0) + 1
                language_counts[entry.language] = language_counts.get(entry.language, 0) + 1
                total_access_count += entry.access_count
            
            return {
                "total_entries": total_entries,
                "total_access_count": total_access_count,
                "service_breakdown": service_counts,
                "language_breakdown": language_counts,
                "cache_type": "in_memory",
                "enabled": self.enabled,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "total_entries": 0,
                "error": str(e),
                "cache_type": "in_memory"
            }
    
    async def clear_cache(
        self, 
        service_type: Optional[str] = None, 
        language: Optional[str] = None
    ) -> int:
        """Clear cache entries"""
        try:
            if service_type is None and language is None:
                # Clear all
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cleared all {count} cache entries")
                return count
            
            # Clear specific entries
            keys_to_remove = []
            for key, entry in self.cache.items():
                should_remove = True
                
                if service_type and entry.service_type != service_type:
                    should_remove = False
                
                if language and entry.language != language:
                    should_remove = False
                
                if should_remove:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
            
            logger.info(f"Cleared {len(keys_to_remove)} cache entries")
            return len(keys_to_remove)
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

# Global FAQ cache instance
faq_cache = InMemoryFAQCache()