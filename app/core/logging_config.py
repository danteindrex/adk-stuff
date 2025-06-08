"""
Logging configuration for the application
"""

import logging
import logging.config
import sys
from typing import Dict, Any
from app.core.config import settings

def setup_logging() -> None:
    """Setup application logging configuration"""
    
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(filename)s %(lineno)d %(funcName)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed" if settings.DEBUG else "default",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False
            },
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"] if settings.ENVIRONMENT == "production" else ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)

class StructuredLogger:
    """Structured logger for consistent logging across the application"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"{message} | {extra_data}" if extra_data else message)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{message} | {extra_data}" if extra_data else message
        
        if error:
            self.logger.error(full_message, exc_info=error)
        else:
            self.logger.error(full_message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.warning(f"{message} | {extra_data}" if extra_data else message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.debug(f"{message} | {extra_data}" if extra_data else message)