import psycopg2
import pandas as pd

# Database connection info (Railway)
DB_HOST = 'yamanote.proxy.rlwy.net'
DB_PORT = 38837
DB_NAME = 'railway'
DB_USER = 'postgres'
DB_PASSWORD = 'KNNUYcidcJqFkwmctFdAnjvYdijsZocv'

# CSV path
csv_path = 'pre_filled_stocks/market_indicators_etf_mapping.csv'

# Connect to the database
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cur = conn.cursor()

# Create the market_etf table if it does not exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS market_etf (
        id SERIAL PRIMARY KEY,
        category VARCHAR NOT NULL,
        indicator VARCHAR NOT NULL,
        etf_index_name VARCHAR NOT NULL,
        ticker VARCHAR NOT NULL,
        UNIQUE(category, indicator, ticker)
    );
""")
conn.commit()

# Read the CSV
df = pd.read_csv(csv_path)

# Insert or update each row
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO market_etf (category, indicator, etf_index_name, ticker)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (category, indicator, ticker) DO UPDATE SET
            etf_index_name=EXCLUDED.etf_index_name;
    """,
    (
        row['Category'],
        row['Indicator'],
        row['ETF/Index Name'],
        row['Ticker'],
    ))
conn.commit()

cur.close()
conn.close()

print('Market ETF table created and updated with market_indicators_etf_mapping.csv.') 