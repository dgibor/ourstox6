import psycopg2
import pandas as pd

# Database connection info (Railway)
DB_HOST = 'yamanote.proxy.rlwy.net'
DB_PORT = 38837
DB_NAME = 'railway'
DB_USER = 'postgres'
DB_PASSWORD = 'KNNUYcidcJqFkwmctFdAnjvYdijsZocv'

# CSV path
csv_path = 'pre_filled_stocks/sector_industry_etf_mapping.csv'

# Connect to the database
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cur = conn.cursor()

# Create the industries table if it does not exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS industries (
        id SERIAL PRIMARY KEY,
        sector VARCHAR NOT NULL,
        industry VARCHAR NOT NULL,
        etf_name VARCHAR NOT NULL,
        etf_ticker VARCHAR NOT NULL,
        UNIQUE(sector, industry, etf_ticker)
    );
""")
conn.commit()

# Read the CSV
df = pd.read_csv(csv_path)

# Insert or update each row
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO industries (sector, industry, etf_name, etf_ticker)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (sector, industry, etf_ticker) DO UPDATE SET
            etf_name=EXCLUDED.etf_name;
    """,
    (
        row['Sector'],
        row['Industry'],
        row['ETF Name'],
        row['ETF Ticker'],
    ))
conn.commit()

cur.close()
conn.close()

print('Industries table created and updated with sector_industry_etf_mapping.csv.') 