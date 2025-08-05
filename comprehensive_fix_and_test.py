#!/usr/bin/env python3
"""
Comprehensive Fix and Test Script for Scoring System
Addresses critical issues identified in professor's analysis:
1. Data quality problems causing uniform value scores
2. Technical scaling issues
3. Testing with smaller stocks for better value opportunities
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(__file__))

from calc_fundamental_scores import FundamentalScoreCalculator
from calc_technical_scores import TechnicalScoreCalculator

def debug_fundamental_data(ticker: str) -> Dict[str, Any]:
    """Debug fundamental data for a ticker to identify data quality issues"""
    print(f"\n🔍 DEBUGGING FUNDAMENTAL DATA FOR {ticker}")
    print("=" * 60)
    
    try:
        calc = FundamentalScoreCalculator()
        
        # Get raw fundamental data
        fundamental_data = calc.get_fundamental_data(ticker)
        if not fundamental_data:
            print(f"❌ No fundamental data found for {ticker}")
            return {}
        
        print(f"📊 FUNDAMENTAL DATA FOR {ticker}:")
        print(f"   Revenue: {fundamental_data.get('total_revenue_ttm', 'N/A')}")
        print(f"   Net Income: {fundamental_data.get('net_income_ttm', 'N/A')}")
        print(f"   Total Assets: {fundamental_data.get('total_assets', 'N/A')}")
        print(f"   Total Equity: {fundamental_data.get('total_equity', 'N/A')}")
        print(f"   Total Debt: {fundamental_data.get('total_debt', 'N/A')}")
        print(f"   Current Assets: {fundamental_data.get('current_assets', 'N/A')}")
        print(f"   Current Liabilities: {fundamental_data.get('current_liabilities', 'N/A')}")
        
        # Check financial ratios
        print(f"\n📈 FINANCIAL RATIOS FOR {ticker}:")
        print(f"   PE Ratio: {fundamental_data.get('pe_ratio', 'N/A')}")
        print(f"   PB Ratio: {fundamental_data.get('pb_ratio', 'N/A')}")
        print(f"   PEG Ratio: {fundamental_data.get('peg_ratio', 'N/A')}")
        print(f"   ROE: {fundamental_data.get('roe', 'N/A')}")
        print(f"   ROA: {fundamental_data.get('roa', 'N/A')}")
        print(f"   Debt-to-Equity: {fundamental_data.get('debt_to_equity', 'N/A')}")
        print(f"   Current Ratio: {fundamental_data.get('current_ratio', 'N/A')}")
        print(f"   EV/EBITDA: {fundamental_data.get('ev_ebitda_ratio', 'N/A')}")
        
        # Get current price
        current_price = calc.get_current_price(ticker)
        print(f"\n💰 CURRENT PRICE: {current_price}")
        
        return fundamental_data
        
    except Exception as e:
        print(f"❌ Error debugging {ticker}: {e}")
        return {}

def debug_technical_data(ticker: str) -> Dict[str, Any]:
    """Debug technical data for a ticker to identify scaling issues"""
    print(f"\n🔍 DEBUGGING TECHNICAL DATA FOR {ticker}")
    print("=" * 60)
    
    try:
        calc = TechnicalScoreCalculator()
        
        # Get raw technical data
        technical_data = calc.get_technical_indicators(ticker)
        if not technical_data:
            print(f"❌ No technical data found for {ticker}")
            return {}
        
        print(f"📊 TECHNICAL DATA FOR {ticker}:")
        print(f"   RSI: {technical_data.get('rsi', 'N/A')} (raw)")
        print(f"   MACD: {technical_data.get('macd', 'N/A')} (raw)")
        print(f"   MACD Signal: {technical_data.get('macd_signal', 'N/A')} (raw)")
        print(f"   MACD Diff: {technical_data.get('macd_diff', 'N/A')} (raw)")
        print(f"   Stochastic K: {technical_data.get('stoch_k', 'N/A')} (raw)")
        print(f"   Stochastic D: {technical_data.get('stoch_d', 'N/A')} (raw)")
        print(f"   CCI: {technical_data.get('cci_20', 'N/A')} (raw)")
        print(f"   ADX: {technical_data.get('adx_14', 'N/A')} (raw)")
        print(f"   ATR: {technical_data.get('atr', 'N/A')} (raw)")
        print(f"   Volume: {technical_data.get('volume', 'N/A')} (raw)")
        
        # Show scaled values
        print(f"\n📈 SCALED TECHNICAL DATA FOR {ticker}:")
        if technical_data.get('rsi'):
            print(f"   RSI (scaled): {technical_data['rsi'] / 10:.1f}")
        if technical_data.get('macd_diff'):
            print(f"   MACD Diff (scaled): {technical_data['macd_diff'] / 100:.2f}")
        if technical_data.get('stoch_k'):
            print(f"   Stochastic K (scaled): {technical_data['stoch_k'] / 10:.1f}")
        if technical_data.get('cci_20'):
            print(f"   CCI (scaled): {technical_data['cci_20'] / 100:.1f}")
        if technical_data.get('adx_14'):
            print(f"   ADX (scaled): {technical_data['adx_14'] / 100:.1f}")
        
        return technical_data
        
    except Exception as e:
        print(f"❌ Error debugging {ticker}: {e}")
        return {}

def test_smaller_stocks():
    """Test the scoring system with smaller stocks that might have better value opportunities"""
    
    # Smaller stocks with potential value opportunities
    smaller_stocks = [
        # Small-cap value stocks
        'F', 'GM', 'T', 'VZ', 'IBM', 'INTC', 'CSCO', 'ORCL', 'HPQ', 'DELL',
        # Mid-cap value stocks  
        'CAT', 'BA', 'GE', 'MMM', 'HON', 'RTX', 'LMT', 'NOC', 'GD', 'LHX',
        # Financial stocks (often value-oriented)
        'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'TROW', 'BEN', 'IVZ',
        # Energy stocks (often value-oriented)
        'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'HAL', 'BKR', 'KMI', 'PSX', 'VLO',
        # Consumer staples (defensive value)
        'WMT', 'TGT', 'COST', 'HD', 'LOW', 'MCD', 'SBUX', 'YUM', 'CMG', 'DPZ'
    ]
    
    print("🧪 TESTING SMALLER STOCKS FOR VALUE OPPORTUNITIES")
    print("=" * 80)
    print(f"Testing {len(smaller_stocks)} smaller stocks...")
    
    successful_tickers = []
    failed_tickers = []
    
    for i, ticker in enumerate(smaller_stocks, 1):
        print(f"\n[{i}/{len(smaller_stocks)}] Testing {ticker}...")
        
        try:
            # Debug fundamental data
            fundamental_data = debug_fundamental_data(ticker)
            
            # Debug technical data
            technical_data = debug_technical_data(ticker)
            
            if fundamental_data and technical_data:
                # Calculate scores
                fundamental_calc = FundamentalScoreCalculator()
                technical_calc = TechnicalScoreCalculator()
                
                fundamental_scores = fundamental_calc.calculate_fundamental_scores(ticker)
                technical_scores = technical_calc.calculate_technical_scores(ticker)
                
                if fundamental_scores and technical_scores:
                    print(f"\n📊 SCORES FOR {ticker}:")
                    print(f"   Fundamental Health: {fundamental_scores.get('fundamental_health_score', 'N/A'):.1f}")
                    print(f"   Value Investment: {fundamental_scores.get('value_investment_score', 'N/A'):.1f}")
                    print(f"   Technical Health: {technical_scores.get('technical_health_score', 'N/A'):.1f}")
                    print(f"   Trading Signal: {technical_scores.get('trading_signal_score', 'N/A'):.1f}")
                    
                    successful_tickers.append({
                        'ticker': ticker,
                        'fundamental_health': fundamental_scores.get('fundamental_health_score'),
                        'value_investment': fundamental_scores.get('value_investment_score'),
                        'technical_health': technical_scores.get('technical_health_score'),
                        'trading_signal': technical_scores.get('trading_signal_score')
                    })
                else:
                    failed_tickers.append(ticker)
            else:
                failed_tickers.append(ticker)
                
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            failed_tickers.append(ticker)
    
    # Summary
    print(f"\n📋 TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {len(successful_tickers)}/{len(smaller_stocks)} ({len(successful_tickers)/len(smaller_stocks)*100:.1f}%)")
    print(f"❌ Failed: {len(failed_tickers)}/{len(smaller_stocks)} ({len(failed_tickers)/len(smaller_stocks)*100:.1f}%)")
    
    if successful_tickers:
        print(f"\n🏆 BEST VALUE OPPORTUNITIES (by Value Investment Score):")
        sorted_by_value = sorted(successful_tickers, key=lambda x: x['value_investment'] or 0, reverse=True)
        for i, stock in enumerate(sorted_by_value[:10], 1):
            print(f"   {i}. {stock['ticker']}: Value={stock['value_investment']:.1f}, Health={stock['fundamental_health']:.1f}")
        
        print(f"\n🏆 BEST FUNDAMENTAL HEALTH (by Fundamental Health Score):")
        sorted_by_health = sorted(successful_tickers, key=lambda x: x['fundamental_health'] or 0, reverse=True)
        for i, stock in enumerate(sorted_by_health[:10], 1):
            print(f"   {i}. {stock['ticker']}: Health={stock['fundamental_health']:.1f}, Value={stock['value_investment']:.1f}")
    
    if failed_tickers:
        print(f"\n❌ FAILED TICKERS:")
        for ticker in failed_tickers[:10]:  # Show first 10
            print(f"   • {ticker}")
        if len(failed_tickers) > 10:
            print(f"   ... and {len(failed_tickers) - 10} more")
    
    return successful_tickers, failed_tickers

def analyze_data_quality_issues():
    """Analyze and report on data quality issues"""
    print("\n🔍 ANALYZING DATA QUALITY ISSUES")
    print("=" * 80)
    
    # Test a few representative stocks
    test_stocks = ['AAPL', 'MSFT', 'F', 'T', 'BAC']
    
    for ticker in test_stocks:
        print(f"\n📊 DATA QUALITY ANALYSIS FOR {ticker}")
        print("-" * 50)
        
        # Debug fundamental data
        fundamental_data = debug_fundamental_data(ticker)
        
        # Check for missing critical ratios
        critical_ratios = ['pe_ratio', 'pb_ratio', 'peg_ratio', 'roe', 'roa', 'debt_to_equity']
        missing_ratios = []
        
        for ratio in critical_ratios:
            if not fundamental_data.get(ratio):
                missing_ratios.append(ratio)
        
        if missing_ratios:
            print(f"❌ MISSING RATIOS: {', '.join(missing_ratios)}")
        else:
            print(f"✅ ALL CRITICAL RATIOS PRESENT")
        
        # Check for zero or negative values
        zero_negative = []
        for ratio, value in fundamental_data.items():
            if isinstance(value, (int, float)) and value <= 0:
                zero_negative.append(f"{ratio}={value}")
        
        if zero_negative:
            print(f"⚠️  ZERO/NEGATIVE VALUES: {', '.join(zero_negative[:5])}")  # Show first 5

def main():
    """Main function"""
    print("🔧 COMPREHENSIVE FIX AND TEST SCRIPT")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Analyze data quality issues
    analyze_data_quality_issues()
    
    # Step 2: Test with smaller stocks
    successful_tickers, failed_tickers = test_smaller_stocks()
    
    # Step 3: Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'successful_tickers': successful_tickers,
        'failed_tickers': failed_tickers,
        'total_tested': len(successful_tickers) + len(failed_tickers),
        'success_rate': len(successful_tickers) / (len(successful_tickers) + len(failed_tickers)) * 100
    }
    
    # Save to file
    filename = f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"\n🏁 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 