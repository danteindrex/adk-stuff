"""
MCP Servers for Uganda E-Gov WhatsApp Helpdesk
Modular MCP server integrations
"""

from .auth_tools import get_google_auth_tools
from .playwright_tools import get_playwright_tools, get_browser_use_tools
from .browser_use_tools import get_browser_use_tools as get_browser_use_mcp_tools, get_smart_automation_tools
from .whatsapp_tools import get_whatsapp_tools
from .faq_cache_tools import get_faq_cache_tools
from .cleanup import cleanup_mcp_connections

__all__ = [
    'get_google_auth_tools',
    'get_playwright_tools', 
    'get_browser_use_tools',
    'get_browser_use_mcp_tools',
    'get_smart_automation_tools',
    'get_whatsapp_tools',
    'get_faq_cache_tools',
    'cleanup_mcp_connections'
]