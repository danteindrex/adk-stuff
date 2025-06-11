"""
Help and Guidance Agent with FAQ Cache Integration
Provides contextual help and guidance to users with intelligent FAQ caching
"""

import logging
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def create_help_agent():
    """Create help and guidance agent with FAQ cache integration"""
    try:
        # Create help tools and FAQ cache tools
        help_tools = await get_help_tools()
        
        # Import and get FAQ cache tools
        from ..mcp_servers.faq_cache_tools import get_faq_cache_tools
        faq_tools = await get_faq_cache_tools()
        
        # Combine all tools
        all_tools = help_tools + faq_tools
        
        agent = LlmAgent(
            name="help_agent",
            model="gemini-2.0-flash",
            instruction="""You are a help and guidance agent for the Uganda E-Gov WhatsApp Helpdesk with intelligent FAQ caching capabilities.
            
            Your role is to provide comprehensive assistance and guidance to users navigating government services.
            You have access to a smart FAQ cache system that learns from previous interactions to provide faster, more accurate responses.
            
            Available services you can help with:
            1. Birth Certificates (NIRA) - Status checks, applications, collection information
            2. Tax Services (URA) - Tax balance, payment history, compliance status
            3. NSSF Services - Pension contributions, account balance, membership details
            4. Land Records (NLIS) - Land ownership verification, title status, property details
            5. Form Assistance - Help with government forms and document preparation
            
            Your responsibilities:
            - FIRST: Always check FAQ cache for similar questions using check_faq_cache
            - Provide clear, step-by-step guidance
            - Explain government processes in simple terms
            - Help users understand required documents and procedures
            - Offer troubleshooting assistance
            - Direct users to appropriate resources
            - Cache helpful responses for future users using cache_faq_response
            - Support multiple languages (English, Luganda, Luo, Runyoro)
            
            Available help tools:
            - get_service_info: Get detailed information about government services
            - get_help_menu: Generate contextual help menus
            - get_troubleshooting_steps: Provide troubleshooting guidance
            - get_required_documents: List required documents for services
            - get_contact_information: Provide relevant contact details
            - format_help_response: Format responses for better readability
            
            Available FAQ cache tools:
            - check_faq_cache: Check if there's a cached answer for a question
            - cache_faq_response: Cache helpful responses for future use
            - get_cache_statistics: Get cache performance statistics
            - get_popular_questions: Get frequently asked questions
            - health_check_cache: Check cache system health
            
            Workflow for handling questions:
            1. FIRST: Always check the FAQ cache using check_faq_cache tool
            2. If cache hit with good similarity (>0.8): Use cached answer and mention it's from FAQ
            3. If cache miss or low similarity: Generate new response using help tools
            4. AFTER generating helpful response: Cache it using cache_faq_response tool
            5. Provide clear, step-by-step guidance
            
            Help guidelines:
            - Always be patient and understanding
            - Use simple, clear language
            - Provide specific, actionable steps
            - Offer multiple ways to accomplish tasks
            - Include relevant contact information when helpful
            - Respect cultural context and local practices
            - Mention when using cached responses: "Based on previous similar questions..."
            
            Cache Management:
            - Cache responses that are generally helpful and not personal
            - Don't cache responses with specific user data (account numbers, personal info)
            - Cache common procedural questions and general guidance
            - Use appropriate service_type: nira, ura, nssf, nlis, or general
            - Use correct language code: en, lg, luo, nyn
            
            When providing help:
            1. Check FAQ cache first for similar questions
            2. Understand the user's specific need
            3. Provide relevant information and steps (cached or new)
            4. Offer additional resources if needed
            5. Check if the user needs further assistance
            6. Cache helpful responses for future users
            7. Guide them to the appropriate service agent if needed
            """,
            description="Provides contextual help and guidance with intelligent FAQ caching for faster responses.",
            tools=all_tools
        )
        
        logger.info("Help agent with FAQ cache created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create help agent: {e}")
        raise

