#!/usr/bin/env python3
"""
Database connection manager for daily_run module
"""

import psycopg2
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from config import Config
from exceptions import DatabaseError

class DatabaseManager:
    """Centralized database connection manager"""
    
    def __init__(self):
        """Initialize database manager"""
        self.config = Config.get_db_config()
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.config)
            self.logger.info("Database connection established")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise DatabaseError("connection", str(e))
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        if not self.connection:
            self.connect()
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            yield cursor
            self.connection.commit()
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            self.logger.error(f"Database operation failed: {e}")
            raise DatabaseError("operation", str(e))
        finally:
            if cursor:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an update query and return affected rows"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def get_tickers(self, table: str = 'stocks', active_only: bool = True) -> List[str]:
        """Get list of tickers from specified table"""
        if table == 'stocks':
            query = "SELECT ticker FROM stocks"
        elif table == 'market_etf':
            query = "SELECT etf_ticker FROM market_etf"
        else:
            raise DatabaseError("query", f"Unknown table: {table}")
        
        results = self.execute_query(query)
        return [row[0] for row in results]
    
    def get_latest_price(self, ticker: str, table: str = 'daily_charts') -> Optional[float]:
        """Get latest price for a ticker"""
        query = f"""
            SELECT close FROM {table} 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
        """
        results = self.execute_query(query, (ticker,))
        if results and results[0][0]:
            return float(results[0][0]) / 100.0  # Convert cents to dollars
        return None
    
    def update_price_data(self, ticker: str, price_data: Dict[str, Any], table: str = 'daily_charts'):
        """Update price data for a ticker"""
        # Price data should always go to daily_charts table
        query = """
            INSERT INTO daily_charts (ticker, date, open, high, low, close, volume)
            VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """
        params = (
            ticker,
            price_data.get('open'),
            price_data.get('high'),
            price_data.get('low'),
            price_data.get('close'),
            price_data.get('volume')
        )
        self.execute_update(query, params)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False

def test_database():
    """Test database manager functionality"""
    print("🧪 Testing Database Manager")
    print("=" * 30)
    
    db = DatabaseManager()
    
    try:
        # Test connection
        if db.test_connection():
            print("✅ Database connection test passed")
        else:
            print("❌ Database connection test failed")
            return
        
        # Test getting tickers
        tickers = db.get_tickers('stocks', active_only=True)
        print(f"✅ Retrieved {len(tickers)} active tickers")
        
        if tickers:
            # Test getting latest price
            test_ticker = tickers[0]
            price = db.get_latest_price(test_ticker)
            if price:
                print(f"✅ Latest price for {test_ticker}: ${price:.2f}")
            else:
                print(f"⚠️  No price data for {test_ticker}")
        
        # Test market ETFs
        etf_tickers = db.get_tickers('market_etf')
        print(f"✅ Retrieved {len(etf_tickers)} ETF tickers")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    finally:
        db.disconnect()
        print("✅ Database manager test completed")

if __name__ == "__main__":
    test_database() 