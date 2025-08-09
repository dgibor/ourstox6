#!/usr/bin/env python3
"""
Investigate why ROKU, SQ, TWLO, CRWD failed in the 20 ticker test
"""

from calc_technical_scores_enhanced import EnhancedTechnicalScoreCalculator
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def investigate_failed_tickers():
    print("INVESTIGATING FAILED TICKERS")
    print("=" * 60)
    
    failed_tickers = ['ROKU', 'SQ', 'TWLO', 'CRWD']
    calc = EnhancedTechnicalScoreCalculator()
    
    # Database connection
    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    for ticker in failed_tickers:
        print(f"\n🔍 INVESTIGATING {ticker}")
        print("-" * 40)
        
        # Check if ticker exists in database
        try:
            conn = psycopg2.connect(**db_config)
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check stocks table
                cursor.execute("SELECT ticker, company_name FROM stocks WHERE ticker = %s", (ticker,))
                stock_info = cursor.fetchone()
                
                if stock_info:
                    print(f"✅ {ticker} exists in stocks table: {stock_info['company_name']}")
                else:
                    print(f"❌ {ticker} NOT FOUND in stocks table")
                    continue
                
                # Check daily_charts data
                cursor.execute("""
                    SELECT COUNT(*) as count, 
                           MIN(date) as min_date, 
                           MAX(date) as max_date,
                           AVG(close) as avg_price
                    FROM daily_charts 
                    WHERE ticker = %s AND close IS NOT NULL
                """, (ticker,))
                
                chart_data = cursor.fetchone()
                
                if chart_data and chart_data['count'] > 0:
                    print(f"📊 Daily charts data:")
                    print(f"   Records: {chart_data['count']}")
                    print(f"   Date range: {chart_data['min_date']} to {chart_data['max_date']}")
                    print(f"   Avg price: ${chart_data['avg_price']:.2f}")
                    
                    # Check for sufficient recent data
                    cursor.execute("""
                        SELECT COUNT(*) as recent_count
                        FROM daily_charts 
                        WHERE ticker = %s 
                        AND date >= CURRENT_DATE - INTERVAL '60 days'
                        AND close IS NOT NULL
                    """, (ticker,))
                    
                    recent_data = cursor.fetchone()
                    print(f"   Recent data (60 days): {recent_data['recent_count']} records")
                    
                    if recent_data['recent_count'] < 30:
                        print(f"⚠️ ISSUE: Only {recent_data['recent_count']} recent records (need 30+ for technical analysis)")
                    
                else:
                    print(f"❌ NO daily charts data found for {ticker}")
                
                # Check company_fundamentals
                cursor.execute("""
                    SELECT COUNT(*) as count, MAX(date) as latest_date
                    FROM company_fundamentals 
                    WHERE ticker = %s
                """, (ticker,))
                
                fund_data = cursor.fetchone()
                if fund_data and fund_data['count'] > 0:
                    print(f"📈 Fundamentals: {fund_data['count']} records, latest: {fund_data['latest_date']}")
                else:
                    print(f"❌ NO fundamentals data for {ticker}")
            
            conn.close()
            
        except Exception as db_e:
            print(f"❌ Database error for {ticker}: {db_e}")
        
        # Try technical calculation
        try:
            print(f"\n🧮 Testing technical calculation for {ticker}:")
            tech_data = calc.get_enhanced_technical_data(ticker)
            
            if tech_data:
                price_count = len(tech_data.get('price_history', []))
                print(f"   Price history: {price_count} records")
                
                if price_count < 30:
                    print(f"   ⚠️ INSUFFICIENT DATA: Only {price_count} price records (need 30+)")
                else:
                    print(f"   ✅ Sufficient price data available")
            else:
                print(f"   ❌ NO technical data returned")
            
            # Try full calculation
            result = calc.calculate_enhanced_technical_scores(ticker)
            
            if result:
                print(f"   ✅ Technical calculation successful")
            else:
                print(f"   ❌ Technical calculation failed")
                
        except Exception as calc_e:
            print(f"   ❌ Calculation error: {calc_e}")

def check_data_requirements():
    """Check what the minimum data requirements are"""
    print("\n" + "=" * 60)
    print("DATA REQUIREMENTS ANALYSIS")
    print("=" * 60)
    
    print("""
📋 Minimum Data Requirements for Enhanced Technical Scoring:

🔹 Daily Charts Data:
   - Minimum 30 days of OHLCV data
   - Close, High, Low prices required
   - Volume data recommended
   - Recent data (within 60 days) preferred

🔹 Price Quality:
   - No zero or null prices
   - Reasonable price ranges (not corrupted data)
   - Consistent data series (no major gaps)

🔹 Technical Calculation Requirements:
   - RSI: 14+ periods
   - ADX: 28+ periods (14 for DM, 14 for ADX smoothing)
   - ATR: 15+ periods  
   - CCI: 20+ periods
   - Bollinger Bands: 20+ periods

❗ LIKELY ISSUES WITH FAILED TICKERS:
   1. Insufficient recent data (common for small caps)
   2. Missing daily_charts entries
   3. Data quality issues (zeros, nulls, outliers)
   4. Recent IPOs or delistings
""")

if __name__ == "__main__":
    investigate_failed_tickers()
    check_data_requirements()
