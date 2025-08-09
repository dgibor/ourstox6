#!/usr/bin/env python3
"""
Database connection manager for daily_run module
"""

import psycopg2
import psycopg2.extras
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
try:
    from .config import Config
    from .exceptions import DatabaseError
except ImportError:
    from config import Config
    from exceptions import DatabaseError
from datetime import date

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
    
    @contextmanager
    def get_dict_cursor(self):
        """Context manager for dictionary cursor"""
        if not self.connection:
            self.connect()
        
        cursor = None
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Execute a query and return a single result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all_dict(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results as dictionaries"""
        with self.get_dict_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an update query and return affected rows"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_batch(self, query: str, params_list: List[tuple]) -> int:
        """Execute batch operations for better performance"""
        if not params_list:
            return 0
            
        with self.get_cursor() as cursor:
            psycopg2.extras.execute_batch(cursor, query, params_list)
            return cursor.rowcount
    
    def execute_values(self, query: str, params_list: List[tuple]) -> int:
        """Execute batch insert using VALUES for better performance"""
        if not params_list:
            return 0
            
        with self.get_cursor() as cursor:
            psycopg2.extras.execute_values(cursor, query, params_list)
            return cursor.rowcount
    
    def get_tickers(self, table: str = 'stocks', active_only: bool = True) -> List[str]:
        """Get list of tickers from specified table"""
        if table == 'stocks':
            query = "SELECT ticker FROM stocks WHERE ticker IS NOT NULL"
            # Note: is_active column doesn't exist in current schema
        elif table == 'market_etf':
            query = "SELECT etf_ticker FROM market_etf WHERE etf_ticker IS NOT NULL"
        else:
            raise DatabaseError("query", f"Unknown table: {table}")
        
        if table == 'stocks':
            query += " ORDER BY ticker"
        else:
            query += " ORDER BY etf_ticker"  # Use etf_ticker for ordering
        results = self.execute_query(query)
        return [row[0] for row in results]
    
    def get_tickers_batch(self, tickers: List[str], table: str = 'stocks') -> List[Dict]:
        """Get ticker information in batch"""
        if not tickers:
            return []
            
        placeholders = ','.join(['%s'] * len(tickers))
        
        if table == 'stocks':
            query = f"""
            SELECT ticker, company_name, sector, market_cap
            FROM stocks 
            WHERE ticker IN ({placeholders})
            ORDER BY ticker
            """
        else:
            raise DatabaseError("query", f"Batch query not supported for table: {table}")
        
        return self.fetch_all_dict(query, tuple(tickers))
    
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
    
    def get_latest_prices_batch(self, tickers: List[str], table: str = 'daily_charts') -> Dict[str, float]:
        """Get latest prices for multiple tickers efficiently"""
        if not tickers:
            return {}
            
        placeholders = ','.join(['%s'] * len(tickers))
        query = f"""
        SELECT DISTINCT ON (ticker) ticker, close
        FROM {table}
        WHERE ticker IN ({placeholders})
        ORDER BY ticker, date DESC
        """
        
        results = self.execute_query(query, tuple(tickers))
        return {
            row[0]: float(row[1]) / 100.0 if row[1] else None 
            for row in results
        }
    
    def get_tickers_needing_historical_data(self, min_days: int = 100) -> List[str]:
        """Get tickers that need more historical data - optimized query"""
        query = """
        SELECT s.ticker
        FROM stocks s
        LEFT JOIN (
            SELECT ticker, COUNT(*) as day_count
            FROM daily_charts
            GROUP BY ticker
        ) dc ON s.ticker = dc.ticker
        WHERE s.ticker IS NOT NULL
        AND (dc.day_count IS NULL OR dc.day_count < %s)
        ORDER BY COALESCE(dc.day_count, 0) ASC
        """
        
        results = self.execute_query(query, (min_days,))
        return [row[0] for row in results]
    
    def get_tickers_needing_fundamentals(self, days_old: int = 30) -> List[str]:
        """Get tickers needing fundamental updates - optimized query"""
        query = """
        SELECT s.ticker
        FROM stocks s
        LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
        WHERE s.ticker IS NOT NULL
        AND (
            cf.ticker IS NULL 
            OR cf.revenue IS NULL
            OR cf.net_income IS NULL
        )
        ORDER BY s.ticker ASC
        """
        
        results = self.execute_query(query)
        return [row[0] for row in results]
    
    def update_price_data(self, ticker: str, price_data: Dict[str, Any], table: str = 'daily_charts'):
        """Update price data for a ticker"""
        # Price data should always go to daily_charts table
        query = """
            INSERT INTO daily_charts (ticker, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """
        current_date = date.today().strftime('%Y-%m-%d')
        
        params = (
            ticker,
            current_date,
            price_data.get('open'),
            price_data.get('high'),
            price_data.get('low'),
            price_data.get('close'),
            price_data.get('volume')
        )
        self.execute_update(query, params)
    
    def update_price_data_batch(self, price_data_list: List[Dict[str, Any]]) -> int:
        """Update price data for multiple tickers efficiently"""
        if not price_data_list:
            return 0
            
        query = """
            INSERT INTO daily_charts (ticker, date, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """
        
        current_date = date.today()
        values = []
        
        for data in price_data_list:
            values.append((
                data.get('ticker'),
                current_date,
                data.get('open'),
                data.get('high'),
                data.get('low'),
                data.get('close'),
                data.get('volume')
            ))
        
        return self.execute_values(query, values)
    
    def get_price_history(self, ticker: str, days: int = 100) -> List[Dict]:
        """Get price history for a ticker"""
        query = """
        SELECT date, open, high, low, close, volume
        FROM daily_charts
        WHERE ticker = %s
        ORDER BY date DESC
        LIMIT %s
        """
        
        return self.fetch_all_dict(query, (ticker, days))
    
    def check_data_freshness(self, table: str = 'daily_charts') -> Dict[str, Any]:
        """Check data freshness statistics"""
        query = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT ticker) as unique_tickers,
            MAX(date) as latest_date,
            MIN(date) as earliest_date,
            COUNT(CASE WHEN date = CURRENT_DATE::text THEN 1 END) as today_records,
            COUNT(CASE WHEN date >= (CURRENT_DATE - INTERVAL '7 days')::date::text THEN 1 END) as week_records
        FROM {table}
        """
        
        result = self.fetch_one(query)
        if result:
            return {
                'total_records': result[0],
                'unique_tickers': result[1],
                'latest_date': result[2],
                'earliest_date': result[3],
                'today_records': result[4],
                'week_records': result[5]
            }
        return {}
    
    def get_price_data_for_technicals(self, ticker: str, days: int = 100) -> List[Dict]:
        """Get price data for technical indicator calculations"""
        query = """
        SELECT date, open, high, low, close, volume
        FROM daily_charts 
        WHERE ticker = %s 
        ORDER BY date DESC 
        LIMIT %s
        """
        return self.fetch_all_dict(query, (ticker, days))
    
    def update_technical_indicators(self, ticker: str, indicators: Dict[str, float], target_date: str = None):
        """Update technical indicators for a ticker - COMPREHENSIVE VERSION"""
        if not target_date:
            target_date = date.today().strftime('%Y-%m-%d')
        
        # Build dynamic update query based on available indicators
        update_fields = []
        values = []
        
        indicator_columns = {
            # Basic Technical Indicators
            'rsi_14': 'rsi_14',
            'ema_20': 'ema_20', 
            'ema_50': 'ema_50',
            'ema_100': 'ema_100',
            'ema_200': 'ema_200',
            'macd_line': 'macd_line',
            'macd_signal': 'macd_signal',
            'macd_histogram': 'macd_histogram',
            
            # Bollinger Bands
            'bb_upper': 'bb_upper',
            'bb_middle': 'bb_middle',
            'bb_lower': 'bb_lower',
            
            # Stochastic
            'stoch_k': 'stoch_k',
            'stoch_d': 'stoch_d',
            
            # Additional Indicators
            'atr_14': 'atr_14',
            'cci_20': 'cci_20',
            'adx_14': 'adx_14',
            'vwap': 'vwap',
            'williams_r': 'williams_r',
            
            # Support & Resistance (Enhanced)
            'pivot_point': 'pivot_point',
            'pivot_fibonacci': 'pivot_fibonacci',
            'pivot_camarilla': 'pivot_camarilla',
            'pivot_woodie': 'pivot_woodie',
            'pivot_demark': 'pivot_demark',
            'resistance_1': 'resistance_1',
            'resistance_2': 'resistance_2',
            'resistance_3': 'resistance_3',
            'support_1': 'support_1',
            'support_2': 'support_2',
            'support_3': 'support_3',
            
            # Swing Levels
            'swing_high_5d': 'swing_high_5d',
            'swing_low_5d': 'swing_low_5d',
            'swing_high_10d': 'swing_high_10d',
            'swing_low_10d': 'swing_low_10d',
            'swing_high_20d': 'swing_high_20d',
            'swing_low_20d': 'swing_low_20d',
            
            # Weekly/Monthly Levels
            'week_high': 'week_high',
            'week_low': 'week_low',
            'month_high': 'month_high',
            'month_low': 'month_low',
            
            # Nearest Levels
            'nearest_support': 'nearest_support',
            'nearest_resistance': 'nearest_resistance',
            'nearest_fib_support': 'nearest_fib_support',
            'nearest_fib_resistance': 'nearest_fib_resistance',
            'nearest_psych_support': 'nearest_psych_support',
            'nearest_psych_resistance': 'nearest_psych_resistance',
            'nearest_volume_support': 'nearest_volume_support',
            'nearest_volume_resistance': 'nearest_volume_resistance',
            
            # Strength Indicators
            'support_strength': 'support_strength',
            'resistance_strength': 'resistance_strength',
            'volume_confirmation': 'volume_confirmation',
            'swing_strengths': 'swing_strengths',
            'level_type': 'level_type',
            
            # Fibonacci Levels
            'fib_236': 'fib_236',
            'fib_382': 'fib_382',
            'fib_500': 'fib_500',
            'fib_618': 'fib_618',
            'fib_786': 'fib_786',
            'fib_1272': 'fib_1272',
            'fib_1618': 'fib_1618',
            'fib_2618': 'fib_2618',
            
            # Dynamic Levels
            'dynamic_resistance': 'dynamic_resistance',
            'dynamic_support': 'dynamic_support',
            'keltner_upper': 'keltner_upper',
            'keltner_lower': 'keltner_lower',
            
            # Volume-weighted Levels
            'volume_weighted_high': 'volume_weighted_high',
            'volume_weighted_low': 'volume_weighted_low',
            
            # Volume Indicators
            'obv': 'obv',
            'vpt': 'vpt'
        }
        
        for indicator, value in indicators.items():
            if indicator in indicator_columns and value is not None:
                try:
                    # Convert float to integer for database storage (multiply by 100 to preserve precision)
                    if isinstance(value, float):
                        # Validate the value range to prevent database overflow
                        # Database precision 15, scale 4 means max value < 10^11
                        # After multiplying by 100, max safe value is 10^9
                        if abs(value) > 1e9:  # Cap at 1 billion to be safe
                            self.logger.warning(f"Capping extreme indicator value for {ticker}.{indicator}: {value} -> 1e9")
                            value = 1e9 if value > 0 else -1e9
                        
                        # Additional validation for common indicators
                        if indicator in ['rsi_14'] and (value < 0 or value > 100):
                            self.logger.warning(f"Invalid RSI value for {ticker}: {value}, setting to 50")
                            value = 50
                        elif indicator in ['adx_14', 'atr_14'] and value < 0:
                            self.logger.warning(f"Invalid {indicator} value for {ticker}: {value}, setting to 0")
                            value = 0
                        elif indicator.startswith('bb_') and abs(value) > 1e6:  # Bollinger Bands should be reasonable
                            self.logger.warning(f"Extreme Bollinger Band value for {ticker}.{indicator}: {value}")
                            value = max(min(value, 1e6), -1e6)
                        
                        value = int(value * 100)
                    
                    update_fields.append(f"{indicator_columns[indicator]} = %s")
                    values.append(value)
                    
                except (ValueError, OverflowError) as e:
                    self.logger.error(f"Error processing indicator {indicator} for {ticker}: {e}")
                    continue
        
        if update_fields:
            # Use batch update for better performance (PostgreSQL optimized)
            try:
                stored_count = self._batch_update_indicators(ticker, target_date, update_fields, values)
                self.logger.info(f"Updated {stored_count} technical indicators for {ticker}")
                return stored_count
            except Exception as e:
                self.logger.error(f"Failed to update technical indicators for {ticker}: {e}")
                return 0
        return 0
    
    def _batch_update_indicators(self, ticker: str, target_date: str, fields: List[str], values: List[Any]) -> int:
        """Optimized batch update for technical indicators"""
        # Split into smaller chunks to avoid massive queries
        chunk_size = 20  # Update 20 fields at a time
        total_updated = 0
        
        for i in range(0, len(fields), chunk_size):
            chunk_fields = fields[i:i + chunk_size]
            chunk_values = values[i:i + chunk_size]
            
            # Build query for this chunk
            chunk_values.extend([ticker, target_date])
            query = f"""
            UPDATE daily_charts 
            SET {', '.join(chunk_fields)}
            WHERE ticker = %s AND date = %s
            """
            
            with self.get_cursor() as cursor:
                cursor.execute(query, tuple(chunk_values))
                if cursor.rowcount > 0:
                    total_updated += len(chunk_fields)
        
        return total_updated

    def upsert_company_scores(self, ticker: str, score_data: Dict[str, Any]) -> bool:
        """
        Upsert company scores using the database function
        """
        try:
            # Call the enhanced upsert_company_scores database function with sentiment support
            query = """
            SELECT upsert_company_scores(
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            # Convert dicts and lists to JSON strings for JSONB parameters
            import json
            
            params = (
                ticker,
                score_data.get('fundamental_health_score', 50.0),
                score_data.get('fundamental_health_grade', 'Neutral'),
                json.dumps(score_data.get('fundamental_health_components', {})),
                score_data.get('fundamental_risk_score', 50.0),
                score_data.get('fundamental_risk_level', 'Medium'),
                json.dumps(score_data.get('fundamental_risk_components', {})),
                score_data.get('value_investment_score', 50.0),
                score_data.get('value_rating', 'Neutral'),
                json.dumps(score_data.get('value_components', {})),
                score_data.get('technical_health_score', 50.0),
                score_data.get('technical_health_grade', 'Neutral'),
                json.dumps(score_data.get('technical_health_components', {})),
                score_data.get('trading_signal_score', 50.0),
                score_data.get('trading_signal_rating', 'Neutral'),
                json.dumps(score_data.get('trading_signal_components', {})),
                score_data.get('technical_risk_score', 50.0),
                score_data.get('technical_risk_level', 'Medium'),
                json.dumps(score_data.get('technical_risk_components', {})),
                score_data.get('overall_score', 50.0),
                score_data.get('overall_grade', 'Neutral'),
                json.dumps(score_data.get('fundamental_red_flags', [])),
                json.dumps(score_data.get('fundamental_yellow_flags', [])),
                json.dumps(score_data.get('technical_red_flags', [])),
                json.dumps(score_data.get('technical_yellow_flags', [])),
                json.dumps(score_data.get('sentiment_components', {})),
                score_data.get('sentiment_score', 0.0),
                score_data.get('sentiment_grade', 'Neutral'),
                score_data.get('sentiment_source', 'unknown')
            )
            
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                
            self.logger.info(f"Successfully upserted scores for {ticker}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upsert scores for {ticker}: {e}")
            return False

    def create_indexes_if_missing(self):
        """Create database indexes for better performance"""
        # Use separate connections for non-transactional index creation
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_daily_charts_ticker_date ON daily_charts(ticker, date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_daily_charts_date ON daily_charts(date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_company_fundamentals_ticker ON company_fundamentals(ticker)",
            "CREATE INDEX IF NOT EXISTS idx_stocks_ticker ON stocks(ticker)"
        ]
        
        for index_sql in indexes:
            try:
                # Use a separate connection for each index to avoid transaction issues
                temp_conn = psycopg2.connect(**self.config)
                temp_conn.autocommit = True
                with temp_conn.cursor() as cursor:
                    cursor.execute(index_sql)
                temp_conn.close()
                self.logger.info(f"Index created/verified: {index_sql.split()[-3]}")
            except Exception as e:
                self.logger.warning(f"Index creation failed (may already exist): {e}")
    
    def analyze_tables(self):
        """Update table statistics for better query planning"""
        tables = ['daily_charts', 'stocks', 'company_fundamentals']
        
        for table in tables:
            try:
                self.execute_update(f"ANALYZE {table}")
                self.logger.info(f"Analyzed table: {table}")
            except Exception as e:
                self.logger.error(f"Failed to analyze table {table}: {e}")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    def begin_transaction(self):
        """Begin a database transaction"""
        if not self.connection:
            self.connect()
        self.connection.autocommit = False
        self.logger.debug("Transaction begun")
    
    def commit(self):
        """Commit the current transaction"""
        if self.connection:
            self.connection.commit()
            self.logger.debug("Transaction committed")
    
    def rollback(self):
        """Rollback the current transaction"""
        if self.connection:
            self.connection.rollback()
            self.logger.debug("Transaction rolled back")
    
    def cursor(self, cursor_factory=None):
        """Get a database cursor with optional factory"""
        if not self.connection:
            self.connect()
        if cursor_factory:
            return self.connection.cursor(cursor_factory=cursor_factory)
        return self.connection.cursor()

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
        
        # Create indexes for better performance
        db.create_indexes_if_missing()
        print("✅ Database indexes checked/created")
        
        # Test getting tickers
        tickers = db.get_tickers('stocks')
        print(f"✅ Retrieved {len(tickers)} tickers")
        
        if tickers:
            # Test batch operations
            sample_tickers = tickers[:5]
            batch_info = db.get_tickers_batch(sample_tickers)
            print(f"✅ Batch ticker info retrieved for {len(batch_info)} tickers")
            
            # Test latest prices batch
            latest_prices = db.get_latest_prices_batch(sample_tickers)
            print(f"✅ Batch latest prices retrieved for {len(latest_prices)} tickers")
            
            # Test data freshness
            freshness = db.check_data_freshness()
            print(f"✅ Data freshness check: {freshness.get('today_records', 0)} records today")
            
            # Test historical data needs
            historical_needed = db.get_tickers_needing_historical_data()
            print(f"✅ Found {len(historical_needed)} tickers needing historical data")
            
            # Test fundamental data needs
            fundamentals_needed = db.get_tickers_needing_fundamentals()
            print(f"✅ Found {len(fundamentals_needed)} tickers needing fundamental updates")
        
        # Test market ETFs
        try:
            etf_tickers = db.get_tickers('market_etf')
            print(f"✅ Retrieved {len(etf_tickers)} ETF tickers")
        except Exception as e:
            print(f"⚠️  ETF table test failed (table may not exist): {e}")
        
        # Analyze tables for better performance
        db.analyze_tables()
        print("✅ Table statistics updated")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()
        print("✅ Database manager test completed")

if __name__ == "__main__":
    test_database() 