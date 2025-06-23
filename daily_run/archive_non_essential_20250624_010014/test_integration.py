#!/usr/bin/env python3
"""
Integration test for the daily pipeline components
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from config import Config
from database import DatabaseManager
from price_service import PriceCollector
from ratios_calculator import RatiosCalculator
from service_factory import ServiceFactory
from new_daily_pipeline import DailyPipeline

def test_integration():
    """Test all components working together"""
    print("🧪 Testing Integration")
    print("=" * 40)
    
    # Test configuration
    print("1. Testing Configuration...")
    db_config = Config.get_db_config()
    print(f"✅ Database host: {db_config.get('host', 'Not set')}")
    print(f"✅ Database name: {db_config.get('dbname', 'Not set')}")
    
    # Test database connection
    print("\n2. Testing Database Connection...")
    db = DatabaseManager()
    try:
        db.connect()
        print("✅ Database connection successful")
        
        # Test getting tickers
        tickers = db.get_tickers('stocks')
        print(f"✅ Found {len(tickers)} tickers in database")
        
        # Use AAPL for testing since it has financial data
        test_ticker = 'AAPL'
        print(f"✅ Using {test_ticker} for testing")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    finally:
        db.disconnect()
    
    # Test price service
    print("\n3. Testing Price Service...")
    price_service = PriceCollector()
    try:
        # Get current price from database
        db = DatabaseManager()
        db.connect()
        current_price = db.get_latest_price(test_ticker)
        if current_price:
            print(f"✅ Got price for {test_ticker}: ${current_price/100:.2f}")
        else:
            print(f"⚠️  No price data for {test_ticker}")
        db.disconnect()
    except Exception as e:
        print(f"❌ Price service error: {e}")
    
    # Test ratios calculator
    print("\n4. Testing Ratios Calculator...")
    calculator = RatiosCalculator()
    try:
        result = calculator.calculate_all_ratios(test_ticker)
        if 'error' not in result:
            print(f"✅ Calculated ratios for {test_ticker}")
            print(f"  Data quality: {result['data_quality_score']}%")
            ratios = result['ratios']
            if ratios.get('pe_ratio'):
                print(f"  P/E: {ratios['pe_ratio']}")
            if ratios.get('pb_ratio'):
                print(f"  P/B: {ratios['pb_ratio']}")
            if ratios.get('ps_ratio'):
                print(f"  P/S: {ratios['ps_ratio']}")
        else:
            print(f"⚠️  Ratio calculation failed: {result['error']}")
    except Exception as e:
        print(f"❌ Ratios calculator error: {e}")
    finally:
        calculator.close()
    
    # Test service factory
    print("\n5. Testing Service Factory...")
    factory = ServiceFactory()
    try:
        # Test fundamental service
        fundamental_service = factory.get_fundamental_service()
        print(f"✅ Created fundamental service: {type(fundamental_service).__name__}")
        
        # Test price service
        price_service = factory.get_price_service()
        print(f"✅ Created price service: {type(price_service).__name__}")
        
    except Exception as e:
        print(f"❌ Service factory error: {e}")
    
    # Test daily pipeline
    print("\n6. Testing Daily Pipeline...")
    pipeline = DailyPipeline()
    try:
        # Test with single ticker
        result = pipeline.process_ticker(test_ticker)
        if result['success']:
            print(f"✅ Pipeline processed {test_ticker} successfully")
            print(f"  Price updated: {result['price_updated']}")
            print(f"  Fundamentals updated: {result['fundamentals_updated']}")
            print(f"  Ratios calculated: {result['ratios_calculated']}")
        else:
            print(f"⚠️  Pipeline failed for {test_ticker}: {result['error']}")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
    finally:
        pipeline.close()
    
    print("\n✅ Integration test completed!")

if __name__ == "__main__":
    test_integration() 