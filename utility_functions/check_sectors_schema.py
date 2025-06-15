import os
import psycopg2
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/check_sectors_schema.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def check_and_create_sectors_table():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check if sectors table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sectors'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            logging.info("Creating sectors table...")
            cur.execute("""
                CREATE TABLE sectors (
                    ticker VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    open BIGINT,
                    high BIGINT,
                    low BIGINT,
                    close BIGINT,
                    volume BIGINT,
                    PRIMARY KEY (ticker, date)
                );
            """)
            conn.commit()
            logging.info("Sectors table created successfully")
        else:
            # Check if columns need to be modified
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'sectors';
            """)
            columns = {row[0]: row[1] for row in cur.fetchall()}
            
            # Check if price columns are BIGINT
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if col in columns and columns[col] != 'bigint':
                    logging.info(f"Converting {col} column to BIGINT...")
                    cur.execute(f"""
                        ALTER TABLE sectors
                        ALTER COLUMN {col} TYPE BIGINT USING {col}::BIGINT;
                    """)
            
            # Check if volume is BIGINT
            if 'volume' in columns and columns['volume'] != 'bigint':
                logging.info("Converting volume column to BIGINT...")
                cur.execute("""
                    ALTER TABLE sectors
                    ALTER COLUMN volume TYPE BIGINT USING volume::BIGINT;
                """)
            
            # Check if primary key exists
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.table_constraints
                WHERE table_name = 'sectors'
                AND constraint_type = 'PRIMARY KEY';
            """)
            has_pk = cur.fetchone()[0] > 0
            
            if not has_pk:
                logging.info("Adding primary key constraint...")
                cur.execute("""
                    ALTER TABLE sectors
                    ADD CONSTRAINT sectors_pkey PRIMARY KEY (ticker, date);
                """)
            
            conn.commit()
            logging.info("Schema check and modifications complete")
        
        # Print current schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'sectors'
            ORDER BY ordinal_position;
        """)
        logging.info("\nCurrent sectors table schema:")
        for row in cur.fetchall():
            logging.info(f"Column: {row[0]}, Type: {row[1]}, Nullable: {row[2]}")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_and_create_sectors_table() 