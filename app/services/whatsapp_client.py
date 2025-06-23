import os
import logging
import aiohttp
import json
from typing import Dict, Optional, Union, List
from pydantic import BaseModel, HttpUrl

# Configure logging
logger = logging.getLogger(__name__)

class WhatsAppMessageRequest(BaseModel):
    """Model for WhatsApp message request"""
    to: str
    type: str = "text"
    template: Optional[Dict] = None
    text: Optional[Dict] = None
    image: Optional[Dict] = None
    document: Optional[Dict] = None
    audio: Optional[Dict] = None
    video: Optional[Dict] = None
    sticker: Optional[Dict] = None
    location: Optional[Dict] = None
    interactive: Optional[Dict] = None
    contacts: Optional[List[Dict]] = None

class WhatsAppClient:
    """Client for interacting with WhatsApp Business Cloud API"""
    
    def __init__(self, phone_number_id: str, access_token: str, api_version: str = "v17.0"):
        """
        Initialize WhatsApp Business API client
        
        Args:
            phone_number_id: The WhatsApp Business Account phone number ID
            access_token: Permanent access token for the WhatsApp Business Account
            api_version: Facebook Graph API version (default: v17.0)
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make an HTTP request to the WhatsApp API"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            ) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    error_message = response_data.get("error", {}).get("message", "Unknown error")
                    logger.error(
                        "WhatsApp API request failed with status %d: %s", 
                        response.status,
                        error_message
                    )
                    raise WhatsAppAPIError(
                        f"WhatsApp API request failed: {error_message}",
                        status_code=response.status,
                        error_data=response_data
                    )
                    
                return response_data
                
        except aiohttp.ClientError as e:
            logger.exception("Error making request to WhatsApp API")
            raise WhatsAppAPIError(f"HTTP request failed: {str(e)}")
    
    async def send_message(self, message_data: Union[Dict, WhatsAppMessageRequest]) -> Dict:
        """
        Send a message via WhatsApp Business API
        
        Args:
            message_data: Message data as a dict or WhatsAppMessageRequest
            
        Returns:
            Dict containing the API response
        """
        if isinstance(message_data, WhatsAppMessageRequest):
            message_data = message_data.dict(exclude_none=True)
            
        if "messaging_product" not in message_data:
            message_data["messaging_product"] = "whatsapp"
            
        return await self._make_request("POST", "messages", message_data)
    
    async def send_text_message(self, to: str, text: str, preview_url: bool = False) -> Dict:
        """Send a text message"""
        message = WhatsAppMessageRequest(
            to=to,
            type="text",
            text={"body": text, "preview_url": preview_url}
        )
        return await self.send_message(message)
    
    async def send_template_message(
        self, 
        to: str, 
        template_name: str, 
        language_code: str = "en_US",
        components: Optional[List[Dict]] = None
    ) -> Dict:
        """Send a template message"""
        template = {
            "name": template_name,
            "language": {"code": language_code}
        }
        
        if components:
            template["components"] = components
            
        message = WhatsAppMessageRequest(
            to=to,
            type="template",
            template=template
        )
        return await self.send_message(message)
    
    async def send_media_message(
        self, 
        to: str, 
        media_type: str, 
        media_id: Optional[str] = None,
        link: Optional[str] = None,
        caption: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict:
        """
        Send a media message (image, document, audio, video, sticker)
        
        Args:
            to: Recipient phone number
            media_type: Type of media (image, document, audio, video, sticker)
            media_id: Media ID (if already uploaded to WhatsApp)
            link: Direct URL to the media (if not using media_id)
            caption: Media caption (optional)
            filename: Filename for documents (optional)
            
        Returns:
            Dict containing the API response
        """
        if media_type not in ["image", "document", "audio", "video", "sticker"]:
            raise ValueError(f"Invalid media type: {media_type}")
            
        media_data = {}
        if media_id:
            media_data["id"] = media_id
        elif link:
            media_data["link"] = link
        else:
            raise ValueError("Either media_id or link must be provided")
            
        if caption and media_type in ["image", "document", "video"]:
            media_data["caption"] = caption
            
        if filename and media_type == "document":
            media_data["filename"] = filename
            
        message = WhatsAppMessageRequest(
            to=to,
            type=media_type,
            **{media_type: media_data}
        )
        return await self.send_message(message)
    
    async def upload_media(
        self, 
        file_path: str, 
        mime_type: str,
        messaging_product: str = "whatsapp"
    ) -> Dict:
        """
        Upload media to WhatsApp servers
        
        Args:
            file_path: Path to the media file
            mime_type: MIME type of the file
            messaging_product: Messaging product (default: whatsapp)
            
        Returns:
            Dict containing the media ID and other metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        url = f"{self.base_url}/media"
        params = {
            "messaging_product": messaging_product,
            "type": mime_type
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            async with aiohttp.MultipartWriter() as mp:
                with open(file_path, 'rb') as f:
                    part = mp.append(f, {
                        'Content-Type': mime_type,
                        'Content-Disposition': f'form-data; name="file"; filename="{os.path.basename(file_path)}"'
                    })
                
                async with self.session.post(
                    url, 
                    params=params, 
                    headers=headers,
                    data=mp
                ) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        error_message = response_data.get("error", {}).get("message", "Unknown error")
                        logger.error(
                            "Failed to upload media: %s", 
                            error_message
                        )
                        raise WhatsAppAPIError(
                            f"Failed to upload media: {error_message}",
                            status_code=response.status,
                            error_data=response_data
                        )
                        
                    return response_data
                    
        except Exception as e:
            logger.exception("Error uploading media to WhatsApp")
            raise WhatsAppAPIError(f"Failed to upload media: {str(e)}")


class WhatsAppAPIError(Exception):
    """Custom exception for WhatsApp API errors"""
    
    def __init__(self, message: str, status_code: int = 500, error_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.error_data = error_data or {}
        super().__init__(self.message)


# Helper function to create a WhatsApp client from environment variables
def create_whatsapp_client() -> WhatsAppClient:
    """Create a WhatsApp client using environment variables"""
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    
    if not phone_number_id or not access_token:
        raise ValueError(
            "WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN must be set in environment"
        )
        
    return WhatsAppClient(phone_number_id, access_token)
