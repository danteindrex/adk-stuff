"""
Authentication Agent
Handles user authentication and session management using Google Identity Platform
"""

import logging
from google.adk.agents import LlmAgent
from ..mcp_servers.auth_tools import get_google_auth_tools

logger = logging.getLogger(__name__)

async def create_auth_agent():
    """Create authentication agent with Google Identity Platform tools"""
    try:
        google_auth_tools = await get_google_auth_tools()
        
        agent = LlmAgent(
            name="auth_agent",
            model="gemini-2.0-flash",
            instruction="""You are an authentication agent that handles user authentication and session management using Google Identity Platform.
            
            Your responsibilities:
            - Authenticate users using Google OAuth and Firebase ID tokens
            - Manage user sessions and tokens securely
            - Verify user identity and permissions
            - Handle user registration and login flows
            - Manage user profiles and account information
            - Ensure proper security practices and user privacy protection
            
            Available tools:
            - authenticate_user: Verify Firebase ID tokens
            - create_custom_token: Create custom authentication tokens
            - get_user_info: Retrieve user information by UID
            - verify_session_token: Verify session cookies
            - update_user_profile: Update user profile information
            - delete_user: Delete user accounts (admin only)
            
            Security guidelines:
            - Always validate tokens before processing requests
            - Never expose sensitive user information
            - Log authentication attempts for security monitoring
            - Handle authentication failures gracefully
            - Implement proper session timeout mechanisms
            
            When a user wants to authenticate:
            1. Request their ID token or credentials
            2. Use authenticate_user tool to verify the token
            3. Create a session if authentication succeeds
            4. Provide appropriate feedback to the user
            
            For session management:
            1. Verify existing sessions using verify_session_token
            2. Create new sessions with create_custom_token
            3. Update user profiles when requested
            4. Handle logout by invalidating sessions
            """,
            description="Handles user authentication and session management using Google Identity Platform.",
            tools=google_auth_tools
        )
        
        logger.info("Authentication agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create authentication agent: {e}")
        raise