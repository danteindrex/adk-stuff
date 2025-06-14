#!/usr/bin/env python3
"""
Local startup script for Uganda E-Gov WhatsApp Helpdesk
Fixed version with internal MCP tools
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment is properly configured"""
    logger.info("Checking environment configuration...")
    
    required_env_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_WHATSAPP_NUMBER',
        'JWT_SECRET_KEY',
        'ENCRYPTION_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.info("The system will use default values for missing variables")
    else:
        logger.info("✅ All required environment variables are set")
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    logger.info("Checking Python dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'google-adk',
        'redis',
        'aiohttp',
        'twilio'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.error("Please install missing packages with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required Python packages are installed")
    return True

def check_redis():
    """Check if Redis is available"""
    logger.info("Checking Redis connection...")
    
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        r.ping()
        logger.info("✅ Redis connection successful")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed: {e}")
        logger.info("The system will work without Redis but sessions won't persist")
        return False

async def test_internal_tools():
    """Test internal MCP tools"""
    logger.info("Testing internal MCP tools...")
    
    try:
        from app.agents.mcp_servers.internal_mcp_tools import get_all_internal_tools
        
        tools = await get_all_internal_tools()
        logger.info(f"✅ Successfully loaded {len(tools)} internal tools")
        
        # Test a simple tool
        from app.agents.mcp_servers.internal_mcp_tools import get_government_portal_tools
        portal_tools = await get_government_portal_tools()
        
        # Test NIRA portal tool
        nira_tool = None
        for tool in portal_tools:
            if tool.func.__name__ == 'automate_nira_portal':
                nira_tool = tool
                break
        
        if nira_tool:
            test_result = nira_tool.func("NIRA/2023/123456", "check_status")
            if test_result.get('status') == 'success':
                logger.info("✅ Internal tools are working correctly")
                return True
            else:
                logger.warning(f"⚠️  Tool test returned: {test_result}")
                return False
        else:
            logger.warning("⚠️  NIRA tool not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Internal tools test failed: {e}")
        return False

async def test_agent_creation():
    """Test agent creation"""
    logger.info("Testing agent creation...")
    
    try:
        from app.agents.adk_agents_modular import create_root_agent
        
        logger.info("Creating root agent...")
        root_agent = await create_root_agent()
        
        if root_agent:
            logger.info("✅ Root agent created successfully")
            return True
        else:
            logger.error("❌ Root agent creation failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Agent creation failed: {e}")
        logger.error("This might be due to missing Google ADK configuration")
        return False

def start_server():
    """Start the FastAPI server"""
    logger.info("Starting Uganda E-Gov WhatsApp Helpdesk server...")
    
    try:
        import uvicorn
        from main import app
        
        # Server configuration
        config = {
            "app": "main:app",
            "host": "0.0.0.0",
            "port": int(os.getenv("PORT_NO", 8080)),
            "reload": os.getenv("ENVIRONMENT", "development") == "development",
            "log_level": os.getenv("LOG_LEVEL", "info").lower(),
            "access_log": True
        }
        
        logger.info(f"Server starting on http://{config['host']}:{config['port']}")
        logger.info("Available endpoints:")
        logger.info("  - Health check: GET /health")
        logger.info("  - WhatsApp webhook: POST /whatsapp/webhook")
        logger.info("  - Admin dashboard: GET /admin/dashboard")
        logger.info("  - System info: GET /system/info")
        
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

async def main():
    """Main startup function"""
    logger.info("🇺🇬 Uganda E-Gov WhatsApp Helpdesk - Local Startup")
    logger.info("=" * 60)
    
    # Run all checks
    checks_passed = 0
    total_checks = 5
    
    # 1. Environment check
    if check_environment():
        checks_passed += 1
    
    # 2. Dependencies check
    if check_dependencies():
        checks_passed += 1
    else:
        logger.error("Cannot continue without required dependencies")
        sys.exit(1)
    
    # 3. Redis check (optional)
    if check_redis():
        checks_passed += 1
    
    # 4. Internal tools test
    if await test_internal_tools():
        checks_passed += 1
    
    # 5. Agent creation test
    if await test_agent_creation():
        checks_passed += 1
    
    logger.info("=" * 60)
    logger.info(f"Startup checks: {checks_passed}/{total_checks} passed")
    
    if checks_passed >= 3:  # Minimum required checks
        logger.info("✅ System ready to start!")
        logger.info("=" * 60)
        start_server()
    else:
        logger.error("❌ Too many checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    # Set environment to development if not set
    if not os.getenv("ENVIRONMENT"):
        os.environ["ENVIRONMENT"] = "development"
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file loading")
    
    # Run the main function
    asyncio.run(main())