"""
Create Earnings Calendar Table

Creates the earnings_calendar table for tracking earnings dates
and enabling earnings-based fundamental updates.
"""

import logging
from database import DatabaseManager

logger = logging.getLogger(__name__)


def create_earnings_calendar_table():
    """Create the earnings_calendar table"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS earnings_calendar (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        last_earnings_date DATE,
        next_earnings_date DATE,
        earnings_period VARCHAR(20),  -- 'Q1', 'Q2', 'Q3', 'Q4', 'ANNUAL'
        estimated_eps DECIMAL(10,4),
        actual_eps DECIMAL(10,4),
        revenue_estimate DECIMAL(20,2),
        actual_revenue DECIMAL(20,2),
        data_source VARCHAR(50),
        last_updated TIMESTAMP DEFAULT NOW(),
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(ticker)
    );
    
    CREATE INDEX IF NOT EXISTS idx_earnings_calendar_ticker ON earnings_calendar(ticker);
    CREATE INDEX IF NOT EXISTS idx_earnings_calendar_next_earnings ON earnings_calendar(next_earnings_date);
    CREATE INDEX IF NOT EXISTS idx_earnings_calendar_last_earnings ON earnings_calendar(last_earnings_date);
    """
    
    try:
        db = DatabaseManager()
        
        # Create table
        db.execute_update(create_table_sql)
        
        logger.info("Earnings calendar table created successfully")
        
        # Verify table structure
        verify_query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'earnings_calendar' 
        ORDER BY ordinal_position
        """
        
        columns = db.execute_query(verify_query)
        
        print("Earnings Calendar Table Structure:")
        print("-" * 50)
        for column in columns:
            print(f"{column[0]:<20} {column[1]:<15} {column[2]}")
        
        # Check if table has data
        count_query = "SELECT COUNT(*) as count FROM earnings_calendar"
        count_result = db.execute_query(count_query)
        
        print(f"\nCurrent records: {count_result[0][0]}")
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Error creating earnings calendar table: {e}")
        raise


def create_financial_ratios_table():
    """Create the financial_ratios table for storing calculated ratios"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS financial_ratios (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        pe_ratio DECIMAL(10,4),
        pb_ratio DECIMAL(10,4),
        ps_ratio DECIMAL(10,4),
        roe DECIMAL(10,4),
        roa DECIMAL(10,4),
        debt_to_equity DECIMAL(10,4),
        current_ratio DECIMAL(10,4),
        quick_ratio DECIMAL(10,4),
        gross_margin DECIMAL(10,4),
        net_margin DECIMAL(10,4),
        calculated_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(ticker)
    );
    
    CREATE INDEX IF NOT EXISTS idx_financial_ratios_ticker ON financial_ratios(ticker);
    CREATE INDEX IF NOT EXISTS idx_financial_ratios_calculated_at ON financial_ratios(calculated_at);
    """
    
    try:
        db = DatabaseManager()
        
        # Create table
        db.execute_update(create_table_sql)
        
        logger.info("Financial ratios table created successfully")
        
        # Verify table structure
        verify_query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'financial_ratios' 
        ORDER BY ordinal_position
        """
        
        columns = db.execute_query(verify_query)
        
        print("Financial Ratios Table Structure:")
        print("-" * 50)
        for column in columns:
            print(f"{column[0]:<20} {column[1]:<15} {column[2]}")
        
        # Check if table has data
        count_query = "SELECT COUNT(*) as count FROM financial_ratios"
        count_result = db.execute_query(count_query)
        
        print(f"\nCurrent records: {count_result[0][0]}")
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Error creating financial ratios table: {e}")
        raise


def create_system_status_table():
    """Create the system_status table for tracking system health"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS system_status (
        id SERIAL PRIMARY KEY,
        status_data JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_system_status_created_at ON system_status(created_at);
    """
    
    try:
        db = DatabaseManager()
        
        # Create table
        db.execute_update(create_table_sql)
        
        logger.info("System status table created successfully")
        
        # Verify table structure
        verify_query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'system_status' 
        ORDER BY ordinal_position
        """
        
        columns = db.execute_query(verify_query)
        
        print("System Status Table Structure:")
        print("-" * 50)
        for column in columns:
            print(f"{column[0]:<20} {column[1]:<15} {column[2]}")
        
        # Check if table has data
        count_query = "SELECT COUNT(*) as count FROM system_status"
        count_result = db.execute_query(count_query)
        
        print(f"\nCurrent records: {count_result[0][0]}")
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Error creating system status table: {e}")
        raise


def verify_daily_charts_table():
    """Verify the daily_charts table exists and has correct structure"""
    
    try:
        db = DatabaseManager()
        
        # Check if table exists
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'daily_charts'
        ) as exists
        """
        
        exists = db.execute_query(check_query)[0][0]
        
        if not exists:
            print("WARNING: daily_charts table does not exist!")
            print("This table is required for storing daily price data.")
            print("Please create it with the following structure:")
            print("""
            CREATE TABLE daily_charts (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open_price DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                close_price DECIMAL(10,2),
                volume BIGINT,
                market_cap DECIMAL(20,2),
                data_source VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(ticker, date)
            );
            """)
        else:
            # Verify table structure
            verify_query = """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'daily_charts' 
            ORDER BY ordinal_position
            """
            
            columns = db.execute_query(verify_query)
            
            print("Daily Charts Table Structure:")
            print("-" * 50)
            for column in columns:
                print(f"{column[0]:<20} {column[1]:<15} {column[2]}")
            
            # Check if table has data
            count_query = "SELECT COUNT(*) as count FROM daily_charts"
            count_result = db.execute_query(count_query)
            
            print(f"\nCurrent records: {count_result[0][0]}")
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Error verifying daily_charts table: {e}")
        raise


def main():
    """Create all required tables for the integrated daily runner v3"""
    logging.basicConfig(level=logging.INFO)
    
    print("Creating tables for Integrated Daily Runner v3")
    print("=" * 60)
    
    try:
        # Create earnings calendar table
        print("\n1. Creating earnings_calendar table...")
        create_earnings_calendar_table()
        
        # Create financial ratios table
        print("\n2. Creating financial_ratios table...")
        create_financial_ratios_table()
        
        # Create system status table
        print("\n3. Creating system_status table...")
        create_system_status_table()
        
        # Verify daily charts table
        print("\n4. Verifying daily_charts table...")
        verify_daily_charts_table()
        
        print("\n" + "=" * 60)
        print("All tables created/verified successfully!")
        print("Integrated Daily Runner v3 is ready to use.")
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 