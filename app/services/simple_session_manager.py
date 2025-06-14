"""
Simple Session Manager for Uganda E-Gov WhatsApp Helpdesk
Uses server-side cache with 2-day expiration instead of Firebase
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import json

from app.services.server_cache_service import cache_service

logger = logging.getLogger(__name__)

class SimpleSessionManager:
    """Manages user sessions using server-side cache"""
    
    def __init__(self):
        """Initialize session manager with server cache"""
        self.session_timeout = timedelta(hours=2)  # 2 hour timeout for active sessions
        self.namespace = "sessions"
        self.user_namespace = "user_sessions"
        
    async def create_session(self, user_id: str, initial_data: Optional[Dict] = None) -> str:
        """Create a new session for a user"""
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "conversation_history": [],
            "current_agent": None,
            "user_context": initial_data or {},
            "is_active": True
        }
        
        # Store session data (will expire in 2 days by default)
        await cache_service.set(session_id, session_data, self.namespace)
        
        # Also store user's latest session reference
        await cache_service.set(f"latest_{user_id}", session_id, self.user_namespace)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID"""
        session = await cache_service.get(session_id, self.namespace)
        
        if session:
            # Check if session is expired based on activity timeout
            last_activity = datetime.fromisoformat(session["last_activity"])
            if datetime.now() - last_activity > self.session_timeout:
                await self.end_session(session_id)
                return None
                
            return session
            
        return None
    
    async def get_user_active_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent active session for a user"""
        # Get user's latest session reference
        latest_session_id = await cache_service.get(f"latest_{user_id}", self.user_namespace)
        
        if latest_session_id:
            session = await self.get_session(latest_session_id)
            if session and session["is_active"]:
                return session
        
        return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        session = await cache_service.get(session_id, self.namespace)
        if not session:
            return False
        
        # Update session data
        session.update(updates)
        session["last_activity"] = datetime.now().isoformat()
        
        # Store updated session
        success = await cache_service.set(session_id, session, self.namespace)
        
        if success:
            logger.debug(f"Updated session {session_id}")
        
        return success
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add a message to the conversation history"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,  # "user" or "assistant"
            "content": content,
            "metadata": metadata or {}
        }
        
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session["conversation_history"].append(message)
        
        # Keep only last 50 messages to prevent memory bloat
        if len(session["conversation_history"]) > 50:
            session["conversation_history"] = session["conversation_history"][-50:]
        
        return await self.update_session(session_id, {
            "conversation_history": session["conversation_history"]
        })
    
    async def set_current_agent(self, session_id: str, agent_name: str) -> bool:
        """Set the current agent handling the session"""
        return await self.update_session(session_id, {"current_agent": agent_name})
    
    async def end_session(self, session_id: str) -> bool:
        """End a session"""
        session = await cache_service.get(session_id, self.namespace)
        if not session:
            return False
        
        # Mark session as inactive
        session["is_active"] = False
        session["ended_at"] = datetime.now().isoformat()
        
        # Store updated session
        success = await cache_service.set(session_id, session, self.namespace)
        
        logger.info(f"Ended session {session_id}")
        return success
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions - handled automatically by cache TTL"""
        # The server cache automatically handles expiration after 2 days
        # We just need to clean up sessions that are inactive due to timeout
        
        try:
            # Get all session entries
            session_entries = await cache_service.get_entries_by_namespace(self.namespace)
            expired_count = 0
            
            for entry_info in session_entries:
                try:
                    session = await cache_service.get(entry_info["key"], self.namespace)
                    if session and session.get("is_active", False):
                        last_activity = datetime.fromisoformat(session["last_activity"])
                        if datetime.now() - last_activity > self.session_timeout:
                            await self.end_session(session["session_id"])
                            expired_count += 1
                except Exception as e:
                    logger.error(f"Error checking session {entry_info['key']}: {e}")
                    continue
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
                
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            # Get all session entries
            session_entries = await cache_service.get_entries_by_namespace(self.namespace)
            user_entries = await cache_service.get_entries_by_namespace(self.user_namespace)
            
            active_count = 0
            total_sessions = len(session_entries)
            
            # Count active sessions
            for entry_info in session_entries:
                try:
                    session = await cache_service.get(entry_info["key"], self.namespace)
                    if session and session.get("is_active", False):
                        # Check if not timed out
                        last_activity = datetime.fromisoformat(session["last_activity"])
                        if datetime.now() - last_activity <= self.session_timeout:
                            active_count += 1
                except:
                    continue
            
            return {
                "total_active_sessions": active_count,
                "total_sessions": total_sessions,
                "unique_users": len(user_entries),
                "session_timeout_hours": self.session_timeout.total_seconds() / 3600,
                "cache_ttl_hours": 48  # Server cache default TTL
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {
                "total_active_sessions": 0,
                "total_sessions": 0,
                "unique_users": 0,
                "error": str(e)
            }
    
    async def get_active_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of active sessions"""
        try:
            session_entries = await cache_service.get_entries_by_namespace(self.namespace)
            active_sessions = []
            
            for entry_info in session_entries:
                try:
                    session = await cache_service.get(entry_info["key"], self.namespace)
                    if session and session.get("is_active", False):
                        # Check if not timed out
                        last_activity = datetime.fromisoformat(session["last_activity"])
                        if datetime.now() - last_activity <= self.session_timeout:
                            # Add cache info
                            session["cache_expires_in_hours"] = entry_info.get("expires_in_hours", 0)
                            active_sessions.append(session)
                except:
                    continue
            
            # Sort by last activity (most recent first)
            active_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
            
            return active_sessions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    async def get_user_conversation_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        session = await self.get_user_active_session(user_id)
        if session:
            history = session.get("conversation_history", [])
            return history[-limit:] if len(history) > limit else history
        return []
    
    async def clear_user_sessions(self, user_id: str) -> int:
        """Clear all sessions for a specific user"""
        try:
            cleared_count = 0
            session_entries = await cache_service.get_entries_by_namespace(self.namespace)
            
            for entry_info in session_entries:
                try:
                    session = await cache_service.get(entry_info["key"], self.namespace)
                    if session and session.get("user_id") == user_id:
                        await cache_service.delete(entry_info["key"], self.namespace)
                        cleared_count += 1
                except:
                    continue
            
            # Also clear user's latest session reference
            await cache_service.delete(f"latest_{user_id}", self.user_namespace)
            
            logger.info(f"Cleared {cleared_count} sessions for user {user_id}")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing user sessions: {e}")
            return 0
    
    async def start_cleanup_task(self):
        """Start background task to clean up expired sessions"""
        async def cleanup_loop():
            while True:
                try:
                    await self.cleanup_expired_sessions()
                    await asyncio.sleep(1800)  # Clean up every 30 minutes
                except Exception as e:
                    logger.error(f"Error in session cleanup: {e}")
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying
        
        asyncio.create_task(cleanup_loop())
        logger.info("Started session cleanup background task")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the session manager"""
        try:
            # Test basic operations
            test_user_id = "test_health_check_user"
            
            # Create test session
            session_id = await self.create_session(test_user_id, {"test": True})
            
            # Retrieve session
            session = await self.get_session(session_id)
            
            # Add test message
            message_added = await self.add_message(session_id, "user", "test message")
            
            # Clean up test session
            await self.end_session(session_id)
            
            return {
                "status": "healthy",
                "healthy": True,
                "session_create": session_id is not None,
                "session_retrieve": session is not None,
                "message_add": message_added,
                "message": "Session manager is operational"
            }
            
        except Exception as e:
            logger.error(f"Session manager health check failed: {e}")
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e),
                "message": "Session manager health check failed"
            }

# Global session manager instance
session_manager = SimpleSessionManager()