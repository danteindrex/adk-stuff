"""
Server-Side Cache Service
Simple in-memory cache with 2-day expiration and automatic cleanup
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import threading

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with expiration tracking"""
    data: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0

class ServerCacheService:
    """
    Server-side cache service with automatic expiration and cleanup
    
    Features:
    - 2-day expiration for all entries
    - Automatic cleanup of expired entries
    - Thread-safe operations
    - Memory usage monitoring
    - Statistics tracking
    """
    
    def __init__(self, default_ttl_hours: int = 48):
        """
        Initialize cache service
        
        Args:
            default_ttl_hours: Default time-to-live in hours (default: 48 hours = 2 days)
        """
        self.default_ttl = default_ttl_hours * 3600  # Convert to seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._cleanup_task = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "cleanups": 0,
            "expired_entries": 0
        }
        
        logger.info(f"Server cache initialized with {default_ttl_hours}h TTL")
    
    async def start_cleanup_task(self):
        """Start the automatic cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cache cleanup task started")
    
    async def stop_cleanup_task(self):
        """Stop the automatic cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Cache cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Background task to clean up expired entries"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired"""
        return time.time() > entry.expires_at
    
    def _create_key(self, namespace: str, key: str) -> str:
        """Create a namespaced cache key"""
        return f"{namespace}:{key}"
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get a value from cache
        
        Args:
            key: Cache key
            namespace: Cache namespace (default: "default")
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._create_key(namespace, key)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            if self._is_expired(entry):
                # Remove expired entry
                del self._cache[cache_key]
                self._stats["misses"] += 1
                self._stats["expired_entries"] += 1
                logger.debug(f"Cache entry expired: {cache_key}")
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = time.time()
            self._stats["hits"] += 1
            
            return entry.data
    
    async def set(self, key: str, value: Any, namespace: str = "default", ttl_hours: Optional[int] = None) -> bool:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace (default: "default")
            ttl_hours: Time-to-live in hours (default: use service default)
            
        Returns:
            True if successful
        """
        cache_key = self._create_key(namespace, key)
        ttl = (ttl_hours * 3600) if ttl_hours else self.default_ttl
        
        now = time.time()
        entry = CacheEntry(
            data=value,
            created_at=now,
            expires_at=now + ttl,
            last_accessed=now
        )
        
        with self._lock:
            self._cache[cache_key] = entry
            self._stats["sets"] += 1
        
        logger.debug(f"Cache entry set: {cache_key} (expires in {ttl/3600:.1f}h)")
        return True
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete a value from cache
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if key existed and was deleted
        """
        cache_key = self._create_key(namespace, key)
        
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                self._stats["deletes"] += 1
                logger.debug(f"Cache entry deleted: {cache_key}")
                return True
            return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        """
        Check if a key exists in cache (and is not expired)
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if key exists and is not expired
        """
        value = await self.get(key, namespace)
        return value is not None
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = []
        
        with self._lock:
            for cache_key, entry in self._cache.items():
                if now > entry.expires_at:
                    expired_keys.append(cache_key)
            
            for cache_key in expired_keys:
                del self._cache[cache_key]
            
            self._stats["cleanups"] += 1
            self._stats["expired_entries"] += len(expired_keys)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    async def clear_namespace(self, namespace: str) -> int:
        """
        Clear all entries in a specific namespace
        
        Args:
            namespace: Namespace to clear
            
        Returns:
            Number of entries removed
        """
        prefix = f"{namespace}:"
        keys_to_remove = []
        
        with self._lock:
            for cache_key in self._cache.keys():
                if cache_key.startswith(prefix):
                    keys_to_remove.append(cache_key)
            
            for cache_key in keys_to_remove:
                del self._cache[cache_key]
        
        logger.info(f"Cleared {len(keys_to_remove)} entries from namespace '{namespace}'")
        return len(keys_to_remove)
    
    async def clear_all(self) -> int:
        """
        Clear all cache entries
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
        
        logger.info(f"Cleared all {count} cache entries")
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_entries = len(self._cache)
            expired_count = 0
            oldest_entry = None
            newest_entry = None
            total_size_estimate = 0
            
            now = time.time()
            for entry in self._cache.values():
                if now > entry.expires_at:
                    expired_count += 1
                
                if oldest_entry is None or entry.created_at < oldest_entry:
                    oldest_entry = entry.created_at
                
                if newest_entry is None or entry.created_at > newest_entry:
                    newest_entry = entry.created_at
                
                # Rough size estimate
                try:
                    total_size_estimate += len(json.dumps(entry.data, default=str))
                except:
                    total_size_estimate += 1000  # Fallback estimate
            
            hit_rate = 0
            if self._stats["hits"] + self._stats["misses"] > 0:
                hit_rate = self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
            
            return {
                "total_entries": total_entries,
                "expired_entries_pending": expired_count,
                "hit_rate": hit_rate,
                "size_estimate_bytes": total_size_estimate,
                "oldest_entry_age_hours": (now - oldest_entry) / 3600 if oldest_entry else 0,
                "newest_entry_age_hours": (now - newest_entry) / 3600 if newest_entry else 0,
                "default_ttl_hours": self.default_ttl / 3600,
                **self._stats
            }
    
    async def get_entries_by_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """
        Get all entries in a specific namespace with metadata
        
        Args:
            namespace: Namespace to query
            
        Returns:
            List of entry information
        """
        prefix = f"{namespace}:"
        entries = []
        now = time.time()
        
        with self._lock:
            for cache_key, entry in self._cache.items():
                if cache_key.startswith(prefix):
                    key_without_namespace = cache_key[len(prefix):]
                    entries.append({
                        "key": key_without_namespace,
                        "created_at": datetime.fromtimestamp(entry.created_at).isoformat(),
                        "expires_at": datetime.fromtimestamp(entry.expires_at).isoformat(),
                        "expires_in_hours": (entry.expires_at - now) / 3600,
                        "access_count": entry.access_count,
                        "last_accessed": datetime.fromtimestamp(entry.last_accessed).isoformat() if entry.last_accessed else None,
                        "is_expired": now > entry.expires_at,
                        "data_type": type(entry.data).__name__
                    })
        
        return sorted(entries, key=lambda x: x["created_at"], reverse=True)

# Global cache service instance
cache_service = ServerCacheService()

# Convenience functions for common operations
async def get_cached(key: str, namespace: str = "default") -> Optional[Any]:
    """Get a value from cache"""
    return await cache_service.get(key, namespace)

async def set_cached(key: str, value: Any, namespace: str = "default", ttl_hours: Optional[int] = None) -> bool:
    """Set a value in cache"""
    return await cache_service.set(key, value, namespace, ttl_hours)

async def delete_cached(key: str, namespace: str = "default") -> bool:
    """Delete a value from cache"""
    return await cache_service.delete(key, namespace)

async def clear_cache_namespace(namespace: str) -> int:
    """Clear all entries in a namespace"""
    return await cache_service.clear_namespace(namespace)