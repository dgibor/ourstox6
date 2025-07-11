#!/usr/bin/env python3
"""
Debug Market Data for Failed Tickers
====================================

This script checks what market data is being returned for failed tickers
and why the ratio calculation is failing.

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
from daily_run.fmp_service import FMPService
from daily_run.ratio_calculator import calculate_ratios, validate_ratios

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_market_data_for_ticker(ticker: str):
    """Debug market data for a specific ticker"""
    print(f"\n{'='*60}")
    print(f"DEBUGGING MARKET DATA FOR {ticker}")
    print(f"{'='*60}")
    
    fmp_service = FMPService()
    
    try:
        # Fetch key statistics
        print(f"Fetching key statistics for {ticker}...")
        key_stats = fmp_service.fetch_key_statistics(ticker)
        
        if not key_stats:
            print(f"❌ No key statistics returned for {ticker}")
            return
        
        print(f"✅ Key statistics fetched successfully")
        
        # Check market data
        market_data = key_stats.get('market_data', {})
        print(f"\n📊 MARKET DATA:")
        print(f"  Current Price: ${market_data.get('current_price', 'N/A')}")
        print(f"  Market Cap: ${market_data.get('market_cap', 'N/A'):,.0f}" if market_data.get('market_cap') else "  Market Cap: N/A")
        print(f"  Enterprise Value: ${market_data.get('enterprise_value', 'N/A'):,.0f}" if market_data.get('enterprise_value') else "  Enterprise Value: N/A")
        print(f"  Shares Outstanding: {market_data.get('shares_outstanding', 'N/A'):,.0f}" if market_data.get('shares_outstanding') else "  Shares Outstanding: N/A")
        
        # Check FMP ratios
        fmp_ratios = key_stats.get('ratios', {})
        print(f"\n📈 FMP RATIOS:")
        print(f"  P/E Ratio: {fmp_ratios.get('pe_ratio', 'N/A')}")
        print(f"  P/B Ratio: {fmp_ratios.get('pb_ratio', 'N/A')}")
        print(f"  P/S Ratio: {fmp_ratios.get('ps_ratio', 'N/A')}")
        print(f"  EV/EBITDA: {fmp_ratios.get('ev_ebitda', 'N/A')}")
        print(f"  ROE: {fmp_ratios.get('roe', 'N/A')}")
        
        # Fetch financial data for ratio calculation
        print(f"\n📋 Fetching financial data for ratio calculation...")
        financial_data = fmp_service.fetch_financial_statements(ticker)
        
        if not financial_data:
            print(f"❌ No financial data returned for {ticker}")
            return
        
        print(f"✅ Financial data fetched successfully")
        
        # Extract raw data for ratio calculation
        income = financial_data.get('income_statement', {})
        balance = financial_data.get('balance_sheet', {})
        cash_flow = financial_data.get('cash_flow', {})
        
        raw_data = {
            'revenue': income.get('revenue'),
            'gross_profit': income.get('gross_profit'),
            'operating_income': income.get('operating_income'),
            'net_income': income.get('net_income'),
            'ebitda': income.get('ebitda'),
            'total_assets': balance.get('total_assets'),
            'total_debt': balance.get('total_debt'),
            'total_equity': balance.get('total_equity'),
            'current_assets': balance.get('current_assets'),
            'current_liabilities': balance.get('current_liabilities'),
            'free_cash_flow': cash_flow.get('free_cash_flow')
        }
        
        print(f"\n📊 RAW FINANCIAL DATA:")
        print(f"  Revenue: ${raw_data['revenue']:,.0f}" if raw_data['revenue'] else "  Revenue: N/A")
        print(f"  Net Income: ${raw_data['net_income']:,.0f}" if raw_data['net_income'] else "  Net Income: N/A")
        print(f"  EBITDA: ${raw_data['ebitda']:,.0f}" if raw_data['ebitda'] else "  EBITDA: N/A")
        print(f"  Total Equity: ${raw_data['total_equity']:,.0f}" if raw_data['total_equity'] else "  Total Equity: N/A")
        print(f"  Total Assets: ${raw_data['total_assets']:,.0f}" if raw_data['total_assets'] else "  Total Assets: N/A")
        
        # Calculate ratios
        print(f"\n🧮 CALCULATING RATIOS...")
        calculated_ratios = calculate_ratios(raw_data, market_data)
        
        print(f"\n📊 CALCULATED RATIOS:")
        print(f"  P/E Ratio: {calculated_ratios.get('pe_ratio', 'N/A')}")
        print(f"  P/B Ratio: {calculated_ratios.get('pb_ratio', 'N/A')}")
        print(f"  P/S Ratio: {calculated_ratios.get('ps_ratio', 'N/A')}")
        print(f"  EV/EBITDA: {calculated_ratios.get('ev_ebitda', 'N/A')}")
        print(f"  ROE: {calculated_ratios.get('roe', 'N/A')}")
        print(f"  ROA: {calculated_ratios.get('roa', 'N/A')}")
        print(f"  Debt/Equity: {calculated_ratios.get('debt_to_equity', 'N/A')}")
        print(f"  Current Ratio: {calculated_ratios.get('current_ratio', 'N/A')}")
        print(f"  Gross Margin: {calculated_ratios.get('gross_margin', 'N/A')}")
        print(f"  Operating Margin: {calculated_ratios.get('operating_margin', 'N/A')}")
        print(f"  Net Margin: {calculated_ratios.get('net_margin', 'N/A')}")
        
        # Check what's causing the None values
        print(f"\n🔍 DEBUGGING NONE VALUES:")
        price = market_data.get('current_price')
        shares = market_data.get('shares_outstanding')
        equity = raw_data.get('total_equity')
        revenue = raw_data.get('revenue')
        net_income = raw_data.get('net_income')
        ebitda = raw_data.get('ebitda')
        enterprise_value = market_data.get('enterprise_value')
        
        print(f"  Current Price: {price} (type: {type(price)})")
        print(f"  Shares Outstanding: {shares} (type: {type(shares)})")
        print(f"  Total Equity: {equity} (type: {type(equity)})")
        print(f"  Revenue: {revenue} (type: {type(revenue)})")
        print(f"  Net Income: {net_income} (type: {type(net_income)})")
        print(f"  EBITDA: {ebitda} (type: {type(ebitda)})")
        print(f"  Enterprise Value: {enterprise_value} (type: {type(enterprise_value)})")
        
        # Calculate per-share metrics manually
        print(f"\n🧮 PER-SHARE CALCULATIONS:")
        eps = net_income / shares if net_income and shares and shares != 0 else None
        book_value_per_share = equity / shares if equity and shares and shares != 0 else None
        revenue_per_share = revenue / shares if revenue and shares and shares != 0 else None
        
        print(f"  EPS: {eps}")
        print(f"  Book Value per Share: {book_value_per_share}")
        print(f"  Revenue per Share: {revenue_per_share}")
        
        # Calculate ratios manually
        pe_ratio = price / eps if price and eps and eps != 0 else None
        pb_ratio = price / book_value_per_share if price and book_value_per_share and book_value_per_share != 0 else None
        ps_ratio = price / revenue_per_share if price and revenue_per_share and revenue_per_share != 0 else None
        ev_ebitda = enterprise_value / ebitda if enterprise_value and ebitda and ebitda != 0 else None
        
        print(f"\n🧮 MANUAL RATIO CALCULATIONS:")
        print(f"  P/E Ratio: {price} / {eps} = {pe_ratio}")
        print(f"  P/B Ratio: {price} / {book_value_per_share} = {pb_ratio}")
        print(f"  P/S Ratio: {price} / {revenue_per_share} = {ps_ratio}")
        print(f"  EV/EBITDA: {enterprise_value} / {ebitda} = {ev_ebitda}")
        
    except Exception as e:
        print(f"❌ Error debugging {ticker}: {e}")
        logger.error(f"Error debugging {ticker}: {e}")
    finally:
        fmp_service.close()

def main():
    """Main execution function"""
    failed_tickers = ['AMD', 'AMZN', 'AVGO', 'INTC', 'MU', 'QCOM']
    
    print("🔍 DEBUGGING MARKET DATA FOR FAILED TICKERS")
    print("="*60)
    
    for ticker in failed_tickers:
        debug_market_data_for_ticker(ticker)
    
    print(f"\n{'='*60}")
    print("DEBUG COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 