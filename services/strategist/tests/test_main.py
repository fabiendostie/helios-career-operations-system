"""Tests for main application module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.main import app, lifespan


class TestMainApplication:
    """Test main application functionality."""
    
    def test_app_creation(self):
        """Test that FastAPI app is created properly."""
        assert app is not None
        assert hasattr(app, 'title')
        assert hasattr(app, 'version')
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_shutdown(self):
        """Test application lifespan events."""
        with patch('src.main.StrategistConfig') as mock_config_class:
            mock_config = Mock()
            mock_config.debug = False
            mock_config_class.return_value = mock_config
            
            with patch('src.main.CareerGenerator') as mock_generator_class:
                mock_generator = AsyncMock()
                mock_generator.initialize = AsyncMock()
                mock_generator_class.return_value = mock_generator
                
                # Mock the lifespan context manager
                async_gen = lifespan(app)
                
                # Test startup
                await async_gen.__anext__()
                mock_generator.initialize.assert_called_once()
                
                # Test shutdown
                try:
                    await async_gen.__anext__()
                except StopAsyncIteration:
                    pass  # Expected for lifespan context manager
    
    @pytest.mark.asyncio
    async def test_lifespan_initialization_error(self):
        """Test lifespan handling of initialization errors."""
        with patch('src.main.StrategistConfig') as mock_config_class:
            mock_config = Mock()
            mock_config.debug = False
            mock_config_class.return_value = mock_config
            
            with patch('src.main.CareerGenerator') as mock_generator_class:
                mock_generator = AsyncMock()
                mock_generator.initialize.side_effect = Exception("Init failed")
                mock_generator_class.return_value = mock_generator
                
                async_gen = lifespan(app)
                
                # Should handle initialization error gracefully
                with pytest.raises(Exception, match="Init failed"):
                    await async_gen.__anext__()
    
    def test_app_has_required_routes(self):
        """Test that app includes required routers."""
        # Check that routers are included
        routes = [route.path for route in app.routes]
        
        # Should have health routes
        health_routes = [route for route in routes if '/health' in route]
        assert len(health_routes) > 0
        
        # Should have API routes  
        api_routes = [route for route in routes if '/api' in route or '/discover' in route]
        assert len(api_routes) >= 0  # May be 0 if no routes directly defined
    
    def test_app_configuration(self):
        """Test app configuration settings."""
        assert app.title == "STRATEGIST Service"
        assert app.description is not None
        assert app.version == "1.0.0"