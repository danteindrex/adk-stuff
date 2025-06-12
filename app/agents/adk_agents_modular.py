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
        
        # Get all internal tools for the root agent
        internal_tools = await get_all_internal_tools()
        
        # Create coordination tools for the root agent
        coordination_tools = await create_coordination_tools()
        
        # Combine all tools
        all_tools = internal_tools + coordination_tools
        
        # Create intelligent root LLM agent
        root_agent = LlmAgent(
            name="uganda_egov_intelligent_root",
            model="gemini-2.0-flash",
            instruction="""You are the intelligent root agent for the Uganda E-Gov WhatsApp Helpdesk.

You have FULL AUTONOMY to handle any user request directly and intelligently. You can:

🎯 CORE RESPONSIBILITIES:
1. Understand user intent from natural language input
2. Provide government service information and assistance
3. Process service requests (NIRA, URA, NSSF, NLIS)
4. Handle multi-language conversations
5. Provide contextual help and guidance

🛠️ AVAILABLE TOOLS:
- automate_nira_portal: Check birth certificate status
- automate_ura_portal: Check tax status and compliance
- automate_nssf_portal: Check pension balance and contributions
- automate_nlis_portal: Verify land ownership and titles
- validate_phone_number: Normalize Uganda phone numbers
- format_whatsapp_response: Format responses for WhatsApp
- simulate_browser_automation: General web automation

🌍 LANGUAGE SUPPORT:
- English (primary)
- Luganda (lg) - Central Uganda
- Luo (luo) - Northern Uganda  
- Runyoro (nyn) - Western Uganda

🎯 INTELLIGENT PROCESSING APPROACH:

1. UNDERSTAND THE USER:
   - Analyze the user's message for intent and context
   - Detect language if not English
   - Identify what government service they need

2. TAKE APPROPRIATE ACTION:
   - For birth certificates: Use automate_nira_portal with reference numbers
   - For tax issues: Use automate_ura_portal with TIN numbers
   - For NSSF: Use automate_nssf_portal with membership numbers
   - For land: Use automate_nlis_portal with plot/GPS info
   - For general help: Provide comprehensive guidance

3. RESPOND INTELLIGENTLY:
   - Give specific, actionable information
   - Include relevant details (office locations, hours, requirements)
   - Offer next steps and alternatives
   - Be conversational and helpful

🔍 EXAMPLE INTERACTIONS:

User: "Hello"
You: Welcome them warmly and explain available services

User: "Check my birth certificate NIRA/2023/123456"
You: Use automate_nira_portal tool and provide detailed status

User: "My TIN is 1234567890, what's my tax status?"
You: Use automate_ura_portal and explain their tax situation

User: "I need help with land verification"
You: Ask for plot details and guide them through the process

User: "Webale" (Luganda for thank you)
You: Respond appropriately in Luganda and offer continued assistance

🎯 KEY PRINCIPLES:
- Be proactive and intelligent in understanding user needs
- Use tools when you have specific information (reference numbers, TINs, etc.)
- Provide comprehensive help even without specific details
- Handle errors gracefully and offer alternatives
- Maintain conversation context and be personable
- Always aim to help the user accomplish their goal

🚀 FLEXIBILITY:
You have complete freedom to:
- Interpret user intent creatively
- Combine multiple tools if needed
- Provide detailed explanations
- Handle edge cases and unusual requests
- Maintain engaging conversations
- Offer proactive suggestions

Remember: You are serving Ugandan citizens who may have varying levels of digital literacy. Be patient, clear, and helpful. Your goal is to make government services accessible through simple WhatsApp conversations.

Always respond in a way that moves the conversation forward and helps the user achieve their goal.""",
            description="Intelligent root agent with full autonomy for handling Uganda government service requests through WhatsApp.",
            tools=all_tools
        )
        
        logger.info("Intelligent root agent created successfully with direct input processing")
        return root_agent
        
    except Exception as e:
        logger.error(f"Failed to create intelligent root agent: {e}")
        raise

