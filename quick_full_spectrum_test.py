#!/usr/bin/env python3
"""
QUICK FULL SPECTRUM TEST
Based on the working comprehensive_ai_comparison_table.py but with 5-level ratings.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the working class
from comprehensive_ai_comparison_table import ComprehensiveAIComparison

class QuickFullSpectrumTest(ComprehensiveAIComparison):
    def __init__(self):
        super().__init__()
    
    def get_rating(self, composite_score, sector_weights):
        """Get full spectrum rating (5 levels)"""
        try:
            # Full spectrum thresholds
            if composite_score >= 78:
                return "Strong Buy"
            elif composite_score >= 68:
                return "Buy"
            elif composite_score >= 55:
                return "Hold"
            elif composite_score >= 40:
                return "Sell"
            else:
                return "Strong Sell"
                
        except Exception as e:
            return "Hold"
    
    def simulate_ai_web_search(self, ticker):
        """Enhanced AI simulation with full spectrum"""
        ai_ratings = {
            # Technology - Mixed
            'AAPL': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$200'},
            'MSFT': {'rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'confidence': 'High', 'price_target': '$450'},
            'GOOGL': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            'AMZN': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'Medium', 'price_target': '$180'},
            'TSLA': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$250'},
            'NVDA': {'rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'confidence': 'High', 'price_target': '$800'},
            'META': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$400'},
            'NFLX': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$600'},
            'AMD': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'High', 'price_target': '$120'},
            'INTC': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$45'},
            'CRM': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$300'},
            'ORCL': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'Medium', 'price_target': '$140'},
            'ADBE': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$600'},
            'CSCO': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$60'},
            'QCOM': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            
            # Healthcare
            'JNJ': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$170'},
            'PFE': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$30'},
            'UNH': {'rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'confidence': 'High', 'price_target': '$600'},
            'ABBV': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            'TMO': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$600'},
            'DHR': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$300'},
            
            # Financial
            'JPM': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$200'},
            'BAC': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$35'},
            'WFC': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$45'},
            'GS': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$400'},
            'MS': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$100'},
            'BLK': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$900'},
            
            # Energy - Weak
            'XOM': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$110'},
            'CVX': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$160'},
            'COP': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'Medium', 'price_target': '$130'},
            'SLB': {'rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'confidence': 'Medium', 'price_target': '$50'},
            
            # Consumer
            'HD': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$350'},
            'MCD': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$320'},
            'KO': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$60'},
            'PEP': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            
            # Industrial
            'CAT': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$280'},
            'BA': {'rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'confidence': 'High', 'price_target': '$200'},
            'GE': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$120'},
            
            # Communication Services
            'DIS': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$80'},
            'CMCSA': {'rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'confidence': 'Medium', 'price_target': '$35'},
        }
        
        return ai_ratings.get(ticker, {
            'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$50'
        })
    
    def analyze_full_spectrum_results(self, results):
        """Analyze full spectrum results"""
        total_stocks = len(results)
        
        print(f"\n📊 FULL SPECTRUM ANALYSIS:")
        print(f"   Total Stocks: {total_stocks}")
        
        # Count our ratings
        our_counts = {}
        ai_counts = {}
        
        for result in results:
            our_rating = result['our_rating']
            ai_rating = result['ai_rating']
            
            our_counts[our_rating] = our_counts.get(our_rating, 0) + 1
            ai_counts[ai_rating] = ai_counts.get(ai_rating, 0) + 1
        
        print(f"\n🎯 OUR RATING DISTRIBUTION:")
        rating_order = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
        for rating in rating_order:
            count = our_counts.get(rating, 0)
            pct = (count / total_stocks * 100) if total_stocks > 0 else 0
            print(f"   {rating}: {count} stocks ({pct:.1f}%)")
        
        print(f"\n🤖 AI RATING DISTRIBUTION:")
        for rating in rating_order:
            count = ai_counts.get(rating, 0)
            pct = (count / total_stocks * 100) if total_stocks > 0 else 0
            print(f"   {rating}: {count} stocks ({pct:.1f}%)")
        
        # Show alignment
        exact_matches = sum(1 for r in results if r['our_rating'] == r['ai_rating'])
        alignment_pct = (exact_matches / total_stocks * 100) if total_stocks > 0 else 0
        
        print(f"\n🔍 ALIGNMENT:")
        print(f"   Exact Matches: {exact_matches}/{total_stocks} ({alignment_pct:.1f}%)")
        
        # Show examples
        print(f"\n📋 EXAMPLES:")
        strong_buys = [r['ticker'] for r in results if r['our_rating'] == 'Strong Buy']
        strong_sells = [r['ticker'] for r in results if r['our_rating'] == 'Strong Sell']
        sells = [r['ticker'] for r in results if r['our_rating'] == 'Sell']
        
        if strong_buys:
            print(f"   Strong Buy: {', '.join(strong_buys)}")
        if sells:
            print(f"   Sell: {', '.join(sells)}")
        if strong_sells:
            print(f"   Strong Sell: {', '.join(strong_sells)}")

def main():
    """Quick test"""
    test_system = QuickFullSpectrumTest()
    
    if not test_system.connect_db():
        return
        
    if not test_system.load_sector_weights():
        test_system.disconnect_db()
        return
    
    # Test on 40 tickers
    test_tickers = [
        # Technology
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
        'CRM', 'ORCL', 'ADBE', 'CSCO', 'QCOM',
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO', 'DHR',
        # Financial
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK',
        # Energy
        'XOM', 'CVX', 'COP', 'SLB',
        # Consumer
        'HD', 'MCD', 'KO', 'PEP',
        # Industrial
        'CAT', 'BA', 'GE',
        # Communication
        'DIS', 'CMCSA'
    ]
    
    print("🚀 RUNNING FULL SPECTRUM TEST ON 40 TICKERS...")
    
    results = []
    for ticker in test_tickers:
        result = test_system.score_stock(ticker)
        if result:
            results.append(result)
    
    # Export to CSV
    test_system.export_to_csv(results, "full_spectrum_results.csv")
    
    # Analyze
    test_system.analyze_full_spectrum_results(results)
    
    test_system.disconnect_db()
    print(f"\n✅ COMPLETED! Results in full_spectrum_results.csv")

if __name__ == "__main__":
    main()
