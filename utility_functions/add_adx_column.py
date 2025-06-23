import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def add_adx_column():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("Adding adx_14 column to daily_charts table...")
        cur.execute("""
            ALTER TABLE daily_charts
            ADD COLUMN IF NOT EXISTS adx_14 integer;
        """)
        conn.commit()
        print("ADX column added successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_adx_column() 