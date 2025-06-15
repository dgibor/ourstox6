import psycopg2
import pandas as pd
import os

# Database connection info (from previous .env)
DB_HOST = 'yamanote.proxy.rlwy.net'
DB_PORT = 38837
DB_NAME = 'railway'
DB_USER = 'postgres'
DB_PASSWORD = 'KNNUYcidcJqFkwmctFdAnjvYdijsZocv'

# CSV path
csv_path = 'pre_filled_stocks/complete_1000_stock.csv'

# Columns to add if not present
new_columns = [
    ('general_description', 'text'),
    ('customers', 'text'),
    ('products_services', 'text'),
    ('hq_location', 'text'),
]

# Connect to the database
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cur = conn.cursor()

# Add new columns if they do not exist
for col, coltype in new_columns:
    cur.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='stocks' AND column_name='{col}'
            ) THEN
                ALTER TABLE stocks ADD COLUMN {col} {coltype};
            END IF;
        END$$;
    """)
conn.commit()

# Ensure unique constraint on ticker
cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
            WHERE tc.table_name = 'stocks' AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'ticker'
        ) THEN
            ALTER TABLE stocks ADD CONSTRAINT unique_ticker UNIQUE (ticker);
        END IF;
    END$$;
""")
conn.commit()

# Read the CSV
df = pd.read_csv(csv_path)

# Insert or update each row
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO stocks (ticker, company_name, sector, industry, general_description, customers, products_services, hq_location, exchange, country, logo_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker) DO UPDATE SET
            company_name=EXCLUDED.company_name,
            sector=EXCLUDED.sector,
            industry=EXCLUDED.industry,
            general_description=EXCLUDED.general_description,
            customers=EXCLUDED.customers,
            products_services=EXCLUDED.products_services,
            hq_location=EXCLUDED.hq_location,
            exchange=EXCLUDED.exchange,
            country=EXCLUDED.country,
            logo_url=EXCLUDED.logo_url;
    """,
    (
        row['ticker'],
        row['company_name'],
        row['sector'],
        row['industry'],
        row['general_description'],
        row['customers'],
        row['products_services'],
        row['hq_location'],
        row['exchange'],
        row['country'],
        row['logo_url'],
    ))
conn.commit()

cur.close()
conn.close()

print('Stocks table updated with complete_1000_stock.csv.') 