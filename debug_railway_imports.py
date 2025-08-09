#!/usr/bin/env python3
"""
Debug Railway import issues - run this to diagnose scoring module imports
"""

import os
import sys
import logging

def test_imports():
    """Test if scoring modules can be imported"""
    
    print("🔍 RAILWAY IMPORT DEBUGGING")
    print("=" * 50)
    
    # Show environment
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📦 Python path: {sys.path}")
    print()
    
    # Show PYTHONPATH environment variable
    pythonpath = os.environ.get('PYTHONPATH', 'Not set')
    print(f"🔗 PYTHONPATH env var: {pythonpath}")
    print()
    
    # Check if files exist in current directory
    print("📋 CHECKING FILES IN CURRENT DIRECTORY:")
    files_to_check = [
        'calc_fundamental_scores.py',
        'calc_technical_scores_enhanced.py',
        'daily_run/daily_trading_system.py'
    ]
    
    for file in files_to_check:
        exists = os.path.exists(file)
        print(f"  {'✅' if exists else '❌'} {file}: {'EXISTS' if exists else 'MISSING'}")
    print()
    
    # Try importing the scoring modules
    print("🧪 TESTING IMPORTS:")
    
    # Test 1: Direct import
    try:
        from calc_fundamental_scores import FundamentalScoreCalculator
        print("  ✅ Direct import of FundamentalScoreCalculator: SUCCESS")
    except ImportError as e:
        print(f"  ❌ Direct import of FundamentalScoreCalculator: FAILED - {e}")
    
    # Test 2: Enhanced technical scores
    try:
        from calc_technical_scores_enhanced import EnhancedTechnicalScoreCalculator
        print("  ✅ Direct import of EnhancedTechnicalScoreCalculator: SUCCESS") 
    except ImportError as e:
        print(f"  ❌ Direct import of EnhancedTechnicalScoreCalculator: FAILED - {e}")
    
    # Test 3: Daily trading system
    try:
        from daily_run.daily_trading_system import DailyTradingSystem
        print("  ✅ Import of DailyTradingSystem: SUCCESS")
    except ImportError as e:
        print(f"  ❌ Import of DailyTradingSystem: FAILED - {e}")
    
    print()
    print("🎯 RECOMMENDATIONS:")
    
    # Check if we're in the right directory
    if not os.path.exists('calc_fundamental_scores.py'):
        print("  🔧 Scoring modules not found in current directory")
        print("  📁 Try: cd /app && python debug_railway_imports.py")
    else:
        print("  ✅ Files found - import error might be due to dependencies")
        print("  🔧 Check if all required modules are available")

if __name__ == "__main__":
    test_imports()
