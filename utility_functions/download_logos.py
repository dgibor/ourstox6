import os
import pandas as pd
import requests
from urllib.parse import urlparse

# Paths
csv_path = '../pre_filled_stocks/all_db_tickers.csv'
logos_dir = '../pre_filled_stocks/logos'

# Ensure the logos directory exists
os.makedirs(logos_dir, exist_ok=True)

# Get existing logo tickers (without extension)
existing_logos = set()
for fname in os.listdir(logos_dir):
    if fname.endswith('.png') or fname.endswith('.jpg'):
        existing_logos.add(os.path.splitext(fname)[0].upper())

# Read the CSV
print(f"Reading tickers from {csv_path}")
df = pd.read_csv(csv_path)

def get_clearbit_logo_url(ticker):
    # Try Clearbit logo API (using domain pattern)
    # This is a fallback and may not always work
    return f'https://logo.clearbit.com/{ticker}.com'

for idx, row in df.iterrows():
    ticker = str(row['ticker']).strip().upper()
    logo_url = str(row['logo_url']).strip() if 'logo_url' in row else ''
    if not ticker or ticker == 'NAN':
        continue
    if ticker in existing_logos:
        continue  # Skip if logo already exists
    # If logo_url is blank, try Clearbit
    if not logo_url or logo_url.lower() == 'nan':
        logo_url = get_clearbit_logo_url(ticker)
    try:
        # Always save as PNG
        filename = f"{ticker}.png"
        filepath = os.path.join(logos_dir, filename)
        resp = requests.get(logo_url, timeout=10)
        if resp.status_code == 200 and resp.headers['Content-Type'].startswith('image'):
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            print(f"Saved logo for {ticker} -> {filename}")
        else:
            print(f"Failed to download logo for {ticker}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"Error downloading logo for {ticker}: {e}") 