async def create_coordination_tools():
    """Create tools for coordinating with other agents and services"""
    
    def get_service_information(service_type: str, tool_context=None) -> dict:
        """Get comprehensive information about government services"""
        try:
            service_info = {
                'nira': {
                    'name': 'NIRA (National Identification and Registration Authority)',
                    'services': ['Birth Certificates', 'National IDs', 'Death Certificates'],
                    'office_locations': [
                        'NIRA House, Plot 10, Kampala Road, Kampala',
                        'Regional offices in Gulu, Mbarara, Mbale, Fort Portal'
                    ],
                    'working_hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
                    'contact': {
                        'phone': '+256-414-123456',
                        'email': 'info@nira.go.ug',
                        'website': 'https://www.nira.go.ug'
                    },
                    'common_requirements': [
                        'Original documents',
                        'Passport photos',
                        'Application fees',
                        'Valid identification'
                    ]
                },
                'ura': {
                    'name': 'URA (Uganda Revenue Authority)',
                    'services': ['Tax Registration', 'Tax Payments', 'Tax Clearance', 'Compliance'],
                    'office_locations': [
                        'URA House, Plot 12, Nakasero Road, Kampala',
                        'Regional offices in all major towns'
                    ],
                    'working_hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
                    'contact': {
                        'phone': '+256-417-123456',
                        'email': 'info@ura.go.ug',
                        'website': 'https://www.ura.go.ug'
                    },
                    'common_requirements': [
                        'TIN number',
                        'Business license',
                        'Bank details',
                        'Valid ID'
                    ]
                },
                'nssf': {
                    'name': 'NSSF (National Social Security Fund)',
                    'services': ['Pension Contributions', 'Benefits', 'Member Services'],
                    'office_locations': [
                        'NSSF House, Plot 4, Jinja Road, Kampala',
                        'Regional offices nationwide'
                    ],
                    'working_hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
                    'contact': {
                        'phone': '+256-414-123789',
                        'email': 'info@nssfug.org',
                        'website': 'https://www.nssfug.org'
                    },
                    'common_requirements': [
                        'NSSF membership number',
                        'National ID',
                        'Employment details',
                        'Bank account'
                    ]
                },
                'nlis': {
                    'name': 'NLIS (National Land Information System)',
                    'services': ['Land Verification', 'Title Search', 'Land Registration'],
                    'office_locations': [
                        'Ministry of Lands, Plot 3, Kampala',
                        'District land offices'
                    ],
                    'working_hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
                    'contact': {
                        'phone': '+256-414-123999',
                        'email': 'info@nlis.go.ug',
                        'website': 'https://nlis.go.ug'
                    },
                    'common_requirements': [
                        'Plot/Block numbers',
                        'GPS coordinates',
                        'Survey plans',
                        'Valid ID'
                    ]
                }
            }
            
            if service_type.lower() in service_info:
                return {
                    "status": "success",
                    "service_info": service_info[service_type.lower()]
                }
            else:
                return {
                    "status": "success",
                    "all_services": service_info
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def detect_user_intent(user_message: str, tool_context=None) -> dict:
        """Analyze user message to detect intent and extract key information"""
        try:
            message_lower = user_message.lower()
            
            # Intent detection patterns
            intents = {
                'birth_certificate': [
                    'birth', 'certificate', 'nira', 'born', 'delivery'
                ],
                'tax_status': [
                    'tax', 'ura', 'tin', 'payment', 'compliance', 'revenue'
                ],
                'nssf_balance': [
                    'nssf', 'pension', 'contribution', 'balance', 'retirement'
                ],
                'land_verification': [
                    'land', 'nlis', 'plot', 'title', 'property', 'ownership'
                ],
                'general_help': [
                    'help', 'assist', 'support', 'guide', 'how'
                ],
                'greeting': [
                    'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'webale'
                ]
            }
            
            # Extract potential reference numbers/IDs
            import re
            nira_ref = re.search(r'NIRA/\d{4}/\d{6}', user_message, re.IGNORECASE)
            tin_number = re.search(r'\b\d{10}\b', user_message)
            nssf_number = re.search(r'\b\d{8,12}\b', user_message)
            phone_number = re.search(r'(\+256|0)\d{9}', user_message)
            
            # Detect primary intent
            detected_intent = 'unknown'
            confidence = 0
            
            for intent, keywords in intents.items():
                matches = sum(1 for keyword in keywords if keyword in message_lower)
                if matches > confidence:
                    confidence = matches
                    detected_intent = intent
            
            return {
                "status": "success",
                "intent": detected_intent,
                "confidence": confidence,
                "extracted_data": {
                    "nira_reference": nira_ref.group() if nira_ref else None,
                    "tin_number": tin_number.group() if tin_number else None,
                    "nssf_number": nssf_number.group() if nssf_number else None,
                    "phone_number": phone_number.group() if phone_number else None
                },
                "message_analysis": {
                    "length": len(user_message),
                    "word_count": len(user_message.split()),
                    "contains_numbers": bool(re.search(r'\d', user_message)),
                    "language_hints": _detect_language_hints(user_message)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def provide_contextual_help(topic: str = None, tool_context=None) -> dict:
        """Provide contextual help based on topic or general guidance"""
        try:
            if topic:
                topic_lower = topic.lower()
                
                if 'birth' in topic_lower or 'nira' in topic_lower:
                    return {
                        "status": "success",
                        "help_content": """📋 NIRA Birth Certificate Help

🔍 What you can do:
• Check application status with reference number
• Get collection information
• Find office locations and hours
• Learn about requirements

📝 Information needed:
• NIRA reference number (format: NIRA/YYYY/NNNNNN)
• Example: NIRA/2023/123456

🏢 Where to go:
• NIRA House, Kampala Road, Kampala
• Regional offices in major towns
• Hours: Monday-Friday, 8:00 AM - 5:00 PM

💡 Tips:
• Keep your reference number safe
• Bring original ID when collecting
• Processing takes 14-21 days"""
                    }
                
                elif 'tax' in topic_lower or 'ura' in topic_lower:
                    return {
                        "status": "success", 
                        "help_content": """💼 URA Tax Services Help

🔍 What you can do:
• Check tax balance and status
• View payment history
• Get compliance information
• Find payment methods

📝 Information needed:
• 10-digit TIN number
• Example: 1234567890

🏢 Where to go:
• URA House, Nakasero Road, Kampala
• Regional tax offices
• Hours: Monday-Friday, 8:00 AM - 5:00 PM

💡 Tips:
• Keep TIN number handy
• Pay taxes on time for compliance
• Use mobile money for payments"""
                    }
                
                elif 'nssf' in topic_lower or 'pension' in topic_lower:
                    return {
                        "status": "success",
                        "help_content": """🏦 NSSF Services Help

🔍 What you can do:
• Check contribution balance
• View payment history
• Get member information
• Plan for retirement

📝 Information needed:
• NSSF membership number (8-12 digits)
• Example: 12345678

🏢 Where to go:
• NSSF House, Jinja Road, Kampala
• Regional NSSF offices
• Hours: Monday-Friday, 8:00 AM - 5:00 PM

💡 Tips:
• Contribute regularly for better benefits
• Update your details when they change
• Plan early for retirement"""
                    }
                
                elif 'land' in topic_lower or 'nlis' in topic_lower:
                    return {
                        "status": "success",
                        "help_content": """🌿 NLIS Land Services Help

🔍 What you can do:
• Verify land ownership
• Check title status
• Search property details
• Confirm boundaries

📝 Information needed:
• Plot/Block numbers OR
• GPS coordinates OR
• Property description

🏢 Where to go:
• Ministry of Lands, Kampala
• District land offices
• Hours: Monday-Friday, 8:00 AM - 5:00 PM

💡 Tips:
• Verify before buying land
• Keep title documents safe
• Use official channels only"""
                    }
            
            # General help
            return {
                "status": "success",
                "help_content": """🇺🇬 Uganda E-Gov Services Help

🎯 Available Services:
1️⃣ Birth Certificate (NIRA) - Status & collection
2️⃣ Tax Status (URA) - Balance & payments
3️⃣ NSSF Balance - Contributions & benefits
4️⃣ Land Verification (NLIS) - Ownership & titles

💬 How to use:
• Just tell me what you need
• Provide reference numbers when you have them
• Ask questions in English, Luganda, Luo, or Runyoro

🆘 Commands:
• 'help' - Get assistance
• 'status' - Check your session
• 'cancel' - Start over
• 'admin' - Emergency contact

🌍 Languages: English, Luganda, Luo, Runyoro

Just describe what you need help with!"""
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _detect_language_hints(text: str) -> list:
        """Detect potential language hints in text"""
        language_hints = []
        
        # Luganda words
        luganda_words = ['webale', 'bambi', 'nkwagala', 'oli otya', 'siiba']
        if any(word in text.lower() for word in luganda_words):
            language_hints.append('luganda')
        
        # Luo words  
        luo_words = ['apwoyo', 'itye nadi', 'amito', 'pwonyo']
        if any(word in text.lower() for word in luo_words):
            language_hints.append('luo')
        
        # Runyoro words
        runyoro_words = ['webale', 'oli ota', 'ninkusiima', 'nkwenda']
        if any(word in text.lower() for word in runyoro_words):
            language_hints.append('runyoro')
        
        return language_hints
    
    # Create coordination tools
    coordination_tools = [
        FunctionTool(get_service_information),
        FunctionTool(detect_user_intent),
        FunctionTool(provide_contextual_help)
    ]
    
    logger.info(f"Created {len(coordination_tools)} coordination tools")
    return coordination_tools

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