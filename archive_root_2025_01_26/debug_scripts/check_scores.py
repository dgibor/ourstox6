#!/usr/bin/env python3
"""Check stored scores in database"""

from daily_run.database import DatabaseManager

def check_scores():
    db = DatabaseManager()
    try:
        db.connect()
        tickers = ['AAON', 'AAPL', 'AAXJ', 'ABBV', 'ABCM']
        result = db.execute_query(f"""
            SELECT ticker, calculation_date, 
                   swing_trader_score, momentum_trader_score, long_term_investor_score,
                   conservative_investor_score, garp_investor_score, deep_value_investor_score,
                   composite_analyst_score
            FROM daily_scores 
            WHERE ticker IN %s
            ORDER BY ticker, calculation_date DESC
        """, (tuple(tickers),))
        print("Stored scores for 5 tickers:")
        print("=" * 80)
        for row in result:
            ticker, date, tech_swing, tech_momentum, tech_long, fund_conservative, fund_garp, fund_deep, analyst = row
            print(f"\n{ticker} ({date}):")
            print(f"  Technical Scores:")
            print(f"    Swing Trader: {tech_swing}")
            print(f"    Momentum Trader: {tech_momentum}")
            print(f"    Long Term Investor: {tech_long}")
            print(f"  Fundamental Scores:")
            print(f"    Conservative Investor: {fund_conservative}")
            print(f"    GARP Investor: {fund_garp}")
            print(f"    Deep Value Investor: {fund_deep}")
            print(f"  Analyst Score: {analyst}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_scores() 