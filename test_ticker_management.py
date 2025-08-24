#!/usr/bin/env python3
"""
Test Script for Stock Ticker Management

This script tests the ticker management functionality without making actual changes
to verify the logic and database connectivity.
"""

import sys
import logging
from datetime import datetime

# Add the daily_run directory to the path
sys.path.append('daily_run')

try:
    from database import DatabaseManager
    from config import Config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connectivity"""
    print("🔌 Testing database connection...")
    
    try:
        db = DatabaseManager()
        if db.connect():
            print("✅ Database connection successful")
            
            # Test basic query
            ticker_count = len(db.get_tickers())
            print(f"✅ Found {ticker_count} tickers in database")
            
            db.disconnect()
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_ticker_verification():
    """Test ticker verification logic"""
    print("\n🔍 Testing ticker verification logic...")
    
    try:
        db = DatabaseManager()
        db.connect()
        
        # Test tickers to delete
        tickers_to_delete = [
            'PBCT', 'PLAN', 'QTS', 'RXN', 'SAI', 'SC', 'SHI', 'SHLX', 
            'SNP', 'SYNC', 'AFTY', 'TIF', 'PTR'
        ]
        
        # Get existing tickers
        existing_tickers = db.get_tickers()
        
        # Check which ones exist
        found_tickers = [t for t in tickers_to_delete if t in existing_tickers]
        missing_tickers = [t for t in tickers_to_delete if t not in existing_tickers]
        
        print(f"📊 Verification Results:")
        print(f"   - Total tickers in database: {len(existing_tickers)}")
        print(f"   - Tickers to delete found: {len(found_tickers)}")
        print(f"   - Tickers to delete missing: {len(missing_tickers)}")
        
        if found_tickers:
            print(f"   - Found tickers: {found_tickers}")
        if missing_tickers:
            print(f"   - Missing tickers: {missing_tickers}")
        
        # Test ABCM/TXNM
        abc_exists = 'ABCM' in existing_tickers
        txn_exists = 'TXNM' in existing_tickers
        
        print(f"\n🔄 Ticker Change Test:")
        print(f"   - ABCM exists: {abc_exists}")
        print(f"   - TXNM exists: {txn_exists}")
        
        if abc_exists and not txn_exists:
            print("   ✅ ABCM can be changed to TXNM")
        elif not abc_exists:
            print("   ⚠️  ABCM not found - cannot change")
        elif txn_exists:
            print("   ⚠️  TXNM already exists - cannot change")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Ticker verification error: {e}")
        return False

def test_safe_operations():
    """Test operations that don't modify data"""
    print("\n🧪 Testing safe operations...")
    
    try:
        db = DatabaseManager()
        db.connect()
        
        # Test transaction management
        print("   - Testing transaction management...")
        db.begin_transaction()
        print("   ✅ Transaction started")
        
        # Test rollback
        db.rollback()
        print("   ✅ Transaction rollback successful")
        
        # Test cursor operations
        print("   - Testing cursor operations...")
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM stocks")
            count = cursor.fetchone()[0]
            print(f"   ✅ Cursor query successful: {count} stocks")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Safe operations error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Stock Ticker Management - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Ticker Verification", test_ticker_verification),
        ("Safe Operations", test_safe_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to run ticker management.")
        print("\n💡 Next steps:")
        print("   1. Review the verification results above")
        print("   2. Ensure you have a backup of your database")
        print("   3. Run: python manage_stock_tickers.py")
    else:
        print("⚠️  Some tests failed. Please fix issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()



