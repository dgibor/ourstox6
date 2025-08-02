#!/usr/bin/env python3
"""
Fix Technical Indicators Issues

This script addresses the critical issues identified in the QA report:
1. Technical indicators not being calculated for recent data
2. Many tickers missing technical indicators despite having price data
3. Insufficient historical data for calculations
4. Poor error handling in technical calculations
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add daily_run to path
sys.path.append('daily_run')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_technical_indicators.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_config():
    """Get database configuration"""
    try:
        from config import Config
        config = Config.get_db_config()
        return config
    except ImportError:
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'dbname': os.getenv('DB_NAME', 'ourstox6'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }

class TechnicalIndicatorsFixer:
    """Fix technical indicator calculation issues"""
    
    def __init__(self):
        self.config = get_db_config()
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to database"""
        try:
            import psycopg2
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_tickers_needing_technical_indicators(self) -> List[str]:
        """Get tickers that have price data but missing technical indicators"""
        query = """
        SELECT DISTINCT ticker
        FROM daily_charts 
        WHERE close IS NOT NULL AND close != 0
        AND (rsi_14 IS NULL OR rsi_14 = 0 OR ema_20 IS NULL OR ema_20 = 0 OR macd_line IS NULL OR macd_line = 0)
        ORDER BY ticker
        """
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_price_data_for_ticker(self, ticker: str, min_days: int = 100) -> Optional[pd.DataFrame]:
        """Get price data for a ticker with proper formatting"""
        try:
            query = """
            SELECT date, open, high, low, close, volume
            FROM daily_charts 
            WHERE ticker = %s AND close IS NOT NULL AND close != 0
            ORDER BY date ASC
            """
            self.cursor.execute(query, (ticker,))
            data = self.cursor.fetchall()
            
            if len(data) < min_days:
                logger.warning(f"Insufficient data for {ticker}: {len(data)} days < {min_days}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Ensure numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            if len(df) < min_days:
                logger.warning(f"After cleaning, insufficient data for {ticker}: {len(df)} days < {min_days}")
                return None
            
            logger.debug(f"Retrieved {len(df)} days of price data for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting price data for {ticker}: {e}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators with improved error handling"""
        indicators = {}
        
        try:
            # RSI calculation
            if len(df) >= 14:
                try:
                    from indicators.rsi import calculate_rsi
                    rsi_result = calculate_rsi(df['close'])
                    if rsi_result is not None and len(rsi_result) > 0:
                        latest_rsi = rsi_result.iloc[-1]
                        if pd.notna(latest_rsi) and latest_rsi != 0:
                            indicators['rsi_14'] = float(latest_rsi)
                            logger.debug(f"RSI calculated: {indicators['rsi_14']:.2f}")
                        else:
                            indicators['rsi_14'] = 0.0
                            logger.warning("RSI calculation returned NaN or zero")
                    else:
                        indicators['rsi_14'] = 0.0
                        logger.warning("RSI calculation returned None or empty")
                except Exception as e:
                    logger.error(f"RSI calculation error: {e}")
                    indicators['rsi_14'] = 0.0
            else:
                indicators['rsi_14'] = 0.0
                logger.warning(f"Insufficient data for RSI: {len(df)} days < 14")
            
            # EMA calculations
            if len(df) >= 20:
                try:
                    from indicators.ema import calculate_ema
                    ema_20 = calculate_ema(df['close'], 20)
                    if ema_20 is not None and len(ema_20) > 0:
                        latest_ema20 = ema_20.iloc[-1]
                        if pd.notna(latest_ema20) and latest_ema20 != 0:
                            indicators['ema_20'] = float(latest_ema20)
                            logger.debug(f"EMA 20 calculated: {indicators['ema_20']:.2f}")
                        else:
                            indicators['ema_20'] = 0.0
                    else:
                        indicators['ema_20'] = 0.0
                except Exception as e:
                    logger.error(f"EMA 20 calculation error: {e}")
                    indicators['ema_20'] = 0.0
            else:
                indicators['ema_20'] = 0.0
            
            if len(df) >= 50:
                try:
                    from indicators.ema import calculate_ema
                    ema_50 = calculate_ema(df['close'], 50)
                    if ema_50 is not None and len(ema_50) > 0:
                        latest_ema50 = ema_50.iloc[-1]
                        if pd.notna(latest_ema50) and latest_ema50 != 0:
                            indicators['ema_50'] = float(latest_ema50)
                            logger.debug(f"EMA 50 calculated: {indicators['ema_50']:.2f}")
                        else:
                            indicators['ema_50'] = 0.0
                    else:
                        indicators['ema_50'] = 0.0
                except Exception as e:
                    logger.error(f"EMA 50 calculation error: {e}")
                    indicators['ema_50'] = 0.0
            else:
                indicators['ema_50'] = 0.0
            
            # MACD calculation
            if len(df) >= 26:
                try:
                    from indicators.macd import calculate_macd
                    macd_result = calculate_macd(df['close'])
                    if macd_result and len(macd_result) == 3:
                        macd_line, signal_line, histogram = macd_result
                        if (macd_line is not None and len(macd_line) > 0 and
                            signal_line is not None and len(signal_line) > 0 and
                            histogram is not None and len(histogram) > 0):
                            
                            # Get latest values
                            latest_macd = macd_line.iloc[-1]
                            latest_signal = signal_line.iloc[-1]
                            latest_histogram = histogram.iloc[-1]
                            
                            if pd.notna(latest_macd):
                                indicators['macd_line'] = float(latest_macd)
                                indicators['macd_signal'] = float(latest_signal) if pd.notna(latest_signal) else 0.0
                                indicators['macd_histogram'] = float(latest_histogram) if pd.notna(latest_histogram) else 0.0
                                logger.debug(f"MACD calculated: {indicators['macd_line']:.4f}")
                            else:
                                indicators['macd_line'] = 0.0
                                indicators['macd_signal'] = 0.0
                                indicators['macd_histogram'] = 0.0
                        else:
                            indicators['macd_line'] = 0.0
                            indicators['macd_signal'] = 0.0
                            indicators['macd_histogram'] = 0.0
                    else:
                        indicators['macd_line'] = 0.0
                        indicators['macd_signal'] = 0.0
                        indicators['macd_histogram'] = 0.0
                except Exception as e:
                    logger.error(f"MACD calculation error: {e}")
                    indicators['macd_line'] = 0.0
                    indicators['macd_signal'] = 0.0
                    indicators['macd_histogram'] = 0.0
            else:
                indicators['macd_line'] = 0.0
                indicators['macd_signal'] = 0.0
                indicators['macd_histogram'] = 0.0
                logger.warning(f"Insufficient data for MACD: {len(df)} days < 26")
            
        except Exception as e:
            logger.error(f"Error in technical indicator calculations: {e}")
            # Return zero indicators on any error
            return {
                'rsi_14': 0.0, 'ema_20': 0.0, 'ema_50': 0.0,
                'macd_line': 0.0, 'macd_signal': 0.0, 'macd_histogram': 0.0
            }
        
        return indicators
    
    def update_technical_indicators(self, ticker: str, indicators: Dict[str, float], target_date: str = None):
        """Update technical indicators for a ticker"""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Build update query
            update_fields = []
            values = []
            
            indicator_columns = {
                'rsi_14': 'rsi_14',
                'ema_20': 'ema_20', 
                'ema_50': 'ema_50',
                'macd_line': 'macd_line',
                'macd_signal': 'macd_signal',
                'macd_histogram': 'macd_histogram'
            }
            
            for indicator, value in indicators.items():
                if indicator in indicator_columns and value is not None:
                    update_fields.append(f"{indicator_columns[indicator]} = %s")
                    values.append(value)
            
            if update_fields:
                values.extend([ticker, target_date])
                query = f"""
                UPDATE daily_charts 
                SET {', '.join(update_fields)}
                WHERE ticker = %s AND date = %s
                """
                
                self.cursor.execute(query, tuple(values))
                self.conn.commit()
                logger.debug(f"Updated technical indicators for {ticker} on {target_date}")
                return True
            else:
                logger.warning(f"No valid indicators to update for {ticker}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating technical indicators for {ticker}: {e}")
            self.conn.rollback()
            return False
    
    def fix_ticker_technical_indicators(self, ticker: str) -> bool:
        """Fix technical indicators for a single ticker"""
        try:
            logger.info(f"Processing {ticker}...")
            
            # Get price data
            df = self.get_price_data_for_ticker(ticker, min_days=26)
            if df is None:
                logger.warning(f"Skipping {ticker}: insufficient price data")
                return False
            
            # Calculate indicators
            indicators = self.calculate_technical_indicators(df)
            if not indicators:
                logger.warning(f"No indicators calculated for {ticker}")
                return False
            
            # Update all recent records for this ticker
            success_count = 0
            total_count = 0
            
            # Get recent dates for this ticker
            query = """
            SELECT DISTINCT date::text
            FROM daily_charts 
            WHERE ticker = %s AND close IS NOT NULL AND close != 0
            ORDER BY date DESC
            LIMIT 30
            """
            self.cursor.execute(query, (ticker,))
            recent_dates = [row[0] for row in self.cursor.fetchall()]
            
            for date_str in recent_dates:
                if self.update_technical_indicators(ticker, indicators, date_str):
                    success_count += 1
                total_count += 1
            
            logger.info(f"Updated {success_count}/{total_count} records for {ticker}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error fixing technical indicators for {ticker}: {e}")
            return False
    
    def run_fix(self):
        """Run the complete technical indicators fix"""
        try:
            logger.info("🔧 Starting Technical Indicators Fix")
            logger.info("=" * 50)
            
            # Connect to database
            self.connect()
            
            # Get tickers needing technical indicators
            tickers = self.get_tickers_needing_technical_indicators()
            logger.info(f"Found {len(tickers)} tickers needing technical indicators")
            
            if not tickers:
                logger.info("No tickers need fixing - all technical indicators are up to date")
                return
            
            # Process tickers
            successful = 0
            failed = 0
            
            for i, ticker in enumerate(tickers, 1):
                logger.info(f"Processing {i}/{len(tickers)}: {ticker}")
                
                if self.fix_ticker_technical_indicators(ticker):
                    successful += 1
                else:
                    failed += 1
                
                # Progress update every 10 tickers
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(tickers)} completed")
            
            # Summary
            logger.info("=" * 50)
            logger.info("🔧 Technical Indicators Fix Complete")
            logger.info(f"Successful: {successful}")
            logger.info(f"Failed: {failed}")
            logger.info(f"Total: {len(tickers)}")
            
        except Exception as e:
            logger.error(f"Error in technical indicators fix: {e}")
        finally:
            self.disconnect()

def main():
    """Main function"""
    fixer = TechnicalIndicatorsFixer()
    fixer.run_fix()

if __name__ == "__main__":
    main() 