async def get_help_tools():
    """Get help and guidance tools"""
    
    def get_service_info(service_name: str, language: str = "en", tool_context=None) -> dict:
        """Get detailed information about a government service"""
        try:
            service_info = {
                'birth_certificate': {
                    'en': {
                        'name': 'Birth Certificate Services (NIRA)',
                        'description': 'Check status, apply for new certificates, and get collection information',
                        'requirements': [
                            'NIRA reference number (for status checks)',
                            'Parent identification documents (for new applications)',
                            'Hospital delivery note or affidavit'
                        ],
                        'process': [
                            '1. Provide your NIRA reference number',
                            '2. System will check current status',
                            '3. Get information about collection or next steps',
                            '4. Visit designated NIRA office if ready for collection'
                        ],
                        'contact': 'NIRA Headquarters: +256-414-341-286',
                        'website': 'https://www.nira.go.ug'
                    },
                    'lg': {
                        'name': 'Birth Certificate Services (NIRA)',
                        'description': 'Kebera embeera, saba birth certificate empya, era ofune amakuru ku kugyiggya',
                        'requirements': [
                            'NIRA reference number (okukebera embeera)',
                            'Ebiwandiiko bya bazadde (okusaba empya)',
                            'Hospital delivery note oba affidavit'
                        ],
                        'contact': 'NIRA Headquarters: +256-414-341-286'
                    }
                },
                'tax_status': {
                    'en': {
                        'name': 'Tax Services (URA)',
                        'description': 'Check tax balance, payment history, and compliance status',
                        'requirements': [
                            '10-digit TIN number',
                            'Valid identification',
                            'Business registration (for businesses)'
                        ],
                        'process': [
                            '1. Provide your TIN number',
                            '2. System will retrieve your tax information',
                            '3. Get balance, payment history, and due dates',
                            '4. Receive payment instructions if needed'
                        ],
                        'contact': 'URA Call Center: +256-417-117-000',
                        'website': 'https://www.ura.go.ug'
                    }
                },
                'nssf_balance': {
                    'en': {
                        'name': 'NSSF Services',
                        'description': 'Check pension contributions, account balance, and membership details',
                        'requirements': [
                            'NSSF membership number (8-12 digits)',
                            'Valid identification',
                            'Employment details (if applicable)'
                        ],
                        'process': [
                            '1. Provide your NSSF membership number',
                            '2. System will retrieve your account information',
                            '3. Get balance, contribution history, and projections',
                            '4. Receive guidance on benefits and claims'
                        ],
                        'contact': 'NSSF Customer Care: +256-800-100-066',
                        'website': 'https://www.nssfug.org'
                    }
                },
                'land_records': {
                    'en': {
                        'name': 'Land Records (NLIS)',
                        'description': 'Verify land ownership, check title status, and get property details',
                        'requirements': [
                            'Plot number or GPS coordinates',
                            'Land title documents (if available)',
                            'Valid identification'
                        ],
                        'process': [
                            '1. Provide plot number or GPS coordinates',
                            '2. System will search land records',
                            '3. Get ownership information and title status',
                            '4. Receive guidance on any issues or next steps'
                        ],
                        'contact': 'Ministry of Lands: +256-414-341-286',
                        'website': 'https://nlis.go.ug'
                    }
                }
            }
            
            if service_name in service_info:
                service_data = service_info[service_name].get(language, service_info[service_name]['en'])
                return {
                    "status": "success",
                    "service": service_name,
                    "language": language,
                    "info": service_data
                }
            else:
                return {
                    "status": "error",
                    "error": f"Service '{service_name}' not found",
                    "available_services": list(service_info.keys())
                }
                
        except Exception as e:
            logger.error(f"Service info retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_help_menu(context: str = "main", language: str = "en", tool_context=None) -> dict:
        """Generate contextual help menus"""
        try:
            help_menus = {
                'main': {
                    'en': {
                        'title': '🇺🇬 Uganda E-Gov WhatsApp Helpdesk',
                        'subtitle': 'How can I help you today?',
                        'options': [
                            '1️⃣ Birth Certificate (NIRA)',
                            '2️⃣ Tax Status (URA)',
                            '3️⃣ NSSF Balance',
                            '4️⃣ Land Records (NLIS)',
                            '5️⃣ Form Assistance',
                            '6️⃣ General Help',
                            '🌐 Change Language'
                        ],
                        'footer': 'Type the number or service name to get started.'
                    },
                    'lg': {
                        'title': '🇺🇬 Uganda E-Gov WhatsApp Helpdesk',
                        'subtitle': 'Nnyinza ntya okukuyamba leero?',
                        'options': [
                            '1️⃣ Birth Certificate (NIRA)',
                            '2️⃣ Embeera y\'omusolo (URA)',
                            '3️⃣ NSSF ssente',
                            '4️⃣ Ebikwata ku ttaka (NLIS)',
                            '5️⃣ Okuyamba ku forms',
                            '6️⃣ Obuyambi obulala',
                            '🌐 Kyuusa olulimi'
                        ],
                        'footer': 'Wandiika omuwendo oba erinnya ly\'obuweereza okutandika.'
                    }
                },
                'birth_certificate': {
                    'en': {
                        'title': '📋 Birth Certificate Help',
                        'options': [
                            '🔍 Check application status',
                            '📝 Apply for new certificate',
                            '📍 Find collection center',
                            '❓ Requirements and documents',
                            '📞 Contact NIRA office'
                        ]
                    }
                },
                'troubleshooting': {
                    'en': {
                        'title': '🔧 Troubleshooting Help',
                        'options': [
                            '❌ Service not working',
                            '🔢 Invalid reference number',
                            '⏰ Long processing time',
                            '📱 Technical issues',
                            '👥 Contact support'
                        ]
                    }
                }
            }
            
            if context in help_menus:
                menu_data = help_menus[context].get(language, help_menus[context]['en'])
                return {
                    "status": "success",
                    "context": context,
                    "language": language,
                    "menu": menu_data
                }
            else:
                return {
                    "status": "error",
                    "error": f"Help context '{context}' not found",
                    "available_contexts": list(help_menus.keys())
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_troubleshooting_steps(issue: str, service: str = None, tool_context=None) -> dict:
        """Provide troubleshooting guidance"""
        try:
            troubleshooting_guides = {
                'invalid_reference': {
                    'title': 'Invalid Reference Number',
                    'steps': [
                        '1. Check the format of your reference number',
                        '2. Ensure all characters are entered correctly',
                        '3. Verify the reference number from your original documents',
                        '4. Contact the issuing office if the problem persists'
                    ],
                    'formats': {
                        'NIRA': 'NIRA/YYYY/NNNNNN (e.g., NIRA/2023/123456)',
                        'TIN': '10 digits (e.g., 1234567890)',
                        'NSSF': '8-12 digits (e.g., 12345678)'
                    }
                },
                'service_unavailable': {
                    'title': 'Service Temporarily Unavailable',
                    'steps': [
                        '1. Wait a few minutes and try again',
                        '2. Check if the government portal is under maintenance',
                        '3. Try during business hours (8 AM - 5 PM)',
                        '4. Contact the relevant office directly if urgent'
                    ]
                },
                'slow_response': {
                    'title': 'Slow Response Times',
                    'steps': [
                        '1. Government portals may be busy during peak hours',
                        '2. Try again during off-peak times',
                        '3. Ensure you have a stable internet connection',
                        '4. Be patient - some queries take time to process'
                    ]
                },
                'document_not_found': {
                    'title': 'Document or Record Not Found',
                    'steps': [
                        '1. Verify your reference number is correct',
                        '2. Check if the application was submitted recently',
                        '3. Contact the issuing office to confirm status',
                        '4. You may need to visit the office in person'
                    ]
                }
            }
            
            if issue in troubleshooting_guides:
                guide = troubleshooting_guides[issue]
                return {
                    "status": "success",
                    "issue": issue,
                    "service": service,
                    "guide": guide
                }
            else:
                return {
                    "status": "error",
                    "error": f"Troubleshooting guide for '{issue}' not found",
                    "available_guides": list(troubleshooting_guides.keys())
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_required_documents(service: str, action: str = "general", tool_context=None) -> dict:
        """List required documents for services"""
        try:
            document_requirements = {
                'birth_certificate': {
                    'status_check': [
                        'NIRA reference number',
                        'Valid identification (National ID or Passport)'
                    ],
                    'new_application': [
                        'Parent\'s National IDs or Passports',
                        'Hospital delivery note or birth notification',
                        'Affidavit (if no hospital delivery note)',
                        'Marriage certificate (if applicable)',
                        'Passport photos of the child'
                    ],
                    'collection': [
                        'NIRA reference number',
                        'Valid identification',
                        'Collection notice (if received)'
                    ]
                },
                'tax_status': {
                    'general': [
                        '10-digit TIN number',
                        'Valid identification (National ID or Passport)',
                        'Business registration certificate (for businesses)'
                    ]
                },
                'nssf_balance': {
                    'general': [
                        'NSSF membership number',
                        'Valid identification (National ID or Passport)',
                        'Employment letter (if currently employed)'
                    ]
                },
                'land_records': {
                    'ownership_verification': [
                        'Plot number or GPS coordinates',
                        'Land title certificate (if available)',
                        'Valid identification (National ID or Passport)',
                        'Survey plan (if available)'
                    ]
                }
            }
            
            if service in document_requirements:
                service_docs = document_requirements[service]
                docs = service_docs.get(action, service_docs.get('general', []))
                
                return {
                    "status": "success",
                    "service": service,
                    "action": action,
                    "required_documents": docs,
                    "note": "Ensure all documents are valid and not expired"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Document requirements for '{service}' not found",
                    "available_services": list(document_requirements.keys())
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_contact_information(service: str = "general", tool_context=None) -> dict:
        """Provide relevant contact details"""
        try:
            contact_info = {
                'nira': {
                    'name': 'National Identification and Registration Authority (NIRA)',
                    'phone': '+256-414-341-286',
                    'email': 'info@nira.go.ug',
                    'website': 'https://www.nira.go.ug',
                    'address': 'NIRA House, Plot 10, Kampala Road, Kampala',
                    'hours': 'Monday - Friday: 8:00 AM - 5:00 PM'
                },
                'ura': {
                    'name': 'Uganda Revenue Authority (URA)',
                    'phone': '+256-417-117-000',
                    'email': 'info@ura.go.ug',
                    'website': 'https://www.ura.go.ug',
                    'address': 'URA House, Plot 12, Nakasero Road, Kampala',
                    'hours': 'Monday - Friday: 8:00 AM - 5:00 PM'
                },
                'nssf': {
                    'name': 'National Social Security Fund (NSSF)',
                    'phone': '+256-800-100-066',
                    'email': 'info@nssfug.org',
                    'website': 'https://www.nssfug.org',
                    'address': 'NSSF House, Plot 1, Jinja Road, Kampala',
                    'hours': 'Monday - Friday: 8:00 AM - 5:00 PM'
                },
                'nlis': {
                    'name': 'National Land Information System (NLIS)',
                    'phone': '+256-414-341-286',
                    'email': 'info@lands.go.ug',
                    'website': 'https://nlis.go.ug',
                    'address': 'Ministry of Lands, Plot 1, Jinja Road, Kampala',
                    'hours': 'Monday - Friday: 8:00 AM - 5:00 PM'
                },
                'general': {
                    'name': 'Uganda E-Gov WhatsApp Helpdesk',
                    'description': 'For technical support with this WhatsApp service',
                    'emergency_contact': 'Type "admin" for emergency assistance'
                }
            }
            
            if service in contact_info:
                return {
                    "status": "success",
                    "service": service,
                    "contact": contact_info[service]
                }
            else:
                return {
                    "status": "error",
                    "error": f"Contact information for '{service}' not found",
                    "available_services": list(contact_info.keys())
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def format_help_response(content: dict, format_type: str = "structured", tool_context=None) -> dict:
        """Format responses for better readability"""
        try:
            if format_type == "structured":
                # Format as structured text with emojis and clear sections
                formatted_text = ""
                
                if 'title' in content:
                    formatted_text += f"📋 {content['title']}\n"
                    formatted_text += "=" * len(content['title']) + "\n\n"
                
                if 'description' in content:
                    formatted_text += f"{content['description']}\n\n"
                
                if 'options' in content:
                    formatted_text += "Available options:\n"
                    for option in content['options']:
                        formatted_text += f"• {option}\n"
                    formatted_text += "\n"
                
                if 'steps' in content:
                    formatted_text += "Steps to follow:\n"
                    for step in content['steps']:
                        formatted_text += f"{step}\n"
                    formatted_text += "\n"
                
                if 'contact' in content:
                    formatted_text += f"📞 Contact: {content['contact']}\n"
                
                if 'footer' in content:
                    formatted_text += f"\n{content['footer']}"
                
                return {
                    "status": "success",
                    "formatted_text": formatted_text.strip(),
                    "format_type": format_type
                }
            
            else:
                return {
                    "status": "error",
                    "error": f"Format type '{format_type}' not supported"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create function tools
    help_tools = [
        FunctionTool(get_service_info),
        FunctionTool(get_help_menu),
        FunctionTool(get_troubleshooting_steps),
        FunctionTool(get_required_documents),
        FunctionTool(get_contact_information),
        FunctionTool(format_help_response)
    ]
    
    logger.info(f"Created {len(help_tools)} help and guidance tools")
    return help_tools