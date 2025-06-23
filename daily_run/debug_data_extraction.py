#!/usr/bin/env python3
"""
Debug what data is being extracted from fundamental services
"""

from service_factory import ServiceFactory
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_data_extraction(ticker='AMC'):
    print(f"Debugging data extraction for {ticker}")
    print("=" * 50)
    
    factory = ServiceFactory()
    fundamental_service = factory.get_fundamental_service()
    
    try:
        # Get data without storing
        print("Fetching fundamental data...")
        data = fundamental_service.get_fundamental_data(ticker)
        
        if data:
            print(f"✅ Data fetched from {data['provider']}")
            
            # Extract the data that would be used for storage
            financial_data = data['data'].get('financial_data', {})
            key_stats = data['data'].get('key_stats', {})
            
            print(f"\nFinancial Data Keys: {list(financial_data.keys())}")
            print(f"Key Stats Keys: {list(key_stats.keys())}")
            
            # Check income statement data
            income = financial_data.get('income_statement', {})
            print(f"\nIncome Statement Data:")
            for key, value in income.items():
                print(f"  {key}: {value}")
            
            # Check market data
            market_data = key_stats.get('market_data', {})
            print(f"\nMarket Data:")
            for key, value in market_data.items():
                print(f"  {key}: {value}")
            
            # Check per share metrics
            per_share = key_stats.get('per_share_metrics', {})
            print(f"\nPer Share Metrics:")
            for key, value in per_share.items():
                print(f"  {key}: {value}")
            
            # Simulate the storage logic
            print(f"\nSimulating storage logic:")
            
            # Prepare update data (same logic as in store_fundamental_data)
            update_data = {
                'market_cap': market_data.get('market_cap'),
                'enterprise_value': market_data.get('enterprise_value'),
                'shares_outstanding': market_data.get('shares_outstanding'),
                'revenue_ttm': income.get('revenue'),
                'net_income_ttm': income.get('net_income'),
                'ebitda_ttm': income.get('ebitda'),
                'diluted_eps_ttm': per_share.get('eps_diluted'),
                'book_value_per_share': per_share.get('book_value_per_share'),
                'total_debt': financial_data.get('balance_sheet', {}).get('total_debt'),
                'shareholders_equity': financial_data.get('balance_sheet', {}).get('total_equity'),
                'cash_and_equivalents': financial_data.get('balance_sheet', {}).get('cash_and_equivalents'),
            }
            
            print(f"Raw update data:")
            for key, value in update_data.items():
                print(f"  {key}: {value}")
            
            # Filter out None values
            filtered_data = {k: v for k, v in update_data.items() if v is not None}
            print(f"\nFiltered update data (non-None values):")
            for key, value in filtered_data.items():
                print(f"  {key}: {value}")
            
            print(f"\nSummary:")
            print(f"  Total fields: {len(update_data)}")
            print(f"  Non-None fields: {len(filtered_data)}")
            print(f"  None fields: {len(update_data) - len(filtered_data)}")
            
            if not filtered_data:
                print(f"❌ No data to update - all values are None!")
            else:
                print(f"✅ {len(filtered_data)} fields would be updated")
                
        else:
            print("❌ No data fetched")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_extraction('AMC') 