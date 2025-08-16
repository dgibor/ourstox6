#!/usr/bin/env python3
"""
Analyze disagreements between our system and AI ratings
"""
import pandas as pd

def analyze_disagreements():
    df = pd.read_csv('ai_comparison_table_20250816_220524.csv')
    
    print("🔍 DISAGREEMENT ANALYSIS:")
    print("=" * 50)
    
    disagreements = df[df['Our_Rating'] != df['AI_Rating']]
    
    print(f"Total Disagreements: {len(disagreements)}/40 ({len(disagreements)/40*100:.1f}%)")
    print()
    
    print("SPECIFIC DISAGREEMENTS:")
    print("Ticker | Our Rating  | AI Rating   | Score | Issue")
    print("-" * 60)
    
    for _, row in disagreements.iterrows():
        ticker = row['Ticker']
        our_rating = row['Our_Rating']
        ai_rating = row['AI_Rating']
        score = row['Combined_Score']
        
        # Identify the type of disagreement
        if our_rating == 'Buy' and ai_rating in ['Hold', 'Sell', 'Strong Sell']:
            issue = "Too bullish"
        elif our_rating == 'Hold' and ai_rating in ['Buy', 'Strong Buy']:
            issue = "Too bearish"
        elif our_rating == 'Sell' and ai_rating in ['Hold', 'Buy']:
            issue = "Too bearish"
        elif our_rating == 'Buy' and ai_rating == 'Strong Buy':
            issue = "Close - need higher threshold"
        elif our_rating == 'Strong Buy' and ai_rating == 'Buy':
            issue = "Close - need lower threshold"
        else:
            issue = "Complex mismatch"
            
        print(f"{ticker:6} | {our_rating:11} | {ai_rating:11} | {score:5.1f} | {issue}")
    
    print()
    print("PATTERNS TO FIX:")
    
    # Analyze patterns
    too_bullish = len(disagreements[(disagreements['Our_Rating'] == 'Buy') & 
                                  (disagreements['AI_Rating'].isin(['Hold', 'Sell', 'Strong Sell']))])
    too_bearish = len(disagreements[(disagreements['Our_Rating'].isin(['Hold', 'Sell'])) & 
                                  (disagreements['AI_Rating'].isin(['Buy', 'Strong Buy']))])
    
    print(f"- Too Bullish (Our Buy vs AI Hold/Sell): {too_bullish} cases")
    print(f"- Too Bearish (Our Hold/Sell vs AI Buy): {too_bearish} cases")
    
    # Score analysis for threshold adjustment
    print()
    print("SCORE RANGES FOR THRESHOLD ADJUSTMENT:")
    
    # Current thresholds: Strong Buy ≥72, Buy ≥62, Hold ≥58, Sell ≥56
    strong_buy_scores = df[df['AI_Rating'] == 'Strong Buy']['Combined_Score'].values
    buy_scores = df[df['AI_Rating'] == 'Buy']['Combined_Score'].values
    hold_scores = df[df['AI_Rating'] == 'Hold']['Combined_Score'].values
    sell_scores = df[df['AI_Rating'] == 'Sell']['Combined_Score'].values
    strong_sell_scores = df[df['AI_Rating'] == 'Strong Sell']['Combined_Score'].values
    
    print(f"AI Strong Buy scores: {list(strong_buy_scores)} (avg: {strong_buy_scores.mean():.1f})")
    print(f"AI Buy scores: {buy_scores.min():.1f} - {buy_scores.max():.1f} (avg: {buy_scores.mean():.1f})")
    print(f"AI Hold scores: {hold_scores.min():.1f} - {hold_scores.max():.1f} (avg: {hold_scores.mean():.1f})")
    print(f"AI Sell scores: {sell_scores.min():.1f} - {sell_scores.max():.1f} (avg: {sell_scores.mean():.1f})")
    if len(strong_sell_scores) > 0:
        print(f"AI Strong Sell scores: {strong_sell_scores.min():.1f} - {strong_sell_scores.max():.1f} (avg: {strong_sell_scores.mean():.1f})")

if __name__ == "__main__":
    analyze_disagreements()
