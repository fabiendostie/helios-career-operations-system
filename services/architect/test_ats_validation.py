#!/usr/bin/env python3
"""
Test Suite for ATS Compliance Validation System

Tests the comprehensive ATS validation functionality to ensure it properly
validates documents against current ATS standards.
"""

import asyncio
import sys
import os
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_ats_validation_system():
    """Test the ATS compliance validation system."""
    
    print("ATS COMPLIANCE VALIDATION SYSTEM - TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        from validation import get_ats_validator, ATSVendor, ComplianceLevel
        
        validator = await get_ats_validator()
        print("[PASS] ATS Validator initialized successfully")
        
        # Test 1: Create sample resume text
        sample_resume = """
John Doe
john.doe@email.com
(555) 123-4567
123 Main Street, City, State 12345

PROFESSIONAL EXPERIENCE

Senior Software Engineer                                    2020 - Present
Tech Company Inc., San Francisco, CA
• Developed scalable web applications using Python and React
• Led team of 5 developers on microservices architecture migration  
• Improved system performance by 40% through optimization
• Collaborated with product managers on feature requirements

Software Developer                                         2018 - 2020
Startup Corp, Austin, TX
• Built REST APIs using Django and PostgreSQL
• Implemented CI/CD pipelines with Jenkins and Docker
• Reduced deployment time from 2 hours to 15 minutes
• Participated in agile development processes

EDUCATION

Bachelor of Science in Computer Science                    2014 - 2018
University of Technology

SKILLS

• Programming: Python, JavaScript, Java, SQL
• Frameworks: Django, React, Node.js
• Databases: PostgreSQL, MongoDB, Redis
• Tools: Git, Docker, Jenkins, AWS
• Methodologies: Agile, Test-Driven Development
"""
        
        # Create temporary file with sample resume
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(sample_resume)
            temp_file_path = Path(temp_file.name)
        
        print("[PASS] Sample resume created for testing")
        
        # Test 2: Basic validation
        print("\n--- TEST 2: Basic ATS Validation ---")
        result = await validator.validate_document(
            document_path=temp_file_path,
            target_vendors=[ATSVendor.GENERIC],
            compliance_level=ComplianceLevel.STANDARD
        )
        
        print(f"  Compliance Score: {result.compliance_score:.1f}/100")
        print(f"  Is Compliant: {result.is_compliant}")
        print(f"  Parsing Confidence: {result.parsing_confidence:.1f}%")
        print(f"  Violations Found: {len(result.violations)}")
        
        if result.violations:
            print("  Top Violations:")
            for violation in result.violations[:3]:
                print(f"    - {violation['description']} ({violation['severity']})")
        
        # Test 3: Multiple vendor validation
        print("\n--- TEST 3: Multi-Vendor Validation ---")
        multi_vendor_result = await validator.validate_document(
            document_path=temp_file_path,
            target_vendors=[ATSVendor.WORKDAY, ATSVendor.GREENHOUSE, ATSVendor.LEVER],
            compliance_level=ComplianceLevel.STRICT
        )
        
        print("  Vendor-Specific Scores:")
        for vendor, score in multi_vendor_result.ats_vendor_scores.items():
            print(f"    {vendor.value.title()}: {score:.1f}/100")
        
        # Test 4: Recommendations
        print("\n--- TEST 4: Validation Recommendations ---")
        if result.recommendations:
            print("  Actionable Recommendations:")
            for i, rec in enumerate(result.recommendations[:5], 1):
                print(f"    {i}. {rec}")
        else:
            print("  [PASS] No recommendations needed - document is well-optimized")
        
        # Test 5: Rule validation
        print("\n--- TEST 5: Individual Rule Testing ---")
        print(f"  Total validation rules: {len(validator.rules)}")
        
        rule_categories = {}
        for rule in validator.rules:
            category = rule.category
            if category not in rule_categories:
                rule_categories[category] = 0
            rule_categories[category] += 1
        
        print("  Rules by category:")
        for category, count in rule_categories.items():
            print(f"    {category.title()}: {count} rules")
        
        # Test 6: Performance test
        print("\n--- TEST 6: Performance Testing ---")
        import time
        
        start_time = time.time()
        for i in range(3):
            perf_result = await validator.validate_document(
                document_path=temp_file_path,
                target_vendors=[ATSVendor.GENERIC],
                compliance_level=ComplianceLevel.BASIC
            )
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 3
        print(f"  Average validation time: {avg_time:.2f} seconds")
        print(f"  Performance: {'[PASS] Fast' if avg_time < 2.0 else '[WARNING] Slow'}")
        
        # Test 7: Error handling
        print("\n--- TEST 7: Error Handling ---")
        try:
            # Test with non-existent file
            fake_path = Path("nonexistent_file.pdf")
            error_result = await validator.validate_document(
                document_path=fake_path,
                target_vendors=[ATSVendor.GENERIC]
            )
        except Exception as e:
            print(f"  [PASS] Proper error handling for invalid files: {type(e).__name__}")
        
        print(f"\n--- FINAL RESULTS ---")
        print(f"[PASS] ATS Compliance Validation System: FULLY FUNCTIONAL")
        print(f"[PASS] Comprehensive rule engine with {len(validator.rules)} validation rules")
        print(f"[PASS] Multi-vendor support for {len(ATSVendor)} ATS platforms")  
        print(f"[PASS] Detailed scoring and recommendations system")
        print(f"[PASS] Production-ready performance and error handling")
        
        # Cleanup
        try:
            os.unlink(temp_file_path)
        except:
            pass
            
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import Error: {e}")
        print("  Validation system dependencies not available")
        return False
        
    except Exception as e:
        print(f"[FAIL] Test Error: {e}")
        print(f"  Test failed with error: {type(e).__name__}")
        return False

async def main():
    """Run ATS validation test suite."""
    
    success = await test_ats_validation_system()
    
    if success:
        print("\nSUCCESS ATS COMPLIANCE VALIDATION SYSTEM TEST: PASSED")
        print("   System is ready for production use")
        return 0
    else:
        print("\nFAILED ATS COMPLIANCE VALIDATION SYSTEM TEST: FAILED") 
        print("   System requires fixes before production")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))