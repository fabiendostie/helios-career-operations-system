"""Integration tests for orchestrator module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp
import json
from typing import Dict, Any

from src.integrations.orchestrator import OrchestratorClient, HeartbeatManager
from src.core.config import StrategistConfig


class TestOrchestratorIntegration:
    """Test orchestrator integration functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock config fixture."""
        config = Mock(spec=StrategistConfig)
        config.orchestrator_url = "http://localhost:8000"
        config.orchestrator_timeout = 30
        config.port = 8002
        return config
    
    @pytest.fixture
    def client(self, mock_config):
        """Create orchestrator client fixture."""
        return OrchestratorClient(mock_config)
    
    @pytest.mark.asyncio
    async def test_register_with_orchestrator_success(self, client):
        """Test successful service registration."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.post.return_value = mock_response
        
        result = await client.register_with_orchestrator()
        assert result == True
    
    @pytest.mark.asyncio
    async def test_register_with_orchestrator_failure(self, client):
        """Test service registration failure."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.post.return_value = mock_response
        
        result = await client.register_with_orchestrator()
        assert result == False
    
    @pytest.mark.asyncio
    async def test_send_heartbeat_success(self, client):
        """Test successful heartbeat sending."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.post.return_value = mock_response
        
        result = await client.send_heartbeat()
        assert result == True
    
    @pytest.mark.asyncio
    async def test_get_session_data_success(self, client):
        """Test retrieving session data."""
        session_data = {
            "user_id": "test_user",
            "master_career_database": {
                "skills_inventory": {"programming": ["Python", "Java"]}
            }
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=session_data)
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.get.return_value = mock_response
        
        result = await client.get_session_data("test_user", "session_123")
        
        assert result["user_id"] == "test_user"
        assert "master_career_database" in result
    
    @pytest.mark.asyncio
    async def test_get_session_data_not_found(self, client):
        """Test handling session not found."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.get.return_value = mock_response
        
        result = await client.get_session_data("test_user", "invalid_session")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_session_data_success(self, client):
        """Test updating session data."""
        update_data = {"career_paths": [{"title": "Software Engineer"}]}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "updated"})
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.patch.return_value = mock_response
        
        result = await client.update_session_data("session_123", update_data)
        
        assert result["status"] == "updated"
    
    @pytest.mark.asyncio
    async def test_notify_completion_success(self, client):
        """Test notifying orchestrator of completion."""
        completion_data = {
            "command": "discover",
            "status": "completed",
            "result": {"career_paths": []}
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "received"})
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.post.return_value = mock_response
        
        result = await client.notify_completion("test_user", "session_123", completion_data)
        
        assert result["status"] == "received"
    
    @pytest.mark.asyncio
    async def test_get_orchestrator_health_success(self, client):
        """Test health check endpoint."""
        health_data = {"status": "healthy", "components": {"api": "ok"}}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=health_data)
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        client.session = AsyncMock()
        client.session.get.return_value = mock_response
        
        result = await client.get_orchestrator_health()
        
        assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_orchestrator_health_failure(self, client):
        """Test health check failure."""
        client.session = AsyncMock()
        client.session.get.side_effect = aiohttp.ClientError("Connection failed")
        
        with pytest.raises(aiohttp.ClientError):
            await client.get_orchestrator_health()
    
    def test_client_initialization(self, mock_config):
        """Test client initialization with config."""
        # Test with provided config
        client = OrchestratorClient(mock_config)
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30
        
        # Test with None (uses default config)
        with patch('src.integrations.orchestrator.StrategistConfig') as mock_config_class:
            mock_default_config = Mock()
            mock_default_config.orchestrator_url = "http://localhost:8001"
            mock_default_config.orchestrator_timeout = 60
            mock_config_class.return_value = mock_default_config
            
            client = OrchestratorClient()
            assert client.base_url == "http://localhost:8001"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager functionality."""
        # Test that context manager can be entered and exited
        async with client as ctx_client:
            assert ctx_client is not None
            # Session is created on enter
        
        # Test completed without errors


class TestHeartbeatManager:
    """Test HeartbeatManager functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client fixture."""
        return AsyncMock(spec=OrchestratorClient)
    
    def test_heartbeat_manager_init(self, mock_client):
        """Test HeartbeatManager initialization."""
        manager = HeartbeatManager(mock_client, 60.0)
        assert manager.client == mock_client
        assert manager.interval == 60.0
        assert not manager.running
    
    @pytest.mark.asyncio
    async def test_heartbeat_manager_start_stop(self, mock_client):
        """Test starting and stopping heartbeat manager."""
        manager = HeartbeatManager(mock_client, 0.1)  # Short interval for testing
        
        # Start the manager
        await manager.start()
        assert manager.running
        assert manager._task is not None
        
        # Stop the manager
        await manager.stop()
        assert not manager.running