#!/usr/bin/env python3
"""
Top 25 Tickers by Market Cap
List the top 25 companies by market cap for database checking
"""

from database import DatabaseManager

def get_top_25_tickers():
    """Get top 25 tickers by market cap"""
    db = DatabaseManager()
    
    try:
        # Get top 25 tickers by market cap
        query = """
            SELECT ticker, company_name, market_cap, sector, industry
            FROM stocks 
            WHERE ticker IS NOT NULL 
            AND market_cap IS NOT NULL 
            AND market_cap > 0
            ORDER BY market_cap DESC
            LIMIT 25
        """
        result = db.execute_query(query)
        
        print("📊 TOP 25 COMPANIES BY MARKET CAP")
        print("=" * 60)
        print("These are the tickers we attempted to process:")
        print()
        
        tickers = []
        for i, row in enumerate(result):
            ticker_info = {
                'rank': i + 1,
                'ticker': row[0],
                'company_name': row[1],
                'market_cap': row[2],
                'sector': row[3],
                'industry': row[4]
            }
            tickers.append(ticker_info)
            
            market_cap_b = ticker_info['market_cap'] / 1_000_000_000
            print(f"{i+1:2d}. {ticker_info['ticker']:6s} - ${market_cap_b:8.1f}B - {ticker_info['company_name']}")
            print(f"     Sector: {ticker_info['sector']}")
            print(f"     Industry: {ticker_info['industry']}")
            print()
        
        # Check fundamental data status for these tickers
        print("🔍 FUNDAMENTAL DATA STATUS")
        print("=" * 60)
        
        for ticker_info in tickers:
            ticker = ticker_info['ticker']
            
            # Check if fundamental data exists
            fundamental_query = """
                SELECT ticker, revenue, net_income, total_assets, total_equity, 
                       shares_outstanding, price_to_earnings, price_to_book, 
                       return_on_equity, last_updated
                FROM company_fundamentals 
                WHERE ticker = %s
            """
            fundamental_result = db.execute_query(fundamental_query, (ticker,))
            
            if fundamental_result:
                data = fundamental_result[0]
                print(f"✅ {ticker:6s} - HAS FUNDAMENTAL DATA")
                print(f"    Revenue: {data[1] if data[1] else 'N/A'}")
                print(f"    Net Income: {data[2] if data[2] else 'N/A'}")
                print(f"    Total Assets: {data[3] if data[3] else 'N/A'}")
                print(f"    Total Equity: {data[4] if data[4] else 'N/A'}")
                print(f"    Shares Outstanding: {data[5] if data[5] else 'N/A'}")
                print(f"    P/E Ratio: {data[6] if data[6] else 'N/A'}")
                print(f"    P/B Ratio: {data[7] if data[7] else 'N/A'}")
                print(f"    ROE: {data[8] if data[8] else 'N/A'}")
                print(f"    Last Updated: {data[9] if data[9] else 'N/A'}")
            else:
                print(f"❌ {ticker:6s} - NO FUNDAMENTAL DATA")
            
            print()
        
        return tickers
        
    except Exception as e:
        print(f"Error getting tickers: {e}")
        return []

def main():
    """Main function"""
    tickers = get_top_25_tickers()
    
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"Total tickers checked: {len(tickers)}")
    print()
    print("To check these tickers in your database, you can run:")
    print("SELECT ticker, company_name, market_cap FROM stocks WHERE ticker IN (")
    ticker_list = [f"'{t['ticker']}'" for t in tickers]
    print(", ".join(ticker_list))
    print(") ORDER BY market_cap DESC;")
    print()
    print("To check fundamental data:")
    print("SELECT ticker, revenue, net_income, total_assets, total_equity, last_updated")
    print("FROM company_fundamentals WHERE ticker IN (")
    print(", ".join(ticker_list))
    print(") ORDER BY ticker;")

if __name__ == "__main__":
    main() 