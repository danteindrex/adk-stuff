"""
Service Dispatcher Agent
Routes requests to appropriate service agents
"""

import logging
from google.adk.agents import SequentialAgent
from .birth_agent import create_birth_agent
from .tax_agent import create_tax_agent
from .nssf_agent import create_nssf_agent
from .land_agent import create_land_agent
from .form_agent import create_form_agent

logger = logging.getLogger(__name__)

async def create_service_dispatcher():
    """Create service dispatcher with all service agents"""
    try:
        # Create all service agents
        logger.info("Creating service agents...")
        
        birth_agent = await create_birth_agent()
        logger.info("Birth agent created")
        
        tax_agent = await create_tax_agent()
        logger.info("Tax agent created")
        
        nssf_agent = await create_nssf_agent()
        logger.info("NSSF agent created")
        
        land_agent = await create_land_agent()
        logger.info("Land agent created")
        
        form_agent = await create_form_agent()
        logger.info("Form agent created")
        
        # Create sequential agent with all service agents
        dispatcher = SequentialAgent(
            name="service_dispatcher",
            description="""Routes user requests to the appropriate government service agent.
            
            Available service agents:
            1. Birth Agent - Handles NIRA birth certificate services
            2. Tax Agent - Handles URA tax status and payment services
            3. NSSF Agent - Handles NSSF pension and contribution services
            4. Land Agent - Handles NLIS land ownership and title services
            5. Form Agent - Handles government form completion and submission
            
            Routing logic:
            - Birth certificate requests → Birth Agent
            - Tax-related requests → Tax Agent
            - NSSF/pension requests → NSSF Agent
            - Land/property requests → Land Agent
            - Form assistance requests → Form Agent
            
            The dispatcher analyzes user intent and routes to the most appropriate agent
            based on keywords, context, and user requirements.
            """,
            sub_agents=[birth_agent, tax_agent, nssf_agent, land_agent, form_agent]
        )
        
        logger.info("Service dispatcher created successfully with 5 service agents")
        return dispatcher
        
    except Exception as e:
        logger.error(f"Failed to create service dispatcher: {e}")
        raise