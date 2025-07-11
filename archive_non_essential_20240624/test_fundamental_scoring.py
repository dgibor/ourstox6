#!/usr/bin/env python3
"""
Test fundamental scoring for target tickers
"""

import sys
sys.path.append('..')

from datetime import date
from score_calculator.fundamental_scorer import FundamentalScorer

def test_fundamental_scoring():
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    scorer = FundamentalScorer()
    
    print("Testing fundamental scoring for target tickers...")
    print("=" * 60)
    
    for ticker in tickers:
        try:
            print(f"\n📊 Calculating fundamental score for {ticker}...")
            
            # Calculate the score
            score_data = scorer.calculate_fundamental_score(ticker, date.today())
            
            if score_data and score_data.get('calculation_status') != 'failed':
                print(f"✅ {ticker} Fundamental Score Calculation:")
                print(f"   Status: {score_data.get('calculation_status', 'unknown')}")
                print(f"   Data Quality: {score_data.get('data_quality_score', 0)}%")
                print(f"   Valuation Score: {score_data.get('valuation_score', 0)}")
                print(f"   Quality Score: {score_data.get('quality_score', 0)}")
                print(f"   Growth Score: {score_data.get('growth_score', 0)}")
                print(f"   Financial Health Score: {score_data.get('financial_health_score', 0)}")
                print(f"   Management Score: {score_data.get('management_score', 0)}")
                print(f"   Conservative Investor Score: {score_data.get('conservative_investor_score', 0)}")
                print(f"   GARP Investor Score: {score_data.get('garp_investor_score', 0)}")
                print(f"   Deep Value Investor Score: {score_data.get('deep_value_investor_score', 0)}")
            else:
                print(f"❌ {ticker} Fundamental Score Calculation Failed:")
                print(f"   Error: {score_data.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error calculating fundamental score for {ticker}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Finished testing fundamental scoring")

if __name__ == "__main__":
    test_fundamental_scoring() 