import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def update_stocks_schema():
    """Update stocks table to accommodate all batch CSV columns"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # Add missing columns to stocks table
        new_columns = [
            ('market_cap_b', 'numeric(10,2)'),
            ('description', 'text'),
            ('business_model', 'text'),
            ('products_services', 'text'),
            ('main_customers', 'text'),
            ('markets', 'text'),
            ('moat', 'text'),
            ('peer_a', 'text'),
            ('peer_b', 'text'),
            ('peer_c', 'text')
        ]
        
        for col_name, col_type in new_columns:
            cur.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='stocks' AND column_name='{col_name}'
                    ) THEN
                        ALTER TABLE stocks ADD COLUMN {col_name} {col_type};
                        RAISE NOTICE 'Added column % to stocks table', '{col_name}';
                    ELSE
                        RAISE NOTICE 'Column % already exists in stocks table', '{col_name}';
                    END IF;
                END$$;
            """)
        
        # Drop materialized view that depends on sector column
        cur.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_matviews 
                    WHERE matviewname = 'mv_latest_company_metrics'
                ) THEN
                    DROP MATERIALIZED VIEW mv_latest_company_metrics;
                    RAISE NOTICE 'Dropped materialized view mv_latest_company_metrics';
                END IF;
            END$$;
        """)
        
        # Update existing columns to text type to accommodate longer values
        columns_to_update = [
            ('sector', 'text'),
            ('industry', 'text'),
            ('business_model', 'text'),
            ('peer_a', 'text'),
            ('peer_b', 'text'),
            ('peer_c', 'text')
        ]
        
        for col_name, col_type in columns_to_update:
            cur.execute(f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='stocks' AND column_name='{col_name}'
                    ) THEN
                        ALTER TABLE stocks ALTER COLUMN {col_name} TYPE {col_type};
                        RAISE NOTICE 'Updated column % to type %', '{col_name}', '{col_type}';
                    END IF;
                END$$;
            """)
        
        # Recreate the materialized view
        cur.execute("""
            CREATE MATERIALIZED VIEW mv_latest_company_metrics AS
            SELECT DISTINCT ON (ticker) 
                ticker, company_name, sector, industry, market_cap_b,
                description, business_model, products_services, main_customers,
                markets, moat, peer_a, peer_b, peer_c, last_updated
            FROM stocks
            ORDER BY ticker, last_updated DESC NULLS LAST;
        """)
        print("✅ Recreated materialized view mv_latest_company_metrics")
        
        # Ensure unique constraint on ticker
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                    WHERE tc.table_name = 'stocks' AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'ticker'
                ) THEN
                    ALTER TABLE stocks ADD CONSTRAINT unique_ticker UNIQUE (ticker);
                    RAISE NOTICE 'Added unique constraint on ticker column';
                ELSE
                    RAISE NOTICE 'Unique constraint on ticker already exists';
                END IF;
            END$$;
        """)
        
        conn.commit()
        print("✅ Stocks table schema updated successfully!")
        
        # Verify the changes
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        print("\n📋 Current stocks table columns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating schema: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_stocks_schema() 