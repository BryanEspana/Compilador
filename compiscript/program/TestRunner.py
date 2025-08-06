"""
Test Runner for Compiscript Compiler
Runs semantic analysis tests and reports results
"""

import sys
import os
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from SemanticAnalyzer import SemanticAnalyzer

class TestResult:
    def __init__(self, test_name: str, expected_success: bool, actual_success: bool, errors: list):
        self.test_name = test_name
        self.expected_success = expected_success
        self.actual_success = actual_success
        self.errors = errors
        self.passed = expected_success == actual_success

def run_semantic_analysis(file_path: str) -> tuple:
    """Run semantic analysis on a file and return (success, errors)"""
    try:
        input_stream = FileStream(file_path)
        lexer = CompiscriptLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(stream)
        
        # Parse the program
        tree = parser.program()
        
        # Check for syntax errors
        if parser.getNumberOfSyntaxErrors() > 0:
            return False, [f"Syntax errors: {parser.getNumberOfSyntaxErrors()}"]
        
        # Semantic Analysis
        semantic_analyzer = SemanticAnalyzer()
        walker = ParseTreeWalker()
        walker.walk(semantic_analyzer, tree)
        
        # Return results
        has_errors = semantic_analyzer.has_errors()
        errors = semantic_analyzer.get_errors()
        
        return not has_errors, errors
        
    except Exception as e:
        return False, [f"Exception: {str(e)}"]

def run_tests():
    """Run all test cases"""
    test_cases = [
        # (file_path, expected_success, description)
        ("tests/test_success.cps", True, "Valid Compiscript code should pass"),
        ("tests/test_errors.cps", False, "Invalid Compiscript code should fail"),
        ("program.cps", False, "Original program has semantic errors"),
    ]
    
    results = []
    
    print("=" * 60)
    print("COMPISCRIPT SEMANTIC ANALYSIS TEST SUITE")
    print("=" * 60)
    
    for file_path, expected_success, description in test_cases:
        print(f"\n[TEST] {file_path}")
        print(f"Description: {description}")
        print(f"Expected: {'PASS' if expected_success else 'FAIL'}")
        
        if not os.path.exists(file_path):
            print(f"[SKIP] File not found: {file_path}")
            continue
        
        actual_success, errors = run_semantic_analysis(file_path)
        result = TestResult(file_path, expected_success, actual_success, errors)
        results.append(result)
        
        print(f"Actual: {'PASS' if actual_success else 'FAIL'}")
        print(f"Result: {'[OK] CORRECT' if result.passed else '[FAIL] INCORRECT'}")
        
        if errors:
            print(f"Errors found ({len(errors)}):")
            for i, error in enumerate(errors[:5]):  # Show first 5 errors
                print(f"  {i+1}. {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
    
    # Detailed results
    if any(not r.passed for r in results):
        print("\nFAILED TESTS:")
        for result in results:
            if not result.passed:
                expected = "should pass" if result.expected_success else "should fail"
                actual = "passed" if result.actual_success else "failed"
                print(f"  - {result.test_name}: {expected} but {actual}")
    
    return passed == total

def run_individual_test(file_path: str):
    """Run a single test file"""
    print(f"Testing: {file_path}")
    print("=" * 50)
    
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return
    
    success, errors = run_semantic_analysis(file_path)
    
    print(f"Result: {'PASS' if success else 'FAIL'}")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for i, error in enumerate(errors):
            print(f"  {i+1}. {error}")
    else:
        print("\nNo semantic errors found.")

def main():
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        run_individual_test(test_file)
    else:
        # Run all tests
        success = run_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
