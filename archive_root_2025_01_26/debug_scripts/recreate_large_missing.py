
import pandas as pd

input_updated_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\missing_tickers_updated.csv'
output_large_missing_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\large_missing.csv'

try:
    df = pd.read_csv(input_updated_file)
    large_caps = df[pd.to_numeric(df['market_cap'], errors='coerce').fillna(0) >= 3_000_000_000]
    large_caps.to_csv(output_large_missing_file, index=False)
    print(f"Successfully re-generated {output_large_missing_file}")
except FileNotFoundError:
    print(f"Error: The file {input_updated_file} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")
