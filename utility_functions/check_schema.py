import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def check_schema():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'company_fundamentals' 
        ORDER BY ordinal_position
    """)
    
    columns = [row[0] for row in cur.fetchall()]
    print("Company fundamentals columns:", columns)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_schema() 