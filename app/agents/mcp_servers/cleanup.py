"""
MCP Connection Cleanup Management
Centralized cleanup for all MCP server connections
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Global exit stacks from all MCP servers
_all_exit_stacks: List = []

def register_exit_stack(exit_stack):
    """Register an exit stack for cleanup"""
    global _all_exit_stacks
    _all_exit_stacks.append(exit_stack)
    logger.debug(f"Registered exit stack. Total: {len(_all_exit_stacks)}")

async def cleanup_mcp_connections():
    """Cleanup all MCP connections"""
    global _all_exit_stacks
    
    cleanup_count = 0
    errors = []
    
    for exit_stack in _all_exit_stacks:
        try:
            await exit_stack.aclose()
            cleanup_count += 1
        except Exception as e:
            logger.error(f"Error cleaning up MCP connection: {e}")
            errors.append(str(e))
    
    _all_exit_stacks.clear()
    
    if cleanup_count > 0:
        logger.info(f"Cleaned up {cleanup_count} MCP connections")
    
    if errors:
        logger.warning(f"Cleanup errors: {errors}")
    
    return {
        "cleaned_up": cleanup_count,
        "errors": errors
    }

def get_connection_status():
    """Get status of MCP connections"""
    return {
        "active_connections": len(_all_exit_stacks),
        "connection_types": [type(stack).__name__ for stack in _all_exit_stacks]
    }