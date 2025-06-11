"""
Pytest configuration and fixtures for Uganda E-Gov WhatsApp Helpdesk tests
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment
# Add Twilio test environment variables
os.environ["TWILIO_ACCOUNT_SID"] = "test_account_sid"
os.environ["TWILIO_AUTH_TOKEN"] = "test_auth_token"
os.environ["TWILIO_WHATSAPP_NUMBER"] = "test_whatsapp_number"
os.environ["TWILIO_WEBHOOK_VERIFY_TOKEN"] = "test_verify_token"

# Legacy WhatsApp variables (can be kept for backward compatibility)
os.environ["WHATSAPP_ACCESS_TOKEN"] = "test_token"
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "test_phone_id"
os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = "test_verify_token"
os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = "test_business_id"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-purposes-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters"
os.environ["ADMIN_WHATSAPP_GROUP"] = "test_admin_group"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_firebase_admin():
    """Mock Firebase Admin SDK"""
    with pytest.mock.patch('firebase_admin.initialize_app'):
        with pytest.mock.patch('firebase_admin.auth') as mock_auth:
            mock_auth.verify_id_token.return_value = {
                'uid': 'test_uid',
                'email': 'test@example.com',
                'name': 'Test User'
            }
            mock_auth.create_custom_token.return_value = b'test_token'
            mock_auth.get_user.return_value = Mock(
                uid='test_uid',
                email='test@example.com',
                display_name='Test User'
            )
            yield mock_auth

@pytest.fixture
def mock_firestore():
    """Mock Firestore client"""
    with pytest.mock.patch('google.cloud.firestore.Client') as mock_client:
        mock_doc = Mock()
        mock_doc.get.return_value.exists = True
        mock_doc.get.return_value.to_dict.return_value = {
            'session_id': 'test_session',
            'user_id': 'test_user',
            'is_active': True
        }
        mock_doc.set.return_value = None
        mock_doc.update.return_value = None
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc
        mock_collection.where.return_value.order_by.return_value.limit.return_value.stream.return_value = []
        
        mock_client.return_value.collection.return_value = mock_collection
        yield mock_client

@pytest.fixture
def mock_google_cloud_monitoring():
    """Mock Google Cloud Monitoring"""
    with pytest.mock.patch('google.cloud.monitoring_v3.MetricServiceClient') as mock_client:
        mock_client.return_value.create_time_series.return_value = None
        yield mock_client

@pytest.fixture
def mock_session_manager(mock_firestore, mock_firebase_admin):
    """Mock session manager"""
    from app.services.google_session_manager import GoogleSessionManager
    
    session_manager = GoogleSessionManager()
    session_manager.active_sessions = {
        'test_session': {
            'session_id': 'test_session',
            'user_id': 'test_user',
            'is_active': True,
            'conversation_history': []
        }
    }
    return session_manager

@pytest.fixture
def mock_monitoring_service():
    """Mock monitoring service"""
    from app.services.enhanced_monitoring import EnhancedMonitoringService
    
    monitoring = EnhancedMonitoringService()
    monitoring.monitoring_client = Mock()
    monitoring.logging_client = Mock()
    return monitoring

@pytest.fixture
def mock_root_agent():
    """Mock root agent"""
    agent = AsyncMock()
    agent.run_async.return_value = AsyncMock()
    return agent

@pytest.fixture
async def app_client(mock_session_manager, mock_monitoring_service, mock_root_agent):
    """Create test client for the FastAPI app"""
    # Mock the global services
    import main
    main.session_manager = mock_session_manager
    main.monitoring_service = mock_monitoring_service
    main.root_agent = mock_root_agent
    
    async with AsyncClient(app=main.app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_whatsapp_message():
    """Sample WhatsApp webhook message"""
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "+256700000001",
                        "text": {"body": "Hello, I need help with my birth certificate"},
                        "id": "test_message_id",
                        "timestamp": "1234567890"
                    }]
                }
            }]
        }]
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "uid": "test_uid",
        "email": "test@example.com",
        "phone": "+256700000001",
        "name": "Test User",
        "language_preference": "en"
    }

@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        "session_id": "test_session",
        "user_id": "test_user",
        "user_phone": "+256700000001",
        "is_active": True,
        "conversation_history": [],
        "current_agent": None,
        "language_preference": "en"
    }

@pytest.fixture
def mock_mcp_tools():
    """Mock MCP tools"""
    with pytest.mock.patch('app.agents.adk_agents.MCPToolset.from_server') as mock_toolset:
        mock_tools = Mock()
        mock_exit_stack = AsyncMock()
        mock_toolset.return_value = (mock_tools, mock_exit_stack)
        yield mock_tools

@pytest.fixture
def mock_adk_agent():
    """Mock ADK agent"""
    with pytest.mock.patch('google.adk.agents.LlmAgent') as mock_agent:
        agent_instance = Mock()
        agent_instance.run_async = AsyncMock()
        mock_agent.return_value = agent_instance
        yield agent_instance