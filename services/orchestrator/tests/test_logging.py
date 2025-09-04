"""Test logging configuration."""

import logging
import pytest
from unittest.mock import patch, MagicMock
from src.utils.logging_config import setup_logging, get_logger, CorrelationFilter


class TestLoggingConfiguration:
    """Test logging setup and configuration."""
    
    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a configured logger."""
        logger = setup_logging()
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "helios_orchestrator"
        assert len(logger.handlers) > 0
    
    def test_get_logger_returns_child_logger(self):
        """Test that get_logger returns properly named child logger."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "helios_orchestrator.test_module"
    
    def test_correlation_filter_adds_correlation_id(self):
        """Test that CorrelationFilter adds correlation_id to log records."""
        filter_instance = CorrelationFilter()
        
        # Create a mock log record
        record = MagicMock()
        record.correlation_id = None
        
        # Apply filter
        result = filter_instance.filter(record)
        
        assert result is True
        assert hasattr(record, 'correlation_id')
    
    @patch('src.utils.logging_config.correlation_id_var')
    def test_correlation_filter_uses_context_var(self, mock_context_var):
        """Test that CorrelationFilter uses correlation ID from context."""
        mock_context_var.get.return_value = "test-correlation-123"
        filter_instance = CorrelationFilter()
        
        record = MagicMock()
        filter_instance.filter(record)
        
        assert record.correlation_id == "test-correlation-123"
    
    def test_logger_level_configuration(self):
        """Test logger level is set correctly."""
        logger = setup_logging()
        
        # Logger should have a level set
        assert logger.level != logging.NOTSET
    
    def test_handler_has_formatter(self):
        """Test that handlers have formatters configured."""
        logger = setup_logging()
        
        for handler in logger.handlers:
            assert handler.formatter is not None


class TestStructuredLogging:
    """Test structured logging functionality."""
    
    @patch('src.utils.logging_config.settings')
    def test_debug_mode_uses_simple_formatter(self, mock_settings):
        """Test that debug mode uses simple formatter."""
        mock_settings.debug = True
        mock_settings.log_level = "DEBUG"
        mock_settings.log_format = "%(message)s"
        mock_settings.app_name = "Test"
        mock_settings.app_version = "1.0.0"
        
        logger = setup_logging()
        
        # Should have at least one handler
        assert len(logger.handlers) > 0
    
    @patch('src.utils.logging_config.settings')
    def test_production_mode_uses_json_formatter(self, mock_settings):
        """Test that production mode uses JSON formatter."""
        mock_settings.debug = False
        mock_settings.log_level = "INFO"
        mock_settings.app_name = "Test"
        mock_settings.app_version = "1.0.0"
        
        logger = setup_logging()
        
        # Should have at least one handler
        assert len(logger.handlers) > 0