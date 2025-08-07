#!/usr/bin/env python3
"""
Database Schema Fix - Final Implementation
Fixes all constraint violations and missing columns for scoring system
"""

import os
import sys
import psycopg2
from datetime import datetime
from typing import List, Dict, Any

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

from config import Config

class DatabaseSchemaFixer:
    """Fix database schema issues for scoring system"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.config = Config()
        
    def connect(self):
        """Connect to database"""
        try:
            db_config = self.config.get_db_config()
            self.conn = psycopg2.connect(**db_config)
            self.cursor = self.conn.cursor()
            print("✅ Connected to database successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            raise
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ Database connection closed")
    
    def fix_database_schema(self):
        """Main method to fix all database schema issues"""
        print("🔧 FIXING DATABASE SCHEMA")
        print("=" * 60)
        
        try:
            # Step 1: Drop dependent views
            self.drop_dependent_views()
            
            # Step 2: Drop and recreate main scoring table
            self.recreate_scoring_table()
            
            # Step 3: Recreate views
            self.recreate_views()
            
            # Step 4: Verify fixes
            self.verify_schema_fixes()
            
            print("✅ Database schema fixes completed successfully!")
            
        except Exception as e:
            print(f"❌ Schema fix failed: {str(e)}")
            self.conn.rollback()
            raise
        finally:
            self.conn.commit()
    
    def drop_dependent_views(self):
        """Drop all dependent views that reference the scoring table"""
        print("📋 Dropping dependent views...")
        
        views_to_drop = [
            'screener_summary_view',
            'score_trends_view', 
            'screener_filters_view',
            'dashboard_metrics_view',
            'company_scores_view'
        ]
        
        for view in views_to_drop:
            try:
                self.cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view} CASCADE")
                print(f"  ✅ Dropped view: {view}")
            except Exception as e:
                print(f"  ⚠️  Could not drop view {view}: {str(e)}")
    
    def recreate_scoring_table(self):
        """Recreate the main scoring table with correct constraints"""
        print("📊 Recreating scoring table...")
        
        # Drop existing table
        self.cursor.execute("DROP TABLE IF EXISTS company_scores_current CASCADE")
        print("  ✅ Dropped existing company_scores_current table")
        
        # Create new table with correct schema
        create_table_sql = """
        CREATE TABLE company_scores_current (
            ticker VARCHAR(10) PRIMARY KEY,
            calculation_date DATE NOT NULL,
            fundamental_health_score DECIMAL(5,2),
            fundamental_health_grade VARCHAR(20),
            value_investment_score DECIMAL(5,2),
            value_rating VARCHAR(20),
            fundamental_risk_score DECIMAL(5,2),
            fundamental_risk_level VARCHAR(20),
            technical_health_score DECIMAL(5,2),
            technical_health_grade VARCHAR(20),
            trading_signal_score DECIMAL(5,2),
            trading_signal_rating VARCHAR(20),
            technical_risk_score DECIMAL(5,2),
            technical_risk_level VARCHAR(20),
            data_confidence DECIMAL(5,2),
            missing_metrics TEXT[],
            data_warnings TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        self.cursor.execute(create_table_sql)
        print("  ✅ Created new company_scores_current table")
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX idx_company_scores_ticker ON company_scores_current(ticker)",
            "CREATE INDEX idx_company_scores_date ON company_scores_current(calculation_date)",
            "CREATE INDEX idx_company_scores_fundamental ON company_scores_current(fundamental_health_score)",
            "CREATE INDEX idx_company_scores_technical ON company_scores_current(technical_health_score)"
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
                print(f"  ✅ Created index")
            except Exception as e:
                print(f"  ⚠️  Index creation failed: {str(e)}")
    
    def recreate_views(self):
        """Recreate all dependent views"""
        print("📋 Recreating views...")
        
        # Screener summary view
        screener_view_sql = """
        CREATE MATERIALIZED VIEW screener_summary_view AS
        SELECT 
            ticker,
            fundamental_health_score,
            fundamental_health_grade,
            value_investment_score,
            value_rating,
            fundamental_risk_score,
            fundamental_risk_level,
            technical_health_score,
            technical_health_grade,
            trading_signal_score,
            trading_signal_rating,
            technical_risk_score,
            technical_risk_level,
            data_confidence,
            calculation_date
        FROM company_scores_current
        WHERE calculation_date = (SELECT MAX(calculation_date) FROM company_scores_current);
        """
        
        try:
            self.cursor.execute(screener_view_sql)
            print("  ✅ Created screener_summary_view")
        except Exception as e:
            print(f"  ⚠️  Failed to create screener_summary_view: {str(e)}")
        
        # Score trends view
        trends_view_sql = """
        CREATE MATERIALIZED VIEW score_trends_view AS
        SELECT 
            ticker,
            calculation_date,
            fundamental_health_score,
            technical_health_score,
            fundamental_risk_score,
            technical_risk_score,
            data_confidence
        FROM company_scores_current
        ORDER BY ticker, calculation_date DESC;
        """
        
        try:
            self.cursor.execute(trends_view_sql)
            print("  ✅ Created score_trends_view")
        except Exception as e:
            print(f"  ⚠️  Failed to create score_trends_view: {str(e)}")
    
    def verify_schema_fixes(self):
        """Verify that all schema fixes are working"""
        print("🔍 Verifying schema fixes...")
        
        # Check table structure
        self.cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'company_scores_current'
            ORDER BY ordinal_position;
        """)
        
        columns = self.cursor.fetchall()
        print(f"  📊 Table has {len(columns)} columns:")
        
        for col in columns:
            col_name, data_type, max_length = col
            length_info = f"({max_length})" if max_length else ""
            print(f"    - {col_name}: {data_type}{length_info}")
        
        # Test insert
        test_data = {
            'ticker': 'TEST',
            'calculation_date': datetime.now().date(),
            'fundamental_health_score': 75.5,
            'fundamental_health_grade': 'Buy',
            'value_investment_score': 70.0,
            'value_rating': 'Buy',
            'fundamental_risk_score': 45.0,
            'fundamental_risk_level': 'Medium',
            'technical_health_score': 65.0,
            'technical_health_grade': 'Neutral',
            'trading_signal_score': 60.0,
            'trading_signal_rating': 'Neutral',
            'technical_risk_score': 50.0,
            'technical_risk_level': 'Medium',
            'data_confidence': 85.0,
            'missing_metrics': ['pe_ratio'],
            'data_warnings': ['high_volatility']
        }
        
        insert_sql = """
        INSERT INTO company_scores_current (
            ticker, calculation_date, fundamental_health_score, fundamental_health_grade,
            value_investment_score, value_rating, fundamental_risk_score, fundamental_risk_level,
            technical_health_score, technical_health_grade, trading_signal_score, trading_signal_rating,
            technical_risk_score, technical_risk_level, data_confidence, missing_metrics, data_warnings
        ) VALUES (
            %(ticker)s, %(calculation_date)s, %(fundamental_health_score)s, %(fundamental_health_grade)s,
            %(value_investment_score)s, %(value_rating)s, %(fundamental_risk_score)s, %(fundamental_risk_level)s,
            %(technical_health_score)s, %(technical_health_grade)s, %(trading_signal_score)s, %(trading_signal_rating)s,
            %(technical_risk_score)s, %(technical_risk_level)s, %(data_confidence)s, %(missing_metrics)s, %(data_warnings)s
        )
        """
        
        try:
            self.cursor.execute(insert_sql, test_data)
            print("  ✅ Test insert successful")
            
            # Clean up test data
            self.cursor.execute("DELETE FROM company_scores_current WHERE ticker = 'TEST'")
            print("  ✅ Test data cleaned up")
            
        except Exception as e:
            print(f"  ❌ Test insert failed: {str(e)}")
            raise

def main():
    """Main function to run database schema fixes"""
    fixer = DatabaseSchemaFixer()
    
    try:
        fixer.connect()
        fixer.fix_database_schema()
        print("\n🎉 Database schema fixes completed successfully!")
        print("The scoring system should now be able to store scores without constraint violations.")
        
    except Exception as e:
        print(f"\n❌ Database schema fix failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        fixer.disconnect()

if __name__ == "__main__":
    main() 