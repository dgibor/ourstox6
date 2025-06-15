import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': 'yamanote.proxy.rlwy.net',
    'port': 38837,
    'dbname': 'railway',
    'user': 'postgres',
    'password': 'KNNUYcidcJqFkwmctFdAnjvYdijsZocv'
}

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(**DB_CONFIG)

def update_column_type(cursor, table_name, column_name):
    """Update a column type to INTEGER"""
    try:
        # First, multiply existing values by 100 to convert to integers
        cursor.execute(f"""
            UPDATE {table_name}
            SET {column_name} = ROUND({column_name} * 100)
            WHERE {column_name} IS NOT NULL;
        """)
        
        # Then alter the column type
        cursor.execute(f"""
            ALTER TABLE {table_name}
            ALTER COLUMN {column_name} TYPE INTEGER
            USING {column_name}::INTEGER;
        """)
        print(f"Updated {column_name} in {table_name} to INTEGER")
    except Exception as e:
        print(f"Error updating {column_name} in {table_name}: {e}")

def main():
    # Columns to update in daily_charts table
    daily_charts_columns = [
        'rsi_14',
        'cci_20',
        'atr_14',
        'ema_20',
        'ema_50',
        'ema_100',
        'ema_200',
        'macd_line',
        'macd_signal',
        'macd_histogram',
        'bb_upper',
        'bb_middle',
        'bb_lower',
        'vwap',
        'stoch_k',
        'stoch_d',
        'pivot_point',
        'resistance_1',
        'resistance_2',
        'resistance_3',
        'support_1',
        'support_2',
        'support_3',
        'swing_high_5d',
        'swing_low_5d',
        'swing_high_10d',
        'swing_low_10d',
        'swing_high_20d',
        'swing_low_20d',
        'week_high',
        'week_low',
        'month_high',
        'month_low',
        'nearest_support',
        'nearest_resistance'
    ]

    # Columns to update in sectors table
    sectors_columns = [
        'rsi_14',
        'cci_20',
        'stoch_k',
        'stoch_d',
        'ema_20',
        'ema_50',
        'ema_100',
        'ema_200',
        'macd_line',
        'macd_signal',
        'macd_histogram',
        'bb_upper',
        'bb_middle',
        'bb_lower',
        'vwap',
        'atr_14',
        'pivot_point',
        'resistance_1',
        'resistance_2',
        'resistance_3',
        'support_1',
        'support_2',
        'support_3'
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update daily_charts table
        print("\nUpdating daily_charts table...")
        for column in daily_charts_columns:
            update_column_type(cursor, 'daily_charts', column)

        # Update sectors table
        print("\nUpdating sectors table...")
        for column in sectors_columns:
            update_column_type(cursor, 'sectors', column)

        # Commit the changes
        conn.commit()
        print("\nColumn type updates completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main() 