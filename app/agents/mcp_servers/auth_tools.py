print("Loaded auth_tools from:", __file__)


"""
User Identification Tools
Simple phone-based user identification for WhatsApp users
"""

import logging
import re
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def get_auth_tools():
    """Get user identification tools (renamed for compatibility)"""
    
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
                r'^[0-9]{9} '      # XXXXXXXXX
            ]
            
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
    
    def format_phone_number(phone_number: str, tool_context=None) -> dict:
        """Format phone number to standard Uganda format"""
        try:
            clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
            
            # Convert to +256 format
            if clean_phone.startswith("+256"):
                formatted = clean_phone
            elif clean_phone.startswith("256"):
                formatted = "+" + clean_phone
            elif clean_phone.startswith("0"):
                formatted = "+256" + clean_phone[1:]
            elif len(clean_phone) == 9:
                formatted = "+256" + clean_phone
            else:
                return {
                    "status": "error",
                    "error": "Invalid phone number format"
                }
            
            return {
                "status": "success",
                "original": phone_number,
                "formatted": formatted,
                "country_code": "+256"
            }
        except Exception as e:
            logger.error(f"Phone formatting failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_user_session_info(phone_number: str, tool_context=None) -> dict:
        """Get basic user session information"""
        try:
            formatted_phone = format_phone_number(phone_number)
            if formatted_phone.get("status") != "success":
                return formatted_phone
            
            return {
                "status": "success",
                "session_id": f"session_{formatted_phone['formatted'].replace('+', '')}",
                "user_id": formatted_phone['formatted'],
                "phone_number": formatted_phone['formatted'],
                "session_type": "whatsapp_verified",
                "authentication_required": False
            }
        except Exception as e:
            logger.error(f"Session info retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create identification tools
    identification_tools = [
        FunctionTool(identify_user_by_phone),
        FunctionTool(validate_phone_number),
        FunctionTool(format_phone_number),
        FunctionTool(get_user_session_info)
    ]
    
    logger.info(f"Created {len(identification_tools)} user identification tools")
    return identification_tools