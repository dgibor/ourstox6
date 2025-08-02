#!/usr/bin/env python3
"""
QA Report: Technical Indicators Analysis
Identifies issues with technical indicator calculations in the daily_run system
"""

import os
import sys
import psycopg2
import pandas as pd
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
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'dbname': os.getenv('DB_NAME', 'ourstox6'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }

def analyze_technical_indicators():
    """Comprehensive analysis of technical indicator issues"""
    
    config = get_db_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        print("🔍 TECHNICAL INDICATORS QA REPORT")
        print("=" * 60)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. OVERALL DATA STATUS
        print("1. OVERALL DATA STATUS")
        print("-" * 30)
        
        cursor.execute("SELECT COUNT(*) FROM daily_charts")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM daily_charts")
        unique_tickers = cursor.fetchone()[0]
        
        print(f"Total Records: {total_records:,}")
        print(f"Unique Tickers: {unique_tickers}")
        print()
        
        # 2. TECHNICAL INDICATOR COVERAGE
        print("2. TECHNICAL INDICATOR COVERAGE")
        print("-" * 30)
        
        indicators = ['rsi_14', 'ema_20', 'ema_50', 'macd_line', 'macd_signal', 'macd_histogram']
        
        for indicator in indicators:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM daily_charts 
                WHERE {indicator} IS NOT NULL AND {indicator} != 0
            """)
            count = cursor.fetchone()[0]
            percentage = (count / total_records * 100) if total_records > 0 else 0
            print(f"{indicator:15}: {count:8,} records ({percentage:5.1f}%)")
        
        print()
        
        # 3. IDENTIFY PROBLEMATIC TICKERS
        print("3. PROBLEMATIC TICKERS ANALYSIS")
        print("-" * 30)
        
        # Find tickers with price data but no technical indicators
        cursor.execute("""
            SELECT ticker, 
                   COUNT(*) as total_records,
                   COUNT(CASE WHEN close IS NOT NULL AND close != 0 THEN 1 END) as price_records,
                   COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) as rsi_records,
                   COUNT(CASE WHEN ema_20 IS NOT NULL AND ema_20 != 0 THEN 1 END) as ema20_records,
                   COUNT(CASE WHEN macd_line IS NOT NULL AND macd_line != 0 THEN 1 END) as macd_records
            FROM daily_charts 
            GROUP BY ticker 
            HAVING COUNT(CASE WHEN close IS NOT NULL AND close != 0 THEN 1 END) > 0
               AND (COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) = 0
                    OR COUNT(CASE WHEN ema_20 IS NOT NULL AND ema_20 != 0 THEN 1 END) = 0
                    OR COUNT(CASE WHEN macd_line IS NOT NULL AND macd_line != 0 THEN 1 END) = 0)
            ORDER BY total_records DESC 
            LIMIT 15
        """)
        
        problematic_tickers = cursor.fetchall()
        print(f"Found {len(problematic_tickers)} tickers with price data but missing technical indicators:")
        print()
        
        for ticker, total, price, rsi, ema20, macd in problematic_tickers:
            missing = []
            if rsi == 0: missing.append("RSI")
            if ema20 == 0: missing.append("EMA20")
            if macd == 0: missing.append("MACD")
            print(f"  {ticker:8}: {total:4} records | Price: {price:4} | Missing: {', '.join(missing)}")
        
        print()
        
        # 4. DATA QUALITY ISSUES
        print("4. DATA QUALITY ISSUES")
        print("-" * 30)
        
        # Check for tickers with insufficient data for calculations
        cursor.execute("""
            SELECT ticker, COUNT(*) as record_count
            FROM daily_charts 
            WHERE close IS NOT NULL AND close != 0
            GROUP BY ticker 
            HAVING COUNT(*) < 26
            ORDER BY record_count ASC
            LIMIT 10
        """)
        
        insufficient_data = cursor.fetchall()
        print(f"Tickers with insufficient data for technical calculations (< 26 days):")
        for ticker, count in insufficient_data:
            print(f"  {ticker}: {count} days (need 26+ for MACD)")
        
        print()
        
        # 5. RECENT DATA ANALYSIS
        print("5. RECENT DATA ANALYSIS")
        print("-" * 30)
        
        cursor.execute("""
            SELECT date::text, COUNT(*) as total_records,
                   COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) as rsi_records,
                   COUNT(CASE WHEN ema_20 IS NOT NULL AND ema_20 != 0 THEN 1 END) as ema20_records,
                   COUNT(CASE WHEN macd_line IS NOT NULL AND macd_line != 0 THEN 1 END) as macd_records
            FROM daily_charts 
            WHERE date::date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY date 
            ORDER BY date DESC
        """)
        
        recent_data = cursor.fetchall()
        print("Recent 7 days technical indicator coverage:")
        for date, total, rsi, ema20, macd in recent_data:
            rsi_pct = (rsi / total * 100) if total > 0 else 0
            ema20_pct = (ema20 / total * 100) if total > 0 else 0
            macd_pct = (macd / total * 100) if total > 0 else 0
            print(f"  {date}: {total:3} records | RSI: {rsi_pct:5.1f}% | EMA20: {ema20_pct:5.1f}% | MACD: {macd_pct:5.1f}%")
        
        print()
        
        # 6. ROOT CAUSE ANALYSIS
        print("6. ROOT CAUSE ANALYSIS")
        print("-" * 30)
        
        # Check if technical calculation process is running
        cursor.execute("""
            SELECT COUNT(*) 
            FROM daily_charts 
            WHERE date::date = CURRENT_DATE - INTERVAL '1 day'
        """)
        yesterday_records = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM daily_charts 
            WHERE date::date = CURRENT_DATE - INTERVAL '1 day'
            AND rsi_14 IS NOT NULL AND rsi_14 != 0
        """)
        yesterday_with_rsi = cursor.fetchone()[0]
        
        print(f"Yesterday's data: {yesterday_records} records")
        print(f"Yesterday with RSI: {yesterday_with_rsi} records")
        
        if yesterday_records > 0 and yesterday_with_rsi == 0:
            print("❌ CRITICAL: Technical indicators not being calculated for recent data")
        elif yesterday_records > 0 and yesterday_with_rsi < yesterday_records:
            print("⚠️  WARNING: Partial technical indicator coverage for recent data")
        else:
            print("✅ Technical indicators appear to be calculated for recent data")
        
        print()
        
        # 7. RECOMMENDATIONS
        print("7. RECOMMENDATIONS")
        print("-" * 30)
        
        print("Based on the analysis, here are the key issues and recommendations:")
        print()
        
        if len(problematic_tickers) > 0:
            print("🔴 CRITICAL ISSUES:")
            print("  1. Many tickers have price data but missing technical indicators")
            print("  2. Technical indicator calculation process may be failing")
            print("  3. Some tickers have insufficient historical data for calculations")
            print()
            print("🔧 RECOMMENDED FIXES:")
            print("  1. Check the daily_trading_system.py technical calculation logic")
            print("  2. Verify that _calculate_technical_indicators_priority1() is being called")
            print("  3. Ensure sufficient historical data is fetched before calculations")
            print("  4. Add better error handling and logging in technical calculations")
            print("  5. Implement a backfill process for missing technical indicators")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False
    
    return True

if __name__ == "__main__":
    analyze_technical_indicators() 