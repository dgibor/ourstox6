#!/usr/bin/env python3
"""
Check Remaining Companies
Analyze remaining companies that need fundamental data and show their market caps
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from datetime import datetime
import pandas as pd

def check_remaining_companies():
    """Check remaining companies that need fundamental data"""
    db = DatabaseManager()
    
    print("🔍 CHECKING REMAINING COMPANIES")
    print("=" * 60)
    
    try:
        # Get current coverage
        total_query = "SELECT COUNT(*) FROM stocks"
        total_result = db.fetch_one(total_query)
        total_stocks = total_result[0] if total_result else 0
        
        complete_query = """
        SELECT COUNT(DISTINCT ticker) FROM company_fundamentals 
        WHERE revenue IS NOT NULL 
        AND net_income IS NOT NULL 
        AND shares_outstanding IS NOT NULL
        """
        complete_result = db.fetch_one(complete_query)
        complete_count = complete_result[0] if complete_result else 0
        
        coverage = (complete_count / total_stocks * 100) if total_stocks > 0 else 0
        
        print(f"📊 CURRENT COVERAGE:")
        print(f"   Total stocks: {total_stocks}")
        print(f"   Complete fundamentals: {complete_count}")
        print(f"   Coverage: {coverage:.1f}%")
        print(f"   Remaining: {total_stocks - complete_count}")
        
        # Get remaining companies that need processing
        remaining_query = """
        SELECT s.ticker, s.company_name, s.market_cap, s.sector, s.industry
        FROM stocks s
        LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
        WHERE cf.ticker IS NULL 
           OR cf.revenue IS NULL 
           OR cf.net_income IS NULL 
           OR cf.shares_outstanding IS NULL
        ORDER BY s.market_cap DESC NULLS LAST
        """
        
        remaining_result = db.execute_query(remaining_query)
        
        if not remaining_result:
            print(f"\n🎉 ALL COMPANIES HAVE COMPLETE FUNDAMENTALS!")
            return
        
        print(f"\n📋 REMAINING COMPANIES ({len(remaining_result)} total):")
        print("=" * 80)
        
        # Create data for table
        companies_data = []
        for row in remaining_result:
            ticker, company_name, market_cap, sector, industry = row
            
            # Format market cap
            if market_cap:
                # Convert decimal to float for calculations
                market_cap_float = float(market_cap)
                if market_cap_float >= 1e12:  # Trillion
                    market_cap_str = f"${market_cap_float/1e12:.2f}T"
                elif market_cap_float >= 1e9:  # Billion
                    market_cap_str = f"${market_cap_float/1e9:.2f}B"
                elif market_cap_float >= 1e6:  # Million
                    market_cap_str = f"${market_cap_float/1e6:.2f}M"
                else:
                    market_cap_str = f"${market_cap_float:,.0f}"
            else:
                market_cap_str = "N/A"
            
            companies_data.append({
                'Ticker': ticker,
                'Company Name': company_name or 'N/A',
                'Market Cap': market_cap_str,
                'Sector': sector or 'N/A',
                'Industry': industry or 'N/A'
            })
        
        # Create and display table
        df = pd.DataFrame(companies_data)
        
        # Display table with better formatting
        print(f"{'Ticker':<8} {'Market Cap':<12} {'Company Name':<30} {'Sector':<20}")
        print("-" * 80)
        
        for _, row in df.iterrows():
            ticker = row['Ticker'][:7]  # Truncate if too long
            market_cap = row['Market Cap']
            company_name = (row['Company Name'][:27] + '...') if len(row['Company Name']) > 30 else row['Company Name']
            sector = (row['Sector'][:17] + '...') if len(row['Sector']) > 20 else row['Sector']
            
            print(f"{ticker:<8} {market_cap:<12} {company_name:<30} {sector:<20}")
        
        # Show summary by market cap ranges
        print(f"\n📈 MARKET CAP BREAKDOWN:")
        print("-" * 40)
        
        market_cap_ranges = {
            'Large Cap (>$10B)': 0,
            'Mid Cap ($2B-$10B)': 0,
            'Small Cap ($300M-$2B)': 0,
            'Micro Cap (<$300M)': 0,
            'Unknown': 0
        }
        
        for row in remaining_result:
            market_cap = row[2]
            if not market_cap:
                market_cap_ranges['Unknown'] += 1
            else:
                market_cap_float = float(market_cap)
                if market_cap_float >= 10e9:
                    market_cap_ranges['Large Cap (>$10B)'] += 1
                elif market_cap_float >= 2e9:
                    market_cap_ranges['Mid Cap ($2B-$10B)'] += 1
                elif market_cap_float >= 300e6:
                    market_cap_ranges['Small Cap ($300M-$2B)'] += 1
                else:
                    market_cap_ranges['Micro Cap (<$300M)'] += 1
        
        for range_name, count in market_cap_ranges.items():
            if count > 0:
                print(f"   {range_name}: {count}")
        
        # Show top 10 by market cap
        print(f"\n🏆 TOP 10 REMAINING BY MARKET CAP:")
        print("-" * 50)
        
        top_10 = [row for row in remaining_result if row[2] is not None][:10]
        for i, (ticker, company_name, market_cap, sector, industry) in enumerate(top_10, 1):
            market_cap_float = float(market_cap)
            if market_cap_float >= 1e12:
                market_cap_str = f"${market_cap_float/1e12:.2f}T"
            elif market_cap_float >= 1e9:
                market_cap_str = f"${market_cap_float/1e9:.2f}B"
            else:
                market_cap_str = f"${market_cap_float/1e6:.2f}M"
            
            company_display = company_name[:25] + '...' if len(company_name) > 28 else company_name
            print(f"   {i:2d}. {ticker:<6} {market_cap_str:<10} {company_display}")
        
        # Save to CSV for reference
        csv_filename = f"remaining_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"\n💾 Data saved to: {csv_filename}")
        
        return companies_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def try_process_remaining():
    """Try to process some of the remaining companies"""
    print(f"\n🔄 ATTEMPTING TO PROCESS REMAINING COMPANIES")
    print("=" * 60)
    
    db = DatabaseManager()
    
    try:
        # Get top 20 remaining by market cap
        top_remaining_query = """
        SELECT s.ticker, s.company_name, s.market_cap
        FROM stocks s
        LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
        WHERE cf.ticker IS NULL 
           OR cf.revenue IS NULL 
           OR cf.net_income IS NULL 
           OR cf.shares_outstanding IS NULL
        ORDER BY s.market_cap DESC NULLS LAST
        LIMIT 20
        """
        
        top_remaining = db.execute_query(top_remaining_query)
        
        if not top_remaining:
            print("No remaining companies to process!")
            return
        
        print(f"Processing top {len(top_remaining)} remaining companies...")
        
        # Import FMP service
        from fmp_service import FMPService
        fmp = FMPService()
        
        success_count = 0
        for i, (ticker, company_name, market_cap) in enumerate(top_remaining, 1):
            print(f"\n[{i}/{len(top_remaining)}] Processing {ticker}...")
            
            try:
                # Try to fetch data
                financial_data = fmp.fetch_financial_statements(ticker)
                key_stats = fmp.fetch_key_statistics(ticker)
                
                if financial_data and key_stats:
                    success = fmp.store_fundamental_data(ticker, financial_data, key_stats)
                    if success:
                        print(f"  ✅ {ticker}: Success")
                        success_count += 1
                    else:
                        print(f"  ❌ {ticker}: Failed to store")
                else:
                    print(f"  ❌ {ticker}: No data available")
                
                # Rate limiting
                import time
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ {ticker}: Error - {str(e)}")
                continue
        
        print(f"\n📊 PROCESSING RESULTS:")
        print(f"   Attempted: {len(top_remaining)}")
        print(f"   Successful: {success_count}")
        print(f"   Success rate: {success_count/len(top_remaining)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")

if __name__ == "__main__":
    # Check remaining companies
    remaining_data = check_remaining_companies()
    
    # Ask if user wants to try processing
    if remaining_data:
        print(f"\n" + "=" * 60)
        response = input("Would you like to try processing some of the remaining companies? (y/n): ")
        if response.lower() in ['y', 'yes']:
            try_process_remaining()
    
    print(f"\n✅ Analysis complete!") 