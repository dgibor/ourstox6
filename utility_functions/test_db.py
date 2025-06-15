import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print(f"Current working directory: {os.getcwd()}")
print("Environment variables used for DB connection:")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def test_connection():
    try:
        # Print connection details (except password)
        print("\nAttempting to connect to database:")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Port: {DB_CONFIG['port']}")
        print(f"Database: {DB_CONFIG['dbname']}")
        print(f"User: {DB_CONFIG['user']}")
        
        # Connect to the database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Test simple query
        print("\nTesting simple query...")
        cur.execute("SELECT COUNT(*) FROM stocks")
        count = cur.fetchone()[0]
        print(f"Total stocks in database: {count}")
        
        # Test stocks table with sectors
        print("\nTesting sector query...")
        cur.execute("""
            SELECT ticker, sector 
            FROM stocks 
            WHERE sector IN (
                'Information Technology',
                'Financials',
                'Health Care',
                'Consumer Discretionary',
                'Energy'
            )
            LIMIT 5
        """)
        
        results = cur.fetchall()
        print("\nTest tickers found:")
        for ticker, sector in results:
            print(f"Ticker: {ticker}, Sector: {sector}")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_connection() 