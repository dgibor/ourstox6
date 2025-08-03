#!/usr/bin/env python3
"""
Simple Database Check Script
Quick analysis of daily_charts and fundamentals tables
"""

import sys
import os
from datetime import datetime

# Add daily_run to path
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager

def check_daily_charts():
    """Check daily_charts table for recent data and indicators"""
    print("=" * 80)
    print("📊 DAILY_CHARTS TABLE CHECK")
    print("=" * 80)
    
    try:
        db = DatabaseManager()
        
        # Check recent data
        print("\n🔍 1. RECENT DATA STATUS")
        print("-" * 50)
        
        recent_query = """
        SELECT 
            COUNT(DISTINCT ticker) as stocks_with_data,
            COUNT(*) as total_records,
            MAX(date::date) as latest_date
        FROM daily_charts 
        WHERE date::date >= CURRENT_DATE - INTERVAL '7 days'
        """
        
        recent = db.fetch_one(recent_query)
        print(f"📈 Stocks with data in last 7 days: {recent[0]}")
        print(f"📊 Total records in last 7 days: {recent[1]}")
        print(f"📅 Latest date: {recent[2]}")
        
        # Check today's data
        today_query = """
        SELECT COUNT(DISTINCT ticker) as stocks_today
        FROM daily_charts 
        WHERE date::date = CURRENT_DATE
        """
        
        today = db.fetch_one(today_query)
        print(f"📅 Stocks with data for TODAY: {today[0]}")
        
        # Check what indicator columns exist
        print("\n🔍 2. TECHNICAL INDICATORS STATUS")
        print("-" * 50)
        
        columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'daily_charts' 
        AND column_name NOT IN ('ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'created_at')
        ORDER BY column_name
        """
        
        columns = db.execute_query(columns_query)
        indicator_columns = [col[0] for col in columns]
        
        print(f"📋 Total indicator columns: {len(indicator_columns)}")
        print("📊 First 10 indicator columns:")
        for i, col in enumerate(indicator_columns[:10]):
            print(f"   {i+1}. {col}")
        
        # Check for OBV specifically
        obv_columns = [col for col in indicator_columns if 'obv' in col.lower()]
        print(f"\n📊 OBV-related columns found: {obv_columns}")
        
        # Check for volume-related columns
        volume_columns = [col for col in indicator_columns if 'volume' in col.lower() or 'vpt' in col.lower()]
        print(f"📊 Volume-related columns found: {volume_columns}")
        
        # Check a few key indicators for recent data
        print("\n🔍 3. KEY INDICATORS DATA CHECK")
        print("-" * 50)
        
        key_indicators = ['rsi_14', 'macd', 'bollinger_upper', 'ema_20']
        for indicator in key_indicators:
            if indicator in indicator_columns:
                check_query = f"""
                SELECT COUNT(DISTINCT ticker) as stocks_with_data
                FROM daily_charts 
                WHERE {indicator} IS NOT NULL AND {indicator} != 0
                AND date::date >= CURRENT_DATE - INTERVAL '7 days'
                """
                result = db.fetch_one(check_query)
                print(f"📊 {indicator}: {result[0]} stocks with data")
            else:
                print(f"❌ {indicator}: Column not found")
        
        # Check for stocks with missing indicators
        print("\n🔍 4. STOCKS WITH MISSING INDICATORS")
        print("-" * 50)
        
        if 'rsi_14' in indicator_columns:
            missing_query = """
            SELECT 
                ticker,
                COUNT(*) as total_records,
                COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) as rsi_records,
                MAX(date::date) as latest_date
            FROM daily_charts 
            WHERE date::date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY ticker
            HAVING COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) = 0
            ORDER BY latest_date DESC
            LIMIT 5
            """
            
            missing = db.execute_query(missing_query)
            print(f"📋 Found {len(missing)} stocks with missing RSI data:")
            for row in missing:
                ticker, total, rsi, latest = row
                print(f"   • {ticker}: {total} records, RSI: {rsi}, Latest: {latest}")
        
        return {
            'recent': recent,
            'today': today,
            'indicators': indicator_columns,
            'obv_columns': obv_columns,
            'volume_columns': volume_columns
        }
        
    except Exception as e:
        print(f"❌ Error checking daily_charts: {e}")
        return None

def check_fundamentals():
    """Check fundamentals table"""
    print("\n" + "=" * 80)
    print("💰 FUNDAMENTALS TABLE CHECK")
    print("=" * 80)
    
    try:
        db = DatabaseManager()
        
        # Check basic stats
        print("\n🔍 1. FUNDAMENTALS STATUS")
        print("-" * 50)
        
        basic_query = """
        SELECT 
            COUNT(DISTINCT ticker) as total_companies,
            COUNT(CASE WHEN price_to_earnings IS NOT NULL THEN 1 END) as pe_count,
            COUNT(CASE WHEN price_to_book IS NOT NULL THEN 1 END) as pb_count,
            COUNT(CASE WHEN price_to_sales IS NOT NULL THEN 1 END) as ps_count,
            COUNT(CASE WHEN market_cap IS NOT NULL THEN 1 END) as market_cap_count
        FROM company_fundamentals
        """
        
        basic = db.fetch_one(basic_query)
        print(f"📊 Total companies: {basic[0]}")
        print(f"📈 P/E Ratio data: {basic[1]}")
        print(f"📈 P/B Ratio data: {basic[2]}")
        print(f"📈 P/S Ratio data: {basic[3]}")
        print(f"📈 Market Cap data: {basic[4]}")
        
        # Check for companies with missing data
        print("\n🔍 2. COMPANIES WITH MISSING DATA")
        print("-" * 50)
        
        missing_query = """
        SELECT 
            ticker,
            CASE WHEN price_to_earnings IS NULL THEN 'Missing' ELSE 'OK' END as pe_status,
            CASE WHEN price_to_book IS NULL THEN 'Missing' ELSE 'OK' END as pb_status,
            CASE WHEN price_to_sales IS NULL THEN 'Missing' ELSE 'OK' END as ps_status
        FROM company_fundamentals
        WHERE price_to_earnings IS NULL 
        OR price_to_book IS NULL 
        OR price_to_sales IS NULL
        ORDER BY ticker
        LIMIT 10
        """
        
        missing = db.execute_query(missing_query)
        print(f"📋 Found {len(missing)} companies with missing fundamental data:")
        for row in missing:
            ticker, pe, pb, ps = row
            print(f"   • {ticker}: P/E: {pe}, P/B: {pb}, P/S: {ps}")
        
        return {
            'basic': basic,
            'missing': missing
        }
        
    except Exception as e:
        print(f"❌ Error checking fundamentals: {e}")
        return None

def generate_summary(daily_charts_data, fundamentals_data):
    """Generate summary and recommendations"""
    print("\n" + "=" * 80)
    print("🎯 SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n📊 KEY FINDINGS:")
    print("-" * 30)
    
    if daily_charts_data:
        recent = daily_charts_data['recent']
        today = daily_charts_data['today']
        indicators = daily_charts_data['indicators']
        obv_columns = daily_charts_data['obv_columns']
        volume_columns = daily_charts_data['volume_columns']
        
        print(f"📈 Price data: {recent[0]} stocks with recent data")
        print(f"📅 Today's data: {today[0]} stocks")
        print(f"📊 Technical indicators: {len(indicators)} columns available")
        print(f"📊 OBV columns: {obv_columns}")
        print(f"📊 Volume columns: {volume_columns}")
        
        # Identify issues
        issues = []
        if today[0] == 0:
            issues.append("❌ No price data for today")
        if not obv_columns:
            issues.append("❌ No OBV columns found")
        if not volume_columns:
            issues.append("❌ No volume-related columns found")
        
        if issues:
            print("\n🚨 IDENTIFIED ISSUES:")
            for issue in issues:
                print(f"   {issue}")
    
    if fundamentals_data:
        basic = fundamentals_data['basic']
        missing = fundamentals_data['missing']
        
        print(f"\n💰 Fundamentals: {basic[0]} companies total")
        print(f"📈 P/E data: {basic[1]} companies")
        print(f"📈 P/B data: {basic[2]} companies")
        print(f"📈 P/S data: {basic[3]} companies")
        
        if basic[1] == 0 and basic[2] == 0 and basic[3] == 0:
            print("❌ No fundamental ratios calculated")
    
    print("\n🔧 RECOMMENDATIONS:")
    print("-" * 30)
    
    recommendations = []
    
    if daily_charts_data and daily_charts_data['today'][0] == 0:
        recommendations.append("1. 🔄 Run price update process - no data for today")
    
    if daily_charts_data and not daily_charts_data['obv_columns']:
        recommendations.append("2. 🔧 Check OBV calculation - no OBV columns found")
    
    if fundamentals_data and fundamentals_data['basic'][1] == 0:
        recommendations.append("3. 🔄 Run fundamental ratio calculation - no P/E data")
    
    if not recommendations:
        recommendations.append("✅ All systems appear to be working correctly")
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print("\n📋 NEXT STEPS:")
    print("-" * 30)
    print("1. Check Railway cron logs for execution status")
    print("2. Verify if today was a trading day")
    print("3. Run manual price update if needed")
    print("4. Run manual fundamental calculation if needed")

def main():
    """Main function"""
    print("🚀 STARTING SIMPLE DATABASE CHECK")
    print(f"⏰ Check started at: {datetime.now()}")
    
    # Run checks
    daily_charts_data = check_daily_charts()
    fundamentals_data = check_fundamentals()
    
    # Generate summary
    generate_summary(daily_charts_data, fundamentals_data)
    
    print(f"\n✅ Check completed at: {datetime.now()}")

if __name__ == "__main__":
    main() 