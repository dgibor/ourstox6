#!/usr/bin/env python3
"""
Test AAPL Fundamental Data Fetching and Processing
Test the complete pipeline: fetch data, calculate ratios, verify completion
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_aapl_fundamentals():
    """Test complete fundamental data pipeline for AAPL"""
    print("🧪 Testing AAPL Fundamental Data Pipeline")
    print("=" * 50)
    
    # Initialize services
    config = Config()
    db = DatabaseManager()
    fmp = FMPService()
    
    ticker = "AAPL"
    
    try:
        print(f"📊 Processing {ticker}...")
        
        # Step 1: Fetch fundamental data
        print(f"\n1️⃣ Fetching fundamental data for {ticker}...")
        fundamental_data = fmp.get_fundamental_data(ticker)
        
        if not fundamental_data:
            print(f"❌ No fundamental data found for {ticker}")
            return False
        
        print(f"✅ Fundamental data fetched: {len(fundamental_data)} records")
        
        # Step 2: Fetch key statistics
        print(f"\n2️⃣ Fetching key statistics for {ticker}...")
        key_stats = fmp.fetch_key_statistics(ticker)
        
        if not key_stats:
            print(f"❌ No key statistics found for {ticker}")
            return False
        
        print(f"✅ Key statistics fetched: {len(key_stats)} records")
        
        # Step 3: Store data
        print(f"\n3️⃣ Storing data for {ticker}...")
        success = fmp.store_fundamental_data(ticker, fundamental_data, key_stats)
        
        if not success:
            print(f"❌ Failed to store data for {ticker}")
            return False
        
        print(f"✅ Data stored successfully")
        
        # Step 4: Verify data in database
        print(f"\n4️⃣ Verifying data in database...")
        verify_data = verify_aapl_data(db, ticker)
        
        if not verify_data:
            print(f"❌ Data verification failed for {ticker}")
            return False
        
        print(f"✅ Data verification passed")
        
        # Step 5: Check if ratios can be calculated
        print(f"\n5️⃣ Checking ratio calculation capability...")
        ratio_status = check_ratio_calculation(db, ticker)
        
        print(f"✅ Ratio calculation check completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        logger.error(f"Error processing {ticker}: {e}")
        return False

def verify_aapl_data(db, ticker):
    """Verify that AAPL has all required fundamental data"""
    print(f"  Checking {ticker} data completeness...")
    
    # Check if record exists
    query = "SELECT COUNT(*) FROM company_fundamentals WHERE ticker = %s"
    result = db.fetch_one(query, (ticker,))
    
    if not result or result[0] == 0:
        print(f"    ❌ No record found for {ticker}")
        return False
    
    print(f"    ✅ Record found for {ticker}")
    
    # Check specific fields
    fields_to_check = [
        'revenue', 'gross_profit', 'operating_income', 'net_income', 'ebitda',
        'total_assets', 'total_debt', 'total_equity', 'cash_and_equivalents',
        'operating_cash_flow', 'free_cash_flow', 'shares_outstanding',
        'eps_diluted', 'book_value_per_share'
    ]
    
    query = f"""
        SELECT {', '.join(fields_to_check)}
        FROM company_fundamentals 
        WHERE ticker = %s
        ORDER BY report_date DESC
        LIMIT 1
    """
    
    result = db.fetch_one(query, (ticker,))
    
    if not result:
        print(f"    ❌ No data found for {ticker}")
        return False
    
    print(f"    📋 Field completion status:")
    for i, field in enumerate(fields_to_check):
        value = result[i]
        status = "✅" if value is not None else "❌"
        if value is not None:
            if isinstance(value, (int, float)) and value > 1000000:
                print(f"      {status} {field}: ${value:,.0f}")
            else:
                print(f"      {status} {field}: {value}")
        else:
            print(f"      {status} {field}: NULL")
    
    return True

def check_ratio_calculation(db, ticker):
    """Check if we have enough data to calculate all ratios"""
    print(f"  Checking ratio calculation capability for {ticker}...")
    
    # Get latest fundamental data
    query = """
        SELECT 
            revenue, gross_profit, operating_income, net_income, ebitda,
            total_assets, total_debt, total_equity, cash_and_equivalents,
            operating_cash_flow, free_cash_flow, shares_outstanding,
            eps_diluted, book_value_per_share
        FROM company_fundamentals 
        WHERE ticker = %s
        ORDER BY report_date DESC
        LIMIT 1
    """
    
    result = db.fetch_one(query, (ticker,))
    
    if not result:
        print(f"    ❌ No fundamental data found for ratio calculation")
        return False
    
    # Get current price
    price_query = "SELECT close FROM daily_charts WHERE ticker = %s ORDER BY date DESC LIMIT 1"
    price_result = db.fetch_one(price_query, (ticker,))
    current_price = price_result[0] / 100.0 if price_result and price_result[0] else None
    
    print(f"    💰 Current price: ${current_price:.2f}" if current_price else "    ❌ No current price found")
    
    # Check what ratios we can calculate
    ratios = {}
    
    # PE Ratio
    if result[12] and current_price:  # eps_diluted and current_price
        ratios['PE Ratio'] = current_price / result[12]
        print(f"    ✅ PE Ratio: {ratios['PE Ratio']:.2f}")
    
    # PB Ratio
    if result[13] and current_price:  # book_value_per_share and current_price
        ratios['PB Ratio'] = current_price / result[13]
        print(f"    ✅ PB Ratio: {ratios['PB Ratio']:.2f}")
    
    # ROE
    if result[5] and result[7]:  # net_income and total_equity
        ratios['ROE'] = (result[5] / result[7]) * 100
        print(f"    ✅ ROE: {ratios['ROE']:.2f}%")
    
    # Debt/Equity
    if result[6] and result[7]:  # total_debt and total_equity
        ratios['Debt/Equity'] = result[6] / result[7]
        print(f"    ✅ Debt/Equity: {ratios['Debt/Equity']:.2f}")
    
    # Gross Margin
    if result[0] and result[1]:  # revenue and gross_profit
        ratios['Gross Margin'] = (result[1] / result[0]) * 100
        print(f"    ✅ Gross Margin: {ratios['Gross Margin']:.2f}%")
    
    # Operating Margin
    if result[0] and result[2]:  # revenue and operating_income
        ratios['Operating Margin'] = (result[2] / result[0]) * 100
        print(f"    ✅ Operating Margin: {ratios['Operating Margin']:.2f}%")
    
    # Net Margin
    if result[0] and result[3]:  # revenue and net_income
        ratios['Net Margin'] = (result[3] / result[0]) * 100
        print(f"    ✅ Net Margin: {ratios['Net Margin']:.2f}%")
    
    print(f"    📊 Calculated {len(ratios)} ratios successfully")
    
    return len(ratios) > 0

if __name__ == "__main__":
    success = test_aapl_fundamentals()
    if success:
        print(f"\n🎉 AAPL fundamental data pipeline test completed successfully!")
    else:
        print(f"\n❌ AAPL fundamental data pipeline test failed!") 