import os
import pandas as pd
import yfinance as yf
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/filter_market_cap_demo.log'),
        logging.StreamHandler()
    ]
)

def check_market_caps_demo():
    """Demo: Check market caps for first 50 missing tickers"""
    
    # Read the missing tickers CSV
    input_file = '../pre_filled_stocks/missing_data/missing_tickers.csv'
    output_file = '../pre_filled_stocks/missing_data/missing_tickers_demo_filtered.csv'
    
    logging.info(f"Reading missing tickers from {input_file}")
    df = pd.read_csv(input_file)
    
    # Take only first 50 tickers for demo
    demo_df = df.head(50)
    logging.info(f"Processing first 50 tickers for demo")
    
    # Track results
    tickers_to_remove = []
    tickers_to_keep = []
    errors = []
    
    for idx, row in demo_df.iterrows():
        ticker = row['ticker']
        
        # Skip if ticker is empty or invalid
        if pd.isna(ticker) or ticker == '':
            continue
            
        logging.info(f"Checking market cap for {ticker} ({idx + 1}/50)")
        
        try:
            # Get stock info from Yahoo Finance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get market cap
            market_cap = info.get('marketCap', 0)
            
            if market_cap is None or market_cap == 0:
                logging.warning(f"No market cap data for {ticker}")
                tickers_to_keep.append(ticker)
                continue
                
            # Convert to billions
            market_cap_b = market_cap / 1_000_000_000
            
            logging.info(f"{ticker}: Market cap = ${market_cap_b:.2f}B")
            
            if market_cap_b < 4.0:
                logging.info(f"REMOVING {ticker}: Market cap ${market_cap_b:.2f}B < $4B")
                tickers_to_remove.append(ticker)
            else:
                logging.info(f"KEEPING {ticker}: Market cap ${market_cap_b:.2f}B >= $4B")
                tickers_to_keep.append(ticker)
                
        except Exception as e:
            logging.error(f"Error checking {ticker}: {e}")
            errors.append(ticker)
            # Keep tickers with errors (conservative approach)
            tickers_to_keep.append(ticker)
        
        # Rate limiting - 3 seconds between requests
        time.sleep(3)
    
    # Filter the dataframe
    filtered_df = demo_df[demo_df['ticker'].isin(tickers_to_keep)]
    
    # Save filtered results
    filtered_df.to_csv(output_file, index=False)
    
    # Create summary
    summary = f"""
Market Cap Filtering Demo Results (First 50 Tickers):
===================================================
Total tickers processed: {len(demo_df)}
Tickers removed (< $4B): {len(tickers_to_remove)}
Tickers kept (>= $4B): {len(tickers_to_keep)}
Errors encountered: {len(errors)}

Removed tickers: {', '.join(tickers_to_remove)}

Files:
- Original: {input_file}
- Demo filtered: {output_file}

Next steps:
- If this demo works well, run the full script on all 603 tickers
- Full script will take approximately 30-45 minutes due to rate limiting
"""
    
    logging.info(summary)
    
    # Save summary to file
    with open('../pre_filled_stocks/missing_data/filtering_demo_summary.md', 'w') as f:
        f.write(summary)
    
    return filtered_df, tickers_to_remove

if __name__ == '__main__':
    check_market_caps_demo() 