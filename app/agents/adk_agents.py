"""
Uganda E-Gov WhatsApp Helpdesk - ADK Multi-Agent System
This file defines the root agent and all sub-agents using Google Agent Development Kit (ADK),
with MCP server integration for Supabase, Playwright, WhatsApp, and more.
"""

import os
import asyncio
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.sessions import InMemorySessionService

# Global variables to store MCP toolsets and exit stacks
_supabase_toolset = None
_playwright_toolset = None
_whatsapp_toolset = None
_exit_stacks = []

async def get_google_auth_tools():
    """Get Google Cloud authentication tools using Firebase Admin SDK"""
    from google.adk.tools import FunctionTool
    
    # Create custom authentication functions using Firebase Admin SDK
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
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create function tools
    auth_tools = [
        FunctionTool(authenticate_user),
        FunctionTool(create_custom_token),
        FunctionTool(get_user_info),
        FunctionTool(verify_session_token)
    ]
    
    return auth_tools

async def get_playwright_tools():
    """Get Playwright MCP tools"""
    global _playwright_toolset
    if _playwright_toolset is None:
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@microsoft/playwright-mcp@latest"
                ]
            )
        )
        _playwright_toolset = tools
        _exit_stacks.append(exit_stack)
    return _playwright_toolset

async def get_whatsapp_tools():
    """Get WhatsApp MCP tools"""
    global _whatsapp_toolset
    if _whatsapp_toolset is None:
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@lharries/whatsapp-mcp@latest"
                ]
            )
        )
        _whatsapp_toolset = tools
        _exit_stacks.append(exit_stack)
    return _whatsapp_toolset

async def cleanup_mcp_connections():
    """Cleanup all MCP connections"""
    global _exit_stacks
    for exit_stack in _exit_stacks:
        await exit_stack.aclose()
    _exit_stacks.clear()

# Async agent creation functions
async def create_auth_agent():
    """Create authentication agent with Google Identity Platform tools"""
    google_auth_tools = await get_google_auth_tools()
    return LlmAgent(
        name="auth_agent",
        model="gemini-2.0-flash",
        instruction="""You are an authentication agent that handles user authentication and session management using Google Identity Platform.
        
        You can:
        - Authenticate users using Google OAuth
        - Manage user sessions and tokens
        - Verify user identity and permissions
        - Handle user registration and login flows
        - Manage user profiles and account information
        
        Use the Google Identity Platform tools to securely authenticate users and manage their sessions.
        Always ensure proper security practices and user privacy protection.""",
        description="Handles user authentication and session management using Google Identity Platform.",
        tools=google_auth_tools
    )

async def create_language_agent():
    """Create language detection agent"""
    return LlmAgent(
        name="language_agent",
        model="gemini-2.0-flash",
        instruction="Detect and translate user language (English, Luganda, Luo, Runyoro).",
        description="Detects and translates user language.",
    )

async def create_intent_agent():
    """Create intent classification agent"""
    return LlmAgent(
        name="intent_agent",
        model="gemini-2.0-flash",
        instruction="Classify user intent and route to the correct service agent.",
        description="Classifies user intent.",
    )

async def create_birth_agent():
    """Create birth certificate agent with Playwright tools"""
    playwright_tools = await get_playwright_tools()
    return LlmAgent(
        name="birth_agent",
        model="gemini-2.0-flash",
        instruction="Automate NIRA portal to check birth certificate status using Playwright MCP tools.",
        description="Handles birth certificate status checks.",
        tools=playwright_tools
    )

async def create_tax_agent():
    """Create tax status agent with Playwright tools"""
    playwright_tools = await get_playwright_tools()
    return LlmAgent(
        name="tax_agent",
        model="gemini-2.0-flash",
        instruction="Automate URA portal to check tax status using Playwright MCP tools.",
        description="Handles tax status checks.",
        tools=playwright_tools
    )

async def create_nssf_agent():
    """Create NSSF balance agent with Playwright tools"""
    playwright_tools = await get_playwright_tools()
    return LlmAgent(
        name="nssf_agent",
        model="gemini-2.0-flash",
        instruction="Automate NSSF portal to check balance using Playwright MCP tools.",
        description="Handles NSSF balance checks.",
        tools=playwright_tools
    )

async def create_land_agent():
    """Create land verification agent with Playwright tools"""
    playwright_tools = await get_playwright_tools()
    return LlmAgent(
        name="land_agent",
        model="gemini-2.0-flash",
        instruction="Automate NLIS portal to verify land ownership using Playwright MCP tools.",
        description="Handles land verification.",
        tools=playwright_tools
    )

async def create_form_agent():
    """Create form processing agent"""
    return LlmAgent(
        name="form_agent",
        model="gemini-2.0-flash",
        instruction="Guide users through government form submission and PDF generation.",
        description="Handles government form processing.",
    )

async def create_help_agent():
    """Create help and guidance agent"""
    return LlmAgent(
        name="help_agent",
        model="gemini-2.0-flash",
        instruction="Provide contextual help and guidance to users.",
        description="Provides help and guidance.",
    )

async def create_service_dispatcher():
    """Create service dispatcher with all service agents"""
    birth_agent = await create_birth_agent()
    tax_agent = await create_tax_agent()
    nssf_agent = await create_nssf_agent()
    land_agent = await create_land_agent()
    form_agent = await create_form_agent()
    help_agent = await create_help_agent()
    
    return SequentialAgent(
        name="service_dispatcher",
        description="Routes requests to the correct service agent.",
        sub_agents=[birth_agent, tax_agent, nssf_agent, land_agent, form_agent, help_agent]
    )

async def create_root_agent():
    """Create the root agent with all sub-agents"""
    auth_agent = await create_auth_agent()
    language_agent = await create_language_agent()
    intent_agent = await create_intent_agent()
    service_dispatcher = await create_service_dispatcher()
    
    return SequentialAgent(
        name="uganda_egov_root",
        description="Root agent for Uganda E-Gov WhatsApp Helpdesk.",
        sub_agents=[auth_agent, language_agent, intent_agent, service_dispatcher]
    )

# For backward compatibility, create a synchronous wrapper
def get_root_agent():
    """Synchronous wrapper to get the root agent"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(create_root_agent())
    finally:
        loop.close()

# Create the root agent instance
root_agent = None  # Will be initialized asynchronously
