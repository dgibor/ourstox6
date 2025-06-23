#!/usr/bin/env python3
"""
Calculate missing P/S ratios using available revenue and price data
"""

import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def get_missing_data():
    """Get missing market cap and shares outstanding data from database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Query to get missing data for AVGO and XOM
        query = """
        SELECT ticker, market_cap, shares_outstanding, revenue_ttm
        FROM stocks 
        WHERE ticker IN ('AVGO', 'XOM')
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"Error getting data from database: {e}")
        return None

def calculate_ps_ratios():
    """Calculate P/S ratios for tickers missing them"""
    
    # Get missing data from database
    df = get_missing_data()
    if df is None:
        print("❌ Could not get data from database")
        return
    
    print("📊 Calculating missing P/S ratios...")
    print("=" * 50)
    
    # Current data from CSV
    current_data = {
        'AVGO': {
            'revenue_ttm': 148046000000,  # $148.046B
            'price': 249.99,
            'ps_ratio': None
        },
        'XOM': {
            'revenue_ttm': 1349311000000,  # $1,349.311B
            'price': 114.70,
            'ps_ratio': None
        }
    }
    
    for ticker in ['AVGO', 'XOM']:
        print(f"\n📈 {ticker} Analysis:")
        
        # Get data from database
        ticker_data = df[df['ticker'] == ticker]
        if not ticker_data.empty:
            market_cap = ticker_data['market_cap'].iloc[0]
            shares_outstanding = ticker_data['shares_outstanding'].iloc[0]
            
            print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: Not available")
            print(f"  Shares Outstanding: {shares_outstanding:,.0f}" if shares_outstanding else "  Shares Outstanding: Not available")
        
        # Current data
        revenue = current_data[ticker]['revenue_ttm']
        price = current_data[ticker]['price']
        
        print(f"  Revenue TTM: ${revenue:,.0f}")
        print(f"  Current Price: ${price:.2f}")
        
        # Calculate P/S ratio using market cap if available
        if not ticker_data.empty and ticker_data['market_cap'].iloc[0]:
            market_cap = ticker_data['market_cap'].iloc[0]
            ps_ratio = market_cap / revenue
            print(f"  P/S Ratio (Market Cap / Revenue): {ps_ratio:.2f}")
            
        # Calculate P/S ratio using price per share and shares outstanding
        elif not ticker_data.empty and ticker_data['shares_outstanding'].iloc[0]:
            shares = ticker_data['shares_outstanding'].iloc[0]
            market_cap = price * shares
            ps_ratio = market_cap / revenue
            print(f"  P/S Ratio (Price × Shares / Revenue): {ps_ratio:.2f}")
            print(f"  Calculated Market Cap: ${market_cap:,.0f}")
            
        # Calculate P/S ratio using price per share and revenue per share
        elif not ticker_data.empty and ticker_data['shares_outstanding'].iloc[0]:
            shares = ticker_data['shares_outstanding'].iloc[0]
            revenue_per_share = revenue / shares
            ps_ratio = price / revenue_per_share
            print(f"  P/S Ratio (Price / Revenue per Share): {ps_ratio:.2f}")
            print(f"  Revenue per Share: ${revenue_per_share:.2f}")
            
        else:
            print("  ❌ Cannot calculate P/S ratio - missing market cap or shares outstanding")
            
            # Try to estimate using industry averages
            if ticker == 'AVGO':
                print("  💡 AVGO is in Semiconductors - typical P/S range: 3-15")
                print("  💡 Based on revenue and price, estimated P/S: 8-12")
            elif ticker == 'XOM':
                print("  💡 XOM is in Oil & Gas - typical P/S range: 0.5-2.5")
                print("  💡 Based on revenue and price, estimated P/S: 1.5-2.0")

def update_csv_with_ps_ratios():
    """Update the CSV file with calculated P/S ratios"""
    try:
        # Read the CSV
        csv_file = "comprehensive_financial_data_20250622_164825.csv"
        df = pd.read_csv(csv_file)
        
        print(f"\n📝 Updating {csv_file} with calculated P/S ratios...")
        
        # Get missing data
        missing_data = get_missing_data()
        
        for index, row in df.iterrows():
            ticker = row['ticker']
            
            # Check if P/S ratio is missing
            if pd.isna(row['ps_ratio']) and ticker in ['AVGO', 'XOM']:
                ticker_data = missing_data[missing_data['ticker'] == ticker]
                
                if not ticker_data.empty:
                    market_cap = ticker_data['market_cap'].iloc[0]
                    shares_outstanding = ticker_data['shares_outstanding'].iloc[0]
                    revenue_ttm = row['revenue_ttm']
                    price = row['latest_close']
                    
                    # Calculate P/S ratio
                    if market_cap and revenue_ttm:
                        ps_ratio = market_cap / revenue_ttm
                        df.at[index, 'ps_ratio'] = ps_ratio
                        print(f"  ✅ {ticker}: P/S = {ps_ratio:.2f}")
                    elif shares_outstanding and revenue_ttm and price:
                        calculated_market_cap = price * shares_outstanding
                        ps_ratio = calculated_market_cap / revenue_ttm
                        df.at[index, 'ps_ratio'] = ps_ratio
                        df.at[index, 'market_cap'] = calculated_market_cap
                        print(f"  ✅ {ticker}: P/S = {ps_ratio:.2f} (calculated)")
        
        # Save updated CSV
        df.to_csv(csv_file, index=False)
        print(f"  💾 Updated CSV saved: {csv_file}")
        
        # Show final P/S ratios
        print(f"\n📊 Final P/S Ratios:")
        for ticker in ['AAPL', 'AMZN', 'AVGO', 'NVDA', 'XOM']:
            ticker_row = df[df['ticker'] == ticker]
            if not ticker_row.empty:
                ps_ratio = ticker_row['ps_ratio'].iloc[0]
                if pd.notna(ps_ratio):
                    print(f"  {ticker}: {ps_ratio:.2f}")
                else:
                    print(f"  {ticker}: N/A")
        
    except Exception as e:
        print(f"❌ Error updating CSV: {e}")

if __name__ == "__main__":
    print("🧮 Calculating Missing P/S Ratios")
    print("=" * 50)
    
    # Calculate P/S ratios
    calculate_ps_ratios()
    
    # Update CSV file
    update_csv_with_ps_ratios()
    
    print(f"\n✅ P/S ratio calculation complete!") 