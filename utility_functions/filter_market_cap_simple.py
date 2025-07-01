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
        logging.FileHandler('logs/filter_market_cap_simple.log'),
        logging.StreamHandler()
    ]
)

def check_market_caps_simple():
    """Check market caps for missing tickers with better rate limiting"""
    
    # Read the missing tickers CSV
    input_file = '../pre_filled_stocks/missing_data/missing_tickers.csv'
    output_file = '../pre_filled_stocks/missing_data/missing_tickers_filtered.csv'
    
    logging.info(f"Reading missing tickers from {input_file}")
    df = pd.read_csv(input_file)
    
    logging.info(f"Found {len(df)} tickers to check")
    
    # Track results
    tickers_to_remove = []
    tickers_to_keep = []
    errors = []
    
    # Process in smaller batches with longer delays
    batch_size = 10
    delay_between_batches = 30  # 30 seconds between batches
    
    for batch_start in range(0, len(df), batch_size):
        batch_end = min(batch_start + batch_size, len(df))
        batch_df = df.iloc[batch_start:batch_end]
        
        logging.info(f"Processing batch {batch_start//batch_size + 1}: tickers {batch_start+1}-{batch_end}")
        
        for idx, row in batch_df.iterrows():
            ticker = row['ticker']
            
            # Skip if ticker is empty or invalid
            if pd.isna(ticker) or ticker == '':
                continue
                
            logging.info(f"Checking market cap for {ticker}")
            
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
            
            # Rate limiting within batch
            time.sleep(2)
        
        # Delay between batches
        if batch_end < len(df):
            logging.info(f"Waiting {delay_between_batches} seconds before next batch...")
            time.sleep(delay_between_batches)
    
    # Filter the dataframe
    filtered_df = df[df['ticker'].isin(tickers_to_keep)]
    
    # Save filtered results
    filtered_df.to_csv(output_file, index=False)
    
    # Create summary
    summary = f"""
Market Cap Filtering Results (Simple Method):
============================================
Total tickers processed: {len(df)}
Tickers removed (< $4B): {len(tickers_to_remove)}
Tickers kept (>= $4B): {len(tickers_to_keep)}
Errors encountered: {len(errors)}

Removed tickers: {', '.join(tickers_to_remove[:20])}{'...' if len(tickers_to_remove) > 20 else ''}

Files:
- Original: {input_file}
- Filtered: {output_file}
"""
    
    logging.info(summary)
    
    # Save summary to file
    with open('../pre_filled_stocks/missing_data/filtering_summary_simple.md', 'w') as f:
        f.write(summary)
    
    return filtered_df, tickers_to_remove

if __name__ == '__main__':
    check_market_caps_simple() 