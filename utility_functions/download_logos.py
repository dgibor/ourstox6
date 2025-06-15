import os
import pandas as pd
import requests
from urllib.parse import urlparse

# Paths
csv_path = 'pre_filled_stocks/complete_1000_stock.csv'
logos_dir = 'pre_filled_stocks/logos'

# Ensure the logos directory exists
os.makedirs(logos_dir, exist_ok=True)

# Get existing logo tickers (without extension)
existing_logos = set()
for fname in os.listdir(logos_dir):
    if fname.endswith('.png') or fname.endswith('.jpg'):
        existing_logos.add(os.path.splitext(fname)[0].upper())

# Read the CSV
df = pd.read_csv(csv_path)

for idx, row in df.iterrows():
    ticker = str(row['ticker']).strip().upper()
    logo_url = str(row['logo_url']).strip()
    if not ticker or not logo_url or logo_url.lower() == 'nan':
        continue
    if ticker in existing_logos:
        continue  # Skip if logo already exists
    try:
        # Get the file extension from the URL
        parsed = urlparse(logo_url)
        ext = os.path.splitext(parsed.path)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            ext = '.png'  # Default to PNG if not png/jpg/jpeg
        elif ext == '.jpeg':
            ext = '.jpg'  # Normalize to .jpg
        filename = f"{ticker}{ext}"
        filepath = os.path.join(logos_dir, filename)
        # Download the image
        resp = requests.get(logo_url, timeout=10)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            print(f"Saved logo for {ticker} -> {filename}")
        else:
            print(f"Failed to download logo for {ticker}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"Error downloading logo for {ticker}: {e}") 