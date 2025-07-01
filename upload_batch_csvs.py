import pandas as pd

# Read CSV file
try:
    df = pd.read_csv(batch_file, on_bad_lines='skip')
    print(f"   Found {len(df)} records (problematic lines skipped)")
except Exception as e:
    print(f"   ❌ Error reading {batch_file}: {e}")
    continue 