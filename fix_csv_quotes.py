import pandas as pd
import re
import os

input_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\large_missing.csv'
temp_file = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\large_missing_temp.csv'

def escape_quotes(text):
    if isinstance(text, str):
        # Replace all occurrences of a single double quote with two double quotes
        # This is the standard CSV escaping for internal quotes
        return text.replace('"', '""')
    return text

try:
    # Read the CSV file, handling potential errors by trying different engines
    try:
        df = pd.read_csv(input_file, encoding='utf-8')
    except Exception:
        df = pd.read_csv(input_file, encoding='latin1')

    # Apply the escaping function to description and business_model columns
    # Only apply if the column exists and is of object type (string)
    for col in ['description', 'business_model']:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].apply(escape_quotes)

    # Write the corrected DataFrame to a temporary file
    # pandas to_csv will automatically handle enclosing fields with quotes if they contain commas or newlines
    df.to_csv(temp_file, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)

    # Replace the original file with the corrected one
    os.replace(temp_file, input_file)

    print(f"Successfully corrected internal quotes in {input_file}")

except FileNotFoundError:
    print(f"Error: The file {input_file} was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")