"""
User Identification Agent
Handles user identification based on WhatsApp phone numbers
"""

import logging
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def create_auth_agent():
    """Create user identification agent that uses phone numbers for identification"""
    try:
        
        def identify_user_by_phone(phone_number: str, tool_context=None) -> dict:
            """Identify user by their WhatsApp phone number"""
            try:
                # Clean and format phone number
                clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
                if not clean_phone.startswith("+"):
                    if clean_phone.startswith("256"):
                        clean_phone = "+" + clean_phone
                    elif clean_phone.startswith("0"):
                        clean_phone = "+256" + clean_phone[1:]
                    else:
                        clean_phone = "+256" + clean_phone
                
                return {
                    "status": "success",
                    "user_id": clean_phone,
                    "phone_number": clean_phone,
                    "identification_method": "whatsapp_phone"
                }
            except Exception as e:
                logger.error(f"User identification failed: {e}")
                return {
                    "status": "error",
                    "error": str(e)
                }
        
        def validate_phone_number(phone_number: str, tool_context=None) -> dict:
            """Validate Uganda phone number format"""
            try:
                clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
                
                # Uganda phone number patterns
                valid_patterns = [
                    r'^\+256[0-9]{9}',  # +256XXXXXXXXX
                    r'^256[0-9]{9}',    # 256XXXXXXXXX
                    r'^0[0-9]{9}',      # 0XXXXXXXXX
                    r'^[0-9]{9} '       # XXXXXXXXX
                ]
                
                import re
                is_valid = any(re.match(pattern, clean_phone) for pattern in valid_patterns)
                
                return {
                    "status": "success",
                    "is_valid": is_valid,
                    "phone_number": clean_phone,
                    "country": "Uganda" if is_valid else "Unknown"
                }
            except Exception as e:
                logger.error(f"Phone validation failed: {e}")
                return {
                    "status": "error",
                    "error": str(e)
                }
        
        # Create identification tools
        identification_tools = [
            FunctionTool(identify_user_by_phone),
            FunctionTool(validate_phone_number)
        ]
        
        agent = LlmAgent(
            name="user_identification_agent",
            model="gemini-2.0-flash",
            instruction="""You are a user identification agent that identifies users based on their WhatsApp phone numbers.

            Your responsibilities:
            - Identify users using their WhatsApp phone numbers
            - Validate Uganda phone number formats
            - Provide consistent user identification across sessions
            - Handle phone number formatting and normalization
            
            Available tools:
            - identify_user_by_phone: Identify user by WhatsApp phone number
            - validate_phone_number: Validate Uganda phone number format
            
            Phone number handling:
            - Accept various formats: +256XXXXXXXXX, 256XXXXXXXXX, 0XXXXXXXXX, XXXXXXXXX
            - Normalize to +256XXXXXXXXX format
            - Use phone number as unique user identifier
            - No additional authentication required since WhatsApp already verifies phone ownership
            
            When processing a user request:
            1. Extract phone number from WhatsApp message metadata
            2. Validate and normalize the phone number format
            3. Use the phone number as the user's unique identifier
            4. Proceed with service requests without additional authentication
            
            Security considerations:
            - WhatsApp Business API already verifies phone number ownership
            - Phone numbers are treated as verified identifiers
            - Log all user interactions for audit purposes
            - Respect user privacy and data protection
            """,
            description="Identifies users based on their WhatsApp phone numbers without additional authentication.",
            tools=identification_tools
        )
        
        logger.info("User identification agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create user identification agent: {e}")
        raise