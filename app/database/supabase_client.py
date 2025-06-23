"""
Supabase Database Client
Handles all database operations for the WhatsApp clone
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class User:
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_method: str = 'google'

@dataclass
class Message:
    id: str
    user_id: str
    session_id: str
    content: str
    message_type: str  # 'user' or 'ai'
    timestamp: datetime
    metadata: Optional[Dict] = None
    processing_time_ms: Optional[int] = None
    ai_model: Optional[str] = None
    intent_classification: Optional[str] = None

@dataclass
class ChatSession:
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    is_active: bool = True
    metadata: Optional[Dict] = None

class SupabaseClient:
    """Supabase database client for WhatsApp clone"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") 
        
        logger.info(f"Initializing Supabase client...")
        logger.info(f"SUPABASE_URL present: {bool(self.supabase_url)}")
        logger.info(f"SUPABASE_SERVICE_ROLE_KEY present: {bool(self.supabase_key)}")
        
        if not self.supabase_url or not self.supabase_key:
            error_msg = "Supabase credentials missing from environment variables. "
            if not self.supabase_url:
                error_msg += "SUPABASE_URL is not set. "
            if not self.supabase_key:
                error_msg += "SUPABASE_ANON_KEY is not set. "
            error_msg += "Please check your .env file."
            
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate URL format
        if not self.supabase_url.startswith(('http://', 'https://')):
            error_msg = f"Invalid SUPABASE_URL format: {self.supabase_url}. Must start with http:// or https://"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
            
            # Test connection
            try:
                # Try a simple query to test the connection
                test_result = self.client.table("whatsapp_users").select("count", count="exact").limit(0).execute()
                logger.info(f"Supabase connection test successful. Users table accessible.")
            except Exception as test_error:
                logger.warning(f"Supabase connection test failed: {test_error}")
                logger.warning("This might indicate missing tables or incorrect permissions")
                
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            logger.error("Please check your Supabase credentials and network connection")
            raise Exception(f"Supabase initialization failed: {str(e)}")
    
    async def create_or_update_user(self, user_data: Dict) -> User:
        """Create or update user in database"""
        try:
            logger.info(f"Creating/updating user: {user_data.get('email', 'unknown')}")
            
            # Validate required fields
            if not user_data.get("email") or not user_data.get("name"):
                raise ValueError("Email and name are required fields")
            
            # Check if user exists
            existing_user = self.client.table("whatsapp_users").select("*").eq("email", user_data["email"]).execute()
            
            # Prepare user record with proper data types
            user_record = {
                "email": user_data["email"],
                "name": user_data["name"],
                "avatar_url": user_data.get("picture") or user_data.get("avatar_url"),
                "phone": user_data.get("phone"),
                "login_method": user_data.get("login_method", "google"),
                "last_login": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values to avoid database issues
            user_record = {k: v for k, v in user_record.items() if v is not None}
            
            if existing_user.data and len(existing_user.data) > 0:
                # Update existing user
                logger.info(f"Updating existing user: {user_data['email']}")
                result = self.client.table("whatsapp_users").update(user_record).eq("email", user_data["email"]).execute()
                
                if not result.data or len(result.data) == 0:
                    # If update didn't return data, fetch the user
                    result = self.client.table("whatsapp_users").select("*").eq("email", user_data["email"]).execute()
                
                user_data_result = result.data[0]
                logger.info(f"Successfully updated user: {user_data['email']}")
            else:
                # Create new user
                logger.info(f"Creating new user: {user_data['email']}")
                user_record["created_at"] = datetime.now(timezone.utc).isoformat()
                
                result = self.client.table("whatsapp_users").insert(user_record).execute()
                
                if not result.data or len(result.data) == 0:
                    raise Exception("Failed to create user - no data returned from insert")
                
                user_data_result = result.data[0]
                logger.info(f"Successfully created new user: {user_data['email']}")
            
            # Create User object from result
            return User(
                id=user_data_result["id"],
                email=user_data_result["email"],
                name=user_data_result["name"],
                avatar_url=user_data_result.get("avatar_url"),
                phone=user_data_result.get("phone"),
                created_at=datetime.fromisoformat(user_data_result["created_at"].replace('Z', '+00:00')) if user_data_result.get("created_at") else None,
                last_login=datetime.fromisoformat(user_data_result["last_login"].replace('Z', '+00:00')) if user_data_result.get("last_login") else None,
                login_method=user_data_result.get("login_method", "google")
            )
            
        except Exception as e:
            logger.error(f"Error creating/updating user {user_data.get('email', 'unknown')}: {str(e)}")
            logger.error(f"User data: {user_data}")
            # Re-raise with more context
            raise Exception(f"Failed to create/update user: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            result = self.client.table("whatsapp_users").select("*").eq("id", user_id).execute()
            
            if result.data:
                data = result.data[0]
                return User(
                    id=data["id"],
                    email=data["email"],
                    name=data["name"],
                    avatar_url=data.get("avatar_url"),
                    phone=data.get("phone"),
                    created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')) if data.get("created_at") else None,
                    last_login=datetime.fromisoformat(data["last_login"].replace('Z', '+00:00')) if data.get("last_login") else None,
                    login_method=data.get("login_method", "google")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def create_chat_session(self, user_id: str, title: str = "New Chat") -> ChatSession:
        """Create a new chat session"""
        try:
            session_data = {
                "user_id": user_id,
                "title": title,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True,
                "message_count": 0,
                "metadata": {}
            }
            
            result = self.client.table("chat_sessions").insert(session_data).execute()
            
            if result.data:
                data = result.data[0]
                logger.info(f"Created new chat session: {data['id']} for user: {user_id}")
                
                return ChatSession(
                    id=data["id"],
                    user_id=data["user_id"],
                    title=data["title"],
                    created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00')),
                    message_count=data.get("message_count", 0),
                    is_active=data.get("is_active", True),
                    metadata=data.get("metadata", {})
                )
            
            raise Exception("Failed to create chat session")
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        try:
            result = self.client.table("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).limit(limit).execute()
            
            sessions = []
            for data in result.data:
                sessions.append(ChatSession(
                    id=data["id"],
                    user_id=data["user_id"],
                    title=data["title"],
                    created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00')),
                    message_count=data.get("message_count", 0),
                    is_active=data.get("is_active", True),
                    metadata=data.get("metadata", {})
                ))
            
            logger.info(f"Retrieved {len(sessions)} sessions for user: {user_id}")
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def save_message(self, user_id: str, session_id: str, content: str, message_type: str, 
                          metadata: Optional[Dict] = None, processing_time_ms: Optional[int] = None,
                          ai_model: Optional[str] = None, intent_classification: Optional[str] = None) -> Message:
        """Save a message to the database"""
        try:
            message_data = {
                "user_id": user_id,
                "session_id": session_id,
                "content": content,
                "message_type": message_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "processing_time_ms": processing_time_ms,
                "ai_model": ai_model,
                "intent_classification": intent_classification
            }
            
            result = self.client.table("messages").insert(message_data).execute()
            
            if result.data:
                data = result.data[0]
                
                # Update session message count and last activity
                await self._update_session_activity(session_id)
                
                logger.info(f"Saved message: {data['id']} for user: {user_id}")
                
                return Message(
                    id=data["id"],
                    user_id=data["user_id"],
                    session_id=data["session_id"],
                    content=data["content"],
                    message_type=data["message_type"],
                    timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')),
                    metadata=data.get("metadata", {}),
                    processing_time_ms=data.get("processing_time_ms"),
                    ai_model=data.get("ai_model"),
                    intent_classification=data.get("intent_classification")
                )
            
            raise Exception("Failed to save message")
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise
    
    async def get_session_messages(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Message]:
        """Get all messages for a chat session"""
        try:
            result = self.client.table("messages").select("*").eq("session_id", session_id).order("timestamp", desc=False).range(offset, offset + limit - 1).execute()
            
            messages = []
            for data in result.data:
                messages.append(Message(
                    id=data["id"],
                    user_id=data["user_id"],
                    session_id=data["session_id"],
                    content=data["content"],
                    message_type=data["message_type"],
                    timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')),
                    metadata=data.get("metadata", {}),
                    processing_time_ms=data.get("processing_time_ms"),
                    ai_model=data.get("ai_model"),
                    intent_classification=data.get("intent_classification")
                ))
            
            logger.info(f"Retrieved {len(messages)} messages for session: {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    async def get_user_messages(self, user_id: str, limit: int = 1000, offset: int = 0) -> List[Message]:
        """Get all messages for a user across all sessions"""
        try:
            result = self.client.table("messages").select("*").eq("user_id", user_id).order("timestamp", desc=True).range(offset, offset + limit - 1).execute()
            
            messages = []
            for data in result.data:
                messages.append(Message(
                    id=data["id"],
                    user_id=data["user_id"],
                    session_id=data["session_id"],
                    content=data["content"],
                    message_type=data["message_type"],
                    timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')),
                    metadata=data.get("metadata", {}),
                    processing_time_ms=data.get("processing_time_ms"),
                    ai_model=data.get("ai_model"),
                    intent_classification=data.get("intent_classification")
                ))
            
            logger.info(f"Retrieved {len(messages)} messages for user: {user_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting user messages: {e}")
            return []
    
    async def search_messages(self, user_id: str, query: str, limit: int = 50) -> List[Message]:
        """Search messages by content"""
        try:
            # Use Supabase full-text search
            result = self.client.table("messages").select("*").eq("user_id", user_id).text_search("content", query).order("timestamp", desc=True).limit(limit).execute()
            
            messages = []
            for data in result.data:
                messages.append(Message(
                    id=data["id"],
                    user_id=data["user_id"],
                    session_id=data["session_id"],
                    content=data["content"],
                    message_type=data["message_type"],
                    timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')),
                    metadata=data.get("metadata", {}),
                    processing_time_ms=data.get("processing_time_ms"),
                    ai_model=data.get("ai_model"),
                    intent_classification=data.get("intent_classification")
                ))
            
            logger.info(f"Found {len(messages)} messages matching query: {query}")
            return messages
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and all its messages"""
        try:
            # First delete all messages in the session
            self.client.table("messages").delete().eq("session_id", session_id).eq("user_id", user_id).execute()
            
            # Then delete the session
            result = self.client.table("chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
            
            logger.info(f"Deleted session: {session_id} for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            # Get total messages
            messages_result = self.client.table("messages").select("id", count="exact").eq("user_id", user_id).execute()
            total_messages = messages_result.count or 0
            
            # Get total sessions
            sessions_result = self.client.table("chat_sessions").select("id", count="exact").eq("user_id", user_id).execute()
            total_sessions = sessions_result.count or 0
            
            # Get user messages
            user_messages_result = self.client.table("messages").select("id", count="exact").eq("user_id", user_id).eq("message_type", "user").execute()
            user_messages = user_messages_result.count or 0
            
            # Get AI messages
            ai_messages_result = self.client.table("messages").select("id", count="exact").eq("user_id", user_id).eq("message_type", "ai").execute()
            ai_messages = ai_messages_result.count or 0
            
            # Get first message date
            first_message_result = self.client.table("messages").select("timestamp").eq("user_id", user_id).order("timestamp", desc=False).limit(1).execute()
            first_message_date = None
            if first_message_result.data:
                first_message_date = first_message_result.data[0]["timestamp"]
            
            return {
                "total_messages": total_messages,
                "total_sessions": total_sessions,
                "user_messages": user_messages,
                "ai_messages": ai_messages,
                "first_message_date": first_message_date,
                "avg_messages_per_session": round(total_messages / max(total_sessions, 1), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    async def _update_session_activity(self, session_id: str):
        """Update session last activity and message count"""
        try:
            # Get current message count
            messages_result = self.client.table("messages").select("id", count="exact").eq("session_id", session_id).execute()
            message_count = messages_result.count or 0
            
            # Update session
            self.client.table("chat_sessions").update({
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "message_count": message_count
            }).eq("id", session_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            # Total users
            users_result = self.client.table("whatsapp_users").select("id", count="exact").execute()
            total_users = users_result.count or 0
            
            # Total messages
            messages_result = self.client.table("messages").select("id", count="exact").execute()
            total_messages = messages_result.count or 0
            
            # Total sessions
            sessions_result = self.client.table("chat_sessions").select("id", count="exact").execute()
            total_sessions = sessions_result.count or 0
            
            # Active users (last 24 hours)
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            active_users_result = self.client.table("whatsapp_users").select("id", count="exact").gte("last_login", yesterday).execute()
            active_users = active_users_result.count or 0
            
            return {
                "total_users": total_users,
                "total_messages": total_messages,
                "total_sessions": total_sessions,
                "active_users_24h": active_users,
                "avg_messages_per_user": round(total_messages / max(total_users, 1), 2),
                "avg_sessions_per_user": round(total_sessions / max(total_users, 1), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}

# Global instance
supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance"""
    global supabase_client
    if supabase_client is None:
        supabase_client = SupabaseClient()
    return supabase_client