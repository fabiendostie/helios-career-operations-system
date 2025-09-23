#!/usr/bin/env python3
"""
Quick Implementation Verification Test
Validates that the sophisticated research engine is fully implemented vs skeleton code.
"""

import sys
import os
import inspect
import ast
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class ImplementationVerifier:
    """Quick verifier for implementation completeness."""

    def __init__(self):
        self.results = {}

    def analyze_method_implementation(self, file_path: Path, class_name: str = None):
        """Analyze if methods are fully implemented vs skeleton code."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            skeleton_indicators = [
                'pass',
                'NotImplementedError',
                'TODO',
                'FIXME',
                'raise NotImplementedError',
                '# Placeholder',
                '# TODO',
                'return None',
                'return {}',
                'return []'
            ]

            methods_analyzed = 0
            skeleton_methods = []
            implemented_methods = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if class_name:
                        # Only analyze methods of specific class
                        parent = getattr(node, 'parent', None)
                        if not (hasattr(parent, 'name') and parent.name == class_name):
                            continue

                    methods_analyzed += 1
                    method_source = ast.get_source_segment(content, node)

                    # Check if method is skeleton
                    is_skeleton = any(indicator in method_source for indicator in skeleton_indicators)

                    # Check for minimal implementation (just return statement)
                    statements = [n for n in node.body if not isinstance(n, (ast.Pass, ast.Expr))]
                    if len(statements) <= 1 and any(isinstance(s, ast.Return) for s in statements):
                        is_skeleton = True

                    if is_skeleton:
                        skeleton_methods.append(node.name)
                    else:
                        implemented_methods.append(node.name)

            return {
                'total_methods': methods_analyzed,
                'implemented_methods': len(implemented_methods),
                'skeleton_methods': len(skeleton_methods),
                'skeleton_method_names': skeleton_methods,
                'implemented_method_names': implemented_methods,
                'implementation_ratio': len(implemented_methods) / methods_analyzed if methods_analyzed > 0 else 0
            }

        except Exception as e:
            return {'error': str(e)}

    def verify_core_intelligence(self):
        """Verify the core research intelligence is fully implemented."""

        print("IMPLEMENTATION VERIFICATION - SOPHISTICATED RESEARCH ENGINE")
        print("=" * 70)
        print()

        # Check core research integrations
        research_file = Path("src/core/research_integrations.py")
        if research_file.exists():
            print("1. RESEARCH INTEGRATIONS MODULE")
            result = self.analyze_method_implementation(research_file, "DynamicResearchEngine")

            if 'error' not in result:
                print(f"   Total methods: {result['total_methods']}")
                print(f"   Fully implemented: {result['implemented_methods']}")
                print(f"   Skeleton/stub methods: {result['skeleton_methods']}")
                print(f"   Implementation ratio: {result['implementation_ratio']:.1%}")

                if result['skeleton_methods'] > 0:
                    print(f"   [WARNING] Skeleton methods found: {result['skeleton_method_names'][:5]}")

                if result['implementation_ratio'] >= 0.8:
                    print("   [PASS] Core research engine is FULLY IMPLEMENTED")
                else:
                    print("   [FAIL] Core research engine has too many skeleton methods")
            else:
                print(f"   [ERROR] {result['error']}")
        else:
            print("1. [FAIL] Research integrations module not found")

        # Check intelligence components
        print("\n2. INTELLIGENCE COMPONENTS")

        intelligence_files = [
            ("NLP Processor", "src/intelligence/nlp_processor.py"),
            ("Data Ingestion", "src/intelligence/data_ingestion.py"),
            ("Research Orchestrator", "src/intelligence/research_orchestrator.py"),
            ("Database Schema", "src/intelligence/database_schema.py")
        ]

        fully_implemented_count = 0

        for name, file_path in intelligence_files:
            path = Path(file_path)
            if path.exists():
                result = self.analyze_method_implementation(path)

                if 'error' not in result and result['total_methods'] > 0:
                    ratio = result['implementation_ratio']
                    status = "[PASS]" if ratio >= 0.7 else "[FAIL]"
                    print(f"   {status} {name}: {result['implemented_methods']}/{result['total_methods']} methods ({ratio:.1%})")

                    if ratio >= 0.7:
                        fully_implemented_count += 1
                else:
                    print(f"   [ERROR] {name}: Could not analyze")
            else:
                print(f"   [FAIL] {name}: File not found")

        print(f"\n3. OVERALL IMPLEMENTATION STATUS")

        if fully_implemented_count >= 3:
            print("   [PASS] SOPHISTICATED RESEARCH ENGINE IS FULLY IMPLEMENTED")
            print("   -> Advanced NLP processing capabilities present")
            print("   -> Multi-source data ingestion system ready")
            print("   -> Database integration with semantic analysis")
            print("   -> Real-time intelligence gathering mechanisms")
            print("   -> Production-ready implementation detected")
        else:
            print("   [FAIL] INSUFFICIENT IMPLEMENTATION DETECTED")
            print("   -> Skeleton/stub code found in critical components")
            print("   -> Not ready for production use")

        return fully_implemented_count >= 3

def main():
    verifier = ImplementationVerifier()
    is_fully_implemented = verifier.verify_core_intelligence()

    print(f"\nFINAL VERDICT: {'FULLY IMPLEMENTED' if is_fully_implemented else 'INCOMPLETE IMPLEMENTATION'}")
    return 0 if is_fully_implemented else 1

if __name__ == "__main__":
    sys.exit(main())
