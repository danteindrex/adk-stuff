# MCP Integration Fixes for Google ADK

## Issues Found and Fixed

### 1. **Incorrect Tool.from_mcp Usage**
**Problem**: The original code used `Tool.from_mcp()` which is not the correct ADK pattern.

**Original Code**:
```python
supabase_tools = [
    Tool.from_mcp(
        name="supabase",
        mcp_server={
            "command": "npx",
            "args": [...]
        }
    )
]
```

**Fixed Code**:
```python
async def get_supabase_tools():
    """Get Supabase MCP tools"""
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@supabase/mcp-server-supabase@latest",
                "--access-token",
                os.getenv("SUPABASE_MCP_PAT", "")
            ],
            env={"SUPABASE_MCP_PAT": os.getenv("SUPABASE_MCP_PAT", "")}
        )
    )
    return tools
```

### 2. **Missing Proper Async Tool Management**
**Problem**: MCP tools need to be initialized asynchronously and their connections properly managed.

**Solution**: 
- Created async functions for tool initialization
- Added proper exit stack management for MCP connections
- Implemented cleanup functions

### 3. **Incorrect Model Names**
**Problem**: Used `"gemini-2.0-pro"` which may not be available.

**Fixed**: Changed to `"gemini-2.0-flash"` which is the standard model in ADK examples.

### 4. **Missing Async Agent Creation**
**Problem**: Agents with MCP tools need to be created asynchronously.

**Solution**: 
- Created async agent creation functions
- Implemented proper agent initialization in the application lifecycle

### 5. **Missing Session Manager Service**
**Problem**: The main.py referenced a SessionManager that didn't exist.

**Solution**: Created a complete SessionManager service with:
- Session creation and management
- Conversation history tracking
- Automatic cleanup of expired sessions
- Integration with Supabase database

## Key Changes Made

### 1. Updated `app/agents/adk_agents.py`
- Replaced `Tool.from_mcp` with proper `MCPToolset.from_server`
- Added async tool initialization functions
- Created async agent creation functions
- Added proper MCP connection cleanup
- Changed model names to `"gemini-2.0-flash"`

### 2. Updated `main.py`
- Added async agent initialization in the lifespan context
- Added MCP connection cleanup on shutdown
- Fixed health check to reference correct variables
- Added proper error handling for agent initialization

### 3. Created `app/services/session_manager.py`
- Complete session management implementation
- Integration with Supabase database
- Automatic session cleanup
- Conversation history tracking

### 4. Updated `app/database/supabase_client.py`
- Added session management methods
- Added proper database integration for sessions

## Proper ADK MCP Integration Pattern

The correct pattern for integrating MCP servers with Google ADK is:

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

async def get_tools():
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "@package/mcp-server"],
            env={"API_KEY": os.getenv("API_KEY")}
        )
    )
    return tools, exit_stack

async def create_agent():
    tools, exit_stack = await get_tools()
    agent = LlmAgent(
        name="agent_name",
        model="gemini-2.0-flash",
        instruction="Agent instructions",
        tools=tools
    )
    return agent, exit_stack
```

## Environment Variables Required

Make sure these environment variables are set:

```bash
SUPABASE_MCP_PAT=your_supabase_mcp_token
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
GOOGLE_API_KEY=your_google_api_key
```

## Testing the Integration

1. Start the application: `python main.py`
2. Check the health endpoint: `GET /health`
3. Test the WhatsApp webhook: `POST /whatsapp/webhook`

The agents should now properly initialize with MCP tools and handle requests correctly.

## Best Practices Implemented

1. **Async Tool Management**: All MCP tools are initialized asynchronously
2. **Proper Resource Cleanup**: Exit stacks are properly managed and cleaned up
3. **Error Handling**: Comprehensive error handling for MCP connections
4. **Environment Configuration**: Proper use of environment variables
5. **Session Management**: Complete session lifecycle management
6. **Health Monitoring**: Proper health checks for all components

This implementation now follows the official Google ADK documentation patterns for MCP integration.