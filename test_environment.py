#!/usr/bin/env python3
"""
Quick Environment Test Script

Run this after setting environment variables to verify they're working.
"""

import os
import sys

def test_environment():
    """Test if environment variables are properly set"""
    print("🔍 TESTING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    # Critical variables
    critical_vars = {
        'DB_HOST': 'Database Host',
        'DB_NAME': 'Database Name', 
        'DB_USER': 'Database User',
        'DB_PASSWORD': 'Database Password',
        'DB_PORT': 'Database Port',
        'FMP_API_KEY': 'FMP API Key',
        'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage API Key',
        'FINNHUB_API_KEY': 'Finnhub API Key'
    }
    
    all_set = True
    
    for var, description in critical_vars.items():
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'KEY' in var:
                print(f"✅ {description}: {'*' * min(len(value), 8)}...")
            else:
                print(f"✅ {description}: {value}")
        else:
            print(f"❌ {description}: NOT SET")
            all_set = False
    
    print("\n" + "=" * 50)
    
    if all_set:
        print("🎉 ALL ENVIRONMENT VARIABLES ARE SET!")
        print("✅ Your cron job should work now.")
        
        # Test database connection
        print("\n🔍 TESTING DATABASE CONNECTION...")
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'),
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stocks;")
            count = cursor.fetchone()
            print(f"✅ Database connected! Found {count[0]} stocks.")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            
    else:
        print("❌ MISSING ENVIRONMENT VARIABLES")
        print("Please set all required variables in Railway dashboard.")
    
    return all_set

if __name__ == "__main__":
    test_environment() 