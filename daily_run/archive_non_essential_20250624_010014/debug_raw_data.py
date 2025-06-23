#!/usr/bin/env python3
"""
Debug the raw data being returned from fundamental services
"""

from service_factory import ServiceFactory
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_raw_data(ticker='AMC'):
    print(f"Debugging raw data for {ticker}")
    print("=" * 50)
    
    factory = ServiceFactory()
    fundamental_service = factory.get_fundamental_service()
    
    try:
        # Get the raw data from the providers
        print("Getting raw data from providers...")
        
        # Access the providers directly
        yahoo_provider = fundamental_service.providers['yahoo']
        fmp_provider = fundamental_service.providers['fmp']
        
        print(f"\n1. Testing Yahoo Finance provider:")
        print("-" * 30)
        
        # Test Yahoo Finance directly
        try:
            financial_data = yahoo_provider.fetch_financial_statements(ticker)
            print(f"Yahoo financial data: {type(financial_data)}")
            if financial_data:
                print(f"Yahoo financial keys: {list(financial_data.keys())}")
                for key, value in financial_data.items():
                    print(f"  {key}: {type(value)} - {value}")
            else:
                print("Yahoo financial data is None")
        except Exception as e:
            print(f"Yahoo financial error: {e}")
        
        try:
            key_stats = yahoo_provider.fetch_key_statistics(ticker)
            print(f"Yahoo key stats: {type(key_stats)}")
            if key_stats:
                print(f"Yahoo key stats keys: {list(key_stats.keys())}")
                for key, value in key_stats.items():
                    print(f"  {key}: {type(value)} - {value}")
            else:
                print("Yahoo key stats is None")
        except Exception as e:
            print(f"Yahoo key stats error: {e}")
        
        print(f"\n2. Testing FMP provider:")
        print("-" * 30)
        
        # Test FMP directly
        try:
            fmp_data = fmp_provider.get_fundamental_data(ticker)
            print(f"FMP data: {type(fmp_data)}")
            if fmp_data:
                print(f"FMP data keys: {list(fmp_data.keys())}")
                for key, value in fmp_data.items():
                    print(f"  {key}: {type(value)} - {value}")
            else:
                print("FMP data is None")
        except Exception as e:
            print(f"FMP error: {e}")
        
        print(f"\n3. Testing consolidated service:")
        print("-" * 30)
        
        # Test the consolidated service
        consolidated_data = fundamental_service.get_fundamental_data(ticker)
        print(f"Consolidated data: {type(consolidated_data)}")
        if consolidated_data:
            print(f"Consolidated data keys: {list(consolidated_data.keys())}")
            for key, value in consolidated_data.items():
                print(f"  {key}: {type(value)} - {value}")
        else:
            print("Consolidated data is None")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_raw_data('AMC') 