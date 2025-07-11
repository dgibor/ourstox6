#!/usr/bin/env python3
"""
Setup and Run Fundamental Data Filling
Helps set up FMP API key and runs the fundamental data filling process
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_fmp_api_key():
    """Check if FMP API key is set"""
    api_key = os.getenv('FMP_API_KEY')
    if api_key:
        logger.info("✅ FMP API key is set")
        return True
    else:
        logger.warning("❌ FMP API key is not set")
        return False

def setup_fmp_api_key():
    """Help user set up FMP API key"""
    print("\n🔑 FMP API Key Setup")
    print("=" * 40)
    print("You need to set your FMP API key to proceed.")
    print("You can get your API key from: https://financialmodelingprep.com/developer/docs/")
    print()
    
    # Try to get from user input
    try:
        api_key = input("Enter your FMP API key: ").strip()
        if api_key:
            # Set environment variable for current session
            os.environ['FMP_API_KEY'] = api_key
            logger.info("✅ FMP API key set for current session")
            
            # Test the API key
            if test_fmp_api_key(api_key):
                logger.info("✅ FMP API key is valid")
                return True
            else:
                logger.error("❌ FMP API key is invalid")
                return False
        else:
            logger.error("❌ No API key provided")
            return False
    except KeyboardInterrupt:
        logger.info("Setup cancelled by user")
        return False

def test_fmp_api_key(api_key):
    """Test if the FMP API key is valid"""
    try:
        import requests
        
        # Test with a simple API call
        url = "https://financialmodelingprep.com/api/v3/profile/AAPL"
        params = {'apikey': api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"API test failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing API key: {e}")
        return False

def run_fundamental_analysis():
    """Run the fundamental data analysis"""
    print("\n📊 Running Fundamental Data Analysis")
    print("=" * 40)
    
    try:
        from analyze_missing_data_corrected import main as run_analysis
        report = run_analysis()
        return report
    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        return None

def run_fundamental_filling(limit=None):
    """Run the fundamental data filling process"""
    print(f"\n🚀 Running Fundamental Data Filling (limit: {limit or 'all'})")
    print("=" * 40)
    
    try:
        from simple_fundamental_filler import SimpleFundamentalFiller
        
        filler = SimpleFundamentalFiller()
        results = filler.process_all_tickers(limit=limit)
        
        return results
    except Exception as e:
        logger.error(f"Error running fundamental filling: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Setup and Run Fundamental Data Filling")
    print("=" * 60)
    
    # Check if FMP API key is set
    if not check_fmp_api_key():
        if not setup_fmp_api_key():
            print("\n❌ Cannot proceed without valid FMP API key")
            return
    
    # Run analysis first
    print("\n1️⃣ Step 1: Analyzing current data state...")
    analysis_report = run_fundamental_analysis()
    
    if not analysis_report:
        print("❌ Analysis failed, cannot proceed")
        return
    
    # Show analysis results
    summary = analysis_report.get('summary', {})
    print(f"\n📊 Analysis Results:")
    print(f"  - Total stocks: {summary.get('total_stocks', 0)}")
    print(f"  - Missing fundamentals: {summary.get('stocks_no_fundamentals', 0)}")
    print(f"  - Stale fundamentals: {summary.get('stocks_stale_fundamentals', 0)}")
    print(f"  - Total tickers needing updates: {summary.get('tickers_needing_updates', 0)}")
    
    # Ask user how many tickers to process
    print(f"\n2️⃣ Step 2: Choose processing scope...")
    print("Options:")
    print("  1. Test with 10 tickers")
    print("  2. Test with 50 tickers") 
    print("  3. Test with 100 tickers")
    print("  4. Process all tickers (use with caution)")
    print("  5. Process tickers needing updates only")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            limit = 10
        elif choice == '2':
            limit = 50
        elif choice == '3':
            limit = 100
        elif choice == '4':
            limit = None  # Process all
        elif choice == '5':
            # Process only tickers needing updates
            tickers_needing_data = analysis_report.get('tickers_needing_data', [])
            limit = len(tickers_needing_data)
            print(f"Processing {limit} tickers that need updates")
        else:
            print("Invalid choice, using 50 tickers as default")
            limit = 50
        
        # Run fundamental filling
        print(f"\n3️⃣ Step 3: Running fundamental data filling...")
        results = run_fundamental_filling(limit)
        
        if results:
            # Show results
            print(f"\n📊 Filling Results:")
            print(f"  - Successful updates: {len(results.get('successful', []))}")
            print(f"  - Failed updates: {len(results.get('failed', []))}")
            print(f"  - Processing time: {results.get('processing_time', 0):.2f}s")
            
            efficiency = results.get('efficiency_metrics', {})
            if efficiency:
                print(f"  - Success rate: {efficiency.get('success_rate_percent', 0):.1f}%")
                print(f"  - API calls used: {efficiency.get('api_calls_used', 0)}")
                print(f"  - API calls remaining: {efficiency.get('api_calls_remaining', 0)}")
            
            # Show some successful tickers
            successful = results.get('successful', [])
            if successful:
                print(f"\n✅ Successfully updated tickers (first 10):")
                for i, ticker in enumerate(successful[:10]):
                    print(f"  {i+1:2d}. {ticker}")
                if len(successful) > 10:
                    print(f"  ... and {len(successful) - 10} more")
            
            # Show some failed tickers
            failed = results.get('failed', [])
            if failed:
                print(f"\n❌ Failed tickers (first 10):")
                for i, ticker in enumerate(failed[:10]):
                    print(f"  {i+1:2d}. {ticker}")
                if len(failed) > 10:
                    print(f"  ... and {len(failed) - 10} more")
        
        print("\n✅ Process completed!")
        
    except KeyboardInterrupt:
        print("\n❌ Process cancelled by user")
    except Exception as e:
        print(f"\n❌ Process failed: {e}")

if __name__ == "__main__":
    main() 