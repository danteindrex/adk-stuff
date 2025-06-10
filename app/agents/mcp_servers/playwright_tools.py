"""
Playwright MCP Tools with Browser-Use Agent Fallback
Enhanced browser automation with intelligent fallback mechanisms
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

# Global variables to store toolsets and exit stacks
_playwright_toolset = None
_browser_use_toolset = None
_exit_stacks = []

async def get_playwright_tools():
    """Get Playwright MCP tools with enhanced error handling"""
    global _playwright_toolset
    
    if _playwright_toolset is None:
        try:
            tools, exit_stack = await MCPToolset.from_server(
                connection_params=StdioServerParameters(
                    command="npx",
                    args=[
                        "-y",
                        "@microsoft/playwright-mcp@latest"
                    ]
                )
            )
            _playwright_toolset = tools
            _exit_stacks.append(exit_stack)
            logger.info("Playwright MCP tools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright MCP tools: {e}")
            # Return empty list if MCP server fails
            _playwright_toolset = []
    
    return _playwright_toolset

async def get_browser_use_tools():
    """Get Browser-Use agent tools as fallback for Playwright failures"""
    
    def browser_use_automation(
        task_description: str,
        url: str,
        actions: List[Dict[str, Any]] = None,
        timeout: int = 30,
        tool_context=None
    ) -> dict:
        """
        Use Browser-Use agent for web automation when Playwright fails
        
        Args:
            task_description: Natural language description of the task
            url: Target URL to automate
            actions: Optional list of specific actions to perform
            timeout: Timeout in seconds
        """
        try:
            # Import browser-use agent
            from browser_use import Agent
            
            # Create browser-use agent instance
            agent = Agent(
                task=task_description,
                llm=None,  # Will use default LLM
                use_vision=True,
                save_conversation_path="./browser_use_logs/"
            )
            
            # Execute the automation task
            result = agent.run(url)
            
            return {
                "status": "success",
                "result": result,
                "method": "browser_use",
                "task": task_description,
                "url": url
            }
            
        except ImportError:
            logger.error("Browser-Use agent not installed. Install with: pip install browser-use")
            return {
                "status": "error",
                "error": "Browser-Use agent not available",
                "suggestion": "Install browser-use package or use alternative automation"
            }
        except Exception as e:
            logger.error(f"Browser-Use automation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "method": "browser_use"
            }
    
    def smart_web_automation(
        task_description: str,
        url: str,
        form_data: Dict[str, Any] = None,
        expected_elements: List[str] = None,
        retry_count: int = 3,
        tool_context=None
    ) -> dict:
        """
        Intelligent web automation that tries multiple approaches
        
        Args:
            task_description: What to accomplish
            url: Target website
            form_data: Data to fill in forms
            expected_elements: Elements that should be present
            retry_count: Number of retry attempts
        """
        attempts = []
        
        for attempt in range(retry_count):
            try:
                # First try: Use Playwright MCP if available
                if _playwright_toolset and len(_playwright_toolset) > 0:
                    try:
                        # This would use the Playwright MCP tools
                        # For now, we'll simulate the call
                        playwright_result = _simulate_playwright_call(
                            task_description, url, form_data, expected_elements
                        )
                        
                        if playwright_result.get("status") == "success":
                            return {
                                "status": "success",
                                "result": playwright_result,
                                "method": "playwright_mcp",
                                "attempt": attempt + 1
                            }
                        else:
                            attempts.append(f"Playwright attempt {attempt + 1}: {playwright_result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        attempts.append(f"Playwright attempt {attempt + 1}: {str(e)}")
                
                # Second try: Use Browser-Use agent
                browser_use_result = browser_use_automation(
                    task_description=task_description,
                    url=url,
                    timeout=30
                )
                
                if browser_use_result.get("status") == "success":
                    return {
                        "status": "success",
                        "result": browser_use_result,
                        "method": "browser_use_fallback",
                        "attempt": attempt + 1,
                        "previous_attempts": attempts
                    }
                else:
                    attempts.append(f"Browser-Use attempt {attempt + 1}: {browser_use_result.get('error', 'Unknown error')}")
                
                # Wait before retry
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                attempts.append(f"Attempt {attempt + 1}: {str(e)}")
        
        return {
            "status": "error",
            "error": "All automation methods failed",
            "attempts": attempts,
            "suggestion": "Check website availability and automation parameters"
        }
    
    def extract_web_data(
        url: str,
        selectors: Dict[str, str],
        wait_for_element: str = None,
        tool_context=None
    ) -> dict:
        """
        Extract data from web pages using multiple methods
        
        Args:
            url: Target URL
            selectors: CSS selectors for data extraction
            wait_for_element: Element to wait for before extraction
        """
        try:
            # Try Browser-Use for data extraction
            task_description = f"Extract data from {url} using selectors: {selectors}"
            
            result = browser_use_automation(
                task_description=task_description,
                url=url,
                timeout=20
            )
            
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "data": result.get("result"),
                    "method": "browser_use_extraction",
                    "selectors": selectors
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error"),
                    "method": "extraction_failed"
                }
                
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def take_screenshot(
        url: str,
        element_selector: str = None,
        full_page: bool = False,
        tool_context=None
    ) -> dict:
        """
        Take screenshot of web page or specific element
        
        Args:
            url: Target URL
            element_selector: CSS selector for specific element
            full_page: Whether to capture full page
        """
        try:
            task_description = f"Take screenshot of {url}"
            if element_selector:
                task_description += f" focusing on element: {element_selector}"
            if full_page:
                task_description += " (full page)"
            
            result = browser_use_automation(
                task_description=task_description,
                url=url,
                timeout=15
            )
            
            return {
                "status": "success" if result.get("status") == "success" else "error",
                "screenshot_path": result.get("result", {}).get("screenshot_path"),
                "method": "browser_use_screenshot",
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Create function tools
    browser_tools = [
        FunctionTool(browser_use_automation),
        FunctionTool(smart_web_automation),
        FunctionTool(extract_web_data),
        FunctionTool(take_screenshot)
    ]
    
    logger.info(f"Created {len(browser_tools)} Browser-Use tools")
    return browser_tools

def _simulate_playwright_call(task_description: str, url: str, form_data: Dict = None, expected_elements: List = None) -> dict:
    """
    Simulate Playwright MCP call (replace with actual MCP tool call)
    This is a placeholder for the actual Playwright MCP integration
    """
    # In a real implementation, this would call the Playwright MCP tools
    # For now, we'll simulate a failure to trigger the Browser-Use fallback
    return {
        "status": "error",
        "error": "Playwright MCP simulation - triggering fallback"
    }

async def get_enhanced_automation_tools():
    """Get combined Playwright and Browser-Use tools"""
    playwright_tools = await get_playwright_tools()
    browser_use_tools = await get_browser_use_tools()
    
    # Combine both toolsets
    all_tools = []
    if playwright_tools:
        all_tools.extend(playwright_tools)
    all_tools.extend(browser_use_tools)
    
    logger.info(f"Created {len(all_tools)} total automation tools")
    return all_tools

# Government portal specific automation functions
async def get_government_portal_tools():
    """Get specialized tools for Uganda government portals"""
    
    def automate_nira_portal(
        reference_number: str,
        action: str = "check_status",
        tool_context=None
    ) -> dict:
        """Automate NIRA (National Identification and Registration Authority) portal"""
        try:
            nira_url = "https://www.nira.go.ug"
            task_description = f"Check birth certificate status for reference: {reference_number}"
            
            # Use smart automation with NIRA-specific parameters
            result = smart_web_automation(
                task_description=task_description,
                url=nira_url,
                form_data={"reference_number": reference_number},
                expected_elements=["#status-result", ".certificate-info"],
                retry_count=3
            )
            
            return {
                "portal": "NIRA",
                "reference_number": reference_number,
                "action": action,
                **result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "portal": "NIRA",
                "error": str(e)
            }
    
    def automate_ura_portal(
        tin_number: str,
        action: str = "check_tax_status",
        tool_context=None
    ) -> dict:
        """Automate URA (Uganda Revenue Authority) portal"""
        try:
            ura_url = "https://www.ura.go.ug"
            task_description = f"Check tax status for TIN: {tin_number}"
            
            result = smart_web_automation(
                task_description=task_description,
                url=ura_url,
                form_data={"tin_number": tin_number},
                expected_elements=["#tax-status", ".payment-info"],
                retry_count=3
            )
            
            return {
                "portal": "URA",
                "tin_number": tin_number,
                "action": action,
                **result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "portal": "URA",
                "error": str(e)
            }
    
    def automate_nssf_portal(
        membership_number: str,
        action: str = "check_balance",
        tool_context=None
    ) -> dict:
        """Automate NSSF (National Social Security Fund) portal"""
        try:
            nssf_url = "https://www.nssfug.org"
            task_description = f"Check NSSF balance for membership: {membership_number}"
            
            result = smart_web_automation(
                task_description=task_description,
                url=nssf_url,
                form_data={"membership_number": membership_number},
                expected_elements=["#balance-info", ".contribution-history"],
                retry_count=3
            )
            
            return {
                "portal": "NSSF",
                "membership_number": membership_number,
                "action": action,
                **result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "portal": "NSSF",
                "error": str(e)
            }
    
    def automate_nlis_portal(
        plot_number: str = None,
        gps_coordinates: str = None,
        action: str = "verify_ownership",
        tool_context=None
    ) -> dict:
        """Automate NLIS (National Land Information System) portal"""
        try:
            nlis_url = "https://nlis.go.ug"
            
            if plot_number:
                task_description = f"Verify land ownership for plot: {plot_number}"
                form_data = {"plot_number": plot_number}
            elif gps_coordinates:
                task_description = f"Verify land ownership for coordinates: {gps_coordinates}"
                form_data = {"gps_coordinates": gps_coordinates}
            else:
                return {
                    "status": "error",
                    "portal": "NLIS",
                    "error": "Either plot_number or gps_coordinates required"
                }
            
            result = smart_web_automation(
                task_description=task_description,
                url=nlis_url,
                form_data=form_data,
                expected_elements=["#ownership-info", ".land-details"],
                retry_count=3
            )
            
            return {
                "portal": "NLIS",
                "plot_number": plot_number,
                "gps_coordinates": gps_coordinates,
                "action": action,
                **result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "portal": "NLIS",
                "error": str(e)
            }
    
    # Create government portal tools
    portal_tools = [
        FunctionTool(automate_nira_portal),
        FunctionTool(automate_ura_portal),
        FunctionTool(automate_nssf_portal),
        FunctionTool(automate_nlis_portal)
    ]
    
    logger.info(f"Created {len(portal_tools)} government portal tools")
    return portal_tools

# Import the smart_web_automation function to make it available globally
def smart_web_automation(task_description: str, url: str, form_data: Dict[str, Any] = None, expected_elements: List[str] = None, retry_count: int = 3) -> dict:
    """Global access to smart web automation"""
    browser_tools = asyncio.run(get_browser_use_tools())
    # Find the smart_web_automation tool and call it
    for tool in browser_tools:
        if tool.func.__name__ == 'smart_web_automation':
            return tool.func(task_description, url, form_data, expected_elements, retry_count)
    
    return {"status": "error", "error": "Smart web automation tool not found"}