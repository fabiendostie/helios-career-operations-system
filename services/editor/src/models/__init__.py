"""Models package for the Editor service."""

from .edit_request import EditRequest, EditResponse, EditType
from .text_analysis import TextAnalysis, GrammarIssue, StyleIssue
from .version_control import Version, ChangeLog, DiffOperation

__all__ = [
    "EditRequest",
    "EditResponse",
    "EditType",
    "TextAnalysis",
    "GrammarIssue",
    "StyleIssue",
    "Version",
    "ChangeLog",
    "DiffOperation",
]