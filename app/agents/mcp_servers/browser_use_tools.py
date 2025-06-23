"""
Browser-Use MCP Tools
AI-powered browser automation using browser-use agent

This module provides production-ready browser automation capabilities using the browser-use package.
It includes features like connection pooling, retries, timeouts, and comprehensive error handling.
"""
import os
import asyncio
import json
import logging
import time
from functools import wraps
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv
import google.generativeai as genai
from browser_use import Agent, BrowserConfig, browser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()




# Initialize the Gemini model
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
llm = genai.GenerativeModel(
    model_name=os.getenv('BROWSER_USE_MODEL', 'gemini-1.5-flash'),
    generation_config={
        'temperature': 0.2,
        
    }
)




logger = logging.getLogger(__name__)





       



async def automate_government_portal(description) -> dict:
    """Helper function for government portal automation"""

    from browser_use import BrowserSession

    browser_session = BrowserSession(
        headless=True,
        
        
    )
            
    task_description = description
        
    agent = Agent(
            task=task_description,
            llm=llm,
            browser_session=browser_session,
            max_steps=5,
            timeout=30,
            use_vision=True,
            max_steps=20,
            save_conversation_path="./logs/browser_use/"
        )
    result = agent.run(portal_url)
    return result
        
