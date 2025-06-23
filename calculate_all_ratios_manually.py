#!/usr/bin/env python3
"""
Calculate all financial ratios manually using basic fundamental data
"""

import os
import psycopg2
import pandas as pd
import requests
import time
from typing import Dict, Optional
from dotenv import load_dotenv
from datetime import datetime

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

# FMP API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def store_data_in_database(data: Dict, ratios: Dict):
    """Store calculated data in the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Update stocks table with fundamental data
        cur.execute("""
            UPDATE stocks 
            SET market_cap = %s,
                shares_outstanding = %s,
                revenue_ttm = %s,
                net_income_ttm = %s,
                ebitda_ttm = %s,
                total_debt = %s,
                shareholders_equity = %s,
                cash_and_equivalents = %s,
                diluted_eps_ttm = %s,
                book_value_per_share = %s,
                fundamentals_last_update = %s
            WHERE ticker = %s
        """, (
            data['market_cap'],
            data['shares_outstanding'],
            data['revenue_ttm'],
            data['net_income_ttm'],
            data['ebitda_ttm'],
            data['total_debt'],
            data['total_equity'],
            data['cash'],
            ratios['eps_ttm'],
            ratios['book_value_per_share'],
            datetime.now(),
            data['ticker']
        ))
        
        # Store ratios in financial_ratios table
        cur.execute("""
            INSERT INTO financial_ratios 
            (ticker, calculation_date, pe_ratio, pb_ratio, ps_ratio, ev_ebitda, graham_number, enterprise_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, calculation_date)
            DO UPDATE SET
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                ps_ratio = EXCLUDED.ps_ratio,
                ev_ebitda = EXCLUDED.ev_ebitda,
                graham_number = EXCLUDED.graham_number,
                enterprise_value = EXCLUDED.enterprise_value
        """, (
            data['ticker'],
            datetime.now().date(),
            ratios['pe_ratio'],
            ratios['pb_ratio'],
            ratios['ps_ratio'],
            ratios['ev_ebitda'],
            ratios['graham_number'],
            ratios['enterprise_value']
        ))
        
        conn.commit()
        print(f"    💾 Data stored in database for {data['ticker']}")
        return True
        
    except Exception as e:
        print(f"    ❌ Database storage error for {data['ticker']}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def fetch_basic_data_from_fmp(ticker: str) -> Optional[Dict]:
    """Fetch basic fundamental data from FMP API"""
    try:
        # Fetch company profile for market data
        profile_url = f"{FMP_BASE_URL}/profile/{ticker}"
        params = {'apikey': FMP_API_KEY}
        
        response = requests.get(profile_url, params=params, timeout=30)
        if response.status_code == 200:
            profile_data = response.json()
            
            # Handle list response
            if isinstance(profile_data, list) and len(profile_data) > 0:
                profile_data = profile_data[0]
            
            if profile_data and isinstance(profile_data, dict):
                # Get market data
                market_cap = float(profile_data.get('mktCap', 0))
                shares_outstanding = float(profile_data.get('sharesOutstanding', 0))
                current_price = float(profile_data.get('price', 0))
                
                # If shares outstanding is 0, try to calculate it from market cap and price
                if shares_outstanding == 0 and market_cap > 0 and current_price > 0:
                    shares_outstanding = market_cap / current_price
                    print(f"    Calculated shares outstanding: {shares_outstanding:,.0f}")
                
                # Fetch income statement for TTM data
                income_url = f"{FMP_BASE_URL}/income-statement/{ticker}"
                income_params = {'apikey': FMP_API_KEY, 'limit': 4}
                
                income_response = requests.get(income_url, params=income_params, timeout=30)
                if income_response.status_code == 200:
                    income_data = income_response.json()
                    
                    # Fetch balance sheet
                    balance_url = f"{FMP_BASE_URL}/balance-sheet-statement/{ticker}"
                    balance_response = requests.get(balance_url, params=income_params, timeout=30)
                    balance_data = balance_response.json() if balance_response.status_code == 200 else []
                    
                    # Calculate TTM from last 4 quarters
                    ttm_revenue = sum(float(q.get('revenue', 0)) for q in income_data[:4] if q.get('revenue'))
                    ttm_net_income = sum(float(q.get('netIncome', 0)) for q in income_data[:4] if q.get('netIncome'))
                    ttm_ebitda = sum(float(q.get('ebitda', 0)) for q in income_data[:4] if q.get('ebitda'))
                    
                    # Get latest balance sheet data
                    total_debt = float(balance_data[0].get('totalDebt', 0)) if balance_data else 0
                    total_equity = float(balance_data[0].get('totalStockholdersEquity', 0)) if balance_data else 0
                    cash = float(balance_data[0].get('cashAndCashEquivalents', 0)) if balance_data else 0
                    
                    return {
                        'ticker': ticker,
                        'market_cap': market_cap,
                        'shares_outstanding': shares_outstanding,
                        'current_price': current_price,
                        'revenue_ttm': ttm_revenue,
                        'net_income_ttm': ttm_net_income,
                        'ebitda_ttm': ttm_ebitda,
                        'total_debt': total_debt,
                        'total_equity': total_equity,
                        'cash': cash
                    }
        
        return None
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def calculate_ratios(data: Dict) -> Dict:
    """Calculate all financial ratios from basic data"""
    ratios = {}
    
    # Extract data
    market_cap = data.get('market_cap', 0)
    shares_outstanding = data.get('shares_outstanding', 0)
    current_price = data.get('current_price', 0)
    revenue_ttm = data.get('revenue_ttm', 0)
    net_income_ttm = data.get('net_income_ttm', 0)
    ebitda_ttm = data.get('ebitda_ttm', 0)
    total_debt = data.get('total_debt', 0)
    total_equity = data.get('total_equity', 0)
    cash = data.get('cash', 0)
    
    # Calculate EPS
    eps_ttm = net_income_ttm / shares_outstanding if shares_outstanding > 0 else 0
    
    # Calculate Book Value per Share
    book_value_per_share = total_equity / shares_outstanding if shares_outstanding > 0 else 0
    
    # 1. P/E Ratio = Price / EPS
    if eps_ttm > 0:
        ratios['pe_ratio'] = current_price / eps_ttm
    else:
        ratios['pe_ratio'] = None
    
    # 2. P/B Ratio = Market Cap / Book Value
    if total_equity > 0:
        ratios['pb_ratio'] = market_cap / total_equity
    else:
        ratios['pb_ratio'] = None
    
    # 3. P/S Ratio = Market Cap / Revenue
    if revenue_ttm > 0:
        ratios['ps_ratio'] = market_cap / revenue_ttm
    else:
        ratios['ps_ratio'] = None
    
    # 4. EV/EBITDA = (Market Cap + Debt - Cash) / EBITDA
    enterprise_value = market_cap + total_debt - cash
    if ebitda_ttm > 0:
        ratios['ev_ebitda'] = enterprise_value / ebitda_ttm
    else:
        ratios['ev_ebitda'] = None
    
    # 5. Graham Number = √(15 × EPS × Book Value per Share)
    if eps_ttm > 0 and book_value_per_share > 0:
        import math
        ratios['graham_number'] = math.sqrt(15 * eps_ttm * book_value_per_share)
    else:
        ratios['graham_number'] = None
    
    # Store calculated values
    ratios['eps_ttm'] = eps_ttm
    ratios['book_value_per_share'] = book_value_per_share
    ratios['enterprise_value'] = enterprise_value
    
    return ratios

def ensure_ticker_exists(ticker: str):
    """Ensure ticker exists in stocks table"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT ticker FROM stocks WHERE ticker = %s", (ticker,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO stocks (ticker, company_name, sector, industry) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (ticker) DO NOTHING
            """, (ticker, f"{ticker} Corp", "Technology", "Technology"))
            conn.commit()
            print(f"    ✅ Added {ticker} to stocks table")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"    ❌ Error ensuring ticker exists: {e}")
        return False

def main():
    """Main function to calculate all ratios for the tickers"""
    tickers = ['AMZN', 'AVGO', 'NVDA', 'AAPL', 'XOM', 'SOFI', 'PLTR', 'AAL', 'BAC', 'MRNA', 'GOOG']
    
    print("🧮 Calculating All Financial Ratios Manually (Extended Set)")
    print("=" * 70)
    
    all_results = []
    
    for ticker in tickers:
        print(f"\n📊 Processing {ticker}...")
        
        # Ensure ticker exists in database
        ensure_ticker_exists(ticker)
        
        # Fetch basic data
        data = fetch_basic_data_from_fmp(ticker)
        
        if data:
            print(f"  ✅ Data fetched successfully")
            print(f"    Market Cap: ${data['market_cap']:,.0f}")
            print(f"    Revenue TTM: ${data['revenue_ttm']:,.0f}")
            print(f"    Net Income TTM: ${data['net_income_ttm']:,.0f}")
            print(f"    EBITDA TTM: ${data['ebitda_ttm']:,.0f}")
            print(f"    Current Price: ${data['current_price']:.2f}")
            
            # Calculate ratios
            ratios = calculate_ratios(data)
            
            print(f"  📈 Calculated Ratios:")
            print(f"    P/E Ratio: {ratios['pe_ratio']:.2f}" if ratios['pe_ratio'] else "    P/E Ratio: N/A")
            print(f"    P/B Ratio: {ratios['pb_ratio']:.2f}" if ratios['pb_ratio'] else "    P/B Ratio: N/A")
            print(f"    P/S Ratio: {ratios['ps_ratio']:.2f}" if ratios['ps_ratio'] else "    P/S Ratio: N/A")
            print(f"    EV/EBITDA: {ratios['ev_ebitda']:.2f}" if ratios['ev_ebitda'] else "    EV/EBITDA: N/A")
            print(f"    Graham Number: ${ratios['graham_number']:.2f}" if ratios['graham_number'] else "    Graham Number: N/A")
            print(f"    EPS TTM: ${ratios['eps_ttm']:.2f}")
            print(f"    Book Value per Share: ${ratios['book_value_per_share']:.2f}")
            
            # Store in database
            store_data_in_database(data, ratios)
            
            # Store results
            result = {
                'ticker': ticker,
                'market_cap': data['market_cap'],
                'shares_outstanding': data['shares_outstanding'],
                'current_price': data['current_price'],
                'revenue_ttm': data['revenue_ttm'],
                'net_income_ttm': data['net_income_ttm'],
                'ebitda_ttm': data['ebitda_ttm'],
                'total_debt': data['total_debt'],
                'total_equity': data['total_equity'],
                'cash': data['cash'],
                'eps_ttm': ratios['eps_ttm'],
                'book_value_per_share': ratios['book_value_per_share'],
                'enterprise_value': ratios['enterprise_value'],
                'pe_ratio': ratios['pe_ratio'],
                'pb_ratio': ratios['pb_ratio'],
                'ps_ratio': ratios['ps_ratio'],
                'ev_ebitda': ratios['ev_ebitda'],
                'graham_number': ratios['graham_number']
            }
            all_results.append(result)
            
        else:
            print(f"  ❌ Failed to fetch data for {ticker}")
        
        # Rate limiting
        time.sleep(1)
    
    # Create comprehensive DataFrame
    if all_results:
        df = pd.DataFrame(all_results)
        
        # Save to CSV
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extended_ratios_calculation_{timestamp}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\n📊 Summary of All Ratios:")
        print("=" * 70)
        print(f"{'Ticker':<6} {'P/E':<8} {'P/B':<8} {'P/S':<8} {'EV/EBITDA':<10} {'Graham':<10}")
        print("-" * 70)
        
        for _, row in df.iterrows():
            pe = f"{row['pe_ratio']:.2f}" if pd.notna(row['pe_ratio']) else "N/A"
            pb = f"{row['pb_ratio']:.2f}" if pd.notna(row['pb_ratio']) else "N/A"
            ps = f"{row['ps_ratio']:.2f}" if pd.notna(row['ps_ratio']) else "N/A"
            ev_ebitda = f"{row['ev_ebitda']:.2f}" if pd.notna(row['ev_ebitda']) else "N/A"
            graham = f"${row['graham_number']:.2f}" if pd.notna(row['graham_number']) else "N/A"
            
            print(f"{row['ticker']:<6} {pe:<8} {pb:<8} {ps:<8} {ev_ebitda:<10} {graham:<10}")
        
        print(f"\n✅ Results saved to: {filename}")
        print(f"📈 Data completeness: {len(all_results)}/{len(tickers)} tickers processed")
        
        # Show data quality
        print(f"\n📋 Data Quality Check:")
        for ratio in ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'graham_number']:
            valid_count = df[ratio].notna().sum()
            print(f"  {ratio}: {valid_count}/{len(df)} ({valid_count/len(df)*100:.1f}%)")
    
    else:
        print("❌ No data was successfully processed")

if __name__ == "__main__":
    main() 