import pandas as pd
import re
import time
from default_api import google_web_search

# Function to parse market cap from a string
def parse_market_cap(text):
    text = text.replace(',', '')
    match = re.search(r'\$(\d+\.?\d*)\s*(B|M|T)', text, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        unit = match.group(2).upper()
        if unit == 'B':
            return value * 1_000_000_000
        elif unit == 'M':
            return value * 1_000_000
        elif unit == 'T':
            return value * 1_000_000_000_000
    return None

# Load the data
input_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\missing_tickers.csv'
df = pd.read_csv(input_file)

# Identify tickers to fetch
df['market_cap_numeric'] = pd.to_numeric(df['market_cap'], errors='coerce')
tickers_to_fetch = df[df['market_cap_numeric'].isna()]['ticker'].tolist()

print(f"Found {len(tickers_to_fetch)} tickers with missing market caps. Starting fetch...")

# Fetch and update market caps
for ticker in tickers_to_fetch:
    try:
        print(f"Fetching market cap for {ticker}...")
        search_results = google_web_search(query=f"{ticker} market cap")
        
        # Find the market cap in the search results
        market_cap_str = None
        if search_results and 'organic_results' in search_results and search_results['organic_results']:
            for result in search_results['organic_results']:
                if 'snippet' in result and 'Market cap' in result['snippet']:
                    market_cap_str = result['snippet']
                    break
        
        if market_cap_str:
            market_cap_value = parse_market_cap(market_cap_str)
            if market_cap_value is not None:
                df.loc[df['ticker'] == ticker, 'market_cap'] = market_cap_value
                print(f"  > Updated {ticker} with market cap: {market_cap_value}")
            else:
                print(f"  > Could not parse market cap for {ticker} from snippet.")
        else:
            print(f"  > No market cap information found for {ticker}.")
            
    except Exception as e:
        print(f"An error occurred while fetching data for {ticker}: {e}")
    time.sleep(1) # To avoid overwhelming the search tool

# Save the updated dataframe
updated_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\missing_tickers_updated.csv'
df.to_csv(updated_file, index=False)
print(f"\nUpdated data saved to {updated_file}")

# Finally, filter the updated data
large_caps_df = df[pd.to_numeric(df['market_cap'], errors='coerce').fillna(0) >= 3_000_000_000]
filtered_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\large_missing.csv'
large_caps_df.to_csv(filtered_file, index=False)

print(f"Filtered large-cap data saved to {filtered_file}")
print(f"Number of large-cap companies found: {len(large_caps_df)}")
