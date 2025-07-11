#!/usr/bin/env python3
"""
Check Actual Ratios in Database
===============================

This script checks the actual ratio values stored in the company_fundamentals table
for the failed tickers to see if the ratios were calculated and stored correctly.

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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_actual_ratios(ticker: str):
    """Check the actual ratio values stored in company_fundamentals for a ticker"""
    db = DatabaseManager()
    
    print(f"\n{'='*60}")
    print(f"ACTUAL RATIOS IN DATABASE FOR {ticker}")
    print(f"{'='*60}")
    
    try:
        # Get the most recent entry for this ticker
        query = """
        SELECT 
            last_updated,
            price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda,
            return_on_equity, return_on_assets, gross_margin, operating_margin, net_margin,
            debt_to_equity_ratio, current_ratio, revenue_growth_yoy, earnings_growth_yoy,
            revenue, net_income, ebitda, total_equity, total_assets
        FROM company_fundamentals
        WHERE ticker = %s
        ORDER BY last_updated DESC
        LIMIT 1
        """
        result = db.execute_query(query, (ticker,))
        
        if not result:
            print(f"❌ No data found for {ticker}")
            return
        
        row = result[0]
        print(f"📅 Last Updated: {row[0]}")
        print(f"\n💰 VALUATION RATIOS:")
        print(f"  P/E Ratio: {row[1]}")
        print(f"  P/B Ratio: {row[2]}")
        print(f"  P/S Ratio: {row[3]}")
        print(f"  EV/EBITDA: {row[4]}")
        
        print(f"\n📊 PROFITABILITY RATIOS:")
        print(f"  ROE: {row[5]}")
        print(f"  ROA: {row[6]}")
        print(f"  Gross Margin: {row[7]}")
        print(f"  Operating Margin: {row[8]}")
        print(f"  Net Margin: {row[9]}")
        
        print(f"\n🏦 FINANCIAL HEALTH RATIOS:")
        print(f"  Debt/Equity: {row[10]}")
        print(f"  Current Ratio: {row[11]}")
        
        print(f"\n📈 GROWTH RATIOS:")
        print(f"  Revenue Growth YoY: {row[12]}")
        print(f"  Earnings Growth YoY: {row[13]}")
        
        print(f"\n📋 RAW FINANCIAL DATA:")
        print(f"  Revenue: ${row[14]:,.0f}" if row[14] else "  Revenue: N/A")
        print(f"  Net Income: ${row[15]:,.0f}" if row[15] else "  Net Income: N/A")
        print(f"  EBITDA: ${row[16]:,.0f}" if row[16] else "  EBITDA: N/A")
        print(f"  Total Equity: ${row[17]:,.0f}" if row[17] else "  Total Equity: N/A")
        print(f"  Total Assets: ${row[18]:,.0f}" if row[18] else "  Total Assets: N/A")
        
        # Check if we have the necessary data to calculate ratios manually
        print(f"\n🧮 MANUAL CALCULATION CHECK:")
        revenue = row[14]
        net_income = row[15]
        ebitda = row[16]
        total_equity = row[17]
        total_assets = row[18]
        
        if net_income and total_equity:
            roe_calc = net_income / total_equity
            print(f"  ROE (Net Income / Total Equity): {net_income:,.0f} / {total_equity:,.0f} = {roe_calc:.4f}")
        
        if net_income and total_assets:
            roa_calc = net_income / total_assets
            print(f"  ROA (Net Income / Total Assets): {net_income:,.0f} / {total_assets:,.0f} = {roa_calc:.4f}")
        
        if revenue and net_income:
            net_margin_calc = net_income / revenue
            print(f"  Net Margin (Net Income / Revenue): {net_income:,.0f} / {revenue:,.0f} = {net_margin_calc:.4f}")
        
    except Exception as e:
        print(f"❌ Error checking ratios for {ticker}: {e}")
        logger.error(f"Error checking ratios for {ticker}: {e}")

def main():
    """Main execution function"""
    failed_tickers = ['AMD', 'AMZN', 'AVGO', 'INTC', 'MU', 'QCOM']
    
    print("🔍 CHECKING ACTUAL RATIOS IN DATABASE")
    print("="*60)
    
    for ticker in failed_tickers:
        check_actual_ratios(ticker)
    
    print(f"\n{'='*60}")
    print("CHECK COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 