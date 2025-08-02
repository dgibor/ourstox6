#!/usr/bin/env python3
"""
Final verification script for target tickers
"""

from daily_run.database import DatabaseManager
from datetime import date

def verify_target_tickers():
    """Verify all target tickers have complete data"""
    
    target_tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    today = date.today()
    
    print("=== FINAL VERIFICATION REPORT ===")
    print(f"Date: {today}")
    print(f"Target Tickers: {', '.join(target_tickers)}")
    print()
    
    db = DatabaseManager()
    
    all_complete = True
    verification_results = {}
    
    for ticker in target_tickers:
        print(f"🔍 Verifying {ticker}...")
        
        # Check daily_scores table
        result = db.execute_query("""
            SELECT 
                technical_calculation_status,
                fundamental_calculation_status,
                analyst_calculation_status,
                swing_trader_score,
                momentum_trader_score,
                long_term_investor_score,
                conservative_investor_score,
                garp_investor_score,
                deep_value_investor_score,
                composite_analyst_score
            FROM daily_scores 
            WHERE ticker = %s AND calculation_date = %s
        """, (ticker, today))
        
        if result:
            row = result[0]
            technical_status = row[0]
            fundamental_status = row[1]
            analyst_status = row[2]
            
            # Check if all scores are calculated
            scores = row[3:10]  # All score values
            
            technical_complete = technical_status == 'success'
            fundamental_complete = fundamental_status == 'success'
            analyst_complete = analyst_status == 'success'
            scores_populated = all(score is not None for score in scores)
            
            ticker_complete = (technical_complete and fundamental_complete and 
                             analyst_complete and scores_populated)
            
            verification_results[ticker] = {
                'technical': technical_complete,
                'fundamental': fundamental_complete,
                'analyst': analyst_complete,
                'scores_populated': scores_populated,
                'complete': ticker_complete,
                'scores': {
                    'swing_trader': row[3],
                    'momentum_trader': row[4],
                    'long_term_investor': row[5],
                    'conservative_investor': row[6],
                    'garp_investor': row[7],
                    'deep_value_investor': row[8],
                    'composite_analyst': row[9]
                }
            }
            
            if ticker_complete:
                print(f"  ✅ {ticker}: COMPLETE")
                print(f"     Technical: {technical_status}")
                print(f"     Fundamental: {fundamental_status}")
                print(f"     Analyst: {analyst_status}")
                print(f"     Scores: {scores_populated}")
            else:
                print(f"  ❌ {ticker}: INCOMPLETE")
                print(f"     Technical: {technical_status}")
                print(f"     Fundamental: {fundamental_status}")
                print(f"     Analyst: {analyst_status}")
                print(f"     Scores: {scores_populated}")
                all_complete = False
        else:
            print(f"  ❌ {ticker}: NO DATA FOUND")
            verification_results[ticker] = {
                'complete': False,
                'error': 'No data found'
            }
            all_complete = False
        
        print()
    
    # Summary
    print("=== SUMMARY ===")
    complete_count = sum(1 for r in verification_results.values() if r.get('complete', False))
    print(f"Complete: {complete_count}/{len(target_tickers)}")
    
    if all_complete:
        print("🎉 ALL TARGET TICKERS COMPLETE!")
        print()
        print("=== SCORE SUMMARY ===")
        for ticker, result in verification_results.items():
            if result.get('complete'):
                scores = result['scores']
                print(f"{ticker}:")
                print(f"  Trading: Swing({scores['swing_trader']}), Momentum({scores['momentum_trader']}), Long-term({scores['long_term_investor']})")
                print(f"  Investor: Conservative({scores['conservative_investor']}), GARP({scores['garp_investor']}), Deep Value({scores['deep_value_investor']})")
                print(f"  Analyst: {scores['composite_analyst']}")
                print()
    else:
        print("⚠️  SOME TICKERS INCOMPLETE")
        for ticker, result in verification_results.items():
            if not result.get('complete'):
                print(f"  ❌ {ticker}: {result.get('error', 'Incomplete data')}")
    
    db.disconnect()
    return all_complete

if __name__ == "__main__":
    verify_target_tickers() 