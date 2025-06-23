#!/usr/bin/env python3
"""
Update fundamental data for a list of tickers using the new pipeline
"""

from service_factory import ServiceFactory
import sys


def update_fundamentals_for_tickers(tickers):
    print(f"Updating fundamentals for: {tickers}")
    factory = ServiceFactory()
    fundamental_service = factory.get_fundamental_service()
    updated = []
    failed = []
    
    for ticker in tickers:
        try:
            # Use the service's built-in method that fetches and stores data
            data = fundamental_service.get_fundamental_data_with_storage(ticker)
            if data:
                updated.append(ticker)
                print(f"  ✅ {ticker} updated.")
            else:
                failed.append(ticker)
                print(f"  ❌ {ticker} no data.")
        except Exception as e:
            failed.append(ticker)
            print(f"  ❌ {ticker} error: {e}")
    
    print(f"Done. Updated: {updated}. Failed: {failed}")

if __name__ == "__main__":
    # Accept tickers as command line args or use a default list
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    update_fundamentals_for_tickers(tickers) 