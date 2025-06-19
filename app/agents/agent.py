"""
Uganda E-Gov WhatsApp Helpdesk - Modular ADK Multi-Agent System
Modular architecture with enhanced browser automation and fallback mechanisms
"""

import logging
import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# Import modular components
from app.agents.mcp_servers import cleanup_mcp_connections
from app.agents.mcp_servers.internal_mcp_tools import get_all_internal_tools
from .core_agents import (
    create_auth_agent,
    create_language_agent,
    create_intent_agent,
    create_help_agent
)
from .service_agents import create_service_dispatcher

logger = logging.getLogger(__name__)

async def create_root_agent():
    """Create the intelligent root agent with direct user input processing"""
    try:
        logger.info("Creating intelligent root agent with direct input processing...")
        
        # Get core automation tools only
        automation_tools = await get_all_internal_tools()
        
        # Use only automation tools - LLM handles everything else
        all_tools = automation_tools
        
        # Create intelligent root LLM agent
        root_agent = LlmAgent(
            name="uganda_egov_assistant",
            model="gemini-2.0-flash",
            instruction="""You are the Uganda E-Government WhatsApp Assistant. You help citizens access government services by navigating websites for them.

🎯 YOUR MISSION:
Help Ugandan citizens access government services through web automation. You can navigate any government website to get information or complete tasks.

🛠️ YOUR TOOLS:

You have TWO powerful automation tools:

1. **Playwright MCP Tools** (Primary) - Professional web automation
   - Navigate to websites, click buttons, fill forms, extract data
   - Fast and reliable for standard web interactions

2. **Browser-Use AI Tools** (Fallback) - Intelligent web automation  
   - AI-powered navigation when Playwright fails
   - Can handle complex or unusual website layouts

🌐 GOVERNMENT SERVICES YOU CAN ACCESS:

**NIRA (Birth Certificates)**: https://www.nira.go.ug
- Check status with reference numbers (format: NIRA/YYYY/NNNNNN)
- Navigate to status check pages, enter reference numbers
- Extract status, collection info, requirements

**URA (Tax Services)**: https://www.ura.go.ug  
- Check tax status with TIN numbers (10 digits)
- Navigate to taxpayer portals, login systems
- Extract balance, compliance status, payment history

**NSSF (Pension Services)**: https://www.nssfug.org
- Check balances with membership numbers (8-12 digits)
- Navigate member portals, contribution pages
- Extract balance, contribution history, benefits

**NLIS (Land Services)**: https://nlis.go.ug
- Verify land ownership with plot numbers or GPS coordinates
- Navigate land search systems, verification pages
- Extract ownership details, title information

🎯 HOW TO HELP:

1. **UNDERSTAND** what the user needs
2. **NAVIGATE** to the appropriate government website
3. **AUTOMATE** the process (forms, searches, data extraction)
4. **EXTRACT** the information they need
5. **EXPLAIN** the results in simple terms

🔍 EXAMPLE WORKFLOWS:

**Birth Certificate Check:**
- User: "Check my birth certificate NIRA/2023/123456"
- You: Navigate to NIRA website → Find status check page → Enter reference → Extract status → Report results

**Tax Status Check:**
- User: "My TIN is 1234567890, what's my tax status?"
- You: Navigate to URA website → Find taxpayer portal → Enter TIN → Extract status → Report results

**NSSF Balance:**
- User: "Check my NSSF balance, membership 12345678"
- You: Navigate to NSSF website → Find member portal → Enter membership → Extract balance → Report results

**Land Verification:**
- User: "Verify ownership of Plot 123, Block 45"
- You: Navigate to NLIS website → Find search page → Enter plot details → Extract ownership → Report results

🎯 KEY PRINCIPLES:

- **Be Autonomous**: Navigate websites yourself, don't ask users to do it
- **Be Thorough**: Extract all relevant information from the websites
- **Be Clear**: Explain what you found in simple, helpful terms
- **Be Helpful**: Provide office locations, contact info, next steps
- **Handle Errors**: If one tool fails, try the other; if websites are down, explain alternatives

🌍 LANGUAGES: English, Luganda, Luo, Runyoro

Your goal: Be the bridge between citizens and government websites - navigate the complexity for them and deliver simple, clear answers.""",
            description="Intelligent root agent with full autonomy for handling Uganda government service requests through WhatsApp.",
            tools=all_tools
        )
        
        logger.info("Intelligent root agent created successfully with direct input processing")
        return root_agent
        
    except Exception as e:
        logger.error(f"Failed to create intelligent root agent: {e}")
        raise

# Coordination tools removed - LLM handles all logic with just the two core automation tools

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