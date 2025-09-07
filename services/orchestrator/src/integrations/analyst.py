"""Integration client for ANALYST service."""

import logging
import aiohttp
from typing import Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)


class AnalystClient:
    """HTTP client for communicating with ANALYST service."""
    
    def __init__(self):
        """Initialize analyst client."""
        self.base_url = getattr(settings, 'analyst_url', 'http://localhost:8003')
        self.timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for analysis
    
    async def analyze_market_position(
        self,
        profile_data: Dict[str, Any],
        career_paths: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Analyze market position based on profile and career paths.
        
        Args:
            profile_data: Master career database from Profile Ingestor
            career_paths: Career paths from Strategist
            session_id: Session identifier
            
        Returns:
            Market analysis results
        """
        logger.info(f"Analyzing market position for session {session_id}")
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/v1/analyze"
                
                payload = {
                    "profile_data": profile_data,
                    "career_paths": career_paths,
                    "session_id": session_id,
                    "analysis_options": {
                        "include_market_demand": True,
                        "include_skill_gaps": True,
                        "include_resume_optimization": True,
                        "include_salary_analysis": True,
                        "geographic_scope": "national"
                    }
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully analyzed market position for session {session_id}")
                        return {
                            "success": True,
                            "analysis": result.get("analysis", {}),
                            "recommendations": result.get("recommendations", [])
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Analyst API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"API error {response.status}: {error_text}"
                        }
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error calling Analyst: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP client error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error calling Analyst: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def analyze_resume(
        self,
        profile_data: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Analyze resume for ATS optimization.
        
        Args:
            profile_data: Master career database from Profile Ingestor
            session_id: Session identifier
            
        Returns:
            Resume analysis results
        """
        logger.info(f"Analyzing resume for session {session_id}")
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/v1/analyze/resume"
                
                payload = {
                    "profile_data": profile_data,
                    "session_id": session_id,
                    "options": {
                        "ats_simulation": True,
                        "keyword_optimization": True,
                        "format_analysis": True
                    }
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully analyzed resume for session {session_id}")
                        return {
                            "success": True,
                            "ats_score": result.get("ats_score", 0),
                            "recommendations": result.get("recommendations", []),
                            "keyword_analysis": result.get("keyword_analysis", {})
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Resume analysis API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"API error {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Analyst service.
        
        Returns:
            Health check results
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/health"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "status": "healthy",
                            "service": "analyst",
                            "details": result
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "service": "analyst",
                            "error": f"HTTP {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"Health check failed for Analyst: {str(e)}")
            return {
                "status": "unhealthy",
                "service": "analyst",
                "error": str(e)
            }
    
    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information.
        
        Returns:
            Service information
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "service": "analyst"
                        }
                        
        except Exception as e:
            return {
                "error": str(e),
                "service": "analyst"
            }