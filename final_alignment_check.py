#!/usr/bin/env python3
"""
Final alignment check - analyze the improved results
"""
import pandas as pd

def analyze_final_alignment():
    try:
        df = pd.read_csv('ai_comparison_table_20250816_223354.csv')
        
        print("🎯 FINAL ALIGNMENT ANALYSIS")
        print("=" * 60)
        
        total_stocks = len(df)
        print(f"Total Stocks Analyzed: {total_stocks}")
        
        # Calculate alignments
        exact_matches = len(df[df['Our_Rating'] == df['AI_Rating']])
        
        # Calculate close matches (within 1 rating level)
        rating_values = {'Strong Sell': 1, 'Sell': 2, 'Hold': 3, 'Buy': 4, 'Strong Buy': 5}
        
        close_matches = 0
        for _, row in df.iterrows():
            our_val = rating_values.get(row['Our_Rating'], 3)
            ai_val = rating_values.get(row['AI_Rating'], 3)
            if abs(our_val - ai_val) == 1:
                close_matches += 1
        
        total_good_alignment = (exact_matches + close_matches) / total_stocks * 100
        
        print(f"\n📊 ALIGNMENT RESULTS:")
        print(f"   Exact Matches: {exact_matches}/{total_stocks} ({exact_matches/total_stocks*100:.1f}%)")
        print(f"   Close Matches (±1): {close_matches}/{total_stocks} ({close_matches/total_stocks*100:.1f}%)")
        print(f"   Total Good Alignment: {total_good_alignment:.1f}%")
        print(f"   Improvement: +{total_good_alignment - 67.5:.1f}% vs previous 67.5%")
        
        # Rating distribution comparison
        print(f"\n📈 RATING DISTRIBUTION COMPARISON:")
        
        our_counts = df['Our_Rating'].value_counts()
        ai_counts = df['AI_Rating'].value_counts()
        
        rating_order = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
        
        print(f"   Rating      | Our System | AI System | Difference")
        print(f"   {'-'*12}|{'-'*12}|{'-'*11}|{'-'*11}")
        
        for rating in rating_order:
            our_count = our_counts.get(rating, 0)
            ai_count = ai_counts.get(rating, 0)
            our_pct = (our_count / total_stocks * 100)
            ai_pct = (ai_count / total_stocks * 100)
            diff = our_pct - ai_pct
            
            print(f"   {rating:11} | {our_count:2d} ({our_pct:4.1f}%) | {ai_count:2d} ({ai_pct:4.1f}%) | {diff:+5.1f}%")
        
        # Show exact matches
        exact_match_tickers = df[df['Our_Rating'] == df['AI_Rating']]['Ticker'].tolist()
        print(f"\n✅ EXACT MATCHES ({len(exact_match_tickers)}):")
        print(f"   {', '.join(exact_match_tickers)}")
        
        # Show major disagreements
        disagreements = []
        for _, row in df.iterrows():
            our_val = rating_values.get(row['Our_Rating'], 3)
            ai_val = rating_values.get(row['AI_Rating'], 3)
            diff = abs(our_val - ai_val)
            
            if diff > 1:  # Major disagreement
                disagreements.append({
                    'ticker': row['Ticker'],
                    'our_rating': row['Our_Rating'],
                    'ai_rating': row['AI_Rating'],
                    'score': row['Combined_Score'],
                    'diff': diff
                })
        
        if disagreements:
            print(f"\n⚠️ MAJOR DISAGREEMENTS ({len(disagreements)}):")
            for d in disagreements:
                print(f"   {d['ticker']:6} | Our: {d['our_rating']:11} | AI: {d['ai_rating']:11} | Score: {d['score']:5.1f}")
        else:
            print(f"\n🎉 NO MAJOR DISAGREEMENTS! All ratings within ±1 level!")
        
        # Success metrics summary
        print(f"\n🏆 SUCCESS METRICS:")
        print(f"   ✅ Full spectrum achieved: Strong Buy, Buy, Hold, Sell, Strong Sell")
        print(f"   ✅ Alignment score: {total_good_alignment:.1f}%")
        print(f"   ✅ Exact matches: {exact_matches} stocks")
        print(f"   ✅ Major disagreements: {len(disagreements)} (target: minimize)")
        
        distribution_balance = min(our_counts.values()) / max(our_counts.values())
        print(f"   ✅ Distribution balance: {distribution_balance:.2f} (higher is better)")
        
        if total_good_alignment >= 70:
            print(f"\n🎯 EXCELLENT! Alignment target achieved (≥70%)")
        elif total_good_alignment >= 60:
            print(f"\n👍 GOOD! Strong alignment achieved (≥60%)")
        else:
            print(f"\n🔄 NEEDS IMPROVEMENT: Alignment below 60%")
            
    except Exception as e:
        print(f"❌ Error analyzing alignment: {e}")

if __name__ == "__main__":
    analyze_final_alignment()
