"""Test configuration management."""

import os
import pytest
from src.core.config import Settings


class TestSettings:
    """Test application settings."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        assert settings.app_name == "HELIOS Orchestrator"
        assert settings.app_version == "1.0.0"
        assert settings.debug is False
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.session_timeout_minutes == 60
        assert "sqlite" in settings.database_url

    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("APP_NAME", "Test Orchestrator")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("PORT", "9000")

        settings = Settings()

        assert settings.app_name == "Test Orchestrator"
        assert settings.debug is True
        assert settings.port == 9000

    def test_cors_origins_list(self):
        """Test CORS origins configuration."""
        settings = Settings()

        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) >= 2
        assert "http://localhost:3000" in settings.cors_origins

    def test_database_url_format(self):
        """Test database URL format."""
        settings = Settings()

        assert "sqlite+aiosqlite" in settings.database_url or "postgresql+asyncpg" in settings.database_url

    def test_timeout_values_positive(self):
        """Test that timeout values are positive."""
        settings = Settings()

        assert settings.session_timeout_minutes > 0
        assert settings.session_cleanup_interval_minutes > 0
        assert settings.http_timeout_seconds > 0
