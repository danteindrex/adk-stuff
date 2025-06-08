"""
WhatsApp Business API models
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class WhatsAppMessage(BaseModel):
    """WhatsApp message model"""
    id: str
    from_number: str = Field(..., alias="from")
    timestamp: str
    type: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        allow_population_by_field_name = True

class WhatsAppContact(BaseModel):
    """WhatsApp contact model"""
    profile: Dict[str, str]
    wa_id: str

class WhatsAppMetadata(BaseModel):
    """WhatsApp metadata model"""
    display_phone_number: str
    phone_number_id: str

class WhatsAppValue(BaseModel):
    """WhatsApp webhook value model"""
    messaging_product: str
    metadata: WhatsAppMetadata
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    statuses: Optional[List[Dict[str, Any]]] = None

class WhatsAppChange(BaseModel):
    """WhatsApp webhook change model"""
    value: WhatsAppValue
    field: str

class WhatsAppEntry(BaseModel):
    """WhatsApp webhook entry model"""
    id: str
    changes: List[WhatsAppChange]

class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook model"""
    object: str
    entry: List[WhatsAppEntry]

class WhatsAppTextMessage(BaseModel):
    """Model for sending text messages"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "text"
    text: Dict[str, str]

class WhatsAppInteractiveButton(BaseModel):
    """Interactive button model"""
    type: str = "reply"
    reply: Dict[str, str]

class WhatsAppInteractiveAction(BaseModel):
    """Interactive action model"""
    buttons: List[WhatsAppInteractiveButton]

class WhatsAppInteractiveHeader(BaseModel):
    """Interactive header model"""
    type: str = "text"
    text: str

class WhatsAppInteractiveBody(BaseModel):
    """Interactive body model"""
    text: str

class WhatsAppInteractiveFooter(BaseModel):
    """Interactive footer model"""
    text: str

class WhatsAppInteractive(BaseModel):
    """Interactive message model"""
    type: str = "button"
    header: Optional[WhatsAppInteractiveHeader] = None
    body: WhatsAppInteractiveBody
    footer: Optional[WhatsAppInteractiveFooter] = None
    action: WhatsAppInteractiveAction

class WhatsAppInteractiveMessage(BaseModel):
    """Model for sending interactive messages"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "interactive"
    interactive: WhatsAppInteractive

class WhatsAppListSection(BaseModel):
    """List section model"""
    title: str
    rows: List[Dict[str, str]]

class WhatsAppListAction(BaseModel):
    """List action model"""
    button: str
    sections: List[WhatsAppListSection]

class WhatsAppList(BaseModel):
    """List message model"""
    type: str = "list"
    header: Optional[WhatsAppInteractiveHeader] = None
    body: WhatsAppInteractiveBody
    footer: Optional[WhatsAppInteractiveFooter] = None
    action: WhatsAppListAction

class WhatsAppListMessage(BaseModel):
    """Model for sending list messages"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "interactive"
    interactive: WhatsAppList

class MessageResponse(BaseModel):
    """Response model for sent messages"""
    messaging_product: str
    contacts: List[Dict[str, str]]
    messages: List[Dict[str, str]]

class ConversationState(BaseModel):
    """Model for conversation state"""
    session_id: str
    user_phone: str
    current_intent: Optional[str] = None
    current_agent: Optional[str] = None
    conversation_data: Dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    last_activity: datetime
    
class UserSession(BaseModel):
    """Model for user session"""
    id: str
    user_id: str
    user_phone: str
    created_at: datetime
    last_activity: datetime
    conversation_state: str
    language_preference: str
    active_operations: List[str] = Field(default_factory=list)
    security_flags: Dict[str, Any] = Field(default_factory=dict)
    session_data: Dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime