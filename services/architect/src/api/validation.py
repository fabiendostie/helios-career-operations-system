"""
ATS Compliance Validation API Endpoints

Provides REST API endpoints for validating documents against ATS compliance standards.
"""

import asyncio
from pathlib import Path
from typing import List, Optional
import tempfile
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

from ..validation import (
    get_ats_validator,
    ATSVendor,
    ComplianceLevel,
    ValidationResult
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/validation", tags=["validation"])

# Request/Response Models

class ValidationRequest(BaseModel):
    """Request model for document validation."""
    
    target_vendors: List[str] = Field(
        default=["generic"],
        description="Target ATS vendors to validate against"
    )
    compliance_level: str = Field(
        default="standard",
        description="Validation strictness level: strict, standard, basic"
    )
    return_recommendations: bool = Field(
        default=True,
        description="Include actionable recommendations in response"
    )

class ValidationResponse(BaseModel):
    """Response model for validation results."""
    
    is_compliant: bool
    compliance_score: float
    parsing_confidence: float
    violations: List[dict]
    recommendations: List[str]
    vendor_scores: dict
    validation_metadata: dict

@router.post(
    "/validate-document",
    response_model=ValidationResponse,
    summary="Validate document ATS compliance",
    description="""
    Upload a document and validate it against ATS compliance standards.
    
    Supports PDF, DOCX, HTML, and TXT formats. Returns detailed compliance
    analysis with scores, violations, and actionable recommendations.
    """
)
async def validate_document_compliance(
    file: UploadFile = File(..., description="Document file to validate"),
    validation_request: ValidationRequest = Body(..., description="Validation parameters")
) -> ValidationResponse:
    """Validate uploaded document against ATS compliance standards."""
    
    logger.info("Starting document ATS validation",
                filename=file.filename,
                content_type=file.content_type,
                target_vendors=validation_request.target_vendors)
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.doc', '.html', '.htm', '.txt'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Supported: {allowed_extensions}"
        )
    
    # Validate file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = Path(temp_file.name)
        
        # Parse validation parameters
        try:
            target_vendors = [ATSVendor(vendor.lower()) for vendor in validation_request.target_vendors]
        except ValueError as e:
            valid_vendors = [v.value for v in ATSVendor]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ATS vendor. Valid options: {valid_vendors}"
            )
        
        try:
            compliance_level = ComplianceLevel(validation_request.compliance_level.lower())
        except ValueError:
            valid_levels = [l.value for l in ComplianceLevel]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid compliance level. Valid options: {valid_levels}"
            )
        
        # Perform validation
        validator = await get_ats_validator()
        result = await validator.validate_document(
            document_path=temp_file_path,
            target_vendors=target_vendors,
            compliance_level=compliance_level
        )
        
        logger.info("ATS validation completed",
                   filename=file.filename,
                   compliance_score=result.compliance_score,
                   is_compliant=result.is_compliant,
                   violations_count=len(result.violations))
        
        # Build response
        response = ValidationResponse(
            is_compliant=result.is_compliant,
            compliance_score=result.compliance_score,
            parsing_confidence=result.parsing_confidence,
            violations=result.violations,
            recommendations=result.recommendations if validation_request.return_recommendations else [],
            vendor_scores={vendor.value: score for vendor, score in result.ats_vendor_scores.items()},
            validation_metadata={
                "file_name": file.filename,
                "file_size_mb": round(len(file_content) / (1024 * 1024), 2),
                "target_vendors": [v.value for v in target_vendors],
                "compliance_level": compliance_level.value,
                "validation_timestamp": structlog.processors.TimeStamper()._make_stamper("iso")
            }
        )
        
        return response
        
    except Exception as e:
        logger.error("Document validation failed",
                    filename=file.filename,
                    error=str(e),
                    error_type=type(e).__name__)
        
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        try:
            if 'temp_file_path' in locals() and temp_file_path.exists():
                os.unlink(temp_file_path)
        except Exception as e:
            logger.warning("Failed to clean up temporary file", error=str(e))

@router.get(
    "/ats-vendors",
    summary="Get supported ATS vendors",
    description="List all supported ATS vendors for compliance validation"
)
async def get_supported_ats_vendors():
    """Get list of supported ATS vendors."""
    
    vendors = [
        {
            "vendor_id": vendor.value,
            "vendor_name": vendor.name.replace('_', ' ').title(),
            "description": _get_vendor_description(vendor)
        }
        for vendor in ATSVendor
    ]
    
    return {"supported_vendors": vendors}

