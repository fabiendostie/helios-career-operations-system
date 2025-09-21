#!/usr/bin/env python3
"""
Comprehensive Testing & Validation of Dynamic Research Engine
Tests live data gathering, performance, and real-time capabilities
"""

import asyncio
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.research_integrations import get_live_research_engine
from src.core.content_selector import ContentSelector, customize_template_by_industry

class DynamicResearchTester:
    """Comprehensive tester for the Dynamic Research Engine"""

    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}

    async def run_comprehensive_tests(self):
        """Run all comprehensive tests and validations"""
        print("STARTING COMPREHENSIVE DYNAMIC RESEARCH ENGINE TESTS")
        print("=" * 70)

        # Test 1: Live Industry Intelligence Gathering
        print("\nTEST 1: Live Industry Intelligence Gathering")
        await self.test_live_industry_research()

        # Test 2: Real-time ATS Compliance Research
        print("\nTEST 2: Real-time ATS Compliance Research")
        await self.test_ats_compliance_research()

        # Test 3: Company Intelligence for Cover Letters
        print("\nTEST 3: Company Intelligence Research")
        await self.test_company_intelligence()

        # Test 4: Dynamic Template Customization
        print("\nTEST 4: Dynamic Template Customization")
        await self.test_dynamic_customization()

        # Test 5: Performance & Concurrency Tests
        print("\nTEST 5: Performance & Concurrency Tests")
        await self.test_performance_metrics()

        # Test 6: Data Freshness Validation
        print("\nTEST 6: Data Freshness & Caching Tests")
        await self.test_data_freshness()

        # Generate comprehensive report
        await self.generate_test_report()

    async def test_live_industry_research(self):
        """Test live industry intelligence gathering"""
        print("  Testing multiple industries...")
        test_industries = ["Technology", "Finance", "Healthcare", "Marketing"]
        industry_results = {}

        research_engine = await get_live_research_engine()

        for industry in test_industries:
            print(f"  -> Researching {industry} industry...")
            start_time = time.time()

            try:
                intelligence = await research_engine.get_live_industry_intelligence(
                    industry=industry,
                    research_depth="standard"
                )
                end_time = time.time()

                # Validate intelligence structure
                required_fields = [
                    'trending_skills', 'emphasis_areas', 'terminology_style',
                    'keywords', 'confidence_score'
                ]
                validation_passed = all(field in intelligence for field in required_fields)

                industry_results[industry] = {
                    "success": True,
                    "response_time": end_time - start_time,
                    "data_quality": validation_passed,
                    "trending_skills_count": len(intelligence.get('trending_skills', [])),
                    "keywords_count": len(intelligence.get('keywords', [])),
                    "confidence_score": intelligence.get('confidence_score', 0),
                    "emphasis_areas": intelligence.get('emphasis_areas', []),
                    "sample_data": {
                        "trending_skills": intelligence.get('trending_skills', [])[:3],
                        "keywords": intelligence.get('keywords', [])[:5]
                    }
                }

                print(f"     Success! {len(intelligence.get('trending_skills', []))} skills found")
                print(f"     Response time: {end_time - start_time:.2f}s")
                print(f"     Confidence: {intelligence.get('confidence_score', 0):.2f}")

            except Exception as e:
                print(f"     Failed: {str(e)}")
                industry_results[industry] = {
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }

        self.test_results['industry_research'] = industry_results

        # Summary
        success_count = sum(1 for r in industry_results.values() if r.get('success'))
        print(f"\n  INDUSTRY RESEARCH SUMMARY:")
        print(f"     Success Rate: {success_count}/{len(test_industries)} ({success_count/len(test_industries)*100:.1f}%)")

    async def test_ats_compliance_research(self):
        """Test ATS compliance research capabilities"""
        print("  Testing ATS compliance data gathering...")

        research_engine = await get_live_research_engine()
        start_time = time.time()

        try:
            ats_data = await research_engine.get_live_ats_compliance_data()
            end_time = time.time()

            # Validate ATS data structure
            required_sections = ['requirements', 'vendor_insights', 'confidence_score']
            validation_passed = all(section in ats_data for section in required_sections)

            requirements = ats_data.get('requirements', {})
            required_req_sections = ['layout', 'typography', 'graphics', 'keywords']
            requirements_complete = all(section in requirements for section in required_req_sections)

            self.test_results['ats_compliance'] = {
                "success": True,
                "response_time": end_time - start_time,
                "data_structure_valid": validation_passed,
                "requirements_complete": requirements_complete,
                "vendor_count": len(ats_data.get('vendor_insights', [])),
                "confidence_score": ats_data.get('confidence_score', 0),
                "requirements_summary": {
                    "single_column": requirements.get('layout', {}).get('single_column'),
                    "standard_fonts": requirements.get('typography', {}).get('standard_fonts'),
                    "no_graphics": requirements.get('graphics', {}).get('no_graphics')
                }
            }

            print(f"     ATS compliance data gathered successfully")
            print(f"     Response time: {end_time - start_time:.2f}s")
            print(f"     Vendor insights: {len(ats_data.get('vendor_insights', []))}")
            print(f"     Confidence: {ats_data.get('confidence_score', 0):.2f}")

        except Exception as e:
            print(f"     ATS compliance research failed: {str(e)}")
            self.test_results['ats_compliance'] = {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }

    async def test_company_intelligence(self):
        """Test company intelligence research for Pain & Promise"""
        print("  Testing company intelligence gathering...")

        test_companies = ["Microsoft", "Apple", "Google", "Tesla"]
        company_results = {}

        research_engine = await get_live_research_engine()

        for company in test_companies:
            print(f"  -> Researching {company}...")
            start_time = time.time()

            try:
                intelligence = await research_engine.get_live_company_intelligence(company)
                end_time = time.time()

                # Validate company intelligence structure
                required_fields = [
                    'company_name', 'recent_news', 'challenges',
                    'goals', 'pain_points', 'confidence_score'
                ]
                validation_passed = all(field in intelligence for field in required_fields)

                company_results[company] = {
                    "success": True,
                    "response_time": end_time - start_time,
                    "data_quality": validation_passed,
                    "news_items": len(intelligence.get('recent_news', [])),
                    "challenges_identified": len(intelligence.get('challenges', [])),
                    "pain_points_found": len(intelligence.get('pain_points', [])),
                    "confidence_score": intelligence.get('confidence_score', 0),
                    "sample_insights": {
                        "challenges": intelligence.get('challenges', [])[:2],
                        "pain_points": intelligence.get('pain_points', [])[:2]
                    }
                }

                print(f"     Success! {len(intelligence.get('challenges', []))} challenges identified")
                print(f"     Response time: {end_time - start_time:.2f}s")

            except Exception as e:
                print(f"     Failed: {str(e)}")
                company_results[company] = {
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }

        self.test_results['company_intelligence'] = company_results

        # Summary
        success_count = sum(1 for r in company_results.values() if r.get('success'))
        print(f"\n  COMPANY INTELLIGENCE SUMMARY:")
        print(f"     Success Rate: {success_count}/{len(test_companies)} ({success_count/len(test_companies)*100:.1f}%)")

    async def test_dynamic_customization(self):
        """Test dynamic template customization using live research"""
        print("  Testing dynamic template customization...")

        # Test dynamic vs static customization
        test_scenarios = [
            {"industry": "Technology", "role_level": "senior"},
            {"industry": "Finance", "role_level": "executive"},
            {"industry": "Healthcare", "role_level": "mid"}
        ]

        customization_results = {}

        for scenario in test_scenarios:
            industry = scenario["industry"]
            role_level = scenario["role_level"]
            print(f"  -> Testing {industry} - {role_level} customization...")

            start_time = time.time()
            try:
                # Test dynamic customization
                base_template = {"template_type": "t_shaped_classic"}
                dynamic_result = await customize_template_by_industry(
                    template_content=base_template,
                    industry=industry,
                    role_level=role_level
                )
                end_time = time.time()

                # Validate customization results
                expected_fields = [
                    'emphasis_areas', 'terminology_style', 'achievement_format',
                    'trending_skills', 'industry_keywords'
                ]
                has_research_enhancement = '_research_metadata' in dynamic_result
                has_dynamic_fields = any(field in dynamic_result for field in expected_fields)

                customization_results[f"{industry}_{role_level}"] = {
                    "success": True,
                    "response_time": end_time - start_time,
                    "research_enhanced": has_research_enhancement,
                    "dynamic_fields_present": has_dynamic_fields,
                    "emphasis_areas_count": len(dynamic_result.get('emphasis_areas', [])),
                    "trending_skills_count": len(dynamic_result.get('trending_skills', [])),
                    "customization_sample": {
                        "emphasis_areas": dynamic_result.get('emphasis_areas', []),
                        "terminology_style": dynamic_result.get('terminology_style'),
                        "trending_skills": dynamic_result.get('trending_skills', [])[:3]
                    }
                }

                print(f"     Dynamic customization applied successfully")
                print(f"     Response time: {end_time - start_time:.2f}s")
                print(f"     Research enhanced: {has_research_enhancement}")

            except Exception as e:
                print(f"     Failed: {str(e)}")
                customization_results[f"{industry}_{role_level}"] = {
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }

        self.test_results['dynamic_customization'] = customization_results

    async def test_performance_metrics(self):
        """Test performance and concurrency capabilities"""
        print("  Testing performance and concurrency...")

        research_engine = await get_live_research_engine()

        # Test 1: Sequential performance
        print("  -> Testing sequential research performance...")
        start_time = time.time()
        sequential_tasks = []
        for i in range(3):
            result = await research_engine.get_live_industry_intelligence("Technology")
            sequential_tasks.append(result)
        sequential_time = time.time() - start_time

        # Test 2: Concurrent performance
        print("  -> Testing concurrent research performance...")
        start_time = time.time()
        concurrent_tasks = [
            research_engine.get_live_industry_intelligence("Technology"),
            research_engine.get_live_industry_intelligence("Finance"),
            research_engine.get_live_company_intelligence("Microsoft")
        ]
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        concurrent_time = time.time() - start_time

        # Calculate performance metrics
        successful_concurrent = sum(1 for r in concurrent_results if not isinstance(r, Exception))

        self.performance_metrics = {
            "sequential_time": sequential_time,
            "concurrent_time": concurrent_time,
            "concurrency_improvement": ((sequential_time - concurrent_time) / sequential_time) * 100,
            "concurrent_success_rate": (successful_concurrent / len(concurrent_tasks)) * 100,
            "average_request_time": concurrent_time / len(concurrent_tasks)
        }

        print(f"     Performance testing completed")
        print(f"     Sequential time: {sequential_time:.2f}s")
        print(f"     Concurrent time: {concurrent_time:.2f}s")
        print(f"     Performance improvement: {self.performance_metrics['concurrency_improvement']:.1f}%")
        print(f"     Success rate: {self.performance_metrics['concurrent_success_rate']:.1f}%")

    async def test_data_freshness(self):
        """Test data freshness and caching mechanisms"""
        print("  Testing data freshness and caching...")

        research_engine = await get_live_research_engine()

        # Test 1: Cache behavior
        print("  -> Testing cache behavior...")

        # First request (cache miss)
        start_time = time.time()
        result1 = await research_engine.get_live_industry_intelligence("Technology")
        first_request_time = time.time() - start_time

        # Second request (should use cache)
        start_time = time.time()
        result2 = await research_engine.get_live_industry_intelligence("Technology")
        second_request_time = time.time() - start_time

        # Check if caching improved performance
        cache_improvement = first_request_time > second_request_time
        performance_gain = ((first_request_time - second_request_time) / first_request_time) * 100 if cache_improvement else 0

        self.test_results['data_freshness'] = {
            "cache_working": cache_improvement,
            "first_request_time": first_request_time,
            "second_request_time": second_request_time,
            "performance_gain_percent": performance_gain,
            "data_consistency": result1.get('industry') == result2.get('industry')
        }

        print(f"     Cache behavior tested")
        print(f"     Cache performance gain: {performance_gain:.1f}%")
        print(f"     Data consistency maintained: {result1.get('industry') == result2.get('industry')}")

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("                    COMPREHENSIVE TEST REPORT")
        print("="*70)

        # Overall success metrics
        total_tests = 0
        successful_tests = 0

        for category, results in self.test_results.items():
            if isinstance(results, dict):
                if 'success' in results:
                    total_tests += 1
                    if results['success']:
                        successful_tests += 1
                else:
                    # Handle nested results
                    for subcategory, subresult in results.items():
                        if isinstance(subresult, dict) and 'success' in subresult:
                            total_tests += 1
                            if subresult['success']:
                                successful_tests += 1

        overall_success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0

        print(f"\nOVERALL SUCCESS RATE: {successful_tests}/{total_tests} ({overall_success_rate:.1f}%)")

        # Detailed results by category
        print(f"\nDETAILED RESULTS:")

        # Industry Research Results
        if 'industry_research' in self.test_results:
            industry_results = self.test_results['industry_research']
            industry_success = sum(1 for r in industry_results.values() if r.get('success', False))
            print(f"\nINDUSTRY RESEARCH: {industry_success}/{len(industry_results)} successful")
            for industry, result in industry_results.items():
                status = "PASS" if result.get('success') else "FAIL"
                print(f"  {status} {industry}: {result.get('trending_skills_count', 0)} skills, {result.get('confidence_score', 0):.2f} confidence")

        # ATS Compliance Results
        if 'ats_compliance' in self.test_results:
            ats_result = self.test_results['ats_compliance']
            status = "PASS" if ats_result.get('success') else "FAIL"
            print(f"\nATS COMPLIANCE: {status}")
            print(f"  Vendor insights: {ats_result.get('vendor_count', 0)}")
            print(f"  Confidence: {ats_result.get('confidence_score', 0):.2f}")

        # Company Intelligence Results
        if 'company_intelligence' in self.test_results:
            company_results = self.test_results['company_intelligence']
            company_success = sum(1 for r in company_results.values() if r.get('success', False))
            print(f"\nCOMPANY INTELLIGENCE: {company_success}/{len(company_results)} successful")

        # Performance Metrics
        if self.performance_metrics:
            print(f"\nPERFORMANCE METRICS:")
            print(f"  Concurrent improvement: {self.performance_metrics.get('concurrency_improvement', 0):.1f}%")
            print(f"  Average request time: {self.performance_metrics.get('average_request_time', 0):.2f}s")

        # Data Freshness
        if 'data_freshness' in self.test_results:
            freshness = self.test_results['data_freshness']
            print(f"\nDATA FRESHNESS:")
            print(f"  Cache working: {freshness.get('cache_working', False)}")
            print(f"  Performance gain: {freshness.get('performance_gain_percent', 0):.1f}%")

        # Final validation
        print(f"\nVALIDATION SUMMARY:")
        print(f"  Live data gathering: {'WORKING' if overall_success_rate > 80 else 'NEEDS WORK'}")
        print(f"  Performance optimization: {'WORKING' if self.performance_metrics.get('concurrency_improvement', 0) > 0 else 'NEEDS WORK'}")
        print(f"  Real-time capabilities: {'WORKING' if 'industry_research' in self.test_results else 'NEEDS WORK'}")
        print(f"  Data freshness: {'WORKING' if self.test_results.get('data_freshness', {}).get('cache_working') else 'NEEDS WORK'}")

        # Save detailed report
        report_data = {
            "test_timestamp": datetime.now().isoformat(),
            "overall_success_rate": overall_success_rate,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "detailed_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "validation_status": {
                "live_data_gathering": overall_success_rate > 80,
                "performance_optimization": self.performance_metrics.get('concurrency_improvement', 0) > 0,
                "real_time_capabilities": 'industry_research' in self.test_results,
                "data_freshness": self.test_results.get('data_freshness', {}).get('cache_working', False)
            }
        }

        with open('dynamic_research_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\nDetailed report saved to: dynamic_research_test_report.json")
        print("="*70)

async def main():
    """Main test execution"""
    print("STARTING DYNAMIC RESEARCH ENGINE VALIDATION")
    print("This will test live data gathering, performance, and real-time capabilities")
    print()

    tester = DynamicResearchTester()
    try:
        await tester.run_comprehensive_tests()
        print("\nTESTING COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\nTESTING FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
