"""
Session Manager for Uganda E-Gov WhatsApp Helpdesk
Handles user sessions and conversation state management
"""

import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions for the WhatsApp helpdesk"""
    
    def __init__(self, supabase_client):
        """Initialize session manager with Supabase client"""
        self.supabase_client = supabase_client
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(minutes=30)  # 30 minute timeout
        
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
        
        # Store in memory
        self.active_sessions[session_id] = session_data
        
        # Store in database
        try:
            await self.supabase_client.insert_session(session_data)
            logger.info(f"Created session {session_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to store session in database: {e}")
            
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID"""
        # Check memory first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Check if session is expired
            last_activity = datetime.fromisoformat(session["last_activity"])
            if datetime.now() - last_activity > self.session_timeout:
                await self.end_session(session_id)
                return None
                
            return session
        
        # Try to load from database
        try:
            session = await self.supabase_client.get_session(session_id)
            if session:
                self.active_sessions[session_id] = session
                return session
        except Exception as e:
            logger.error(f"Failed to load session from database: {e}")
            
        return None
    
    async def get_user_active_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent active session for a user"""
        # Check memory first
        user_sessions = [
            session for session in self.active_sessions.values()
            if session["user_id"] == user_id and session["is_active"]
        ]
        
        if user_sessions:
            # Return the most recent session
            return max(user_sessions, key=lambda x: x["last_activity"])
        
        # Try database
        try:
            session = await self.supabase_client.get_user_active_session(user_id)
            if session:
                self.active_sessions[session["session_id"]] = session
                return session
        except Exception as e:
            logger.error(f"Failed to load user session from database: {e}")
            
        return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        if session_id not in self.active_sessions:
            session = await self.get_session(session_id)
            if not session:
                return False
        
        # Update memory
        self.active_sessions[session_id].update(updates)
        self.active_sessions[session_id]["last_activity"] = datetime.now().isoformat()
        
        # Update database
        try:
            await self.supabase_client.update_session(session_id, updates)
            return True
        except Exception as e:
            logger.error(f"Failed to update session in database: {e}")
            return False
    
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
        return await self.update_session(session_id, {
            "conversation_history": session["conversation_history"]
        })
    
    async def set_current_agent(self, session_id: str, agent_name: str) -> bool:
        """Set the current agent handling the session"""
        return await self.update_session(session_id, {"current_agent": agent_name})
    
    async def end_session(self, session_id: str) -> bool:
        """End a session"""
        updates = {
            "is_active": False,
            "ended_at": datetime.now().isoformat()
        }
        
        success = await self.update_session(session_id, updates)
        
        # Remove from memory
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            
        logger.info(f"Ended session {session_id}")
        return success
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            last_activity = datetime.fromisoformat(session["last_activity"])
            if current_time - last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.end_session(session_id)
            
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        active_count = len([s for s in self.active_sessions.values() if s["is_active"]])
        
        return {
            "total_active_sessions": active_count,
            "total_sessions_in_memory": len(self.active_sessions),
            "session_timeout_minutes": self.session_timeout.total_seconds() / 60
        }
    
    async def start_cleanup_task(self):
        """Start background task to clean up expired sessions"""
        async def cleanup_loop():
            while True:
                try:
                    await self.cleanup_expired_sessions()
                    await asyncio.sleep(300)  # Clean up every 5 minutes
                except Exception as e:
                    logger.error(f"Error in session cleanup: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        asyncio.create_task(cleanup_loop())
        logger.info("Started session cleanup background task")