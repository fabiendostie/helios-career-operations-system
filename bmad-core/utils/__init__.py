"""
BMAD Core Utilities
Shared utilities for the Helios Career Operations System
"""

from .internet_datetime import get_current_datetime, get_current_date, format_date_for_filename
from .documentation_timestamps import (
    get_doc_timestamp,
    get_doc_header,
    get_pydoc_timestamp,
    get_markdown_timestamp,
    get_report_header,
    get_filename_timestamp,
    format_audit_timestamp,
    format_log_timestamp,
    generate_document
)

__all__ = [
    # Internet datetime functions
    "get_current_datetime",
    "get_current_date",
    "format_date_for_filename",
    # Documentation timestamp functions
    "get_doc_timestamp",
    "get_doc_header",
    "get_pydoc_timestamp",
    "get_markdown_timestamp",
    "get_report_header",
    "get_filename_timestamp",
    "format_audit_timestamp",
    "format_log_timestamp",
    "generate_document"
]
