# Uganda E-Gov WhatsApp Helpdesk - Modular Architecture

## Overview

The Uganda E-Gov WhatsApp Helpdesk has been redesigned with a modular architecture that provides enhanced browser automation, better maintainability, and improved scalability. The system now uses a combination of Playwright MCP tools and Browser-Use agent as a fallback mechanism.

## Architecture Components

### 1. MCP Servers (`app/agents/mcp_servers/`)

#### `auth_tools.py`
- **Purpose**: Google Firebase authentication and user management
- **Tools**: 
  - `authenticate_user`: Verify Firebase ID tokens
  - `create_custom_token`: Generate custom authentication tokens
  - `get_user_info`: Retrieve user information by UID
  - `verify_session_token`: Validate session cookies
  - `update_user_profile`: Update user profile information
  - `delete_user`: Remove user accounts

#### `playwright_tools.py`
- **Purpose**: Enhanced browser automation with intelligent fallback
- **Primary Tools**:
  - `get_playwright_tools`: Standard Playwright MCP integration
  - `get_browser_use_tools`: Browser-Use agent fallback
  - `smart_web_automation`: Intelligent automation with retry logic
  - `extract_web_data`: Data extraction from web pages
  - `take_screenshot`: Capture screenshots for verification
- **Government Portal Tools**:
  - `automate_nira_portal`: NIRA birth certificate automation
  - `automate_ura_portal`: URA tax status automation
  - `automate_nssf_portal`: NSSF balance automation
  - `automate_nlis_portal`: NLIS land records automation

#### `whatsapp_tools.py`
- **Purpose**: WhatsApp Business API integration
- **Tools**:
  - `send_whatsapp_message`: Send text messages
  - `send_whatsapp_template`: Send template messages
  - `send_whatsapp_media`: Send media messages
  - `get_whatsapp_media`: Retrieve media URLs
  - `mark_message_read`: Mark messages as read
  - `create_whatsapp_button_message`: Interactive buttons
  - `create_whatsapp_list_message`: Interactive lists

#### `cleanup.py`
- **Purpose**: Centralized MCP connection management
- **Functions**:
  - `register_exit_stack`: Register connections for cleanup
  - `cleanup_mcp_connections`: Clean up all connections
  - `get_connection_status`: Monitor connection health

### 2. Core Agents (`app/agents/core_agents/`)

#### `auth_agent.py`
- **Purpose**: User authentication and session management
- **Capabilities**:
  - Firebase ID token verification
  - Custom token generation
  - User profile management
  - Session lifecycle management
  - Security policy enforcement

#### `language_agent.py`
- **Purpose**: Multi-language support and translation
- **Supported Languages**: English, Luganda, Luo, Runyoro
- **Capabilities**:
  - Language detection using patterns and langdetect
  - Basic translation for common phrases
  - Language preference management
  - Localized system messages
  - Cultural context awareness

#### `intent_agent.py`
- **Purpose**: Intent classification and request routing
- **Intent Categories**:
  - `BIRTH_CERTIFICATE`: NIRA services
  - `TAX_STATUS`: URA services
  - `NSSF_BALANCE`: NSSF services
  - `LAND_RECORDS`: NLIS services
  - `FORM_ASSISTANCE`: Government forms
  - `AUTHENTICATION`: Login/logout
  - `LANGUAGE_CHANGE`: Language preferences
  - `GENERAL_HELP`: General assistance
- **Features**:
  - Entity extraction (reference numbers, dates, etc.)
  - Confidence scoring
  - Clarification suggestions
  - Multi-language keyword recognition

#### `help_agent.py`
- **Purpose**: Contextual help and guidance
- **Capabilities**:
  - Service information and requirements
  - Step-by-step guidance
  - Troubleshooting assistance
  - Document requirements
  - Contact information
  - Formatted help responses

### 3. Service Agents (`app/agents/service_agents/`)

#### `birth_agent.py`
- **Purpose**: NIRA birth certificate services
- **Automation Strategy**:
  1. Primary: Playwright MCP tools
  2. Fallback: Browser-Use agent
  3. Manual: Step-by-step instructions
- **Services**:
  - Status checks using NIRA reference numbers
  - Application guidance
  - Collection information
  - Requirements explanation

#### `tax_agent.py`
- **Purpose**: URA tax services
- **Automation Strategy**: Same as birth agent
- **Services**:
  - Tax balance inquiries
  - Payment history
  - Compliance status
  - TIN validation
  - Payment instructions

#### `nssf_agent.py`
- **Purpose**: NSSF pension services
- **Automation Strategy**: Same as birth agent
- **Services**:
  - Account balance checks
  - Contribution history
  - Benefit calculations
  - Membership verification
  - Pension projections

#### `land_agent.py`
- **Purpose**: NLIS land records services
- **Automation Strategy**: Same as birth agent
- **Services**:
  - Ownership verification
  - Title status checks
  - Encumbrance searches
  - Property details
  - Boundary information

#### `form_agent.py`
- **Purpose**: Government form assistance
- **Capabilities**:
  - Form template retrieval
  - Data validation
  - PDF generation
  - Submission guidance
  - Status tracking
- **Supported Forms**:
  - Birth certificate applications
  - National ID applications
  - Tax registration
  - Business registration
  - Land title applications

#### `service_dispatcher.py`
- **Purpose**: Route requests to appropriate service agents
- **Architecture**: Sequential agent containing all service agents
- **Routing Logic**: Based on intent classification results

## Enhanced Browser Automation

### Automation Flow

1. **Primary Attempt**: Playwright MCP tools
   - Fast, reliable automation
   - Direct browser control
   - Structured data extraction

