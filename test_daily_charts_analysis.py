#!/usr/bin/env python3
"""
Test script to analyze daily_charts table and identify missing technical indicators
"""

import os
import sys
import psycopg2
from datetime import datetime

# Add daily_run to path
sys.path.append('daily_run')

def get_db_config():
    """Get database configuration from daily_run config"""
    try:
        from config import Config
        config = Config.get_db_config()
        return config
    except ImportError:
        # Fallback to environment variables
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'dbname': os.getenv('DB_NAME', 'ourstox6'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }

def analyze_daily_charts():
    """Analyze the daily_charts table to identify missing technical indicators"""
    
    config = get_db_config()
    
    try:
        # Connect to database
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        print("🔍 Analyzing daily_charts table...")
        print("=" * 50)
        
        # Get total records
        cursor.execute("SELECT COUNT(*) FROM daily_charts")
        total_records = cursor.fetchone()[0]
        print(f"Total records in daily_charts: {total_records:,}")
        
        # Get unique tickers
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM daily_charts")
        unique_tickers = cursor.fetchone()[0]
        print(f"Unique tickers: {unique_tickers}")
        
        # Check technical indicator columns
        technical_indicators = [
            'rsi_14', 'ema_20', 'ema_50', 'macd_line', 'macd_signal', 'macd_histogram',
            'bb_upper', 'bb_middle', 'bb_lower', 'atr_14', 'cci_20', 'stoch_k', 'stoch_d'
        ]
        
        print("\n📊 Technical Indicator Analysis:")
        print("-" * 40)
        
        for indicator in technical_indicators:
            # Check if column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'daily_charts' AND column_name = %s
            """, (indicator,))
            
            if cursor.fetchone():
                # Count non-null and non-zero values
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM daily_charts 
                    WHERE {indicator} IS NOT NULL AND {indicator} != 0
                """)
                count = cursor.fetchone()[0]
                percentage = (count / total_records * 100) if total_records > 0 else 0
                print(f"{indicator:15}: {count:8,} records ({percentage:5.1f}%)")
            else:
                print(f"{indicator:15}: Column does not exist")
        
        # Check recent data (fixed SQL query)
        print("\n📅 Recent Data Analysis:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT date::text, COUNT(*) as records
            FROM daily_charts 
            WHERE date::date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY date 
            ORDER BY date DESC 
            LIMIT 10
        """)
        
        recent_data = cursor.fetchall()
        print("Records per day (last 30 days):")
        for date, count in recent_data:
            print(f"  {date}: {count:,} records")
        
        # Check for tickers with no technical indicators
        print("\n❌ Tickers with Missing Technical Indicators:")
        print("-" * 50)
        
        cursor.execute("""
            SELECT ticker, COUNT(*) as total_records,
                   COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) as rsi_count,
                   COUNT(CASE WHEN ema_20 IS NOT NULL AND ema_20 != 0 THEN 1 END) as ema20_count,
                   COUNT(CASE WHEN macd_line IS NOT NULL AND macd_line != 0 THEN 1 END) as macd_count
            FROM daily_charts 
            GROUP BY ticker 
            HAVING COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) = 0
               OR COUNT(CASE WHEN ema_20 IS NOT NULL AND ema_20 != 0 THEN 1 END) = 0
               OR COUNT(CASE WHEN macd_line IS NOT NULL AND macd_line != 0 THEN 1 END) = 0
            ORDER BY total_records DESC 
            LIMIT 20
        """)
        
        missing_indicators = cursor.fetchall()
        print(f"Found {len(missing_indicators)} tickers with missing indicators:")
        for ticker, total, rsi, ema20, macd in missing_indicators:
            missing = []
            if rsi == 0: missing.append("RSI")
            if ema20 == 0: missing.append("EMA20")
            if macd == 0: missing.append("MACD")
            print(f"  {ticker}: {total:,} records, missing: {', '.join(missing)}")
        
        # Check price data availability
        print("\n💰 Price Data Analysis:")
        print("-" * 40)
        
        price_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in price_columns:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM daily_charts 
                WHERE {col} IS NOT NULL AND {col} != 0
            """)
            count = cursor.fetchone()[0]
            percentage = (count / total_records * 100) if total_records > 0 else 0
            print(f"{col:10}: {count:8,} records ({percentage:5.1f}%)")
        
        # Check data quality by ticker
        print("\n🔍 Data Quality Analysis by Ticker:")
        print("-" * 50)
        
        cursor.execute("""
            SELECT ticker, 
                   COUNT(*) as total_records,
                   COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) as rsi_records,
                   COUNT(CASE WHEN ema_20 IS NOT NULL AND ema_20 != 0 THEN 1 END) as ema20_records,
                   COUNT(CASE WHEN macd_line IS NOT NULL AND macd_line != 0 THEN 1 END) as macd_records,
                   COUNT(CASE WHEN close IS NOT NULL AND close != 0 THEN 1 END) as price_records
            FROM daily_charts 
            GROUP BY ticker 
            ORDER BY total_records DESC 
            LIMIT 10
        """)
        
        top_tickers = cursor.fetchall()
        print("Top 10 tickers by record count:")
        for ticker, total, rsi, ema20, macd, price in top_tickers:
            rsi_pct = (rsi / total * 100) if total > 0 else 0
            ema20_pct = (ema20 / total * 100) if total > 0 else 0
            macd_pct = (macd / total * 100) if total > 0 else 0
            price_pct = (price / total * 100) if total > 0 else 0
            print(f"  {ticker}: {total:,} records | RSI: {rsi_pct:.1f}% | EMA20: {ema20_pct:.1f}% | MACD: {macd_pct:.1f}% | Price: {price_pct:.1f}%")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    analyze_daily_charts() 