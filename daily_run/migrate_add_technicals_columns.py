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

COLUMNS = [
    'rsi_14', 'cci_20', 'ema_20', 'ema_50', 'ema_100', 'ema_200',
    'bb_upper', 'bb_middle', 'bb_lower',
    'macd_line', 'macd_signal', 'macd_histogram',
    'atr_14', 'vwap'
]

ALTER_TEMPLATE = """
ALTER TABLE market_data
{clauses};
"""

if __name__ == "__main__":
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        clauses = []
        for col in COLUMNS:
            clauses.append(f"ADD COLUMN IF NOT EXISTS {col} INTEGER")
        alter_sql = ALTER_TEMPLATE.format(clauses=",\n".join(clauses))
        cur.execute(alter_sql)
        conn.commit()
        print("Migration successful: columns added if not present.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close() 