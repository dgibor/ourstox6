
import pandas as pd

# Define the file path
input_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\missing_tickers.csv'

try:
    # Read the CSV
    df = pd.read_csv(input_file)

    # Create a numeric market cap column, coercing errors to NaN
    df['market_cap_numeric'] = pd.to_numeric(df['market_cap'], errors='coerce')

    # Find tickers with missing market caps
    missing_market_cap_df = df[df['market_cap_numeric'].isna()]
    tickers_to_fetch = missing_market_cap_df['ticker'].tolist()

    print("Tickers with missing market caps:")
    for ticker in tickers_to_fetch:
        print(ticker)

except FileNotFoundError:
    print(f"Error: The file {input_file} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")
