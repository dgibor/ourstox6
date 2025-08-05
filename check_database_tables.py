import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_database_tables():
    """Check what tables exist in the database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("Available tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if company_fundamentals exists and its structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_fundamentals' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("\ncompany_fundamentals table structure:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
        else:
            print("\ncompany_fundamentals table does not exist")
        
        # Check if financial_ratios exists
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'financial_ratios' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("\nfinancial_ratios table structure:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
        else:
            print("\nfinancial_ratios table does not exist")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database_tables() 