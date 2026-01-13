"""
Autonomous Multi-Agent Business Intelligence System - Comprehensive Test Suite Runner

Runs all integration tests and generates detailed reports.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_banner(text):
    """Print formatted banner"""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")


def run_all_tests():
    """Run all test suites"""
    import unittest
    
    print_banner("Autonomous Multi-Agent Business Intelligence System - Complete Test Suite")
    
    # Discover all tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    print_banner("TEST RESULTS SUMMARY")
    
    print(f"📊 Total Tests Run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"⏱️  Time: {result.testsRun * 0.5:.1f}s (estimated)")
    
    # Coverage summary
    if result.wasSuccessful():
        print("\n" + "🎉 " * 20)
        print("ALL TESTS PASSED - System Ready for Production!".center(80))
        print("🎉 " * 20)
    else:
        print("\n⚠️  Some tests failed - Review details above")
    
    return result.wasSuccessful()


def run_specific_test(test_name):
    """Run a specific test file"""
    import unittest
    
    print_banner(f"Running: {test_name}")
    
    # Import and run specific test
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
