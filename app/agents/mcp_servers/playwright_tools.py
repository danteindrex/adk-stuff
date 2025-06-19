"""
Playwright MCP Server with Browser-Use Agent Fallback
Uses actual MCP Playwright server with browser-use as fallback function tool
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

# Global variables to store toolsets and exit stacks
_playwright_toolset = None
_exit_stacks = []

async def get_playwright_mcp_tools():
    """Get actual Playwright MCP server tools"""
    global _playwright_toolset
    
    if _playwright_toolset is None:
        try:
            logger.info("Initializing Playwright MCP server...")
            
            # Create MCPToolset directly with connection parameters

            # Note: Playwright MCP may not be available in all environments
            # The system will gracefully fall back to browser-use tools
            try:
                playwright_toolset = MCPToolset(
                    connection_params=StdioConnectionParams(
                        command="npx",
                        args=[
                            "-y", 
                            "@modelcontextprotocol/server-playwright@latest"
                        ]
                    )
                )
            except Exception as mcp_error:
                logger.warning(f"Playwright MCP initialization failed: {mcp_error}")
                logger.info("Continuing with browser-use tools only")
                return []
            
            # Store the toolset as a single item list to match expected interface
            _playwright_toolset = [playwright_toolset]
            logger.info(f"Playwright MCP server initialized successfully")
            logger.info(f"Playwright MCP toolset created: {playwright_toolset}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Playwright MCP server: {e}")
            logger.warning("Playwright MCP server not available - browser-use fallback will be used")
            _playwright_toolset = []
    
    return _playwright_toolset if _playwright_toolset else []

def get_browser_use_fallback_tools():
    """Get browser-use agent tools as fallback function tools"""
    
    def browser_use_automation(
        task_description: str,
        url: str,
        max_steps: int = 10,
        timeout: int = 60,
        use_vision: bool = True
    ) -> dict:
        """
        Use Browser-Use agent for AI-powered web automation when Playwright MCP fails
        
        Args:
            task_description: Natural language description of the task
            url: Target URL to automate
            max_steps: Maximum number of automation steps
            timeout: Timeout in seconds
            use_vision: Whether to use vision capabilities
            
        Returns:
            Dictionary with automation results
        """
        try:
            logger.info(f"Using browser-use fallback for: {task_description}")
            
            # Try to import browser-use
            try:
                from browser_use import Agent
            except ImportError:
                logger.error("Browser-Use agent not installed. Install with: pip install browser-use")
                return {
                    "status": "error",
                    "error": "Browser-Use agent not available",
                    "suggestion": "Install browser-use package: pip install browser-use",
                    "method": "browser_use_fallback"
                }
            
            # Create browser-use agent instance
            agent = Agent(
                task=task_description,
                llm=None,  # Will use default LLM
                use_vision=use_vision,
                max_steps=max_steps,
                save_conversation_path="./logs/browser_use/"
            )
            
            # Execute the automation task
            result = agent.run(url)
            
            return {
                "status": "success",
                "result": result,
                "method": "browser_use_fallback",
                "task": task_description,
                "url": url,
                "steps_taken": getattr(result, 'steps_taken', 0)
            }
            
        except Exception as e:
            logger.error(f"Browser-Use automation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "browser_use_fallback"
            }
    
    def extract_data_with_browser_use(
        url: str,
        data_description: str,
        selectors: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Extract data from web pages using AI-powered automation
        
        Args:
            url: Target URL
            data_description: Description of what data to extract
            selectors: Optional CSS selectors as hints
            
        Returns:
            Dictionary with extracted data
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
                    "method": "browser_use_extraction",
                    "data_description": data_description
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"AI data extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "browser_use_extraction"
            }
    
    def fill_form_with_browser_use(
        url: str,
        form_data: Dict[str, Any],
        submit: bool = True
    ) -> dict:
        """
        Fill web forms using AI-powered automation
        
        Args:
            url: Target URL with the form
            form_data: Data to fill in the form
            submit: Whether to submit the form after filling
            
        Returns:
            Dictionary with form filling results
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
                "method": "browser_use_form_filling",
                "form_data": form_data,
                "submitted": submit,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"AI form filling failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "browser_use_form_filling"
            }
    
    def take_screenshot_with_browser_use(
        url: str,
        context_description: Optional[str] = None,
        element_description: Optional[str] = None
    ) -> dict:
        """
        Take contextual screenshots using AI
        
        Args:
            url: Target URL
            context_description: Description of what to focus on
            element_description: Specific element to screenshot
            
        Returns:
            Dictionary with screenshot information
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
                "method": "browser_use_screenshot",
                "context": context_description,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"AI screenshot failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "browser_use_screenshot"
            }
    
    # Create Browser-Use fallback tools as FunctionTools
    browser_use_tools = [
        FunctionTool(browser_use_automation),
        FunctionTool(extract_data_with_browser_use),
        FunctionTool(fill_form_with_browser_use),
        FunctionTool(take_screenshot_with_browser_use)
    ]
    
    logger.info(f"Created {len(browser_use_tools)} Browser-Use fallback tools")
    return browser_use_tools

async def get_combined_automation_tools():
    """Get combined Playwright MCP tools with browser-use fallbacks"""
    try:
        # First try to get Playwright MCP tools
        playwright_tools = await get_playwright_mcp_tools()
        
        # Always get browser-use fallback tools
        browser_use_tools = get_browser_use_fallback_tools()
        
        # Combine both toolsets
        all_tools = []
        
        if playwright_tools:
            all_tools.extend(playwright_tools)
            logger.info(f"Added {len(playwright_tools)} Playwright MCP tools")
        else:
            logger.warning("No Playwright MCP tools available")
        
        all_tools.extend(browser_use_tools)
        logger.info(f"Added {len(browser_use_tools)} browser-use fallback tools")
        
        logger.info(f"Total automation tools available: {len(all_tools)}")
        return all_tools
        
    except Exception as e:
        logger.error(f"Error getting combined automation tools: {e}")
        # Return just browser-use tools as fallback
        return get_browser_use_fallback_tools()

# Government portal specific automation functions
async def get_government_portal_tools():
    """Get specialized tools for Uganda government portals"""
    
    def automate_nira_portal(
        reference_number: str,
        action: str = "check_status"
    ) -> dict:
        """
        Automate NIRA (National Identification and Registration Authority) portal
        
        Args:
            reference_number: NIRA reference number (format: NIRA/YYYY/NNNNNN)
            action: Action to perform (default: check_status)
            
        Returns:
            Dictionary with portal automation results
        """
        try:
            nira_url = "https://www.nira.go.ug"
            task_description = f"Check birth certificate status for reference: {reference_number}"
            
            # Use browser-use automation for NIRA portal
            result = browser_use_automation(
                task_description=task_description,
                url=nira_url,
                max_steps=10,
                timeout=60
            )
            
            return {
                "portal": "NIRA",
                "reference_number": reference_number,
                "action": action,
                "automation_result": result,
                "method": "government_portal_automation"
            }
            
        except Exception as e:
            logger.error(f"NIRA portal automation failed: {e}")
            return {
                "status": "error",
                "portal": "NIRA",
                "error": str(e)
            }
    
    def automate_ura_portal(
        tin_number: str,
        action: str = "check_tax_status"
    ) -> dict:
        """
        Automate URA (Uganda Revenue Authority) portal
        
        Args:
            tin_number: Tax Identification Number (10 digits)
            action: Action to perform (default: check_tax_status)
            
        Returns:
            Dictionary with portal automation results
        """
        try:
            ura_url = "https://www.ura.go.ug"
            task_description = f"Check tax status for TIN: {tin_number}"
            
            result = browser_use_automation(
                task_description=task_description,
                url=ura_url,
                max_steps=10,
                timeout=60
            )
            
            return {
                "portal": "URA",
                "tin_number": tin_number,
                "action": action,
                "automation_result": result,
                "method": "government_portal_automation"
            }
            
        except Exception as e:
            logger.error(f"URA portal automation failed: {e}")
            return {
                "status": "error",
                "portal": "URA",
                "error": str(e)
            }
    
    def automate_nssf_portal(
        membership_number: str,
        action: str = "check_balance"
    ) -> dict:
        """
        Automate NSSF (National Social Security Fund) portal
        
        Args:
            membership_number: NSSF membership number (8-12 digits)
            action: Action to perform (default: check_balance)
            
        Returns:
            Dictionary with portal automation results
        """
        try:
            nssf_url = "https://www.nssfug.org"
            task_description = f"Check NSSF balance for membership: {membership_number}"
            
            result = browser_use_automation(
                task_description=task_description,
                url=nssf_url,
                max_steps=10,
                timeout=60
            )
            
            return {
                "portal": "NSSF",
                "membership_number": membership_number,
                "action": action,
                "automation_result": result,
                "method": "government_portal_automation"
            }
            
        except Exception as e:
            logger.error(f"NSSF portal automation failed: {e}")
            return {
                "status": "error",
                "portal": "NSSF",
                "error": str(e)
            }
    
    def automate_nlis_portal(
        plot_number: Optional[str] = None,
        gps_coordinates: Optional[str] = None,
        action: str = "verify_ownership"
    ) -> dict:
        """
        Automate NLIS (National Land Information System) portal
        
        Args:
            plot_number: Plot number for land verification
            gps_coordinates: GPS coordinates for land verification
            action: Action to perform (default: verify_ownership)
            
        Returns:
            Dictionary with portal automation results
        """
        try:
            nlis_url = "https://nlis.go.ug"
            
            if plot_number:
                task_description = f"Verify land ownership for plot: {plot_number}"
            elif gps_coordinates:
                task_description = f"Verify land ownership for coordinates: {gps_coordinates}"
            else:
                return {
                    "status": "error",
                    "portal": "NLIS",
                    "error": "Either plot_number or gps_coordinates required"
                }
            
            result = browser_use_automation(
                task_description=task_description,
                url=nlis_url,
                max_steps=10,
                timeout=60
            )
            
            return {
                "portal": "NLIS",
                "plot_number": plot_number,
                "gps_coordinates": gps_coordinates,
                "action": action,
                "automation_result": result,
                "method": "government_portal_automation"
            }
            
        except Exception as e:
            logger.error(f"NLIS portal automation failed: {e}")
            return {
                "status": "error",
                "portal": "NLIS",
                "error": str(e)
            }
    
    # Create government portal tools as FunctionTools
    portal_tools = [
        FunctionTool(automate_nira_portal),
        FunctionTool(automate_ura_portal),
        FunctionTool(automate_nssf_portal),
        FunctionTool(automate_nlis_portal)
    ]
    
    logger.info(f"Created {len(portal_tools)} government portal tools")
    return portal_tools

async def cleanup_playwright():
    """Clean up Playwright MCP connections and resources"""
    global _playwright_toolset, _exit_stacks
    
    try:
        # Clean up exit stacks
        for exit_stack in _exit_stacks:
            try:
                await exit_stack.aclose()
            except Exception as e:
                logger.error(f"Error closing exit stack: {e}")
        
        # Reset global variables
        _playwright_toolset = None
        _exit_stacks.clear()
        
        logger.info("Playwright MCP connections cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error during Playwright cleanup: {e}")

# Helper function for browser-use automation (used by government portal tools)
def browser_use_automation(task_description: str, url: str, max_steps: int = 10, timeout: int = 60) -> dict:
    """Helper function for browser-use automation"""
    try:
        from browser_use import Agent
        
        agent = Agent(
            task=task_description,
            llm=None,
            use_vision=True,
            max_steps=max_steps,
            save_conversation_path="./logs/browser_use/"
        )
        
        result = agent.run(url)
        
        return {
            "status": "success",
            "result": result,
            "method": "browser_use_helper"
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