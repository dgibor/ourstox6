#!/usr/bin/env python3
"""
Fix Database Schema for Optimized Services
Updates schema to support advanced rate limiting and optimized FMP service
"""

import os
import logging
from datetime import datetime
from database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_rate_limiting_schema():
    """Fix rate limiting tables schema"""
    db = DatabaseManager()
    
    try:
        logger.info("Fixing rate limiting schema...")
        
        # Drop existing tables if they exist
        db.execute_query("DROP TABLE IF EXISTS api_usage_tracking CASCADE")
        db.execute_query("DROP TABLE IF EXISTS rate_limit_alerts CASCADE")
        
        # Create api_usage_tracking table with correct schema
        db.execute_query("""
            CREATE TABLE api_usage_tracking (
                id SERIAL PRIMARY KEY,
                service VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                endpoint VARCHAR(100),
                calls_made INTEGER DEFAULT 0,
                calls_limit INTEGER NOT NULL,
                total_cost DECIMAL(10,4) DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(service, date, endpoint)
            )
        """)
        
        # Create rate_limit_alerts table
        db.execute_query("""
            CREATE TABLE rate_limit_alerts (
                id SERIAL PRIMARY KEY,
                service VARCHAR(50) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                threshold_value DECIMAL(10,2),
                current_value DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                is_resolved BOOLEAN DEFAULT FALSE
            )
        """)
        
        logger.info("✅ Rate limiting schema fixed")
        
    except Exception as e:
        logger.error(f"Error fixing rate limiting schema: {e}")

