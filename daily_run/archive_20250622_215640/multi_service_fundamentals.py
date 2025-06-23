#!/usr/bin/env python3
"""
Multi-service fundamental data fetcher with FMP fallback
"""

import os
import logging
import time
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

class MultiServiceFundamentals:
    """Multi-service fundamental data fetcher with fallback logic"""
    
    def __init__(self):
        """Initialize all services"""
        self.services = {}
        self.setup_services()
        
    def setup_services(self):
        """Setup all available services"""
        try:
            # Yahoo Finance Service
            from daily_run.yahoo_finance_service import YahooFinanceService
            self.services['yahoo'] = YahooFinanceService()
            logging.info("Yahoo Finance service initialized")
        except Exception as e:
            logging.warning(f"Yahoo Finance service not available: {e}")
        
        try:
            # Alpha Vantage Service
            from daily_run.alpha_vantage_service import AlphaVantageService
            self.services['alphavantage'] = AlphaVantageService()
            logging.info("Alpha Vantage service initialized")
        except Exception as e:
            logging.warning(f"Alpha Vantage service not available: {e}")
        
        try:
            # FMP Service
            from daily_run.fmp_service import FMPService
            self.services['fmp'] = FMPService()
            logging.info("FMP service initialized")
        except Exception as e:
            logging.warning(f"FMP service not available: {e}")
        
        try:
            # Finnhub Service
            from daily_run.finnhub_service import FinnhubService
            self.services['finnhub'] = FinnhubService()
            logging.info("Finnhub service initialized")
        except Exception as e:
            logging.warning(f"Finnhub service not available: {e}")

    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get fundamental data with fallback logic"""
        # Service priority order
        service_order = ['yahoo', 'alphavantage', 'fmp', 'finnhub']
        
        for service_name in service_order:
            if service_name not in self.services:
                logging.warning(f"Service {service_name} not available, skipping")
                continue
                
            try:
                logging.info(f"Trying {service_name} for {ticker}")
                service = self.services[service_name]
                
                # Get fundamental data from service
                result = service.get_fundamental_data(ticker)
                
                if result:
                    logging.info(f"Successfully got data from {service_name} for {ticker}")
                    return {
                        'data': result,
                        'source': service_name,
                        'timestamp': datetime.now()
                    }
                else:
                    logging.warning(f"No data from {service_name} for {ticker}")
                    
            except Exception as e:
                logging.error(f"Error with {service_name} for {ticker}: {e}")
                continue
        
        logging.error(f"All services failed for {ticker}")
        return None

    def get_fundamental_data_batch(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get fundamental data for multiple tickers with fallback logic"""
        results = {}
        
        for ticker in tickers:
            try:
                result = self.get_fundamental_data(ticker)
                if result:
                    results[ticker] = result
                else:
                    results[ticker] = {'error': 'All services failed', 'timestamp': datetime.now()}
                    
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Error processing {ticker}: {e}")
                results[ticker] = {'error': str(e), 'timestamp': datetime.now()}
        
        return results

    def close(self):
        """Close all service connections"""
        for service_name, service in self.services.items():
            try:
                service.close()
                logging.info(f"Closed {service_name} service")
            except Exception as e:
                logging.warning(f"Error closing {service_name} service: {e}")

def test_multi_service_fundamentals():
    """Test the multi-service fundamental data fetcher"""
    print("🧮 Testing Multi-Service Fundamental Data Fetcher")
    print("=" * 60)
    
    fetcher = MultiServiceFundamentals()
    
    # Test tickers
    test_tickers = ['AAPL', 'AMZN', 'AVGO', 'NVDA', 'XOM']
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}:")
        print("-" * 30)
        
        try:
            result = fetcher.get_fundamental_data(ticker)
            
            if result and 'data' in result:
                source = result['source']
                data = result['data']
                print(f"✅ Success from {source}")
                
                if data.get('financial_data'):
                    financial = data['financial_data']
                    if financial.get('income_statement'):
                        income = financial['income_statement']
                        print(f"  Revenue TTM: ${income.get('revenue', 0):,.0f}")
                        print(f"  Net Income TTM: ${income.get('net_income', 0):,.0f}")
                        print(f"  EBITDA TTM: ${income.get('ebitda', 0):,.0f}")
                
                if data.get('key_stats'):
                    stats = data['key_stats']
                    if stats.get('market_data'):
                        market = stats['market_data']
                        print(f"  Market Cap: ${market.get('market_cap', 0):,.0f}")
                        print(f"  Current Price: ${market.get('current_price', 0):.2f}")
            else:
                print(f"❌ Failed to get data")
                if result and 'error' in result:
                    print(f"  Error: {result['error']}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    fetcher.close()
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    test_multi_service_fundamentals() 