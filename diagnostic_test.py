#!/usr/bin/env python3
"""
Diagnostic Test - Identify Why Testing Gets Stuck
Step-by-step diagnostic to find the exact issue
"""

import os
import sys
import time
from datetime import datetime

def test_step(step_name, test_func):
    """Test a single step and report results"""
    print(f"\n🔍 Testing: {step_name}")
    print("-" * 50)
    
    start_time = time.time()
    try:
        result = test_func()
        elapsed = time.time() - start_time
        print(f"✅ PASSED in {elapsed:.2f}s")
        return True, result
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ FAILED after {elapsed:.2f}s")
        print(f"   Error: {e}")
        return False, str(e)

def test_environment():
    """Test environment variables"""
    print("Checking environment variables...")
    
    required_vars = [
        'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
        'news_api_key', 'fred_api_key', 'openai_api_key'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: {'*' * len(value)} (length: {len(value)})")
    
    if missing_vars:
        raise Exception(f"Missing environment variables: {missing_vars}")
    
    return "Environment OK"

def test_file_existence():
    """Test if required files exist"""
    print("Checking required files...")
    
    required_files = [
        'calc_fundamental_scores.py',
        'calc_technical_scores.py',
        'enhanced_sentiment_analyzer.py',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✅ {file}: {size} bytes")
            if size < 1000:
                print(f"     ⚠️  Warning: File is very small, may be corrupted")
        else:
            missing_files.append(file)
            print(f"  ❌ {file}: NOT FOUND")
    
    if missing_files:
        raise Exception(f"Missing files: {missing_files}")
    
    return "Files OK"

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    
    from dotenv import load_dotenv
    import psycopg2
    
    load_dotenv()
    
    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print(f"  Connecting to: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Test basic query
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"  ✅ Connected to PostgreSQL: {version.split(',')[0]}")
    
    # Check required tables
    required_tables = ['daily_charts', 'financial_ratios', 'company_scores_current']
    for table in required_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1")
        count = cursor.fetchone()[0]
        print(f"  ✅ Table {table}: {count} rows")
    
    cursor.close()
    conn.close()
    
    return "Database OK"

def test_imports():
    """Test module imports"""
    print("Testing module imports...")
    
    # Add current directory to path
    sys.path.append(os.path.dirname(__file__))
    
    # Test imports one by one
    try:
        from calc_fundamental_scores import FundamentalScoreCalculator
        print("  ✅ FundamentalScoreCalculator imported")
    except Exception as e:
        raise Exception(f"Failed to import FundamentalScoreCalculator: {e}")
    
    try:
        from calc_technical_scores import TechnicalScoreCalculator
        print("  ✅ TechnicalScoreCalculator imported")
    except Exception as e:
        raise Exception(f"Failed to import TechnicalScoreCalculator: {e}")
    
    try:
        from enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer
        print("  ✅ EnhancedSentimentAnalyzer imported")
    except Exception as e:
        raise Exception(f"Failed to import EnhancedSentimentAnalyzer: {e}")
    
    return "Imports OK"

def test_calculator_initialization():
    """Test calculator initialization"""
    print("Testing calculator initialization...")
    
    from calc_fundamental_scores import FundamentalScoreCalculator
    from calc_technical_scores import TechnicalScoreCalculator
    
    # Test fundamental calculator
    fundamental_calc = FundamentalScoreCalculator()
    print("  ✅ FundamentalScoreCalculator initialized")
    
    # Check calibration factors
    if hasattr(fundamental_calc, 'score_calibration'):
        print(f"  ✅ Score calibration found: {fundamental_calc.score_calibration}")
    else:
        print("  ⚠️  No score calibration found")
    
    # Test technical calculator
    technical_calc = TechnicalScoreCalculator()
    print("  ✅ TechnicalScoreCalculator initialized")
    
    # Check calibration factors
    if hasattr(technical_calc, 'score_calibration'):
        print(f"  ✅ Technical calibration found: {technical_calc.score_calibration}")
    else:
        print("  ⚠️  No technical calibration found")
    
    return "Calculators OK"

def test_single_calculation():
    """Test single calculation without database"""
    print("Testing single calculation...")
    
    from calc_fundamental_scores import FundamentalScoreCalculator
    from calc_technical_scores import TechnicalScoreCalculator
    
    fundamental_calc = FundamentalScoreCalculator()
    technical_calc = TechnicalScoreCalculator()
    
    # Test with AAPL
    print("  Testing AAPL calculation...")
    
    # This will likely fail due to database dependency, but we'll see where it fails
    try:
        fundamental_scores = fundamental_calc.calculate_fundamental_scores('AAPL')
        print("  ✅ Fundamental calculation completed")
        print(f"     Overall Score: {fundamental_scores.get('overall_score', 0):.1f}")
    except Exception as e:
        print(f"  ❌ Fundamental calculation failed: {e}")
        return f"Calculation failed: {e}"
    
    try:
        technical_scores = technical_calc.calculate_technical_scores('AAPL')
        print("  ✅ Technical calculation completed")
        print(f"     Technical Health: {technical_scores.get('technical_health_score', 0):.1f}")
    except Exception as e:
        print(f"  ❌ Technical calculation failed: {e}")
        return f"Technical calculation failed: {e}"
    
    return "Calculation OK"

def main():
    """Run all diagnostic tests"""
    print("🔧 DIAGNOSTIC TEST - Finding the Issue")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Environment Variables", test_environment),
        ("File Existence", test_file_existence),
        ("Database Connection", test_database_connection),
        ("Module Imports", test_imports),
        ("Calculator Initialization", test_calculator_initialization),
        ("Single Calculation", test_single_calculation)
    ]
    
    results = []
    
    for step_name, test_func in tests:
        success, result = test_step(step_name, test_func)
        results.append((step_name, success, result))
        
        if not success:
            print(f"\n💥 STOPPED AT: {step_name}")
            print(f"   This is likely the cause of the testing issues.")
            break
    
    # Summary
    print(f"\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! The system should work.")
        print("   The issue might be with the test script itself.")
    else:
        print(f"\n💥 Found {total - passed} issue(s).")
        print("   Fix the issues above before running the main test.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Diagnostic completed successfully!")
    else:
        print("\n❌ Diagnostic found issues that need to be fixed.")