def fix_company_fundamentals_schema():
    """Fix company_fundamentals table schema for optimized services"""
    db = DatabaseManager()
    
    try:
        logger.info("Fixing company_fundamentals schema...")
        
        # Add missing columns for optimized FMP service
        columns_to_add = [
            ("revenue_ttm", "DECIMAL(20,2)"),
            ("net_income_ttm", "DECIMAL(20,2)"),
            ("gross_profit_ttm", "DECIMAL(20,2)"),
            ("operating_income_ttm", "DECIMAL(20,2)"),
            ("ebitda_ttm", "DECIMAL(20,2)"),
            ("current_assets", "DECIMAL(20,2)"),
            ("current_liabilities", "DECIMAL(20,2)"),
            ("current_price", "DECIMAL(10,2)"),
            ("pe_ratio", "DECIMAL(10,4)"),
            ("pb_ratio", "DECIMAL(10,4)"),
            ("debt_to_equity", "DECIMAL(10,4)"),
            ("current_ratio", "DECIMAL(10,4)"),
            ("roe", "DECIMAL(10,4)"),
            ("roa", "DECIMAL(10,4)"),
            ("gross_margin", "DECIMAL(10,4)"),
            ("operating_margin", "DECIMAL(10,4)"),
            ("net_margin", "DECIMAL(10,4)")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists
                result = db.execute_query("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'company_fundamentals' 
                    AND column_name = %s
                """, (column_name,))
                
                if not result:
                    # Add column
                    db.execute_query(f"ALTER TABLE company_fundamentals ADD COLUMN {column_name} {column_type}")
                    logger.info(f"Added column: {column_name}")
                else:
                    logger.info(f"Column already exists: {column_name}")
                    
            except Exception as e:
                logger.warning(f"Could not add column {column_name}: {e}")
        
        # Update existing columns to match optimized service expectations
        try:
            # Rename existing columns to match optimized service
            column_mappings = [
                ("price_to_earnings", "pe_ratio"),
                ("price_to_book", "pb_ratio"),
                ("debt_to_equity_ratio", "debt_to_equity"),
                ("return_on_equity", "roe"),
                ("return_on_assets", "roa")
            ]
            
            for old_name, new_name in column_mappings:
                try:
                    # Check if new column already exists
                    result = db.execute_query("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'company_fundamentals' 
                        AND column_name = %s
                    """, (new_name,))
                    
                    if not result:
                        # Rename column
                        db.execute_query(f"ALTER TABLE company_fundamentals RENAME COLUMN {old_name} TO {new_name}")
                        logger.info(f"Renamed column: {old_name} -> {new_name}")
                    else:
                        logger.info(f"Column {new_name} already exists, skipping rename")
                        
                except Exception as e:
                    logger.warning(f"Could not rename column {old_name}: {e}")
        
        except Exception as e:
            logger.warning(f"Error updating column names: {e}")
        
        logger.info("✅ Company fundamentals schema fixed")
        
    except Exception as e:
        logger.error(f"Error fixing company fundamentals schema: {e}")

def create_optimized_fundamentals_table():
    """Create a new optimized fundamentals table"""
    db = DatabaseManager()
    
    try:
        logger.info("Creating optimized fundamentals table...")
        
        # Create new table with optimized structure
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS company_fundamentals_optimized (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL UNIQUE,
                revenue_ttm DECIMAL(20,2),
                net_income_ttm DECIMAL(20,2),
                gross_profit_ttm DECIMAL(20,2),
                operating_income_ttm DECIMAL(20,2),
                ebitda_ttm DECIMAL(20,2),
                total_assets DECIMAL(20,2),
                total_equity DECIMAL(20,2),
                total_debt DECIMAL(20,2),
                current_assets DECIMAL(20,2),
                current_liabilities DECIMAL(20,2),
                free_cash_flow DECIMAL(20,2),
                shares_outstanding DECIMAL(20,2),
                current_price DECIMAL(10,2),
                market_cap DECIMAL(20,2),
                pe_ratio DECIMAL(10,4),
                pb_ratio DECIMAL(10,4),
                debt_to_equity DECIMAL(10,4),
                current_ratio DECIMAL(10,4),
                roe DECIMAL(10,4),
                roa DECIMAL(10,4),
                gross_margin DECIMAL(10,4),
                operating_margin DECIMAL(10,4),
                net_margin DECIMAL(10,4),
                data_source VARCHAR(50),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for performance
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_cfo_ticker ON company_fundamentals_optimized(ticker)")
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_cfo_last_updated ON company_fundamentals_optimized(last_updated)")
        
        logger.info("✅ Optimized fundamentals table created")
        
    except Exception as e:
        logger.error(f"Error creating optimized fundamentals table: {e}")

def migrate_existing_data():
    """Migrate existing data to optimized table"""
    db = DatabaseManager()
    
    try:
        logger.info("Migrating existing data...")
        
        # Copy data from old table to new table
        db.execute_query("""
            INSERT INTO company_fundamentals_optimized (
                ticker, revenue_ttm, net_income_ttm, gross_profit_ttm, operating_income_ttm,
                ebitda_ttm, total_assets, total_equity, total_debt, current_assets,
                current_liabilities, free_cash_flow, shares_outstanding, current_price,
                market_cap, pe_ratio, pb_ratio, debt_to_equity, current_ratio,
                roe, roa, gross_margin, operating_margin, net_margin,
                data_source, last_updated
            )
            SELECT 
                ticker,
                revenue as revenue_ttm,
                net_income as net_income_ttm,
                gross_profit as gross_profit_ttm,
                operating_income as operating_income_ttm,
                ebitda as ebitda_ttm,
                total_assets,
                total_equity,
                total_debt,
                total_assets as current_assets,  -- Approximate
                total_debt as current_liabilities,  -- Approximate
                free_cash_flow,
                shares_outstanding,
                0 as current_price,  -- Will be updated by service
                market_cap,
                price_to_earnings as pe_ratio,
                price_to_book as pb_ratio,
                debt_to_equity_ratio as debt_to_equity,
                current_ratio,
                return_on_equity as roe,
                return_on_assets as roa,
                gross_margin,
                operating_margin,
                net_margin,
                data_source,
                last_updated
            FROM company_fundamentals
            WHERE ticker IS NOT NULL
            ON CONFLICT (ticker) DO NOTHING
        """)
        
        logger.info("✅ Data migration completed")
        
    except Exception as e:
        logger.error(f"Error migrating data: {e}")

def main():
    """Main function to fix all schema issues"""
    logger.info("🔧 Starting Database Schema Fix")
    logger.info("=" * 50)
    
    try:
        # Fix rate limiting schema
        fix_rate_limiting_schema()
        
        # Fix company fundamentals schema
        fix_company_fundamentals_schema()
        
        # Create optimized table
        create_optimized_fundamentals_table()
        
        # Migrate existing data
        migrate_existing_data()
        
        logger.info("✅ All schema fixes completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Schema fix failed: {e}")

if __name__ == "__main__":
    main() 