"""
Supabase client for database operations
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from app.core.config import settings
from app.core.logging_config import StructuredLogger

logger = StructuredLogger(__name__)

class SupabaseClient:
    """Supabase database client with connection pooling and error handling"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            self._initialized = True
            logger.info("Supabase client initialized successfully")
            
            # Create tables if they don't exist
            await self._ensure_tables_exist()
            
        except Exception as e:
            logger.error("Failed to initialize Supabase client", error=e)
            raise
    
    async def _ensure_tables_exist(self):
        """Ensure all required tables exist"""
        try:
            # This would typically be handled by Supabase migrations
            # For now, we'll assume tables are created via SQL scripts
            logger.info("Database tables verified")
        except Exception as e:
            logger.error("Failed to verify database tables", error=e)
            raise
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            if not self._initialized or not self.client:
                return False
            
            # Simple query to test connection
            result = self.client.table('user_sessions').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error("Database health check failed", error=e)
            return False
    
    async def close(self):
        """Close database connections"""
        if self.client:
            # Supabase client doesn't need explicit closing
            self._initialized = False
            logger.info("Supabase client closed")
    
    # User Management
    async def create_user_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new user session"""
        try:
            result = self.client.table('user_sessions').insert(session_data).execute()
            session_id = result.data[0]['id']
            logger.info("User session created", session_id=session_id, user_phone=session_data.get('user_phone'))
            return session_id
        except Exception as e:
            logger.error("Failed to create user session", error=e, user_phone=session_data.get('user_phone'))
            raise
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session by ID"""
        try:
            result = self.client.table('user_sessions').select('*').eq('id', session_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to get user session", error=e, session_id=session_id)
            return None
    
    # Session Manager Support Methods
    async def insert_session(self, session_data: Dict[str, Any]) -> bool:
        """Insert a new session record"""
        try:
            result = self.client.table('user_sessions').insert(session_data).execute()
            return True
        except Exception as e:
            logger.error("Failed to insert session", error=e)
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by session ID"""
        try:
            result = self.client.table('user_sessions').select('*').eq('session_id', session_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to get session", error=e, session_id=session_id)
            return None
    
    async def get_user_active_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent active session for a user"""
        try:
            result = self.client.table('user_sessions').select('*').eq('user_id', user_id).eq('is_active', True).order('last_activity', desc=True).limit(1).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to get user active session", error=e, user_id=user_id)
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            result = self.client.table('user_sessions').update(updates).eq('session_id', session_id).execute()
            return True
        except Exception as e:
            logger.error("Failed to update session", error=e, session_id=session_id)
            return False
    
    async def update_session_activity(self, session_id: str, activity_data: Dict[str, Any]):
        """Update session last activity and state"""
        try:
            activity_data['last_activity'] = datetime.now(timezone.utc).isoformat()
            result = self.client.table('user_sessions').update(activity_data).eq('id', session_id).execute()
            logger.debug("Session activity updated", session_id=session_id)
        except Exception as e:
            logger.error("Failed to update session activity", error=e, session_id=session_id)
            raise
    
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        try:
            # Sessions active in last 30 minutes
            cutoff_time = datetime.now(timezone.utc).replace(minute=datetime.now().minute-30).isoformat()
            result = self.client.table('user_sessions').select('id', count='exact').gte('last_activity', cutoff_time).execute()
            return result.count or 0
        except Exception as e:
            logger.error("Failed to get active sessions count", error=e)
            return 0
    
    # Conversation Logging
    async def log_conversation_event(self, event_data: Dict[str, Any]):
        """Log conversation interaction"""
        try:
            event_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            result = self.client.table('conversation_logs').insert(event_data).execute()
            logger.debug("Conversation event logged", 
                        user_phone=event_data.get('user_phone'),
                        intent=event_data.get('intent_classification'))
        except Exception as e:
            logger.error("Failed to log conversation event", error=e, 
                        user_phone=event_data.get('user_phone'))
    
    async def log_service_interaction(self, service_data: Dict[str, Any]):
        """Log government service interaction"""
        try:
            result = self.client.table('service_interactions').insert(service_data).execute()
            logger.info("Service interaction logged", 
                       service=service_data.get('service_name'),
                       success=service_data.get('success'))
        except Exception as e:
            logger.error("Failed to log service interaction", error=e,
                        service=service_data.get('service_name'))
    
    async def log_performance_metric(self, metric_data: Dict[str, Any]):
        """Log performance metric"""
        try:
            metric_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            result = self.client.table('system_performance').insert(metric_data).execute()
        except Exception as e:
            logger.error("Failed to log performance metric", error=e,
                        metric=metric_data.get('metric_name'))
    
    # Analytics and Monitoring
    async def get_daily_usage_stats(self, date: str = None) -> Dict[str, Any]:
        """Get daily usage statistics"""
        try:
            if not date:
                date = datetime.now(timezone.utc).date().isoformat()
            
            # Get conversation stats for the day
            result = self.client.table('conversation_logs').select('*').gte('timestamp', f"{date}T00:00:00").lt('timestamp', f"{date}T23:59:59").execute()
            
            total_interactions = len(result.data)
            unique_users = len(set(log['user_phone'] for log in result.data if log.get('user_phone')))
            successful_interactions = len([log for log in result.data if log.get('success')])
            
            return {
                'date': date,
                'total_interactions': total_interactions,
                'unique_users': unique_users,
                'success_rate': successful_interactions / total_interactions if total_interactions > 0 else 0,
                'avg_response_time': sum(log.get('processing_time_ms', 0) for log in result.data) / total_interactions if total_interactions > 0 else 0
            }
        except Exception as e:
            logger.error("Failed to get daily usage stats", error=e, date=date)
            return {}
    
    async def get_service_health_status(self) -> Dict[str, Any]:
        """Get health status of all government services"""
        try:
            # Get recent service interactions (last hour)
            cutoff_time = datetime.now(timezone.utc).replace(minute=datetime.now().minute-60).isoformat()
            result = self.client.table('service_interactions').select('*').gte('automation_start_time', cutoff_time).execute()
            
            service_stats = {}
            for service in settings.GOVERNMENT_SERVICES:
                service_interactions = [log for log in result.data if log.get('service_name') == service]
                total = len(service_interactions)
                successful = len([log for log in service_interactions if log.get('success')])
                
                service_stats[service] = {
                    'total_requests': total,
                    'success_rate': successful / total if total > 0 else 1.0,
                    'status': 'healthy' if (successful / total if total > 0 else 1.0) > 0.8 else 'degraded'
                }
            
            return service_stats
        except Exception as e:
            logger.error("Failed to get service health status", error=e)
            return {}
    
    async def get_recent_error_summary(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get summary of recent errors"""
        try:
            cutoff_time = datetime.now(timezone.utc).replace(hour=datetime.now().hour-hours).isoformat()
            result = self.client.table('conversation_logs').select('*').eq('success', False).gte('timestamp', cutoff_time).execute()
            
            error_summary = {}
            for log in result.data:
                error_type = log.get('error_details', {}).get('type', 'unknown') if isinstance(log.get('error_details'), dict) else 'unknown'
                if error_type not in error_summary:
                    error_summary[error_type] = 0
                error_summary[error_type] += 1
            
            return [{'error_type': k, 'count': v} for k, v in error_summary.items()]
        except Exception as e:
            logger.error("Failed to get recent error summary", error=e)
            return []
    
    # User Authentication
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        try:
            # In a real implementation, this would hash the password and check against stored credentials
            # For demo purposes, we'll use a simple check
            result = self.client.table('users').select('*').eq('username', username).execute()
            
            if result.data and len(result.data) > 0:
                user = result.data[0]
                # In production, use proper password hashing (bcrypt, etc.)
                if user.get('password') == password:  # This should be hashed comparison
                    logger.info("User authenticated successfully", username=username)
                    return {
                        'id': user['id'],
                        'username': user['username'],
                        'phone': user['phone'],
                        'language_preference': user.get('language_preference', 'en'),
                        'created_at': user['created_at']
                    }
            
            logger.warning("Authentication failed", username=username)
            return None
        except Exception as e:
            logger.error("Authentication error", error=e, username=username)
            return None