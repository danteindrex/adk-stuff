"""
Google Cloud Session Manager for Uganda E-Gov WhatsApp Helpdesk
Handles user sessions using Google Cloud services (Firestore, Identity Platform)
"""

import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json
import os

# Google Cloud imports
from google.cloud import firestore
from google.oauth2 import service_account
from firebase_admin import auth, credentials, initialize_app
import firebase_admin

logger = logging.getLogger(__name__)

class GoogleSessionManager:
    """Manages user sessions using Google Cloud services"""
    
    def __init__(self):
        """Initialize session manager with Google Cloud services"""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(minutes=30)  # 30 minute timeout
        
        # Initialize Firebase Admin SDK
        self._initialize_firebase()
        
        # Initialize Firestore client
        self._initialize_firestore()
        
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase app is already initialized
            firebase_admin.get_app()
            logger.info("Firebase Admin SDK already initialized")
        except ValueError:
            # Initialize Firebase Admin SDK
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if service_account_path:
                cred = credentials.Certificate(service_account_path)
                initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with service account")
            else:
                # Use default credentials
                initialize_app()
                logger.info("Firebase Admin SDK initialized with default credentials")
    
    def _initialize_firestore(self):
        """Initialize Firestore client"""
        try:
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if service_account_path:
                credentials_obj = service_account.Credentials.from_service_account_file(
                    service_account_path
                )
                self.db = firestore.Client(credentials=credentials_obj)
            else:
                self.db = firestore.Client()
            logger.info("Firestore client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            raise
    
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
        
        # Store in Firestore
        try:
            doc_ref = self.db.collection('user_sessions').document(session_id)
            doc_ref.set(session_data)
            logger.info(f"Created session {session_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to store session in Firestore: {e}")
            
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
        
        # Try to load from Firestore
        try:
            doc_ref = self.db.collection('user_sessions').document(session_id)
            doc = doc_ref.get()
            if doc.exists:
                session = doc.to_dict()
                self.active_sessions[session_id] = session
                return session
        except Exception as e:
            logger.error(f"Failed to load session from Firestore: {e}")
            
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
        
        # Try Firestore
        try:
            sessions_ref = self.db.collection('user_sessions')
            query = sessions_ref.where('user_id', '==', user_id).where('is_active', '==', True).order_by('last_activity', direction=firestore.Query.DESCENDING).limit(1)
            docs = query.stream()
            
            for doc in docs:
                session = doc.to_dict()
                self.active_sessions[session["session_id"]] = session
                return session
        except Exception as e:
            logger.error(f"Failed to load user session from Firestore: {e}")
            
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
        
        # Update Firestore
        try:
            doc_ref = self.db.collection('user_sessions').document(session_id)
            doc_ref.update({
                **updates,
                "last_activity": datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Failed to update session in Firestore: {e}")
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
    
    async def authenticate_user_with_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Authenticate user using Firebase ID token"""
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            user_info = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'phone_number': decoded_token.get('phone_number'),
                'email_verified': decoded_token.get('email_verified', False),
                'provider': decoded_token.get('firebase', {}).get('sign_in_provider')
            }
            
            logger.info(f"User authenticated successfully: {user_info['uid']}")
            return user_info
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    async def create_custom_token(self, uid: str, additional_claims: Optional[Dict] = None) -> Optional[str]:
        """Create a custom token for a user"""
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to create custom token: {e}")
            return None
    
    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user information by UID"""
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'phone_number': user_record.phone_number,
                'email_verified': user_record.email_verified,
                'disabled': user_record.disabled,
                'creation_timestamp': user_record.user_metadata.creation_timestamp,
                'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp
            }
        except Exception as e:
            logger.error(f"Failed to get user by UID: {e}")
            return None
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        active_count = len([s for s in self.active_sessions.values() if s["is_active"]])
        
        # Get total sessions from Firestore
        try:
            sessions_ref = self.db.collection('user_sessions')
            total_sessions = len(list(sessions_ref.stream()))
        except Exception as e:
            logger.error(f"Failed to get session count from Firestore: {e}")
            total_sessions = 0
        
        return {
            "total_active_sessions": active_count,
            "total_sessions_in_memory": len(self.active_sessions),
            "total_sessions_in_firestore": total_sessions,
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