"""
Google Authentication Tools using Firebase Admin SDK
"""

import logging
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def get_google_auth_tools():
    """Get Google Cloud authentication tools using Firebase Admin SDK"""
    
    def authenticate_user(id_token: str, tool_context=None) -> dict:
        """Authenticate user using Firebase ID token"""
        try:
            import firebase_admin
            from firebase_admin import auth
            
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            return {
                "status": "success",
                "user": {
                    "uid": decoded_token["uid"],
                    "email": decoded_token.get("email"),
                    "name": decoded_token.get("name"),
                    "picture": decoded_token.get("picture"),
                    "email_verified": decoded_token.get("email_verified", False),
                    "provider": decoded_token.get("firebase", {}).get("sign_in_provider")
                }
            }
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def create_custom_token(uid: str, additional_claims: dict = None, tool_context=None) -> dict:
        """Create a custom token for a user"""
        try:
            import firebase_admin
            from firebase_admin import auth
            
            custom_token = auth.create_custom_token(uid, additional_claims)
            return {
                "status": "success",
                "token": custom_token.decode('utf-8')
            }
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_user_info(uid: str, tool_context=None) -> dict:
        """Get user information by UID"""
        try:
            import firebase_admin
            from firebase_admin import auth
            
            user_record = auth.get_user(uid)
            return {
                "status": "success",
                "user": {
                    "uid": user_record.uid,
                    "email": user_record.email,
                    "display_name": user_record.display_name,
                    "photo_url": user_record.photo_url,
                    "phone_number": user_record.phone_number,
                    "email_verified": user_record.email_verified,
                    "disabled": user_record.disabled,
                    "creation_timestamp": user_record.user_metadata.creation_timestamp,
                    "last_sign_in_timestamp": user_record.user_metadata.last_sign_in_timestamp
                }
            }
        except Exception as e:
            logger.error(f"User info retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def verify_session_token(session_cookie: str, tool_context=None) -> dict:
        """Verify a session cookie"""
        try:
            import firebase_admin
            from firebase_admin import auth
            
            decoded_claims = auth.verify_session_cookie(session_cookie)
            return {
                "status": "success",
                "claims": decoded_claims
            }
        except Exception as e:
            logger.error(f"Session verification failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def update_user_profile(uid: str, profile_data: dict, tool_context=None) -> dict:
        """Update user profile information"""
        try:
            import firebase_admin
            from firebase_admin import auth
            
            # Filter allowed profile fields
            allowed_fields = ['display_name', 'email', 'phone_number', 'photo_url', 'disabled']
            update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
            
            auth.update_user(uid, **update_data)
            return {
                "status": "success",
                "message": "User profile updated successfully"
            }
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def delete_user(uid: str, tool_context=None) -> dict:
        """Delete a user account"""
        try:
            import firebase_admin
            from firebase_admin import auth
            
            auth.delete_user(uid)
            return {
                "status": "success",
                "message": "User deleted successfully"
            }
        except Exception as e:
            logger.error(f"User deletion failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create function tools
    auth_tools = [
        FunctionTool(authenticate_user),
        FunctionTool(create_custom_token),
        FunctionTool(get_user_info),
        FunctionTool(verify_session_token),
        FunctionTool(update_user_profile),
        FunctionTool(delete_user)
    ]
    
    logger.info(f"Created {len(auth_tools)} Google authentication tools")
    return auth_tools