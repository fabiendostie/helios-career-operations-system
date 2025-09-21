"""Centralized logging configuration with correlation ID support."""

import logging
import sys
from typing import Dict, Any
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

from ..core.config import settings


# Correlation ID context variable (imported from main.py)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to the log record."""
        record.correlation_id = correlation_id_var.get("unknown")
        return True


class StructuredFormatter(jsonlogger.JsonFormatter):
    """JSON formatter for structured logging."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add service information
        log_record["service"] = settings.app_name
        log_record["version"] = settings.app_version

        # Add correlation ID
        log_record["correlation_id"] = getattr(record, "correlation_id", "unknown")

        # Ensure level is always present
        if "level" not in log_record:
            log_record["level"] = record.levelname


def setup_logging() -> logging.Logger:
    """Configure application logging."""

    # Create root logger
    logger = logging.getLogger("helios_orchestrator")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Add correlation filter
    correlation_filter = CorrelationFilter()
    console_handler.addFilter(correlation_filter)

    # Choose formatter based on debug mode
    if settings.debug:
        # Simple format for development
        formatter = logging.Formatter(settings.log_format)
    else:
        # Structured JSON format for production
        formatter = StructuredFormatter()

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Configure FastAPI/Uvicorn loggers
    logging.getLogger("uvicorn").setLevel(getattr(logging, settings.log_level.upper()))
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(getattr(logging, settings.log_level.upper()))

    # Prevent duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(f"helios_orchestrator.{name}")


# Initialize logging on module import
setup_logging()
