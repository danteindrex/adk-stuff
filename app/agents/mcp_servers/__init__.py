"""
MCP Servers for Uganda E-Gov WhatsApp Helpdesk
"""

from .auth_tools import get_auth_tools
from .browser_tools import get_browser_tools
from .playwright_tools import get_playwright_tools
from .twilio_tools import get_twilio_tools  # Add this line

# Legacy import (can be removed after migration)
# from .whatsapp_tools import get_whatsapp_tools

async def cleanup_mcp_connections():
    """Clean up any MCP connections"""
    from .playwright_tools import cleanup_playwright
    await cleanup_playwright()

__all__ = [
    'get_auth_tools',
    'get_browser_tools',
    'get_playwright_tools',
    'get_twilio_tools',  # Add this line
    'cleanup_mcp_connections',
    # Legacy export (can be removed after migration)
    # 'get_whatsapp_tools',
]