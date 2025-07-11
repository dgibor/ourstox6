import pandas as pd

# Define file paths
large_missing_path = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\large_missing.csv'
batch1_fixed_path = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\batch1_fixed.csv'

# Columns to update
columns_to_update = [
    'description', 'business_model', '''moat_1''', '''moat_2''', '''moat_3''', '''moat_4''',
    'peer_a', 'peer_b', 'peer_c'
]

try:
    # Load the DataFrames
    df_large_missing = pd.read_csv(large_missing_path)
    df_batch1_fixed = pd.read_csv(batch1_fixed_path)

    # Set 'Ticker' as index for easier lookup (corrected from 'ticker')
    df_batch1_fixed = df_batch1_fixed.set_index('Ticker')

    # Iterate through df_large_missing and update columns
    updated_rows_count = 0
    for index, row in df_large_missing.iterrows():
        ticker = row['ticker'] # Still use 'ticker' for df_large_missing as it was created with lowercase
        if ticker in df_batch1_fixed.index:
            for col in columns_to_update:
                if col in df_batch1_fixed.columns:
                    df_large_missing.loc[index, col] = df_batch1_fixed.loc[ticker, col]
            updated_rows_count += 1

    # Save the updated large_missing.csv
    df_large_missing.to_csv(large_missing_path, index=False)

    print(f"Successfully updated {updated_rows_count} rows in {large_missing_path}")
    print("Columns updated: ", columns_to_update)

except FileNotFoundError as e:
    print(f"Error: File not found - {e.filename}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")