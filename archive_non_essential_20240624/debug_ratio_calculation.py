#!/usr/bin/env python3
"""
Debug Ratio Calculation
=======================

This script tests the ratio calculation with actual data from the database
to see why the valuation ratios are not being calculated.

Author: AI Assistant
Date: 2025-01-26
"""

import sys
import os
from datetime import date, datetime
from typing import List, Dict, Optional
import logging

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_run.database import DatabaseManager
from daily_run.ratio_calculator import calculate_ratios, validate_ratios

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_ratio_calculation(ticker: str):
    """Debug ratio calculation for a specific ticker"""
    db = DatabaseManager()
    
    print(f"\n{'='*60}")
    print(f"DEBUGGING RATIO CALCULATION FOR {ticker}")
    print(f"{'='*60}")
    
    try:
        # Get the most recent fundamental data
        query = """
        SELECT 
            revenue, net_income, ebitda, total_equity, total_assets,
            total_debt, gross_profit, operating_income, free_cash_flow,
            shares_outstanding
        FROM company_fundamentals
        WHERE ticker = %s
        ORDER BY last_updated DESC
        LIMIT 1
        """
        result = db.execute_query(query, (ticker,))
        
        if not result:
            print(f"❌ No fundamental data found for {ticker}")
            return
        
        row = result[0]
        print(f"📊 FUNDAMENTAL DATA FROM DATABASE:")
        print(f"  Revenue: ${row[0]:,.0f}" if row[0] else "  Revenue: N/A")
        print(f"  Net Income: ${row[1]:,.0f}" if row[1] else "  Net Income: N/A")
        print(f"  EBITDA: ${row[2]:,.0f}" if row[2] else "  EBITDA: N/A")
        print(f"  Total Equity: ${row[3]:,.0f}" if row[3] else "  Total Equity: N/A")
        print(f"  Total Assets: ${row[4]:,.0f}" if row[4] else "  Total Assets: N/A")
        print(f"  Total Debt: ${row[5]:,.0f}" if row[5] else "  Total Debt: N/A")
        print(f"  Gross Profit: ${row[6]:,.0f}" if row[6] else "  Gross Profit: N/A")
        print(f"  Operating Income: ${row[7]:,.0f}" if row[7] else "  Operating Income: N/A")
        print(f"  Free Cash Flow: ${row[8]:,.0f}" if row[8] else "  Free Cash Flow: N/A")
        print(f"  Shares Outstanding: {row[9]:,.0f}" if row[9] else "  Shares Outstanding: N/A")
        
        # Get market data from stocks table
        market_query = """
        SELECT 
            market_cap, enterprise_value, shares_outstanding
        FROM stocks
        WHERE ticker = %s
        """
        market_result = db.execute_query(market_query, (ticker,))
        
        if not market_result:
            print(f"❌ No market data found for {ticker}")
            return
        
        market_row = market_result[0]
        print(f"\n📈 MARKET DATA FROM STOCKS TABLE:")
        print(f"  Market Cap: ${market_row[0]:,.0f}" if market_row[0] else "  Market Cap: N/A")
        print(f"  Enterprise Value: ${market_row[1]:,.0f}" if market_row[1] else "  Enterprise Value: N/A")
        print(f"  Shares Outstanding: {market_row[2]:,.0f}" if market_row[2] else "  Shares Outstanding: N/A")
        
        # Get current price from daily_charts
        current_price = db.get_latest_price(ticker)
        print(f"  Current Price: ${current_price:.2f}" if current_price else "  Current Price: N/A")
        
        # Prepare raw data for ratio calculation
        raw_data = {
            'revenue': row[0],
            'net_income': row[1],
            'ebitda': row[2],
            'total_equity': row[3],
            'total_assets': row[4],
            'total_debt': row[5],
            'gross_profit': row[6],
            'operating_income': row[7],
            'free_cash_flow': row[8]
        }
        
        market_data = {
            'current_price': current_price,
            'shares_outstanding': market_row[2],
            'enterprise_value': market_row[1]
        }
        
        print(f"\n🧮 INPUT DATA FOR RATIO CALCULATION:")
        print(f"  Raw Data: {raw_data}")
        print(f"  Market Data: {market_data}")
        
        # Calculate ratios
        print(f"\n🧮 CALCULATING RATIOS...")
        calculated_ratios = calculate_ratios(raw_data, market_data)
        
        print(f"\n📊 CALCULATED RATIOS:")
        for ratio_name, ratio_value in calculated_ratios.items():
            print(f"  {ratio_name}: {ratio_value}")
        
        # Manual calculation check
        print(f"\n🔍 MANUAL CALCULATION CHECK:")
        price = current_price
        shares = market_row[2]
        net_income = row[1]
        equity = row[3]
        revenue = row[0]
        ebitda = row[2]
        enterprise_value = market_row[1]
        
        if price and shares and net_income:
            eps = net_income / shares
            print(f"  EPS: {net_income:,.0f} / {shares:,.0f} = {eps:.4f}")
            pe_ratio = price / eps
            print(f"  P/E Ratio: {price:.2f} / {eps:.4f} = {pe_ratio:.2f}")
        else:
            print(f"  P/E Ratio: Cannot calculate (missing price, shares, or net income)")
        
        if price and shares and equity:
            book_value_per_share = equity / shares
            print(f"  Book Value per Share: {equity:,.0f} / {shares:,.0f} = {book_value_per_share:.4f}")
            pb_ratio = price / book_value_per_share
            print(f"  P/B Ratio: {price:.2f} / {book_value_per_share:.4f} = {pb_ratio:.2f}")
        else:
            print(f"  P/B Ratio: Cannot calculate (missing price, shares, or equity)")
        
        if price and shares and revenue:
            revenue_per_share = revenue / shares
            print(f"  Revenue per Share: {revenue:,.0f} / {shares:,.0f} = {revenue_per_share:.4f}")
            ps_ratio = price / revenue_per_share
            print(f"  P/S Ratio: {price:.2f} / {revenue_per_share:.4f} = {ps_ratio:.2f}")
        else:
            print(f"  P/S Ratio: Cannot calculate (missing price, shares, or revenue)")
        
        if enterprise_value and ebitda:
            ev_ebitda = enterprise_value / ebitda
            print(f"  EV/EBITDA: {enterprise_value:,.0f} / {ebitda:,.0f} = {ev_ebitda:.2f}")
        else:
            print(f"  EV/EBITDA: Cannot calculate (missing enterprise value or ebitda)")
        
    except Exception as e:
        print(f"❌ Error debugging ratio calculation for {ticker}: {e}")
        logger.error(f"Error debugging ratio calculation for {ticker}: {e}")

def main():
    """Main execution function"""
    failed_tickers = ['AMD']
    
    print("🔍 DEBUGGING RATIO CALCULATION")
    print("="*60)
    
    for ticker in failed_tickers:
        debug_ratio_calculation(ticker)
    
    print(f"\n{'='*60}")
    print("DEBUG COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 