@router.get(
    "/compliance-levels",
    summary="Get validation compliance levels",
    description="List available compliance validation levels"
)
async def get_compliance_levels():
    """Get list of compliance validation levels."""
    
    levels = [
        {
            "level_id": level.value,
            "level_name": level.name.title(),
            "description": _get_level_description(level),
            "threshold_score": _get_level_threshold(level)
        }
        for level in ComplianceLevel
    ]
    
    return {"compliance_levels": levels}

@router.post(
    "/validate-text",
    response_model=ValidationResponse,
    summary="Validate text content for ATS compliance",
    description="Validate raw text content without file upload"
)
async def validate_text_content(
    text_content: str = Body(..., description="Text content to validate"),
    validation_request: ValidationRequest = Body(..., description="Validation parameters")
) -> ValidationResponse:
    """Validate raw text content against ATS compliance standards."""
    
    logger.info("Starting text content ATS validation",
                content_length=len(text_content),
                target_vendors=validation_request.target_vendors)
    
    if len(text_content) < 50:
        raise HTTPException(
            status_code=400,
            detail="Text content too short for meaningful validation (minimum 50 characters)"
        )
    
    try:
        # Create temporary text file
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = Path(temp_file.name)
        
        # Parse validation parameters
        try:
            target_vendors = [ATSVendor(vendor.lower()) for vendor in validation_request.target_vendors]
        except ValueError:
            valid_vendors = [v.value for v in ATSVendor]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ATS vendor. Valid options: {valid_vendors}"
            )
        
        try:
            compliance_level = ComplianceLevel(validation_request.compliance_level.lower())
        except ValueError:
            valid_levels = [l.value for l in ComplianceLevel]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid compliance level. Valid options: {valid_levels}"
            )
        
        # Perform validation
        validator = await get_ats_validator()
        result = await validator.validate_document(
            document_path=temp_file_path,
            target_vendors=target_vendors,
            compliance_level=compliance_level
        )
        
        logger.info("Text content validation completed",
                   compliance_score=result.compliance_score,
                   is_compliant=result.is_compliant,
                   violations_count=len(result.violations))
        
        # Build response
        response = ValidationResponse(
            is_compliant=result.is_compliant,
            compliance_score=result.compliance_score,
            parsing_confidence=result.parsing_confidence,
            violations=result.violations,
            recommendations=result.recommendations if validation_request.return_recommendations else [],
            vendor_scores={vendor.value: score for vendor, score in result.ats_vendor_scores.items()},
            validation_metadata={
                "content_type": "text",
                "content_length": len(text_content),
                "target_vendors": [v.value for v in target_vendors],
                "compliance_level": compliance_level.value,
                "validation_timestamp": structlog.processors.TimeStamper()._make_stamper("iso")
            }
        )
        
        return response
        
    except Exception as e:
        logger.error("Text content validation failed",
                    content_length=len(text_content),
                    error=str(e),
                    error_type=type(e).__name__)
        
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        try:
            if 'temp_file_path' in locals() and temp_file_path.exists():
                os.unlink(temp_file_path)
        except Exception as e:
            logger.warning("Failed to clean up temporary file", error=str(e))

# Helper functions

def _get_vendor_description(vendor: ATSVendor) -> str:
    """Get description for ATS vendor."""
    descriptions = {
        ATSVendor.WORKDAY: "Enterprise HCM platform with advanced parsing capabilities",
        ATSVendor.GREENHOUSE: "Popular recruiting software with strong resume parsing",
        ATSVendor.LEVER: "Modern ATS focused on candidate experience",
        ATSVendor.BAMBOO_HR: "SMB-focused HR platform with basic parsing",
        ATSVendor.TALEO: "Oracle's enterprise recruiting solution",
        ATSVendor.SUCCESSFACTORS: "SAP's cloud-based HR suite",
        ATSVendor.ICIMS: "Talent acquisition platform for large organizations",
        ATSVendor.JOBVITE: "Social recruiting and candidate management",
        ATSVendor.GENERIC: "Generic ATS with standard parsing capabilities"
    }
    return descriptions.get(vendor, "ATS vendor for recruitment processing")

def _get_level_description(level: ComplianceLevel) -> str:
    """Get description for compliance level."""
    descriptions = {
        ComplianceLevel.STRICT: "Maximum compatibility - passes 95%+ of ATS systems",
        ComplianceLevel.STANDARD: "Industry standard - compatible with most ATS platforms",
        ComplianceLevel.BASIC: "Minimal requirements - basic ATS parsing compatibility"
    }
    return descriptions.get(level, "Compliance validation level")

def _get_level_threshold(level: ComplianceLevel) -> float:
    """Get score threshold for compliance level."""
    thresholds = {
        ComplianceLevel.STRICT: 95.0,
        ComplianceLevel.STANDARD: 85.0,
        ComplianceLevel.BASIC: 70.0
    }
    return thresholds.get(level, 85.0)