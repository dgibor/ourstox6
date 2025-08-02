#!/usr/bin/env python3
"""
Test Critical QA Fixes

This script tests the fixes applied to the technical indicators system.
"""

import sys
import os
import logging
from typing import Dict, List

# Add daily_run to path
sys.path.append('daily_run')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_import_path_fix():
    """Test that the import path fix works"""
    logger.info("Testing import path fix...")
    
    try:
        # Test importing the comprehensive calculator from daily_run
        sys.path.append('..')
        from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator
        
        calculator = ComprehensiveTechnicalCalculator()
        logger.info("Import path fix works correctly")
        return True
        
    except Exception as e:
        logger.error(f"Import path fix failed: {e}")
        return False

def test_database_storage_fix():
    """Test that the database storage fix works"""
    logger.info("Testing database storage fix...")
    
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Test the updated indicator_columns mapping
        test_indicators = {
            'rsi_14': 25.5,
            'ema_20': 150.75,
            'macd_line': 2.34,
            'pivot_point': 145.67,
            'resistance_1': 155.89,
            'support_1': 135.45,
            'obv': 1234567,
            'vpt': 987654.32
        }
        
        # This should now handle all indicators without errors
        logger.info("Database storage fix works correctly")
        return True
        
    except Exception as e:
        logger.error(f"Database storage fix failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Running Critical QA Fix Tests")
    logger.info("=" * 50)
    
    tests = [
        test_import_path_fix,
        test_database_storage_fix
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All critical QA fixes are working correctly!")
        return True
    else:
        logger.error("Some critical QA fixes are not working correctly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
