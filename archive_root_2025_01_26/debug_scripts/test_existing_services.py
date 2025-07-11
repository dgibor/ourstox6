#!/usr/bin/env python3
"""
Test existing services to fetch fundamental data for remaining tickers
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Load environment variables
load_dotenv()

def test_existing_services():
    """Test existing services to fetch fundamental data"""
    print("🧮 Testing Existing Services for Fundamental Data")
    print("=" * 60)
    
    # Test tickers that need fundamental data
    test_tickers = ['AMZN', 'AVGO', 'NVDA', 'XOM']
    
    # Try Yahoo Finance first
    print("\n📊 Phase 1: Yahoo Finance")
    print("-" * 30)
    
    try:
        from daily_run.yahoo_finance_service import YahooFinanceService
        yahoo_service = YahooFinanceService()
        
        for ticker in test_tickers:
            print(f"\n🔍 Testing {ticker} with Yahoo Finance:")
            try:
                result = yahoo_service.get_fundamental_data(ticker)
                if result:
                    print(f"  ✅ Success from Yahoo Finance")
                    if result.get('financial_data'):
                        financial = result['financial_data']
                        if financial.get('income_statement'):
                            income = financial['income_statement']
                            print(f"    Revenue TTM: ${income.get('revenue', 0):,.0f}")
                            print(f"    Net Income TTM: ${income.get('net_income', 0):,.0f}")
                            print(f"    EBITDA TTM: ${income.get('ebitda', 0):,.0f}")
                else:
                    print(f"  ❌ No data from Yahoo Finance")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        yahoo_service.close()
        
    except Exception as e:
        print(f"❌ Yahoo Finance service error: {e}")
    
    # Try Alpha Vantage
    print("\n📊 Phase 2: Alpha Vantage")
    print("-" * 30)
    
    try:
        from daily_run.alpha_vantage_service import AlphaVantageService
        alpha_service = AlphaVantageService()
        
        for ticker in test_tickers:
            print(f"\n🔍 Testing {ticker} with Alpha Vantage:")
            try:
                result = alpha_service.get_fundamental_data(ticker)
                if result:
                    print(f"  ✅ Success from Alpha Vantage")
                    if result.get('financial_data'):
                        financial = result['financial_data']
                        if financial.get('income_statement'):
                            income = financial['income_statement']
                            print(f"    Revenue TTM: ${income.get('revenue', 0):,.0f}")
                            print(f"    Net Income TTM: ${income.get('net_income', 0):,.0f}")
                            print(f"    EBITDA TTM: ${income.get('ebitda', 0):,.0f}")
                else:
                    print(f"  ❌ No data from Alpha Vantage")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        alpha_service.close()
        
    except Exception as e:
        print(f"❌ Alpha Vantage service error: {e}")
    
    # Try Finnhub
    print("\n📊 Phase 3: Finnhub")
    print("-" * 30)
    
    try:
        from daily_run.finnhub_service import FinnhubService
        finnhub_service = FinnhubService()
        
        for ticker in test_tickers:
            print(f"\n🔍 Testing {ticker} with Finnhub:")
            try:
                result = finnhub_service.get_fundamental_data(ticker)
                if result:
                    print(f"  ✅ Success from Finnhub")
                    if result.get('financial_data'):
                        financial = result['financial_data']
                        if financial.get('income_statement'):
                            income = financial['income_statement']
                            print(f"    Revenue TTM: ${income.get('revenue', 0):,.0f}")
                            print(f"    Net Income TTM: ${income.get('net_income', 0):,.0f}")
                            print(f"    EBITDA TTM: ${income.get('ebitda', 0):,.0f}")
                else:
                    print(f"  ❌ No data from Finnhub")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        finnhub_service.close()
        
    except Exception as e:
        print(f"❌ Finnhub service error: {e}")
    
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    test_existing_services() 