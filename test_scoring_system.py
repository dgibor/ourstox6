#!/usr/bin/env python3
"""
Test script for the enhanced scoring system with 5-level normalization
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(__file__))

from calc_fundamental_scores import FundamentalScoreCalculator
from calc_technical_scores import TechnicalScoreCalculator

def test_single_ticker(ticker):
    """Test scoring for a single ticker"""
    print(f"\n{'='*80}")
    print(f"TESTING {ticker}")
    print(f"{'='*80}")
    
    try:
        # Calculate fundamental scores
        fundamental_calc = FundamentalScoreCalculator()
        fundamental_scores = fundamental_calc.calculate_fundamental_scores(ticker)
        
        if not fundamental_scores:
            print(f"❌ No fundamental scores calculated for {ticker}")
            return False
        
        # Calculate technical scores
        technical_calc = TechnicalScoreCalculator()
        technical_scores = technical_calc.calculate_technical_scores(ticker)
        
        if not technical_scores:
            print(f"❌ No technical scores calculated for {ticker}")
            return False
        
        # Display results with 5-level normalization
        print(f"\n📊 FUNDAMENTAL ANALYSIS - {ticker}")
        print(f"   Health Score: {fundamental_scores['fundamental_health_score']:.1f} → {fundamental_scores['fundamental_health_normalized']}/5 ({fundamental_scores['fundamental_health_grade']})")
        print(f"   Description: {fundamental_scores['fundamental_health_description']}")
        print(f"   Value Score: {fundamental_scores['value_investment_score']:.1f} → {fundamental_scores['value_investment_normalized']}/5 ({fundamental_scores['value_rating']})")
        print(f"   Description: {fundamental_scores['value_description']}")
        print(f"   Risk Score: {fundamental_scores['fundamental_risk_score']:.1f} → {fundamental_scores['fundamental_risk_normalized']}/5 ({fundamental_scores['fundamental_risk_level']})")
        print(f"   Description: {fundamental_scores['fundamental_risk_description']}")
        
        print(f"\n📈 TECHNICAL ANALYSIS - {ticker}")
        print(f"   Health Score: {technical_scores['technical_health_score']:.1f} → {technical_scores['technical_health_normalized']}/5 ({technical_scores['technical_health_grade']})")
        print(f"   Description: {technical_scores['technical_health_description']}")
        print(f"   Signal Score: {technical_scores['trading_signal_score']:.1f} → {technical_scores['trading_signal_normalized']}/5 ({technical_scores['trading_signal_rating']})")
        print(f"   Description: {technical_scores['trading_signal_description']}")
        print(f"   Risk Score: {technical_scores['technical_risk_score']:.1f} → {technical_scores['technical_risk_normalized']}/5 ({technical_scores['technical_risk_level']})")
        print(f"   Description: {technical_scores['technical_risk_description']}")
        
        # Show alerts
        if fundamental_scores.get('fundamental_red_flags'):
            print(f"\n🚨 FUNDAMENTAL RED FLAGS:")
            for flag in fundamental_scores['fundamental_red_flags']:
                print(f"   • {flag}")
        
        if fundamental_scores.get('fundamental_yellow_flags'):
            print(f"\n⚠️  FUNDAMENTAL YELLOW FLAGS:")
            for flag in fundamental_scores['fundamental_yellow_flags']:
                print(f"   • {flag}")
        
        if technical_scores.get('technical_red_flags'):
            print(f"\n🚨 TECHNICAL RED FLAGS:")
            for flag in technical_scores['technical_red_flags']:
                print(f"   • {flag}")
        
        if technical_scores.get('technical_yellow_flags'):
            print(f"\n⚠️  TECHNICAL YELLOW FLAGS:")
            for flag in technical_scores['technical_yellow_flags']:
                print(f"   • {flag}")
        
        # Store in database
        try:
            fundamental_calc.store_fundamental_scores(ticker, fundamental_scores, technical_scores)
            print(f"\n✅ Scores stored in database for {ticker}")
        except Exception as e:
            print(f"\n❌ Error storing scores for {ticker}: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 TESTING ENHANCED SCORING SYSTEM WITH 5-LEVEL NORMALIZATION")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test tickers - expanded to 20 as requested
    test_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'BRK-B', 'UNH', 'JNJ',
        'JPM', 'PG', 'HD', 'MA', 'PFE', 'ABBV', 'KO', 'PEP', 'AVGO', 'COST'
    ]
    
    successful_tickers = []
    failed_tickers = []
    
    for ticker in test_tickers:
        if test_single_ticker(ticker):
            successful_tickers.append(ticker)
        else:
            failed_tickers.append(ticker)
    
    # Summary
    print(f"\n{'='*80}")
    print("📋 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successful: {len(successful_tickers)}/{len(test_tickers)} ({len(successful_tickers)/len(test_tickers)*100:.1f}%)")
    print(f"❌ Failed: {len(failed_tickers)}/{len(test_tickers)} ({len(failed_tickers)/len(test_tickers)*100:.1f}%)")
    
    if successful_tickers:
        print(f"\n✅ Successful tickers: {', '.join(successful_tickers)}")
    
    if failed_tickers:
        print(f"\n❌ Failed tickers: {', '.join(failed_tickers)}")
    
    print(f"\n🎯 5-LEVEL NORMALIZATION SCALE:")
    print("   5 = Strong Buy (Excellent fundamentals/technical health)")
    print("   4 = Buy (Good fundamentals/technical health)")
    print("   3 = Neutral (Average fundamentals/technical health)")
    print("   2 = Sell (Poor fundamentals/technical health)")
    print("   1 = Strong Sell (Very poor fundamentals/technical health)")
    
    print(f"\n📊 SCORE INTERPRETATION:")
    print("   • Fundamental Health: Higher scores = better company health")
    print("   • Value Investment: Higher scores = better value opportunity")
    print("   • Risk Assessment: Lower scores = lower risk (better)")
    print("   • Technical Health: Higher scores = better technical position")
    print("   • Trading Signal: Higher scores = stronger buy signals")
    print("   • Technical Risk: Lower scores = lower technical risk (better)")
    
    print(f"\n🏁 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 