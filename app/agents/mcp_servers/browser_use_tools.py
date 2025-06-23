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
from typing import Dict, Any, Optional, List, Tuple, Callable
from functools import wraps
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv
import google.generativeai as genai
from browser_use import Agent
from google.adk.tools import FunctionTool
from typing import Union, List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '300'))  # 5 minutes
MAX_RETRIES = int(os.getenv('BROWSER_MAX_RETRIES', '3'))
BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
BROWSER_SLOW_MO = int(os.getenv('BROWSER_SLOW_MO', '0'))  # milliseconds
CONVERSATION_LOG_DIR = os.getenv('CONVERSATION_LOG_DIR', './logs/browser_use/')

# Ensure log directory exists
os.makedirs(CONVERSATION_LOG_DIR, exist_ok=True)

# Initialize the Gemini model
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel(
    model_name=os.getenv('BROWSER_USE_MODEL', 'gemini-1.5-flash'),
    generation_config={
        'temperature': 0.2,
        'max_output_tokens': 2048,
    }
)

class BrowserAutomationError(Exception):
    """Custom exception for browser automation errors"""
    pass

class BrowserType(str, Enum):
    """Supported browser types"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

@dataclass
class BrowserConfig:
    """Configuration for browser automation"""
    headless: bool = BROWSER_HEADLESS
    slow_mo: int = BROWSER_SLOW_MO
    browser_type: BrowserType = BrowserType.CHROMIUM
    viewport: Optional[Dict[str, int]] = None
    user_agent: Optional[str] = None
    proxy: Optional[Dict[str, str]] = None
    extra_http_headers: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for browser-use"""
        return {
            'headless': self.headless,
            'slow_mo': self.slow_mo,
            'browser_type': self.browser_type.value,
            'viewport': self.viewport,
            'user_agent': self.user_agent,
            'proxy': self.proxy,
            'extra_http_headers': self.extra_http_headers
        }

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = MAX_RETRIES, backoff_factor: float = 1.0):
    """Decorator to retry a function on failure with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        wait_time = backoff_factor * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {wait_time:.1f} seconds..."
                        )
                        await asyncio.sleep(wait_time)
            raise BrowserAutomationError(
                f"Failed after {max_retries} attempts. Last error: {str(last_exception)}"
            ) from last_exception
        return wrapper
    return decorator

@asynccontextmanager
async def create_browser_agent(
    task_description: str,
    config: Optional[BrowserConfig] = None,
    **kwargs
):
    """Context manager for browser agent with proper resource cleanup"""
    config = config or BrowserConfig()
    agent = None
    try:
        agent = Agent(
            task=task_description,
            llm=llm,
            **config.to_dict(),
            **kwargs
        )
        yield agent
    except Exception as e:
        logger.error(f"Failed to create browser agent: {e}")
        raise BrowserAutomationError(f"Browser agent creation failed: {e}") from e
    finally:
        if agent:
            try:
                await agent.close()
            except Exception as e:
                logger.error(f"Error closing browser agent: {e}")

async def get_browser_tools():
    """
    Get Browser-Use agent tools for AI-powered browser automation
    
    Returns:
        List of FunctionTool instances for browser automation
    """
    
    @retry_on_failure()
    async def browser_use_automation(
        task_description: str,
        url: str,
        max_steps: int = 10,
        timeout: int = DEFAULT_TIMEOUT,
        use_vision: bool = True,
        tool_context: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute AI-powered web automation using Browser-Use agent
        
        Args:
            task_description: Natural language description of the task
            url: Target URL to automate
            max_steps: Maximum number of automation steps
            timeout: Timeout in seconds
            use_vision: Whether to use vision capabilities
            tool_context: Additional context for the tool
            config: Browser configuration overrides
            
        Returns:
            Dictionary with automation results or error information
        """
        start_time = time.time()
        logger.info(f"Starting browser automation for: {url}")
        
        try:
            # Parse config
            browser_config = BrowserConfig(
                **config
            ) if config else BrowserConfig()
            
            # Generate unique task ID for logging
            task_id = f"task_{int(time.time())}"
            log_path = os.path.join(CONVERSATION_LOG_DIR, f"{task_id}")
            
            async with create_browser_agent(
                task=task_description,
                config=browser_config,
                use_vision=use_vision,
                max_steps=max_steps,
                save_conversation_path=log_path,
                timeout=timeout * 1000,  # Convert to milliseconds
            ) as agent:
                
                logger.info(f"Executing task: {task_description}")
                
                # Execute the automation task asynchronously
                result = await agent.run(url)
                
                execution_time = time.time() - start_time
                logger.info(
                    f"Browser automation completed in {execution_time:.2f}s. "
                    f"Steps taken: {getattr(result, 'steps_taken', 'N/A')}"
                )
                
                return {
                    "status": "success",
                    "result": str(result),
                    "method": "browser_use",
                    "task": task_description,
                    "url": url,
                    "steps_taken": getattr(result, 'steps_taken', 0),
                    "execution_time": execution_time,
                    "log_path": log_path
                }
                
        except ImportError as e:
            error_msg = "Browser-Use agent not installed. Install with: pip install browser-use playwright"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "suggestion": "Run: pip install browser-use playwright && playwright install chromium"
            }
        except TimeoutError as e:
            error_msg = f"Browser automation timed out after {timeout} seconds"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "suggestion": "Increase timeout or simplify the task"
            }
        except Exception as e:
            error_msg = f"Browser automation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "error": error_msg,
                "method": "browser_use"
            }
    
    @retry_on_failure()
    async def extract_data_with_ai(
        url: str,
        data_description: str,
        selectors: Optional[Dict[str, str]] = None,
        tool_context: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from web pages using AI-powered automation
        
        Args:
            url: Target URL to extract data from
            data_description: Natural language description of the data to extract
            selectors: Optional CSS selectors as hints for extraction
            tool_context: Additional context for the extraction
            config: Browser configuration overrides
            
        Returns:
            Dictionary with extracted data or error information
        """
        task_description = f"Extract {data_description} from {url}"
        if selectors:
            task_description += f" using these selectors as hints: {selectors}"
            
        # Execute the browser automation
        result = await browser_use_automation(
            task_description=task_description,
            url=url,
            config=config,
            tool_context=tool_context
        )
        
        if result["status"] == "success":
            # Process the result to extract structured data
            try:
                # Here you would add logic to parse the result into structured data
                # This is a simplified example
                extracted_data = {
                    "url": url,
                    "extracted_at": time.time(),
                    "data": str(result.get("result", "")),
                    "selectors_used": selectors or {}
                }
                result["extracted_data"] = extracted_data
            except Exception as e:
                logger.error(f"Failed to process extracted data: {e}")
                result.update({
                    "status": "error",
                    "error": f"Data processing failed: {str(e)}"
                })
        
        return result
        try:
            task_description = f"Extract {data_description} from {url}"
            if selectors:
                task_description += f" using these selectors as hints: {selectors}"
            
            result = browser_use_automation(
                task_description=task_description,
                url=url,
                max_steps=5,
                timeout=30
            )
            
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "data": result.get("result"),
                    "method": "ai_extraction",
                    "data_description": data_description
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"AI data extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def fill_form_with_ai(
        url: str,
        form_data: Dict[str, Any],
        submit: bool = True,
        tool_context=None
    ) -> dict:
        """
        Fill web forms using AI-powered automation
        
        Args:
            url: Target URL with the form
            form_data: Data to fill in the form
            submit: Whether to submit the form after filling
        """
        try:
            task_description = f"Fill the form at {url} with the following data: {form_data}"
            if submit:
                task_description += " and submit the form"
            
            result = browser_use_automation(
                task_description=task_description,
                url=url,
                max_steps=15,
                timeout=45
            )
            
            return {
                "status": result.get("status"),
                "result": result.get("result"),
                "method": "ai_form_filling",
                "form_data": form_data,
                "submitted": submit,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"AI form filling failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def navigate_and_interact(
        url: str,
        interactions: List[str],
        tool_context=None
    ) -> dict:
        """
        Navigate website and perform multiple interactions
        
        Args:
            url: Starting URL
            interactions: List of interaction descriptions
        """
        try:
            task_description = f"Navigate to {url} and perform these interactions: {'; '.join(interactions)}"
            
            result = browser_use_automation(
                task_description=task_description,
                url=url,
                max_steps=len(interactions) * 3,
                timeout=60
            )
            
            return {
                "status": result.get("status"),
                "result": result.get("result"),
                "method": "ai_navigation",
                "interactions": interactions,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"AI navigation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def take_screenshot_with_context(
        url: str,
        context_description: str = None,
        element_description: str = None,
        tool_context=None
    ) -> dict:
        """
        Take contextual screenshots using AI
        
        Args:
            url: Target URL
            context_description: Description of what to focus on
            element_description: Specific element to screenshot
        """
        try:
            task_description = f"Take a screenshot of {url}"
            if context_description:
                task_description += f" focusing on {context_description}"
            if element_description:
                task_description += f" specifically the {element_description}"
            
            result = browser_use_automation(
                task_description=task_description,
                url=url,
                max_steps=3,
                timeout=20
            )
            
            return {
                "status": result.get("status"),
                "screenshot_info": result.get("result"),
                "method": "ai_screenshot",
                "context": context_description,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"AI screenshot failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Government portal specific AI automation
    def automate_government_portal(
        portal_name: str,
        portal_url: str,
        service_type: str,
        user_data: Dict[str, Any],
        tool_context=None
    ) -> dict:
        """
        Automate Uganda government portals using AI
        
        Args:
            portal_name: Name of the government portal (NIRA, URA, NSSF, NLIS)
            portal_url: Portal URL
            service_type: Type of service to access
            user_data: User data for the service
        """
        try:
            task_description = f"""
            Access the {portal_name} government portal at {portal_url} to {service_type}.
            Use the following user information: {user_data}
            Navigate through the portal, fill any required forms, and retrieve the requested information.
            Handle any authentication, captchas, or multi-step processes automatically.
            """
            
            result = browser_use_automation(
                task_description=task_description,
                url=portal_url,
                max_steps=20,
                timeout=120,
                use_vision=True
            )
            
            return {
                "status": result.get("status"),
                "portal": portal_name,
                "service_type": service_type,
                "result": result.get("result"),
                "method": "ai_government_portal",
                "user_data_used": bool(user_data),
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Government portal automation failed: {e}")
            return {
                "status": "error",
                "portal": portal_name,
                "error": str(e)
            }
    
    # Create Browser-Use tools
    browser_use_tools = [
        FunctionTool(browser_use_automation),
        FunctionTool(extract_data_with_ai),
        FunctionTool(fill_form_with_ai),
        FunctionTool(navigate_and_interact),
        FunctionTool(take_screenshot_with_context),
        FunctionTool(automate_government_portal)
    ]
    
    logger.info(f"Created {len(browser_use_tools)} Browser-Use AI automation tools")
    return browser_use_tools

async def get_smart_automation_tools():
    """Get intelligent automation tools that combine multiple approaches"""
    
    def smart_government_service(
        service_name: str,
        user_phone: str,
        service_data: Dict[str, Any],
        preferred_method: str = "ai_first",
        tool_context=None
    ) -> dict:
        """
        Smart government service automation with multiple fallback methods
        
        Args:
            service_name: Government service (birth_certificate, tax_status, nssf_balance, land_verification)
            user_phone: User's phone number for identification
            service_data: Service-specific data
            preferred_method: Preferred automation method
        """
        try:
            # Map services to portals
            service_mapping = {
                "birth_certificate": {
                    "portal": "NIRA",
                    "url": "https://www.nira.go.ug",
                    "service_type": "birth certificate verification"
                },
                "tax_status": {
                    "portal": "URA", 
                    "url": "https://www.ura.go.ug",
                    "service_type": "tax status check"
                },
                "nssf_balance": {
                    "portal": "NSSF",
                    "url": "https://www.nssfug.org", 
                    "service_type": "balance inquiry"
                },
                "land_verification": {
                    "portal": "NLIS",
                    "url": "https://nlis.go.ug",
                    "service_type": "land ownership verification"
                }
            }
            
            if service_name not in service_mapping:
                return {
                    "status": "error",
                    "error": f"Unknown service: {service_name}",
                    "available_services": list(service_mapping.keys())
                }
            
            portal_info = service_mapping[service_name]
            
            # Prepare user data
            user_data = {
                "phone_number": user_phone,
                **service_data
            }
            
            # Try AI automation first
            result = automate_government_portal(
                portal_name=portal_info["portal"],
                portal_url=portal_info["url"],
                service_type=portal_info["service_type"],
                user_data=user_data
            )
            
            return {
                "service": service_name,
                "portal": portal_info["portal"],
                "user_phone": user_phone,
                "automation_result": result,
                "method": "smart_automation"
            }
            
        except Exception as e:
            logger.error(f"Smart government service failed: {e}")
            return {
                "status": "error",
                "service": service_name,
                "error": str(e)
            }
    
    # Create smart automation tools
    smart_tools = [
        FunctionTool(smart_government_service)
    ]
    
    logger.info(f"Created {len(smart_tools)} smart automation tools")
    return smart_tools

# Helper function for government portal automation
def automate_government_portal(portal_name: str, portal_url: str, service_type: str, user_data: Dict[str, Any]) -> dict:
    """Helper function for government portal automation"""
    try:
        from browser_use import Agent
        
        task_description = f"""
        Access the {portal_name} government portal at {portal_url} to {service_type}.
        Use the following user information: {user_data}
        Navigate through the portal, fill any required forms, and retrieve the requested information.
        Handle any authentication, captchas, or multi-step processes automatically.
        """
        
        agent = Agent(
            task=task_description,
            llm=llm,
            use_vision=True,
            max_steps=20,
            save_conversation_path="./logs/browser_use/"
        )
        
        result = agent.run(portal_url)
        
        return {
            "status": "success",
            "result": result,
            "method": "browser_use_government"
        }
        
    except ImportError:
        return {
            "status": "error",
            "error": "Browser-Use agent not available"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e)
        }