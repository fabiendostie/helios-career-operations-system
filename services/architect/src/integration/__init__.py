"""
Service Integration Module for ARCHITECT Service

Provides integration with other Helios services:
- Orchestrator: Session management and coordination
- ANALYST: Market analysis and resume optimization recommendations
- STRATEGIST: Career path and skill adjacency data
"""

from .service_clients import (
    OrchestratorClient,
    AnalystClient,
    StrategistClient,
    get_service_clients
)
from .data_contracts import (
    AnalystRecommendations,
    StrategistInsights,
    OrchestratorSession,
    DocumentGenerationRequest,
    DocumentGenerationResponse
)

__all__ = [
    'OrchestratorClient',
    'AnalystClient', 
    'StrategistClient',
    'get_service_clients',
    'AnalystRecommendations',
    'StrategistInsights',
    'OrchestratorSession',
    'DocumentGenerationRequest',
    'DocumentGenerationResponse'
]