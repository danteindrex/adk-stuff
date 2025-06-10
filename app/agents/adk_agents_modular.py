"""
Uganda E-Gov WhatsApp Helpdesk - Modular ADK Multi-Agent System
Modular architecture with enhanced browser automation and fallback mechanisms
"""

import logging
import asyncio
from google.adk.agents import SequentialAgent

# Import modular components
from .mcp_servers import cleanup_mcp_connections
from .core_agents import (
    create_auth_agent,
    create_language_agent,
    create_intent_agent,
    create_help_agent
)
from .service_agents import create_service_dispatcher

logger = logging.getLogger(__name__)

async def create_root_agent():
    """Create the root agent with all sub-agents using modular architecture"""
    try:
        logger.info("Creating modular ADK agent system...")
        
        # Create core agents
        logger.info("Creating core agents...")
        auth_agent = await create_auth_agent()
        language_agent = await create_language_agent()
        intent_agent = await create_intent_agent()
        help_agent = await create_help_agent()
        
        # Create service dispatcher (which creates all service agents)
        logger.info("Creating service dispatcher...")
        service_dispatcher = await create_service_dispatcher()
        
        # Create root sequential agent
        root_agent = SequentialAgent(
            name="uganda_egov_root",
            description="""Root agent for Uganda E-Gov WhatsApp Helpdesk with modular architecture.
            
            This agent coordinates the entire multi-agent system for providing government services
            through WhatsApp. It manages the flow between different specialized agents:
            
            Core Agents:
            1. Authentication Agent - Handles user authentication and session management
            2. Language Agent - Detects language and provides translation services
            3. Intent Agent - Classifies user intent and routes requests
            4. Help Agent - Provides general help and guidance
            
            Service Agents (via Service Dispatcher):
            1. Birth Agent - NIRA birth certificate services with enhanced automation
            2. Tax Agent - URA tax status and payment services
            3. NSSF Agent - NSSF pension and contribution services
            4. Land Agent - NLIS land ownership and title services
            5. Form Agent - Government form completion and submission
            
            Enhanced Features:
            - Intelligent browser automation with Playwright MCP and Browser-Use fallback
            - Multi-language support (English, Luganda, Luo, Runyoro)
            - Comprehensive error handling and recovery mechanisms
            - Real-time government portal automation
            - Secure session management with Firebase
            - Contextual help and guidance system
            
            The system automatically routes user requests to the appropriate agent based on
            intent classification and provides seamless service delivery through WhatsApp.
            """,
            sub_agents=[auth_agent, language_agent, intent_agent, service_dispatcher, help_agent]
        )
        
        logger.info("Modular ADK agent system created successfully")
        return root_agent
        
    except Exception as e:
        logger.error(f"Failed to create modular root agent: {e}")
        raise

# Backward compatibility functions
async def create_auth_agent_compat():
    """Backward compatibility wrapper for auth agent"""
    return await create_auth_agent()

async def create_language_agent_compat():
    """Backward compatibility wrapper for language agent"""
    return await create_language_agent()

async def create_intent_agent_compat():
    """Backward compatibility wrapper for intent agent"""
    return await create_intent_agent()

async def create_birth_agent_compat():
    """Backward compatibility wrapper for birth agent"""
    from .service_agents.birth_agent import create_birth_agent
    return await create_birth_agent()

async def create_tax_agent_compat():
    """Backward compatibility wrapper for tax agent"""
    from .service_agents.tax_agent import create_tax_agent
    return await create_tax_agent()

async def create_nssf_agent_compat():
    """Backward compatibility wrapper for NSSF agent"""
    from .service_agents.nssf_agent import create_nssf_agent
    return await create_nssf_agent()

async def create_land_agent_compat():
    """Backward compatibility wrapper for land agent"""
    from .service_agents.land_agent import create_land_agent
    return await create_land_agent()

async def create_form_agent_compat():
    """Backward compatibility wrapper for form agent"""
    from .service_agents.form_agent import create_form_agent
    return await create_form_agent()

async def create_help_agent_compat():
    """Backward compatibility wrapper for help agent"""
    return await create_help_agent()

async def create_service_dispatcher_compat():
    """Backward compatibility wrapper for service dispatcher"""
    return await create_service_dispatcher()

# Export main functions
__all__ = [
    'create_root_agent',
    'cleanup_mcp_connections',
    # Backward compatibility
    'create_auth_agent_compat',
    'create_language_agent_compat',
    'create_intent_agent_compat',
    'create_birth_agent_compat',
    'create_tax_agent_compat',
    'create_nssf_agent_compat',
    'create_land_agent_compat',
    'create_form_agent_compat',
    'create_help_agent_compat',
    'create_service_dispatcher_compat'
]