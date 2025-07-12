import yfinance as yf
import time

# Tickers from the error logs
tickers = [
    'REP', 'SBA', 'SCG', 'SDE', 'SOUP', 'STO', 'SYNC', 'TCB', 'TES', 'TEV', 
    'TIF', 'TII', 'TOT', 'TXR', 'ZA', 'ZE', 'BRK.B', 'SNE', 'PLT', 'SWP'
]

print("Checking ticker status...")
print("=" * 50)

for ticker in tickers:
    try:
        # Get ticker info
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        # Check if ticker exists and is active
        if info and 'longName' in info and info['longName']:
            print(f"✅ {ticker}: {info['longName']} - ACTIVE")
        else:
            # Try to get current price
            hist = ticker_obj.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                print(f"✅ {ticker}: Current price ${current_price:.2f} - ACTIVE")
            else:
                print(f"❌ {ticker}: No data found - LIKELY DELISTED")
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
        
    except Exception as e:
        print(f"❌ {ticker}: Error - {str(e)}")

print("\n" + "=" * 50)
print("Summary: Check above for ✅ (active) vs ❌ (delisted/error)") 