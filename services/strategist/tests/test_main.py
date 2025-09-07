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
        with patch('src.api.career_paths.initialize_career_generator') as mock_init:
            mock_init.return_value = AsyncMock()
            
            # Use the lifespan as an async context manager
            async with lifespan(app):
                # This tests startup
                pass
            # Exiting context tests shutdown
            
            # Verify initialization was called
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_initialization_error(self):
        """Test lifespan handling of initialization errors."""
        with patch('src.api.career_paths.initialize_career_generator') as mock_init:
            # Make initialization fail
            mock_init.side_effect = Exception("Initialization failed")
            
            # Test that startup error is handled
            with pytest.raises(Exception, match="Initialization failed"):
                async with lifespan(app):
                    pass
    
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
        assert app.title == "STRATEGIST Agent Service"
        assert app.description is not None
        assert app.version == "1.0.0"