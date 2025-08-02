#!/usr/bin/env python3
"""
Run technical indicators calculation for target tickers
"""

import subprocess
import logging
from daily_run.database import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_technical_indicators():
    """Run technical indicators calculation for target tickers"""
    
    # Target tickers
    target_tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    
    print(f"Starting technical indicators calculation for: {', '.join(target_tickers)}")
    
    results = {}
    
    for ticker in target_tickers:
        print(f"\nProcessing {ticker}...")
        try:
            # Run the calc_technicals script for this ticker
            result = subprocess.run([
                'python', 'daily_run/calc_technicals.py',
                '--table', 'daily_charts',
                '--ticker_col', 'ticker',
                '--ticker', ticker
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {ticker}: Success")
                results[ticker] = {'success': True, 'output': result.stdout}
            else:
                print(f"❌ {ticker}: Failed")
                print(f"Error: {result.stderr}")
                results[ticker] = {'success': False, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {ticker}: Timeout")
            results[ticker] = {'success': False, 'error': 'Timeout'}
        except Exception as e:
            print(f"💥 {ticker}: Exception - {e}")
            results[ticker] = {'success': False, 'error': str(e)}
    
    # Verify results
    print("\n=== VERIFICATION ===")
    db = DatabaseManager()
    
    for ticker in target_tickers:
        try:
            # Check if EMA_100 and ADX_14 are now populated
            result = db.execute_query("""
                SELECT ema_100, adx_14 
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """, (ticker,))
            
            if result and result[0]:
                ema_100, adx_14 = result[0]
                if ema_100 is not None and adx_14 is not None:
                    print(f"✅ {ticker}: EMA_100 and ADX_14 populated")
                else:
                    print(f"⚠️  {ticker}: EMA_100={ema_100}, ADX_14={adx_14}")
            else:
                print(f"❌ {ticker}: No data found")
                
        except Exception as e:
            print(f"💥 {ticker}: Database error - {e}")
    
    db.disconnect()
    
    # Summary
    print("\n=== SUMMARY ===")
    success_count = sum(1 for r in results.values() if r['success'])
    print(f"Success: {success_count}/{len(target_tickers)}")
    
    for ticker, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {ticker}")
    
    return results

if __name__ == "__main__":
    run_technical_indicators() 