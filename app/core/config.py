"""
Application configuration settings
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Twilio WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str = Field(..., env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(..., env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str = Field(..., env="TWILIO_WHATSAPP_NUMBER")
    TWILIO_WEBHOOK_VERIFY_TOKEN: str = Field(..., env="TWILIO_WEBHOOK_VERIFY_TOKEN")
    TWILIO_API_KEY_SID: Optional[str] = Field(None, env="TWILIO_API_KEY_SID")
    
    # Legacy WhatsApp Business API (can be removed after migration)
    WHATSAPP_ACCESS_TOKEN: Optional[str] = Field(None, env="WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = Field(None, env="WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: Optional[str] = Field(None, env="WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = Field(None, env="WHATSAPP_BUSINESS_ACCOUNT_ID")
    
    # Firebase Configuration (for FAQ caching)
    FIREBASE_PROJECT_ID: Optional[str] = Field(None, env="FIREBASE_PROJECT_ID")
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = Field(None, env="FIREBASE_PRIVATE_KEY_ID")
    FIREBASE_PRIVATE_KEY: Optional[str] = Field(None, env="FIREBASE_PRIVATE_KEY")
    FIREBASE_CLIENT_EMAIL: Optional[str] = Field(None, env="FIREBASE_CLIENT_EMAIL")
    FIREBASE_CLIENT_ID: Optional[str] = Field(None, env="FIREBASE_CLIENT_ID")
    FIREBASE_AUTH_URI: str = Field(default="https://accounts.google.com/o/oauth2/auth", env="FIREBASE_AUTH_URI")
    FIREBASE_TOKEN_URI: str = Field(default="https://oauth2.googleapis.com/token", env="FIREBASE_TOKEN_URI")
    
    # Google Cloud (Optional - only needed for advanced features)
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(None, env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Security
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    ENCRYPTION_KEY: str = Field(..., env="ENCRYPTION_KEY")
    ADMIN_WHATSAPP_GROUP: str = Field(..., env="ADMIN_WHATSAPP_GROUP")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # MCP Servers
    MCP_SERVER_URLS: str = Field(default="http://localhost:8001", env="MCP_SERVER_URLS")
    
    # Frontend (for CORS)
    FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    MAX_CONCURRENT_SESSIONS: int = Field(default=1000, env="MAX_CONCURRENT_SESSIONS")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Service Configuration
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    RETRY_DELAY_SECONDS: int = Field(default=2, env="RETRY_DELAY_SECONDS")
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    
    # Supported Languages
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "lg", "luo", "nyn"], 
        env="SUPPORTED_LANGUAGES"
    )
    
    # Government Services
    GOVERNMENT_SERVICES: List[str] = Field(
        default=["nira", "ura", "nssf", "nlis"],
        env="GOVERNMENT_SERVICES"
    )
    
    # FAQ Cache Configuration
    FAQ_CACHE_ENABLED: bool = Field(default=True, env="FAQ_CACHE_ENABLED")
    FAQ_CACHE_TTL_HOURS: int = Field(default=24, env="FAQ_CACHE_TTL_HOURS")
    FAQ_SIMILARITY_THRESHOLD: float = Field(default=0.8, env="FAQ_SIMILARITY_THRESHOLD")
    FAQ_MAX_CACHE_SIZE: int = Field(default=1000, env="FAQ_MAX_CACHE_SIZE")
    
    @property
    def mcp_server_list(self) -> List[str]:
        """Get list of MCP server URLs"""
        return [url.strip() for url in self.MCP_SERVER_URLS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()