2. **Fallback Mechanism**: Browser-Use agent
   - AI-powered browser automation
   - Natural language task description
   - Visual understanding of web pages
   - Handles complex scenarios

3. **Error Recovery**: Manual instructions
   - Step-by-step user guidance
   - Contact information
   - Alternative methods

### Smart Web Automation Features

- **Retry Logic**: Exponential backoff with multiple attempts
- **Error Detection**: Automatic failure detection and recovery
- **Screenshot Verification**: Visual confirmation of operations
- **Data Validation**: Verify extracted information
- **Timeout Handling**: Graceful timeout management

## Integration Points

### Browser-Use Agent Integration

```python
def browser_use_automation(
    task_description: str,
    url: str,
    actions: List[Dict[str, Any]] = None,
    timeout: int = 30
) -> dict:
    """Use Browser-Use agent for complex automation tasks"""
```

### Government Portal Automation

```python
def automate_nira_portal(
    reference_number: str,
    action: str = "check_status"
) -> dict:
    """Automate NIRA portal with intelligent fallback"""
```

## Configuration

### Environment Variables

```bash
# Browser automation
BROWSER_USE_ENABLED=true
PLAYWRIGHT_TIMEOUT=30
AUTOMATION_RETRY_COUNT=3

# Government portals
NIRA_PORTAL_URL=https://www.nira.go.ug
URA_PORTAL_URL=https://www.ura.go.ug
NSSF_PORTAL_URL=https://www.nssfug.org
NLIS_PORTAL_URL=https://nlis.go.ug
```

### MCP Server Configuration

```bash
# MCP servers
PLAYWRIGHT_MCP_ENABLED=true
WHATSAPP_MCP_ENABLED=true
BROWSER_USE_FALLBACK=true
```

## Usage Examples

### Running the Modular System

```bash
# Start the modular system
python main_modular.py

# Or use the original system
python main.py
```

### Testing Individual Components

```python
# Test authentication agent
from app.agents.core_agents.auth_agent import create_auth_agent
auth_agent = await create_auth_agent()

# Test browser automation
from app.agents.mcp_servers.playwright_tools import smart_web_automation
result = await smart_web_automation(
    task_description="Check birth certificate status",
    url="https://www.nira.go.ug",
    form_data={"reference": "NIRA/2024/123456"}
)
```

## Monitoring and Debugging

### System Information Endpoint

```bash
GET /system/info
```

Returns detailed information about the modular architecture, components, and automation capabilities.

### Health Checks

The system includes comprehensive health checks for:
- MCP server connections
- Agent initialization status
- Browser automation capabilities
- Database connectivity

### Logging

Enhanced logging includes:
- Component-specific log levels
- Automation attempt tracking
- Fallback mechanism usage
- Performance metrics

## Migration Guide

### From Original to Modular

1. **Update imports**:
   ```python
   # Old
   from app.agents.adk_agents import create_root_agent
   
   # New
   from app.agents.adk_agents_modular import create_root_agent
   ```

2. **Use new main file**:
   ```bash
   # Use main_modular.py instead of main.py
   python main_modular.py
   ```

3. **Install browser-use**:
   ```bash
   pip install browser-use
   ```

### Backward Compatibility

The modular system maintains backward compatibility through wrapper functions in `adk_agents_modular.py`.

## Performance Optimizations

### Browser Automation

- **Connection Pooling**: Reuse browser instances
- **Parallel Processing**: Multiple automation tasks
- **Caching**: Cache portal responses
- **Smart Retries**: Intelligent retry strategies

### Agent Communication

- **Async Operations**: All agent operations are async
- **Resource Management**: Proper cleanup of resources
- **Memory Optimization**: Efficient memory usage
- **Connection Management**: Centralized MCP connection handling

## Security Considerations

### Browser Automation Security

- **Sandboxed Execution**: Browser operations in isolated environment
- **Input Validation**: Validate all automation inputs
- **Screenshot Sanitization**: Remove sensitive data from screenshots
- **Audit Logging**: Log all automation attempts

### Data Protection

- **Encryption**: Encrypt sensitive data in transit
- **Access Control**: Role-based access to automation features
- **Session Management**: Secure session handling
- **Privacy Protection**: Respect user privacy in automation

## Future Enhancements

### Planned Features

1. **AI-Powered Form Filling**: Intelligent form completion
2. **Visual Verification**: Computer vision for result validation
3. **Multi-Portal Sessions**: Maintain sessions across portals
4. **Predictive Automation**: Anticipate user needs
5. **Advanced Error Recovery**: Self-healing automation

### Scalability Improvements

1. **Distributed Automation**: Scale across multiple instances
2. **Load Balancing**: Distribute automation load
3. **Caching Layer**: Cache portal responses
4. **Queue Management**: Handle high-volume requests

## Troubleshooting

### Common Issues

1. **Browser-Use Installation**: Ensure proper installation
2. **MCP Server Connectivity**: Check network connectivity
3. **Portal Changes**: Handle portal structure changes
4. **Authentication Issues**: Verify credentials

### Debug Commands

```bash
# Test browser automation
python -c "from app.agents.mcp_servers.playwright_tools import get_browser_use_tools; print('Browser-Use available')"

# Check MCP connections
python -c "from app.agents.mcp_servers.cleanup import get_connection_status; print(get_connection_status())"
```

## Support

For issues with the modular architecture:

1. Check the logs for component-specific errors
2. Verify MCP server connectivity
3. Test browser automation independently
4. Review configuration settings
5. Contact the development team

---

**The modular architecture provides a robust, scalable, and maintainable foundation for the Uganda E-Gov WhatsApp Helpdesk system with enhanced browser automation capabilities.**