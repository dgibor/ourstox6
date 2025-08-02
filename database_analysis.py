#!/usr/bin/env python3
"""
Comprehensive Database Analysis Script
Analyzes daily_charts and fundamentals tables to identify missing data issues
"""

import sys
import os
from datetime import datetime, date, timedelta
import pandas as pd

# Add daily_run to path
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager

def analyze_daily_charts():
    """Analyze daily_charts table for recent data and missing indicators"""
    print("=" * 80)
    print("📊 DAILY_CHARTS TABLE ANALYSIS")
    print("=" * 80)
    
    try:
        # Connect to database
        db = DatabaseManager()
        
        # 1. Check recent price data
        print("\n🔍 1. RECENT PRICE DATA ANALYSIS")
        print("-" * 50)
        
        # Check how many stocks have recent data (fix date casting)
        recent_data_query = """
        SELECT 
            COUNT(DISTINCT ticker) as stocks_with_recent_data,
            COUNT(*) as total_records,
            MIN(date::date) as earliest_date,
            MAX(date::date) as latest_date
        FROM daily_charts 
        WHERE date::date >= CURRENT_DATE - INTERVAL '7 days'
        """
        
        recent_data = db.fetch_one(recent_data_query)
        print(f"📈 Stocks with data in last 7 days: {recent_data[0]}")
        print(f"📊 Total records in last 7 days: {recent_data[1]}")
        print(f"📅 Date range: {recent_data[2]} to {recent_data[3]}")
        
        # Check today's data specifically
        today_query = """
        SELECT 
            COUNT(DISTINCT ticker) as stocks_today,
            COUNT(*) as records_today
        FROM daily_charts 
        WHERE date::date = CURRENT_DATE
        """
        
        today_data = db.fetch_one(today_query)
        print(f"📅 Stocks with data for TODAY: {today_data[0]}")
        print(f"📊 Records for TODAY: {today_data[1]}")
        
        # 2. Check specific indicators (OBV, Volume, etc.)
        print("\n🔍 2. TECHNICAL INDICATORS ANALYSIS")
        print("-" * 50)
        
        # Check OBV specifically
        obv_query = """
        SELECT 
            COUNT(DISTINCT ticker) as stocks_with_obv,
            COUNT(*) as obv_records
        FROM daily_charts 
        WHERE obv_20 IS NOT NULL AND obv_20 != 0
        AND date::date >= CURRENT_DATE - INTERVAL '7 days'
        """
        
        obv_data = db.fetch_one(obv_query)
        print(f"📊 Stocks with OBV data (last 7 days): {obv_data[0]}")
        print(f"📈 OBV records (last 7 days): {obv_data[1]}")
        
        # Check volume data
        volume_query = """
        SELECT 
            COUNT(DISTINCT ticker) as stocks_with_volume,
            COUNT(*) as volume_records
        FROM daily_charts 
        WHERE volume IS NOT NULL AND volume > 0
        AND date::date >= CURRENT_DATE - INTERVAL '7 days'
        """
        
        volume_data = db.fetch_one(volume_query)
        print(f"📊 Stocks with volume data (last 7 days): {volume_data[0]}")
        print(f"📈 Volume records (last 7 days): {volume_data[1]}")
        
        # 3. Check all technical indicators
        print("\n🔍 3. ALL TECHNICAL INDICATORS STATUS")
        print("-" * 50)
        
        # Get list of all indicator columns
        columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'daily_charts' 
        AND column_name NOT IN ('ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'created_at')
        ORDER BY column_name
        """
        
        columns = db.execute_query(columns_query)
        indicator_columns = [col[0] for col in columns]
        
        print(f"📋 Total indicator columns found: {len(indicator_columns)}")
        
        # Check each indicator for recent data
        indicator_stats = []
        for indicator in indicator_columns[:20]:  # Check first 20 indicators
            check_query = f"""
            SELECT 
                COUNT(DISTINCT ticker) as stocks_with_data,
                COUNT(*) as total_records
            FROM daily_charts 
            WHERE {indicator} IS NOT NULL AND {indicator} != 0
            AND date::date >= CURRENT_DATE - INTERVAL '7 days'
            """
            
            result = db.fetch_one(check_query)
            indicator_stats.append({
                'indicator': indicator,
                'stocks_with_data': result[0],
                'total_records': result[1]
            })
        
        # Display indicator stats
        for stat in indicator_stats:
            print(f"📊 {stat['indicator']}: {stat['stocks_with_data']} stocks, {stat['total_records']} records")
        
        # 4. Check for stocks with missing data
        print("\n🔍 4. STOCKS WITH MISSING DATA")
        print("-" * 50)
        
        missing_data_query = """
        SELECT 
            ticker,
            COUNT(*) as total_records,
            COUNT(CASE WHEN obv_20 IS NOT NULL AND obv_20 != 0 THEN 1 END) as obv_records,
            COUNT(CASE WHEN volume IS NOT NULL AND volume > 0 THEN 1 END) as volume_records,
            MAX(date::date) as latest_date
        FROM daily_charts 
        WHERE date::date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY ticker
        HAVING COUNT(CASE WHEN obv_20 IS NOT NULL AND obv_20 != 0 THEN 1 END) = 0
        OR COUNT(CASE WHEN volume IS NOT NULL AND volume > 0 THEN 1 END) = 0
        ORDER BY latest_date DESC
        LIMIT 10
        """
        
        missing_data = db.execute_query(missing_data_query)
        print(f"📋 Found {len(missing_data)} stocks with missing OBV or volume data:")
        for row in missing_data:
            ticker, total, obv, volume, latest = row
            print(f"   • {ticker}: {total} records, OBV: {obv}, Volume: {volume}, Latest: {latest}")
        
        return {
            'recent_data': recent_data,
            'today_data': today_data,
            'obv_data': obv_data,
            'volume_data': volume_data,
            'indicator_stats': indicator_stats,
            'missing_data': missing_data
        }
        
    except Exception as e:
        print(f"❌ Error analyzing daily_charts: {e}")
        return None

def analyze_fundamentals():
    """Analyze fundamentals tables for missing data"""
    print("\n" + "=" * 80)
    print("💰 FUNDAMENTALS ANALYSIS")
    print("=" * 80)
    
    try:
        # Connect to database
        db = DatabaseManager()
        
        # Check company_fundamentals table
        print("\n🔍 1. COMPANY_FUNDAMENTALS TABLE")
        print("-" * 50)
        
        # First check what columns exist
        columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'company_fundamentals'
        ORDER BY column_name
        """
        
        columns = db.execute_query(columns_query)
        column_names = [col[0] for col in columns]
        print(f"📋 Available columns: {', '.join(column_names)}")
        
        # Check if updated_at or created_at exists
        has_updated_at = 'updated_at' in column_names
        has_created_at = 'created_at' in column_names
        
        # Build query based on available columns
        if has_updated_at:
            latest_column = 'updated_at'
        elif has_created_at:
            latest_column = 'created_at'
        else:
            latest_column = None
        
        fundamentals_query = f"""
        SELECT 
            COUNT(DISTINCT ticker) as total_companies,
            COUNT(CASE WHEN price_to_earnings IS NOT NULL THEN 1 END) as pe_ratio_count,
            COUNT(CASE WHEN price_to_book IS NOT NULL THEN 1 END) as pb_ratio_count,
            COUNT(CASE WHEN price_to_sales IS NOT NULL THEN 1 END) as ps_ratio_count,
            COUNT(CASE WHEN debt_to_equity_ratio IS NOT NULL THEN 1 END) as debt_equity_count,
            COUNT(CASE WHEN market_cap IS NOT NULL THEN 1 END) as market_cap_count
            {f", MAX({latest_column}) as latest_update" if latest_column else ""}
        FROM company_fundamentals
        """
        
        fundamentals = db.fetch_one(fundamentals_query)
        print(f"📊 Total companies: {fundamentals[0]}")
        print(f"📈 P/E Ratio data: {fundamentals[1]}")
        print(f"📈 P/B Ratio data: {fundamentals[2]}")
        print(f"📈 P/S Ratio data: {fundamentals[3]}")
        print(f"📈 Debt/Equity data: {fundamentals[4]}")
        print(f"📈 Market Cap data: {fundamentals[5]}")
        if latest_column:
            print(f"📅 Latest update: {fundamentals[6]}")
        
        # Check recent fundamental updates if we have a timestamp column
        if latest_column:
            recent_fundamentals_query = f"""
            SELECT 
                COUNT(DISTINCT ticker) as recently_updated
            FROM company_fundamentals
            WHERE {latest_column} >= CURRENT_DATE - INTERVAL '7 days'
            """
            
            recent_fundamentals = db.fetch_one(recent_fundamentals_query)
            print(f"📅 Companies updated in last 7 days: {recent_fundamentals[0]}")
        else:
            recent_fundamentals = (0,)
            print("📅 Cannot check recent updates - no timestamp column")
        
        # Check for companies with missing fundamental data
        missing_fundamentals_query = """
        SELECT 
            ticker,
            CASE WHEN price_to_earnings IS NULL THEN 'Missing P/E' ELSE 'OK' END as pe_status,
            CASE WHEN price_to_book IS NULL THEN 'Missing P/B' ELSE 'OK' END as pb_status,
            CASE WHEN price_to_sales IS NULL THEN 'Missing P/S' ELSE 'OK' END as ps_status
            {f", {latest_column}" if latest_column else ""}
        FROM company_fundamentals
        WHERE price_to_earnings IS NULL 
        OR price_to_book IS NULL 
        OR price_to_sales IS NULL
        {f"ORDER BY {latest_column} DESC" if latest_column else "ORDER BY ticker"}
        LIMIT 10
        """
        
        missing_fundamentals = db.execute_query(missing_fundamentals_query)
        print(f"\n📋 Found {len(missing_fundamentals)} companies with missing fundamental data:")
        for row in missing_fundamentals:
            if latest_column:
                ticker, pe, pb, ps, updated = row
                print(f"   • {ticker}: P/E: {pe}, P/B: {pb}, P/S: {ps}, Updated: {updated}")
            else:
                ticker, pe, pb, ps = row
                print(f"   • {ticker}: P/E: {pe}, P/B: {pb}, P/S: {ps}")
        
        return {
            'fundamentals': fundamentals,
            'recent_fundamentals': recent_fundamentals,
            'missing_fundamentals': missing_fundamentals
        }
        
    except Exception as e:
        print(f"❌ Error analyzing fundamentals: {e}")
        return None

def analyze_trading_days():
    """Analyze trading day data"""
    print("\n" + "=" * 80)
    print("📅 TRADING DAYS ANALYSIS")
    print("=" * 80)
    
    try:
        # Connect to database
        db = DatabaseManager()
        
        # Check if trading_days table exists
        table_exists_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'trading_days'
        )
        """
        
        table_exists = db.fetch_one(table_exists_query)[0]
        
        if table_exists:
            trading_days_query = """
            SELECT 
                COUNT(*) as total_trading_days,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                COUNT(CASE WHEN date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_trading_days
            FROM trading_days
            """
            
            trading_days = db.fetch_one(trading_days_query)
            print(f"📊 Total trading days: {trading_days[0]}")
            print(f"📅 Date range: {trading_days[1]} to {trading_days[2]}")
            print(f"📅 Trading days in last 30 days: {trading_days[3]}")
            
            # Check if today is marked as a trading day
            today_trading_query = """
            SELECT COUNT(*) 
            FROM trading_days 
            WHERE date = CURRENT_DATE
            """
            
            today_trading = db.fetch_one(today_trading_query)[0]
            print(f"📅 Today marked as trading day: {'Yes' if today_trading > 0 else 'No'}")
            
        else:
            print("❌ trading_days table does not exist")
            trading_days = None
            today_trading = 0
        
        return {
            'table_exists': table_exists,
            'trading_days': trading_days,
            'today_trading': today_trading
        }
        
    except Exception as e:
        print(f"❌ Error analyzing trading days: {e}")
        return None

def generate_recommendations(daily_charts_data, fundamentals_data, trading_days_data):
    """Generate recommendations based on analysis"""
    print("\n" + "=" * 80)
    print("🎯 ANALYSIS SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n📊 KEY FINDINGS:")
    print("-" * 30)
    
    if daily_charts_data:
        recent_data = daily_charts_data['recent_data']
        today_data = daily_charts_data['today_data']
        obv_data = daily_charts_data['obv_data']
        volume_data = daily_charts_data['volume_data']
        
        print(f"📈 Recent price data: {recent_data[0]} stocks in last 7 days")
        print(f"📅 Today's data: {today_data[0]} stocks")
        print(f"📊 OBV data: {obv_data[0]} stocks with OBV")
        print(f"📊 Volume data: {volume_data[0]} stocks with volume")
        
        # Identify issues
        issues = []
        if today_data[0] == 0:
            issues.append("❌ No price data for today")
        if obv_data[0] == 0:
            issues.append("❌ No OBV data in last 7 days")
        if volume_data[0] == 0:
            issues.append("❌ No volume data in last 7 days")
        
        if issues:
            print("\n🚨 IDENTIFIED ISSUES:")
            for issue in issues:
                print(f"   {issue}")
    
    if fundamentals_data:
        fundamentals = fundamentals_data['fundamentals']
        recent_fundamentals = fundamentals_data['recent_fundamentals']
        
        print(f"\n💰 Fundamentals: {fundamentals[0]} companies total")
        print(f"📅 Recently updated: {recent_fundamentals[0]} companies")
        
        if recent_fundamentals[0] == 0:
            print("❌ No fundamental data updated in last 7 days")
    
    print("\n🔧 RECOMMENDATIONS:")
    print("-" * 30)
    
    recommendations = []
    
    if daily_charts_data and daily_charts_data['today_data'][0] == 0:
        recommendations.append("1. 🔄 Run price update process - no data for today")
    
    if daily_charts_data and daily_charts_data['obv_data'][0] == 0:
        recommendations.append("2. 🔧 Check OBV calculation - no OBV data found")
    
    if daily_charts_data and daily_charts_data['volume_data'][0] == 0:
        recommendations.append("3. 🔧 Check volume data collection - no volume data found")
    
    if fundamentals_data and fundamentals_data['recent_fundamentals'][0] == 0:
        recommendations.append("4. 🔄 Run fundamental update process - no recent updates")
    
    if not recommendations:
        recommendations.append("✅ All systems appear to be working correctly")
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print("\n📋 NEXT STEPS:")
    print("-" * 30)
    print("1. Check the cron job logs for any errors")
    print("2. Verify API keys and rate limits")
    print("3. Run manual price update if needed")
    print("4. Run manual fundamental update if needed")
    print("5. Check if today was actually a trading day")

def main():
    """Main analysis function"""
    print("🚀 STARTING COMPREHENSIVE DATABASE ANALYSIS")
    print(f"⏰ Analysis started at: {datetime.now()}")
    
    # Run all analyses
    daily_charts_data = analyze_daily_charts()
    fundamentals_data = analyze_fundamentals()
    trading_days_data = analyze_trading_days()
    
    # Generate recommendations
    generate_recommendations(daily_charts_data, fundamentals_data, trading_days_data)
    
    print(f"\n✅ Analysis completed at: {datetime.now()}")

if __name__ == "__main__":
    main() 