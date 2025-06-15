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

def alter_table():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("Altering daily_charts table: changing open, high, low, close to BIGINT...")
        cur.execute("""
            ALTER TABLE daily_charts
            ALTER COLUMN open TYPE BIGINT USING open::BIGINT,
            ALTER COLUMN high TYPE BIGINT USING high::BIGINT,
            ALTER COLUMN low TYPE BIGINT USING low::BIGINT,
            ALTER COLUMN close TYPE BIGINT USING close::BIGINT;
        """)
        conn.commit()
        print("Columns changed to BIGINT successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    alter_table() 