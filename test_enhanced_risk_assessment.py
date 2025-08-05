#!/usr/bin/env python3
"""
Test script to verify the enhanced risk assessment algorithm
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(__file__))

from calc_fundamental_scores import FundamentalScoreCalculator

def test_enhanced_risk_assessment(ticker):
    """Test the enhanced risk assessment for a specific ticker"""
    print(f"\n{'='*80}")
    print(f"ENHANCED RISK ASSESSMENT TEST FOR {ticker}")
    print(f"{'='*80}")
    
    try:
        # Calculate fundamental scores
        fundamental_calc = FundamentalScoreCalculator()
        fundamental_scores = fundamental_calc.calculate_fundamental_scores(ticker)
        
        if not fundamental_scores:
            print(f"❌ No fundamental scores calculated for {ticker}")
            return False
        
        # Display results with focus on risk assessment
        print(f"\n📊 FUNDAMENTAL ANALYSIS - {ticker}")
        print(f"   Health Score: {fundamental_scores['fundamental_health_score']:.1f} → {fundamental_scores['fundamental_health_normalized']}/5 ({fundamental_scores['fundamental_health_grade']})")
        print(f"   Value Score: {fundamental_scores['value_investment_score']:.1f} → {fundamental_scores['value_investment_normalized']}/5 ({fundamental_scores['value_rating']})")
        print(f"   Risk Score: {fundamental_scores['fundamental_risk_score']:.1f} → {fundamental_scores['fundamental_risk_normalized']}/5 ({fundamental_scores['fundamental_risk_level']})")
        print(f"   Risk Description: {fundamental_scores['fundamental_risk_description']}")
        
        # Show key ratios that influence risk assessment
        print(f"\n🔍 KEY RISK FACTORS:")
        if 'pe_ratio' in fundamental_scores:
            print(f"   PE Ratio: {fundamental_scores['pe_ratio']:.2f}")
        if 'pb_ratio' in fundamental_scores:
            print(f"   PB Ratio: {fundamental_scores['pb_ratio']:.2f}")
        if 'debt_to_equity' in fundamental_scores:
            print(f"   Debt-to-Equity: {fundamental_scores['debt_to_equity']:.2f}")
        if 'current_ratio' in fundamental_scores:
            print(f"   Current Ratio: {fundamental_scores['current_ratio']:.2f}")
        if 'roe' in fundamental_scores:
            print(f"   ROE: {fundamental_scores['roe']:.2f}%")
        if 'market_cap' in fundamental_scores:
            print(f"   Market Cap: ${fundamental_scores['market_cap']:,.0f}")
        if 'sector' in fundamental_scores:
            print(f"   Sector: {fundamental_scores['sector']}")
        
        # Professor analysis
        print(f"\n🎓 PROFESSOR ANALYSIS:")
        risk_score = fundamental_scores['fundamental_risk_score']
        risk_grade = fundamental_scores['fundamental_risk_level']
        
        if ticker == 'TSLA':
            if risk_score >= 60:
                print(f"✅ CORRECT: TSLA got a high-risk score ({risk_score:.1f}) - appropriate for a growth stock")
            else:
                print(f"❌ PROBLEM: TSLA got a low-risk score ({risk_score:.1f}) - should be higher risk")
        elif ticker in ['NVDA', 'MSFT']:
            if risk_score >= 50:
                print(f"✅ CORRECT: {ticker} got a moderate-high risk score ({risk_score:.1f}) - appropriate")
            else:
                print(f"⚠️  QUESTIONABLE: {ticker} got a low-risk score ({risk_score:.1f}) - may be too low")
        else:
            print(f"📊 {ticker} risk score: {risk_score:.1f} ({risk_grade})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 TESTING ENHANCED RISK ASSESSMENT ALGORITHM")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test tickers - focus on growth stocks that should be high-risk
    test_tickers = ['TSLA', 'NVDA', 'MSFT', 'AAPL', 'META', 'AMZN']
    
    success_count = 0
    total_count = len(test_tickers)
    
    for ticker in test_tickers:
        if test_enhanced_risk_assessment(ticker):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Successfully tested: {success_count}/{total_count} tickers")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_count:
        print("✅ All tests completed successfully!")
    else:
        print(f"⚠️  {total_count - success_count} tests failed")

if __name__ == "__main__":
    main() 