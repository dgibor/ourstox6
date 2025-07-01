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
        logging.FileHandler('logs/filter_market_cap_batch.log'),
        logging.StreamHandler()
    ]
)

def check_market_caps_batch():
    """Check market caps for missing tickers using batch queries"""
    
    # Read the missing tickers CSV
    input_file = '../pre_filled_stocks/missing_data/missing_tickers.csv'
    output_file = '../pre_filled_stocks/missing_data/missing_tickers_filtered.csv'
    
    logging.info(f"Reading missing tickers from {input_file}")
    df = pd.read_csv(input_file)
    
    logging.info(f"Found {len(df)} tickers to check")
    
    # Get list of tickers
    tickers = df['ticker'].dropna().tolist()
    
    # Filter out invalid tickers
    valid_tickers = [ticker for ticker in tickers if ticker and ticker != '' and not ticker.startswith('COMMUNICATION') and not ticker.startswith('CONSUMER') and not ticker.startswith('FINANCIALS') and not ticker.startswith('HEALTH') and not ticker.startswith('INDUSTRIALS') and not ticker.startswith('INFORMATION') and not ticker.startswith('MATERIALS') and not ticker.startswith('UTILITIES')]
    
    logging.info(f"Processing {len(valid_tickers)} valid tickers")
    
    # Track results
    tickers_to_remove = []
    tickers_to_keep = []
    errors = []
    
    # Process in batches of 50 (Yahoo Finance batch limit)
    batch_size = 50
    
    for i in range(0, len(valid_tickers), batch_size):
        batch_tickers = valid_tickers[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(valid_tickers) + batch_size - 1) // batch_size
        
        logging.info(f"Processing batch {batch_num}/{total_batches}: {len(batch_tickers)} tickers")
        
        try:
            # Create batch ticker object
            batch_symbols = ' '.join(batch_tickers)
            tickers_batch = yf.Tickers(batch_symbols)
            
            # Get info for all tickers in batch using the correct method
            batch_info = {}
            for ticker in batch_tickers:
                try:
                    ticker_obj = tickers_batch.tickers[ticker]
                    info = ticker_obj.info
                    batch_info[ticker] = info
                except Exception as e:
                    logging.error(f"Error getting info for {ticker}: {e}")
                    batch_info[ticker] = {}
            
            # Process each ticker in the batch
            for ticker in batch_tickers:
                try:
                    # Get market cap for this ticker
                    if ticker in batch_info and batch_info[ticker] and 'marketCap' in batch_info[ticker]:
                        market_cap = batch_info[ticker]['marketCap']
                        
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
                    else:
                        logging.warning(f"No market cap data for {ticker}")
                        tickers_to_keep.append(ticker)
                        
                except Exception as e:
                    logging.error(f"Error processing {ticker}: {e}")
                    errors.append(ticker)
                    tickers_to_keep.append(ticker)
            
            # Rate limiting between batches
            if i + batch_size < len(valid_tickers):
                logging.info("Waiting 5 seconds before next batch...")
                time.sleep(5)
                
        except Exception as e:
            logging.error(f"Error processing batch {batch_num}: {e}")
            # If batch fails, keep all tickers in this batch
            tickers_to_keep.extend(batch_tickers)
            errors.extend(batch_tickers)
    
    # Filter the dataframe
    filtered_df = df[df['ticker'].isin(tickers_to_keep)]
    
    # Save filtered results
    filtered_df.to_csv(output_file, index=False)
    
    # Create summary
    summary = f"""
Market Cap Filtering Results (Batch Method):
===========================================
Total tickers processed: {len(df)}
Valid tickers checked: {len(valid_tickers)}
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
    with open('../pre_filled_stocks/missing_data/filtering_summary_batch.md', 'w') as f:
        f.write(summary)
    
    return filtered_df, tickers_to_remove

if __name__ == '__main__':
    check_market_caps_batch() 