import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def check_schema():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Print current database name
        cur.execute("SELECT current_database();")
        dbname = cur.fetchone()[0]
        print(f"\nConnected to database: {dbname}")

        print("\n--- List of tables and schemas ---")
        cur.execute("""
            SELECT table_schema, table_name FROM information_schema.tables WHERE table_type='BASE TABLE';
        """)
        for row in cur.fetchall():
            print(f"Schema: {row[0]}, Table: {row[1]}")

        print("\n--- daily_charts table schema ---")
        cur.execute("""
            SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'daily_charts';
        """)
        for row in cur.fetchall():
            print(f"Column: {row[0]}, Type: {row[1]}")

        print("\n--- Row count in daily_charts ---")
        cur.execute("SELECT COUNT(*) FROM daily_charts;")
        count = cur.fetchone()[0]
        print(f"Row count: {count}")

        print("\n--- First 10 rows in daily_charts ---")
        cur.execute("SELECT * FROM daily_charts LIMIT 10;")
        for row in cur.fetchall():
            print(row)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema() 