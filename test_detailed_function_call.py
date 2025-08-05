import os
import psycopg2
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_detailed_function_call():
    """Test the function call with the exact same data structure as the scoring system"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        with conn.cursor() as cursor:
            # Create test data that mimics the scoring system output
            fundamental_scores = {
                'fundamental_health_score': 68.0,
                'fundamental_health_grade': 'B',
                'fundamental_health_components': {
                    'financial_health': 50.0,
                    'profitability': 100.0,
                    'quality': 65.0,
                    'growth': 50.0
                },
                'fundamental_risk_score': 40.0,
                'fundamental_risk_level': 'Moderate Risk',
                'fundamental_risk_components': {
                    'debt_risk': 50,
                    'liquidity_risk': 50,
                    'profitability_risk': 0,
                    'growth_risk': 50
                },
                'value_investment_score': 50.0,
                'value_rating': 'Fair Value',
                'value_components': {
                    'pe_ratio': 50,
                    'pb_ratio': 50,
                    'peg_ratio': 50,
                    'graham_number': 50,
                    'ev_ebitda': 50
                },
                'fundamental_red_flags': [],
                'fundamental_yellow_flags': []
            }
            
            technical_scores = {
                'technical_health_score': 63.52,
                'technical_health_grade': 'B',
                'technical_health_components': {
                    'trend_strength': 60.5,
                    'momentum': 34.0,
                    'support_resistance': 100.0,
                    'volume_confirmation': 59.0
                },
                'trading_signal_score': 60.0,
                'trading_signal_rating': 'Buy',
                'trading_signal_components': {
                    'buy_signals': 65.0,
                    'sell_signals': 35.0,
                    'signal_strength': 100
                },
                'technical_risk_score': 74.06,
                'technical_risk_level': 'Very High Risk',
                'technical_risk_components': {
                    'volatility_risk': 93.75,
                    'trend_reversal_risk': 75,
                    'support_breakdown_risk': 75,
                    'volume_risk': 25
                },
                'technical_red_flags': ['RSI at extreme levels (704.0)', 'Extremely high volatility (ATR > 15%)'],
                'technical_yellow_flags': ['RSI approaching extremes (704.0)', 'High volatility (ATR > 10%)']
            }
            
            # Calculate overall score
            overall_score = (fundamental_scores['fundamental_health_score'] + 
                           technical_scores['technical_health_score']) / 2
            overall_grade = 'B'  # Simplified for test
            
            # Create parameters exactly like the scoring system
            params = (
                'AAPL',  # ticker
                fundamental_scores['fundamental_health_score'],
                fundamental_scores['fundamental_health_grade'],
                json.dumps(fundamental_scores['fundamental_health_components']),
                fundamental_scores['fundamental_risk_score'],
                fundamental_scores['fundamental_risk_level'],
                json.dumps(fundamental_scores['fundamental_risk_components']),
                fundamental_scores['value_investment_score'],
                fundamental_scores['value_rating'],
                json.dumps(fundamental_scores['value_components']),
                technical_scores['technical_health_score'],
                technical_scores['technical_health_grade'],
                json.dumps(technical_scores['technical_health_components']),
                technical_scores['trading_signal_score'],
                technical_scores['trading_signal_rating'],
                json.dumps(technical_scores['trading_signal_components']),
                technical_scores['technical_risk_score'],
                technical_scores['technical_risk_level'],
                json.dumps(technical_scores['technical_risk_components']),
                overall_score,
                overall_grade,
                json.dumps(fundamental_scores['fundamental_red_flags']),
                json.dumps(fundamental_scores['fundamental_yellow_flags']),
                json.dumps(technical_scores['technical_red_flags']),
                json.dumps(technical_scores['technical_yellow_flags'])
            )
            
            print(f"Testing with {len(params)} parameters:")
            for i, param in enumerate(params):
                print(f"  {i+1}: {type(param).__name__} = {param}")
            
            print("\nCalling function...")
            
            cursor.execute("SELECT upsert_company_scores(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", params)
            
            print("✅ Function call successful!")
            
            # Check if data was inserted
            cursor.execute("SELECT ticker, fundamental_health_score, technical_health_score FROM company_scores_current WHERE ticker = 'AAPL'")
            result = cursor.fetchone()
            if result:
                print(f"✅ Data inserted: {result}")
            else:
                print("❌ No data found in company_scores_current")
            
            # Clean up test data
            cursor.execute("DELETE FROM company_scores_current WHERE ticker = 'AAPL'")
            cursor.execute("DELETE FROM company_scores_historical WHERE ticker = 'AAPL'")
            conn.commit()
            print("✅ Test data cleaned up")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_detailed_function_call() 