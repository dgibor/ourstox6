import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def get_table_columns(cursor, table_name):
    """Get current columns for a table"""
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s
    """, (table_name,))
    return cursor.fetchall()

def add_column(cursor, table_name, column_name, data_type):
    """Add a new column to a table"""
    try:
        cursor.execute(sql.SQL("""
            ALTER TABLE {} 
            ADD COLUMN IF NOT EXISTS {} {}
        """).format(
            sql.Identifier(table_name),
            sql.Identifier(column_name),
            sql.SQL(data_type)
        ))
        print(f"Added column {column_name} to {table_name}")
    except Exception as e:
        print(f"Error adding column {column_name} to {table_name}: {e}")

def main():
    # Required technical indicator columns based on the specification
    required_columns = {
        'ticker_RSI_14': 'INTEGER',
        'ticker_CCI_20': 'INTEGER',
        'ticker_EMA_20': 'INTEGER',
        'ticker_EMA_100': 'INTEGER',
        'ticker_EMA_200': 'INTEGER',
        'ticker_BB_upper': 'INTEGER',
        'ticker_BB_middle': 'INTEGER',
        'ticker_BB_lower': 'INTEGER',
        'ticker_MACD': 'INTEGER',
        'ticker_MACD_signal': 'INTEGER',
        'ticker_ATR_14': 'INTEGER',
        'ticker_VWAP': 'INTEGER'
    }

    # Tables to update
    tables = ['daily_charts', 'sectors', 'market_data']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for table in tables:
            print(f"\nChecking table: {table}")
            current_columns = dict(get_table_columns(cursor, table))
            
            # Check and add missing columns
            for column, data_type in required_columns.items():
                if column not in current_columns:
                    print(f"Adding missing column {column} to {table}")
                    add_column(cursor, table, column, data_type)
                else:
                    print(f"Column {column} already exists in {table}")

        # Commit the changes
        conn.commit()
        print("\nSchema update completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main() 