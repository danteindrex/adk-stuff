"""
WhatsApp MCP Tools
Enhanced WhatsApp Business API integration
"""

import logging
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

# Global variables
_whatsapp_toolset = None
_exit_stacks = []

async def get_whatsapp_tools():
    """Get WhatsApp MCP tools with fallback to custom implementation"""
    global _whatsapp_toolset
    
    if _whatsapp_toolset is None:
        try:
            # Try to get WhatsApp MCP tools
            tools, exit_stack = await MCPToolset.from_server(
                connection_params=StdioServerParameters(
                    command="npx",
                    args=[
                        "-y",
                        "@lharries/whatsapp-mcp@latest"
                    ]
                )
            )
            _whatsapp_toolset = tools
            _exit_stacks.append(exit_stack)
            logger.info("WhatsApp MCP tools initialized successfully")
        except Exception as e:
            logger.warning(f"WhatsApp MCP tools failed to initialize: {e}")
            # Fallback to custom WhatsApp tools
            _whatsapp_toolset = await get_custom_whatsapp_tools()
    
    return _whatsapp_toolset

async def get_custom_whatsapp_tools():
    """Get custom WhatsApp tools as fallback"""
    
    def send_whatsapp_message(
        phone_number: str,
        message: str,
        message_type: str = "text",
        tool_context=None
    ) -> dict:
        """Send WhatsApp message using Business API"""
        try:
            import requests
            import os
            
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            
            if not access_token or not phone_number_id:
                return {
                    "status": "error",
                    "error": "WhatsApp credentials not configured"
                }
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": message_type,
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message_id": response.json().get("messages", [{}])[0].get("id"),
                    "phone_number": phone_number
                }
            else:
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"WhatsApp message sending failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def send_whatsapp_template(
        phone_number: str,
        template_name: str,
        template_params: list = None,
        language_code: str = "en",
        tool_context=None
    ) -> dict:
        """Send WhatsApp template message"""
        try:
            import requests
            import os
            
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            
            if not access_token or not phone_number_id:
                return {
                    "status": "error",
                    "error": "WhatsApp credentials not configured"
                }
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            template_data = {
                "name": template_name,
                "language": {"code": language_code}
            }
            
            if template_params:
                template_data["components"] = [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in template_params]
                }]
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": template_data
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message_id": response.json().get("messages", [{}])[0].get("id"),
                    "template_name": template_name,
                    "phone_number": phone_number
                }
            else:
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"WhatsApp template sending failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def send_whatsapp_media(
        phone_number: str,
        media_url: str,
        media_type: str = "image",
        caption: str = None,
        tool_context=None
    ) -> dict:
        """Send WhatsApp media message"""
        try:
            import requests
            import os
            
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            
            if not access_token or not phone_number_id:
                return {
                    "status": "error",
                    "error": "WhatsApp credentials not configured"
                }
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            media_data = {"link": media_url}
            if caption and media_type in ["image", "video"]:
                media_data["caption"] = caption
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": media_type,
                media_type: media_data
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message_id": response.json().get("messages", [{}])[0].get("id"),
                    "media_type": media_type,
                    "phone_number": phone_number
                }
            else:
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"WhatsApp media sending failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_whatsapp_media(
        media_id: str,
        tool_context=None
    ) -> dict:
        """Get WhatsApp media URL"""
        try:
            import requests
            import os
            
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            
            if not access_token:
                return {
                    "status": "error",
                    "error": "WhatsApp access token not configured"
                }
            
            url = f"https://graph.facebook.com/v18.0/{media_id}"
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                media_info = response.json()
                return {
                    "status": "success",
                    "media_url": media_info.get("url"),
                    "media_type": media_info.get("mime_type"),
                    "file_size": media_info.get("file_size"),
                    "media_id": media_id
                }
            else:
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"WhatsApp media retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def mark_message_read(
        message_id: str,
        tool_context=None
    ) -> dict:
        """Mark WhatsApp message as read"""
        try:
            import requests
            import os
            
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            
            if not access_token or not phone_number_id:
                return {
                    "status": "error",
                    "error": "WhatsApp credentials not configured"
                }
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message_id": message_id
                }
            else:
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Message read status update failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create custom WhatsApp tools
    whatsapp_tools = [
        FunctionTool(send_whatsapp_message),
        FunctionTool(send_whatsapp_template),
        FunctionTool(send_whatsapp_media),
        FunctionTool(get_whatsapp_media),
        FunctionTool(mark_message_read)
    ]
    
    logger.info(f"Created {len(whatsapp_tools)} custom WhatsApp tools")
    return whatsapp_tools

async def get_whatsapp_business_tools():
    """Get enhanced WhatsApp Business tools"""
    
    def create_whatsapp_button_message(
        phone_number: str,
        body_text: str,
        buttons: list,
        header_text: str = None,
        footer_text: str = None,
        tool_context=None
    ) -> dict:
        """Create interactive button message"""
        try:
            import requests
            import os
            
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            
            if not access_token or not phone_number_id:
                return {
                    "status": "error",
                    "error": "WhatsApp credentials not configured"
                }
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            interactive_data = {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"btn_{i}",
                                "title": button[:20]  # Max 20 chars
                            }
                        } for i, button in enumerate(buttons[:3])  # Max 3 buttons
                    ]
                }
            }
            
            if header_text:
                interactive_data["header"] = {"type": "text", "text": header_text}
            
            if footer_text:
                interactive_data["footer"] = {"text": footer_text}
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": interactive_data
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message_id": response.json().get("messages", [{}])[0].get("id"),
                    "message_type": "button",
                    "phone_number": phone_number
                }
            else:
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Button message creation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def create_whatsapp_list_message(
        phone_number: str,
        body_text: str,
        button_text: str,
        sections: list,
        header_text: str = None,
        footer_text: str = None,
        tool_context=None
    ) -> dict:
        """Create interactive list message"""
        try:
            import requests
            import os
            
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            
            if not access_token or not phone_number_id:
                return {
                    "status": "error",
                    "error": "WhatsApp credentials not configured"
                }
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            interactive_data = {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
            
            if header_text:
                interactive_data["header"] = {"type": "text", "text": header_text}
            
            if footer_text:
                interactive_data["footer"] = {"text": footer_text}
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": interactive_data
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message_id": response.json().get("messages", [{}])[0].get("id"),
                    "message_type": "list",
                    "phone_number": phone_number
                }
            else:
                return {
                    "status": "error",
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"List message creation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create business tools
    business_tools = [
        FunctionTool(create_whatsapp_button_message),
        FunctionTool(create_whatsapp_list_message)
    ]
    
    logger.info(f"Created {len(business_tools)} WhatsApp Business tools")
    return business_tools