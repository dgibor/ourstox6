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

def fix_schema():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # Add missing columns to market_data
        cur.execute("""
            ALTER TABLE market_data
            ADD COLUMN IF NOT EXISTS ticker character varying(20),
            ADD COLUMN IF NOT EXISTS open numeric(10,2),
            ADD COLUMN IF NOT EXISTS high numeric(10,2),
            ADD COLUMN IF NOT EXISTS low numeric(10,2),
            ADD COLUMN IF NOT EXISTS close numeric(10,2),
            ADD COLUMN IF NOT EXISTS volume bigint,
            ADD COLUMN IF NOT EXISTS rsi_14 smallint,
            ADD COLUMN IF NOT EXISTS cci_20 smallint,
            ADD COLUMN IF NOT EXISTS ema_20 numeric(8,2),
            ADD COLUMN IF NOT EXISTS ema_50 numeric(8,2),
            ADD COLUMN IF NOT EXISTS ema_100 numeric(8,2),
            ADD COLUMN IF NOT EXISTS ema_200 numeric(8,2),
            ADD COLUMN IF NOT EXISTS macd_line numeric(6,3),
            ADD COLUMN IF NOT EXISTS macd_signal numeric(6,3),
            ADD COLUMN IF NOT EXISTS macd_histogram numeric(6,3),
            ADD COLUMN IF NOT EXISTS bb_upper numeric(8,2),
            ADD COLUMN IF NOT EXISTS bb_middle numeric(8,2),
            ADD COLUMN IF NOT EXISTS bb_lower numeric(8,2),
            ADD COLUMN IF NOT EXISTS atr_14 numeric(6,2),
            ADD COLUMN IF NOT EXISTS vwap numeric(8,2),
            ADD COLUMN IF NOT EXISTS category character varying(50),
            ADD COLUMN IF NOT EXISTS indicator character varying(50),
            ADD COLUMN IF NOT EXISTS etf_name character varying(200),
            ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP;
        """)
        
        # Add missing columns to sectors
        cur.execute("""
            ALTER TABLE sectors
            ADD COLUMN IF NOT EXISTS sector_name character varying(100),
            ADD COLUMN IF NOT EXISTS sector_category character varying(50),
            ADD COLUMN IF NOT EXISTS etf_name character varying(200),
            ADD COLUMN IF NOT EXISTS open numeric(10,2),
            ADD COLUMN IF NOT EXISTS high numeric(10,2),
            ADD COLUMN IF NOT EXISTS low numeric(10,2),
            ADD COLUMN IF NOT EXISTS close numeric(10,2),
            ADD COLUMN IF NOT EXISTS volume bigint,
            ADD COLUMN IF NOT EXISTS rsi_14 smallint,
            ADD COLUMN IF NOT EXISTS cci_20 smallint,
            ADD COLUMN IF NOT EXISTS ema_20 numeric(8,2),
            ADD COLUMN IF NOT EXISTS ema_50 numeric(8,2),
            ADD COLUMN IF NOT EXISTS ema_100 numeric(8,2),
            ADD COLUMN IF NOT EXISTS ema_200 numeric(8,2),
            ADD COLUMN IF NOT EXISTS macd_line numeric(6,3),
            ADD COLUMN IF NOT EXISTS macd_signal numeric(6,3),
            ADD COLUMN IF NOT EXISTS macd_histogram numeric(6,3),
            ADD COLUMN IF NOT EXISTS bb_upper numeric(8,2),
            ADD COLUMN IF NOT EXISTS bb_middle numeric(8,2),
            ADD COLUMN IF NOT EXISTS bb_lower numeric(8,2),
            ADD COLUMN IF NOT EXISTS atr_14 numeric(6,2),
            ADD COLUMN IF NOT EXISTS vwap numeric(8,2),
            ADD COLUMN IF NOT EXISTS created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
            ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP;
        """)
        
        # Add unique constraints
        cur.execute("""
            ALTER TABLE market_data
            ADD CONSTRAINT market_data_ticker_date_key UNIQUE (ticker, date);
            
            ALTER TABLE sectors
            ADD CONSTRAINT sectors_ticker_date_key UNIQUE (ticker, date);
        """)
        
        conn.commit()
        print("Schema updated successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating schema: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_schema() 