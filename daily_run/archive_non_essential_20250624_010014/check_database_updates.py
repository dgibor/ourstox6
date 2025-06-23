#!/usr/bin/env python3
"""
Check database updates to see which tables and stocks were modified
"""

from database import DatabaseManager
import datetime

def check_recent_updates():
    """Check recent database updates"""
    print("Database Update Check")
    print("=" * 50)
    
    db = DatabaseManager()
    db.connect()
    
    # First, let's see what tables exist
    print("\n0. Available Tables:")
    print("-" * 40)
    
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print("Available tables:")
            for row in results:
                print(f"  - {row[0]}")
        else:
            print("No tables found")
    except Exception as e:
        print(f"Error checking tables: {e}")
    
    # Check stocks table for recent price updates
    print("\n1. Recent Price Updates in 'stocks' table:")
    print("-" * 40)
    
    query = """
    SELECT ticker, close, volume, date, updated_at 
    FROM stocks 
    WHERE updated_at >= NOW() - INTERVAL '1 hour'
    ORDER BY updated_at DESC
    LIMIT 20
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print(f"Found {len(results)} recent updates:")
            for row in results:
                ticker, close, volume, date, updated_at = row
                print(f"  {ticker}: ${close/100:.2f} | Vol: {volume:,} | Date: {date} | Updated: {updated_at}")
        else:
            print("No recent updates found in stocks table")
    except Exception as e:
        print(f"Error querying stocks table: {e}")
    
    # Check daily_charts table for recent updates
    print("\n2. Recent Updates in 'daily_charts' table:")
    print("-" * 40)
    
    query = """
    SELECT ticker, close, volume, date, created_at 
    FROM daily_charts 
    WHERE created_at >= NOW() - INTERVAL '1 hour'
    ORDER BY created_at DESC
    LIMIT 20
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print(f"Found {len(results)} recent updates:")
            for row in results:
                ticker, close, volume, date, created_at = row
                print(f"  {ticker}: ${close/100:.2f} | Vol: {volume:,} | Date: {date} | Created: {created_at}")
        else:
            print("No recent updates found in daily_charts table")
    except Exception as e:
        print(f"Error querying daily_charts table: {e}")
    
    # Check financial_ratios table for recent updates
    print("\n3. Recent Updates in 'financial_ratios' table:")
    print("-" * 40)
    
    query = """
    SELECT ticker, pe_ratio, pb_ratio, ps_ratio, debt_to_equity, updated_at 
    FROM financial_ratios 
    WHERE updated_at >= NOW() - INTERVAL '1 hour'
    ORDER BY updated_at DESC
    LIMIT 20
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print(f"Found {len(results)} recent updates:")
            for row in results:
                ticker, pe, pb, ps, debt_eq, updated_at = row
                print(f"  {ticker}: P/E: {pe:.2f} | P/B: {pb:.2f} | P/S: {ps:.2f} | D/E: {debt_eq:.2f} | Updated: {updated_at}")
        else:
            print("No recent updates found in financial_ratios table")
    except Exception as e:
        print(f"Error querying financial_ratios table: {e}")
    
    # Check fundamentals table for recent updates
    print("\n4. Recent Updates in 'fundamentals' table:")
    print("-" * 40)
    
    query = """
    SELECT ticker, market_cap, revenue, net_income, total_debt, updated_at 
    FROM fundamentals 
    WHERE updated_at >= NOW() - INTERVAL 1 HOUR
    ORDER BY updated_at DESC
    LIMIT 20
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print(f"Found {len(results)} recent updates:")
            for row in results:
                ticker, market_cap, revenue, net_income, total_debt, updated_at = row
                print(f"  {ticker}: MC: ${market_cap/1e9:.1f}B | Rev: ${revenue/1e9:.1f}B | NI: ${net_income/1e9:.1f}B | Updated: {updated_at}")
        else:
            print("No recent updates found in fundamentals table")
    except Exception as e:
        print(f"Error querying fundamentals table: {e}")
    
    # Summary of all tables
    print("\n5. Table Summary:")
    print("-" * 40)
    
    tables = ['stocks', 'daily_charts', 'financial_ratios', 'fundamentals']
    for table in tables:
        try:
            count_query = f"SELECT COUNT(*) FROM {table}"
            result = db.execute_query(count_query)
            total_count = result[0][0] if result else 0
            
            recent_query = f"SELECT COUNT(*) FROM {table} WHERE updated_at >= NOW() - INTERVAL '1 hour'"
            result = db.execute_query(recent_query)
            recent_count = result[0][0] if result else 0
            
            print(f"  {table}: {total_count} total records, {recent_count} updated in last hour")
        except Exception as e:
            print(f"  {table}: Error checking - {e}")
    
    db.disconnect()
    
    print(f"\n{'='*50}")
    print("Database Check Complete")
    print(f"{'='*50}")

if __name__ == "__main__":
    check_recent_updates() 