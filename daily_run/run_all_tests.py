#!/usr/bin/env python3
"""
Comprehensive Test Runner for Daily Run System

Runs all tests and provides a detailed summary report.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_tests():
    """Run all tests in the daily_run system"""
    print("🧪 COMPREHENSIVE TEST RUNNER FOR DAILY RUN SYSTEM")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check if we're in the right location
    if not os.path.exists('tests'):
        print("❌ Error: 'tests' directory not found. Please run from daily_run directory.")
        return False
    
    # List all test files
    test_files = []
    for file in os.listdir('tests'):
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(file)
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  📁 {test_file}")
    print()
    
    # Run each test file
    results = {}
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for test_file in test_files:
        print(f"🔍 Running tests in {test_file}...")
        
        try:
            # Run pytest on the specific test file
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', f'tests/{test_file}', '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse results
            output_lines = result.stdout.split('\n')
            passed = 0
            failed = 0
            
            for line in output_lines:
                if 'PASSED' in line:
                    passed += 1
                elif 'FAILED' in line:
                    failed += 1
            
            results[test_file] = {
                'passed': passed,
                'failed': failed,
                'total': passed + failed,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None,
                'return_code': result.returncode
            }
            
            total_tests += passed + failed
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASSED" if failed == 0 else "❌ FAILED"
            print(f"  {status}: {passed} passed, {failed} failed")
            
        except subprocess.TimeoutExpired:
            print(f"  ⏰ TIMEOUT: {test_file} took too long to run")
            results[test_file] = {
                'passed': 0,
                'failed': 0,
                'total': 0,
                'output': '',
                'error': 'Test execution timed out',
                'return_code': -1
            }
            total_failed += 1
        except Exception as e:
            print(f"  💥 ERROR: {test_file} failed to run: {e}")
            results[test_file] = {
                'passed': 0,
                'failed': 0,
                'total': 0,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
            total_failed += 1
    
    print()
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total test files: {len(test_files)}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed} ✅")
    print(f"Failed: {total_failed} ❌")
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    print()
    
    # Detailed results
    print("📋 DETAILED RESULTS")
    print("=" * 60)
    
    for test_file, result in results.items():
        status = "✅ PASSED" if result['failed'] == 0 else "❌ FAILED"
        print(f"{test_file}: {status}")
        print(f"  Tests: {result['passed']} passed, {result['failed']} failed")
        
        if result['error']:
            print(f"  Error: {result['error']}")
        
        if result['failed'] > 0 and result['output']:
            # Show failed test details
            failed_lines = [line for line in result['output'].split('\n') if 'FAILED' in line]
            if failed_lines:
                print("  Failed tests:")
                for line in failed_lines[:3]:  # Show first 3 failures
                    print(f"    {line.strip()}")
                if len(failed_lines) > 3:
                    print(f"    ... and {len(failed_lines) - 3} more")
        print()
    
    # Overall status
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED! The daily run system is working correctly.")
        return True
    else:
        print("⚠️  SOME TESTS FAILED. Please review the failures above.")
        return False

def main():
    """Main function"""
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
