"""Configuration management for ARCHITECT service."""

import os
from functools import lru_cache
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Service configuration
    service_name: str = "architect"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server configuration  
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8004, env="PORT")
    
    # External service URLs
    orchestrator_url: str = Field(default="http://localhost:8001", env="ORCHESTRATOR_URL")
    analyst_url: str = Field(default="http://localhost:8003", env="ANALYST_URL")
    strategist_url: str = Field(default="http://localhost:8002", env="STRATEGIST_URL")
    
    # Service timeouts (seconds)
    orchestrator_timeout: float = Field(default=10.0, env="ORCHESTRATOR_TIMEOUT")
    analyst_timeout: float = Field(default=15.0, env="ANALYST_TIMEOUT")
    strategist_timeout: float = Field(default=10.0, env="STRATEGIST_TIMEOUT")
    
    # Template configuration
    template_cache_size: int = Field(default=50, env="TEMPLATE_CACHE_SIZE")
    template_cache_ttl: int = Field(default=3600, env="TEMPLATE_CACHE_TTL")  # 1 hour
    
    # Document generation settings
    max_concurrent_generations: int = Field(default=5, env="MAX_CONCURRENT_GENERATIONS")
    generation_timeout: float = Field(default=30.0, env="GENERATION_TIMEOUT")
    temp_file_cleanup_interval: int = Field(default=300, env="TEMP_FILE_CLEANUP_INTERVAL")  # 5 minutes
    
    # Performance thresholds
    memory_warning_threshold: float = Field(default=80.0, env="MEMORY_WARNING_THRESHOLD")
    memory_critical_threshold: float = Field(default=90.0, env="MEMORY_CRITICAL_THRESHOLD")
    response_time_warning: float = Field(default=25.0, env="RESPONSE_TIME_WARNING")
    
    # Template paths
    template_base_path: str = Field(default="src/templates", env="TEMPLATE_BASE_PATH")
    resume_template_path: str = Field(default="resume", env="RESUME_TEMPLATE_PATH")
    cover_letter_template_path: str = Field(default="cover_letter", env="COVER_LETTER_TEMPLATE_PATH")
    styles_path: str = Field(default="styles", env="STYLES_PATH")
    
    # ATS compliance settings
    ats_compliance_strict: bool = Field(default=True, env="ATS_COMPLIANCE_STRICT")
    supported_fonts: List[str] = Field(
        default=["Arial", "Calibri", "Helvetica", "Times New Roman"],
        env="SUPPORTED_FONTS"
    )
    min_font_size: int = Field(default=10, env="MIN_FONT_SIZE")
    max_font_size: int = Field(default=16, env="MAX_FONT_SIZE")
    
    # Output format settings
    default_output_format: str = Field(default="pdf", env="DEFAULT_OUTPUT_FORMAT")
    supported_formats: List[str] = Field(
        default=["pdf", "html", "markdown", "docx"],
        env="SUPPORTED_FORMATS"
    )
    
    # PDF generation settings
    pdf_dpi: int = Field(default=300, env="PDF_DPI")
    pdf_optimize_size: bool = Field(default=True, env="PDF_OPTIMIZE_SIZE")
    pdf_version: str = Field(default="1.4", env="PDF_VERSION")
    
    # Security settings
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    allowed_mime_types: List[str] = Field(
        default=["application/pdf", "text/html", "text/markdown", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        env="ALLOWED_MIME_TYPES"
    )
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Configuration constants
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "generation_time_warning": 25.0,
    "generation_time_critical": 30.0,
    "memory_usage_warning": 80.0,
    "memory_usage_critical": 90.0,
    "concurrent_requests_warning": 8,
    "concurrent_requests_critical": 12,
    "template_cache_hit_rate_warning": 70.0,
    "pdf_conversion_time_warning": 10.0,
    "ats_validation_time_warning": 2.0,
}


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()

# ATS compliance rules (2025 standards)
ATS_COMPLIANCE_RULES = {
    "layout": {
        "single_column": True,
        "no_tables_for_layout": True,
        "linear_reading_order": True,
        "no_absolute_positioning": True,
        "no_negative_margins": True,
    },
    "typography": {
        "standard_fonts": ["Arial", "Calibri", "Helvetica", "Times New Roman"],
        "font_size_min": 10,
        "font_size_max": 16,
        "no_text_decorations": ["text-shadow", "text-outline"],
        "no_custom_fonts": True,
    },
    "graphics": {
        "no_background_images": True,
        "no_icons": True,
        "no_skill_bars": True,
        "no_charts": True,
        "no_complex_borders": True,
    },
    "structure": {
        "proper_headings": ["h1", "h2", "h3"],
        "semantic_markup": True,
        "no_div_for_headings": True,
        "consistent_formatting": True,
    },
    "content": {
        "keywords_in_context": True,
        "no_keyword_stuffing": True,
        "readable_text": True,
        "proper_spacing": True,
    }
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "generation_time_warning": 25.0,  # seconds
    "generation_time_critical": 30.0,  # seconds
    "memory_usage_warning": 80.0,     # percent
    "memory_usage_critical": 90.0,    # percent
    "concurrent_requests_warning": 8,
    "concurrent_requests_critical": 12,
    "template_cache_hit_rate_warning": 70.0,  # percent
    "pdf_conversion_time_warning": 10.0,  # seconds
    "ats_validation_time_warning": 2.0,   # seconds
}