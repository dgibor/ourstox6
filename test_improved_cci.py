#!/usr/bin/env python3
"""
Test improved CCI calculation
"""

from calc_technical_scores_enhanced import EnhancedTechnicalScoreCalculator

def test_improved_cci():
    print("TESTING IMPROVED CCI CALCULATION")
    print("=" * 50)
    
    calc = EnhancedTechnicalScoreCalculator()
    chart_values = {'CSCO': 29.5, 'MNST': 17.7, 'AAPL': 13.9}
    
    results = {}
    errors = []
    
    for ticker in ['CSCO', 'MNST', 'AAPL']:
        try:
            result = calc.calculate_enhanced_technical_scores(ticker)
            if result and 'technical_data' in result:
                cci = result['technical_data']['cci_20']
                chart_cci = chart_values[ticker]
                error = abs(cci - chart_cci)
                
                results[ticker] = cci
                errors.append(error)
                
                print(f"{ticker}: {cci:.1f} (chart: {chart_cci:.1f}) - error: {error:.1f}")
            else:
                print(f"{ticker}: Failed to calculate")
        except Exception as e:
            print(f"{ticker}: Error - {e}")
    
    if errors:
        avg_error = sum(errors) / len(errors)
        print(f"\nAverage error: {avg_error:.1f}")
        print("✅ CCI calculation improved!" if avg_error < 10 else "⚠️ CCI needs more tuning")

if __name__ == "__main__":
    test_improved_cci()
