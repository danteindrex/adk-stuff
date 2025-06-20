"""
Browser-Use MCP Tools
AI-powered browser automation using browser-use agent
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent
from dotenv import load_dotenv

# Read GOOGLE_API_KEY into env
load_dotenv()

# Initialize the model
llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp')
import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def get_browser_tools():
    """Get Browser-Use agent tools for AI-powered browser automation"""
    
    def browser_use_automation(
        task_description: str,
        url: str,
        max_steps: int = 10,
        timeout: int = 60,
        use_vision: bool = True,
        tool_context=None
    ) -> dict:
        """
        Use Browser-Use agent for AI-powered web automation
        
        Args:
            task_description: Natural language description of the task
            url: Target URL to automate
            max_steps: Maximum number of automation steps
            timeout: Timeout in seconds
            use_vision: Whether to use vision capabilities
        """
        try:
            from browser_use import Agent
            
            # Create browser-use agent instance
            agent = Agent(
                task=task_description,
                llm=llm,  # Will use default LLM
                use_vision=use_vision,
                max_steps=max_steps,
                save_conversation_path="./logs/browser_use/"
            )
            
            # Execute the automation task
            result = agent.run(url)
            
            return {
                "status": "success",
                "result": result,
                "method": "browser_use",
                "task": task_description,
                "url": url,
                "steps_taken": getattr(result, 'steps_taken', 0)
            }
            
        except ImportError:
            logger.error("Browser-Use agent not installed. Install with: pip install browser-use")
            return {
                "status": "error",
                "error": "Browser-Use agent not available",
                "suggestion": "Install browser-use package: pip install browser-use"
            }
        except Exception as e:
            logger.error(f"Browser-Use automation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "browser_use"
            }
    
    def extract_data_with_ai(
        url: str,
        data_description: str,
        selectors: Optional[Dict[str, str]] = None,
        tool_context=None
    ) -> dict:
        """
        Extract data from web pages using AI-powered automation
        
        Args:
            url: Target URL
            data_description: Description of what data to extract
            selectors: Optional CSS selectors as hints
        """
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