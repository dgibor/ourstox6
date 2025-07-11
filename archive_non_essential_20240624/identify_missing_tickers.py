#!/usr/bin/env python3
"""
Identify Missing Fundamental Data Tickers
Clean identification of tickers missing fundamental data
"""

from database import DatabaseManager
from datetime import datetime, timedelta

def identify_missing_tickers():
    """Identify tickers missing fundamental data"""
    db = DatabaseManager()
    
    try:
        # Get tickers with no fundamental data at all
        no_fundamentals_query = """
            SELECT DISTINCT s.ticker, s.company_name, s.market_cap, s.sector, s.industry
            FROM stocks s
            LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE s.ticker IS NOT NULL 
            AND s.market_cap IS NOT NULL 
            AND s.market_cap > 0
            AND cf.ticker IS NULL
            ORDER BY s.market_cap DESC
        """
        no_fundamentals_result = db.execute_query(no_fundamentals_query)
        
        # Get tickers with incomplete fundamental data
        incomplete_fundamentals_query = """
            SELECT DISTINCT s.ticker, s.company_name, s.market_cap, s.sector, s.industry
            FROM stocks s
            INNER JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE s.ticker IS NOT NULL 
            AND s.market_cap IS NOT NULL 
            AND s.market_cap > 0
            AND (cf.revenue IS NULL OR cf.revenue = 0 OR
                 cf.total_assets IS NULL OR cf.total_assets = 0 OR
                 cf.total_equity IS NULL OR cf.total_equity = 0 OR
                 cf.shares_outstanding IS NULL OR cf.shares_outstanding = 0)
            ORDER BY s.market_cap DESC
        """
        incomplete_fundamentals_result = db.execute_query(incomplete_fundamentals_query)
        
        # Get tickers with stale data (older than 7 days)
        stale_data_query = """
            SELECT DISTINCT s.ticker, s.company_name, s.market_cap, s.sector, s.industry
            FROM stocks s
            INNER JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE s.ticker IS NOT NULL 
            AND s.market_cap IS NOT NULL 
            AND s.market_cap > 0
            AND cf.last_updated < %s
            ORDER BY s.market_cap DESC
        """
        cutoff_date = datetime.now() - timedelta(days=7)
        stale_data_result = db.execute_query(stale_data_query, (cutoff_date,))
        
        # Combine and deduplicate results
        all_missing = {}
        
        # Add no fundamentals
        for row in no_fundamentals_result:
            ticker = row[0]
            if ticker not in all_missing:
                all_missing[ticker] = {
                    'ticker': row[0],
                    'company_name': row[1],
                    'market_cap': row[2],
                    'sector': row[3],
                    'industry': row[4],
                    'reason': 'No fundamental data'
                }
        
        # Add incomplete fundamentals
        for row in incomplete_fundamentals_result:
            ticker = row[0]
            if ticker not in all_missing:
                all_missing[ticker] = {
                    'ticker': row[0],
                    'company_name': row[1],
                    'market_cap': row[2],
                    'sector': row[3],
                    'industry': row[4],
                    'reason': 'Incomplete fundamental data'
                }
        
        # Add stale data
        for row in stale_data_result:
            ticker = row[0]
            if ticker not in all_missing:
                all_missing[ticker] = {
                    'ticker': row[0],
                    'company_name': row[1],
                    'market_cap': row[2],
                    'sector': row[3],
                    'industry': row[4],
                    'reason': 'Stale data (>7 days)'
                }
        
        # Convert to list and sort by market cap
        missing_list = list(all_missing.values())
        missing_list.sort(key=lambda x: x['market_cap'], reverse=True)
        
        return missing_list
        
    except Exception as e:
        print(f"Error identifying missing tickers: {e}")
        return []

def main():
    """Main function"""
    print("🔍 Identifying Missing Fundamental Data Tickers")
    print("=" * 60)
    
    missing_tickers = identify_missing_tickers()
    
    if not missing_tickers:
        print("✅ No tickers missing fundamental data!")
        return
    
    print(f"📊 Found {len(missing_tickers)} tickers missing fundamental data")
    print()
    
    # Show top 25 by market cap
    print("📈 TOP 25 MISSING TICKERS BY MARKET CAP:")
    print("=" * 60)
    
    for i, ticker_info in enumerate(missing_tickers[:25]):
        market_cap_b = ticker_info['market_cap'] / 1_000_000_000
        print(f"{i+1:2d}. {ticker_info['ticker']:6s} - ${market_cap_b:8.1f}B - {ticker_info['company_name']}")
        print(f"     Sector: {ticker_info['sector']}")
        print(f"     Industry: {ticker_info['industry']}")
        print(f"     Reason: {ticker_info['reason']}")
        print()
    
    # Show summary by reason
    print("📋 SUMMARY BY REASON:")
    print("=" * 60)
    
    reasons = {}
    for ticker_info in missing_tickers:
        reason = ticker_info['reason']
        if reason not in reasons:
            reasons[reason] = []
        reasons[reason].append(ticker_info)
    
    for reason, tickers in reasons.items():
        total_market_cap = sum(t['market_cap'] for t in tickers)
        market_cap_b = total_market_cap / 1_000_000_000
        print(f"{reason}: {len(tickers)} tickers (${market_cap_b:.1f}B total market cap)")
    
    print()
    
    # Show market cap distribution
    print("💰 MARKET CAP DISTRIBUTION:")
    print("=" * 60)
    
    large_cap = [t for t in missing_tickers if t['market_cap'] >= 10_000_000_000]  # $10B+
    mid_cap = [t for t in missing_tickers if 1_000_000_000 <= t['market_cap'] < 10_000_000_000]  # $1B-$10B
    small_cap = [t for t in missing_tickers if t['market_cap'] < 1_000_000_000]  # <$1B
    
    print(f"Large Cap ($10B+): {len(large_cap)} tickers")
    print(f"Mid Cap ($1B-$10B): {len(mid_cap)} tickers")
    print(f"Small Cap (<$1B): {len(small_cap)} tickers")
    
    print()
    
    # Provide SQL queries for checking
    print("📋 SQL QUERIES FOR DATABASE CHECKING:")
    print("=" * 60)
    
    # Top 25 tickers for checking
    top_25_tickers = [t['ticker'] for t in missing_tickers[:25]]
    ticker_list = "', '".join(top_25_tickers)
    
    print("Check these tickers in stocks table:")
    print(f"SELECT ticker, company_name, market_cap FROM stocks WHERE ticker IN ('{ticker_list}') ORDER BY market_cap DESC;")
    print()
    
    print("Check fundamental data for these tickers:")
    print(f"SELECT ticker, revenue, net_income, total_assets, total_equity, last_updated FROM company_fundamentals WHERE ticker IN ('{ticker_list}') ORDER BY ticker;")
    print()
    
    # Show recommendation
    print("💡 RECOMMENDATION:")
    print("=" * 60)
    print(f"Start with the top {min(25, len(missing_tickers))} largest companies by market cap.")
    print("These represent the highest priority for fundamental data filling.")
    print()
    print("Top 10 tickers to prioritize:")
    for i, ticker_info in enumerate(missing_tickers[:10]):
        market_cap_b = ticker_info['market_cap'] / 1_000_000_000
        print(f"  {i+1:2d}. {ticker_info['ticker']} (${market_cap_b:.1f}B)")

if __name__ == "__main__":
    main() 