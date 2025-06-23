"""
Application configuration settings
"""
from pydantic import BaseSettings, Field, validator
from typing import List, Optional, Union, Annotated
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # WhatsApp Business Cloud API Configuration
    WHATSAPP_PHONE_NUMBER_ID: str = Field(..., env="WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_ACCESS_TOKEN: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = Field(..., env="WHATSAPP_BUSINESS_ACCOUNT_ID")
    WHATSAPP_APP_ID: str = Field(..., env="WHATSAPP_APP_ID")
    WHATSAPP_APP_SECRET: str = Field(..., env="WHATSAPP_APP_SECRET")
    WHATSAPP_VERIFY_TOKEN: str = Field(..., env="WHATSAPP_VERIFY_TOKEN")
    WHATSAPP_WEBHOOK_SECRET: Optional[str] = Field(None, env="WHATSAPP_WEBHOOK_SECRET")
    WHATSAPP_API_VERSION: str = Field(default="v17.0", env="WHATSAPP_API_VERSION")
    WHATSAPP_API_URL: str = Field(default="https://graph.facebook.com", env="WHATSAPP_API_URL")
    
    # WhatsApp Message Configuration
    WHATSAPP_MESSAGE_TEMPLATE_NAMESPACE: Optional[str] = Field(
        default=None, 
        env="WHATSAPP_MESSAGE_TEMPLATE_NAMESPACE"
    )
    WHATSAPP_MESSAGE_PREVIEW_URL: bool = Field(default=False, env="WHATSAPP_MESSAGE_PREVIEW_URL")
    WHATSAPP_MESSAGE_TIMEOUT: int = Field(default=30, env="WHATSAPP_MESSAGE_TIMEOUT")
    
    # WhatsApp Webhook Configuration
    WHATSAPP_WEBHOOK_PATH: str = Field(
        default="/api/v1/whatsapp/webhook", 
        env="WHATSAPP_WEBHOOK_PATH"
    )
    WHATSAPP_WEBHOOK_VERIFY_TIMEOUT: int = Field(
        default=5, 
        env="WHATSAPP_WEBHOOK_VERIFY_TIMEOUT"
    )
    
    # Server Cache Configuration
    CACHE_DEFAULT_TTL_HOURS: int = Field(default=48, env="CACHE_DEFAULT_TTL_HOURS")  # 2 days
    
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
    
  
    
    # FAQ Cache Configuration
    FAQ_CACHE_ENABLED: bool = Field(default=True, env="FAQ_CACHE_ENABLED")
    FAQ_CACHE_TTL_HOURS: int = Field(default=24, env="FAQ_CACHE_TTL_HOURS")
    FAQ_SIMILARITY_THRESHOLD: float = Field(default=0.8, env="FAQ_SIMILARITY_THRESHOLD")
    FAQ_MAX_CACHE_SIZE: int = Field(default=1000, env="FAQ_MAX_CACHE_SIZE")
    SUPPORTED_LANGUAGES: Optional[List[str]] = Field(
        default_factory=lambda: ["en", "lg", "luo", "nyn"], env="SUPPORTED_LANGUAGES"
    )
    GOVERNMENT_SERVICES: Optional[List[str]] = Field(
        default_factory=lambda: ["nira", "ura", "nssf", "nlis"], env="GOVERNMENT_SERVICES"
    )

    # Validators to split the raw CSV strings into lists
    @validator("SUPPORTED_LANGUAGES", "GOVERNMENT_SERVICES", pre=True)
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive=True
        extra="ignore"  # avoid errors on other .env entries


    @property
    def mcp_server_list(self) -> List[str]:
        """Get list of MCP server URLs"""
        return [url.strip() for url in self.MCP_SERVER_URLS.split(",")]


# Create global settings instance
settings = Settings()