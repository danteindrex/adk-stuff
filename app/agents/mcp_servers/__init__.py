"""
MCP Servers for Uganda E-Gov WhatsApp Helpdesk
"""
from .auth_tools import get_auth_tools
from .browser_use_tools import get_browser_tools
from .playwright_tools import get_playwright_mcp_tools, get_combined_automation_tools
from .internal_mcp_tools import get_all_internal_tools, cleanup_internal_tools

# Legacy import (can be removed after migration)
# from .whatsapp_tools import get_whatsapp_tools

async def cleanup_mcp_connections():
    """Clean up any MCP connections"""
    try:
        from .playwright_tools import cleanup_playwright
        await cleanup_playwright()
    except Exception as e:
        print(f"Error cleaning up playwright: {e}")
    
    try:
        await cleanup_internal_tools()
    except Exception as e:
        print(f"Error cleaning up internal tools: {e}")

__all__ = [
    'get_auth_tools',
    'get_browser_tools',
    'get_playwright_mcp_tools',
    'get_combined_automation_tools',
    'get_twilio_tools',
    'get_all_internal_tools',
    'cleanup_mcp_connections',
    # Legacy export (can be removed after migration)
    # 'get_whatsapp_tools',
]