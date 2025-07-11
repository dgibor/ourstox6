#!/usr/bin/env python3
"""
Debug fundamental scoring to see what ratios are being used
"""

import sys
sys.path.append('..')

from datetime import date
from score_calculator.fundamental_scorer import FundamentalScorer

def debug_fundamental_scoring():
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    scorer = FundamentalScorer()
    
    print("=== DEBUGGING FUNDAMENTAL SCORING ===")
    print("=" * 60)
    
    for ticker in tickers:
        try:
            print(f"\n📊 Debugging {ticker}...")
            
            # Get the ratios being used
            ratios = scorer.get_latest_ratios(ticker)
            
            if ratios:
                print(f"✅ Ratios found for {ticker}:")
                print(f"   PE: {ratios.get('pe_ratio')}")
                print(f"   PB: {ratios.get('pb_ratio')}")
                print(f"   ROE: {ratios.get('roe')}")
                print(f"   D/E: {ratios.get('debt_to_equity')}")
                print(f"   CR: {ratios.get('current_ratio')}")
                print(f"   EV/EBITDA: {ratios.get('ev_ebitda')}")
                print(f"   P/S: {ratios.get('ps_ratio')}")
                print(f"   ROIC: {ratios.get('roic')}")
                print(f"   Gross Margin: {ratios.get('gross_margin')}")
                print(f"   Operating Margin: {ratios.get('operating_margin')}")
                print(f"   Revenue Growth: {ratios.get('revenue_growth_yoy')}")
                print(f"   Earnings Growth: {ratios.get('earnings_growth_yoy')}")
                
                # Get sector info
                sector, industry = scorer.get_sector_info(ticker)
                print(f"   Sector: {sector}, Industry: {industry}")
                
                # Get thresholds
                thresholds = scorer.get_sector_thresholds(sector, industry)
                print(f"   PE Good Threshold: {thresholds.get('pe_ratio_good_threshold')}")
                print(f"   PE Bad Threshold: {thresholds.get('pe_ratio_bad_threshold')}")
                
                # Calculate individual scores
                valuation_score = scorer.calculate_valuation_score(ratios, thresholds)
                quality_score = scorer.calculate_quality_score(ratios)
                growth_score = scorer.calculate_growth_score(ratios, thresholds)
                financial_health_score = scorer.calculate_financial_health_score(ratios, thresholds)
                management_score = scorer.calculate_management_score(ratios)
                
                print(f"   Valuation Score: {valuation_score}")
                print(f"   Quality Score: {quality_score}")
                print(f"   Growth Score: {growth_score}")
                print(f"   Financial Health Score: {financial_health_score}")
                print(f"   Management Score: {management_score}")
                
            else:
                print(f"❌ No ratios found for {ticker}")
                
        except Exception as e:
            print(f"❌ Error debugging {ticker}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Finished debugging fundamental scoring")

if __name__ == "__main__":
    debug_fundamental_scoring() 