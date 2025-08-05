import os
import psycopg2
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_function_exists():
    """Test if the upsert_company_scores function exists and can be called"""
    
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
            # Check if function exists
            cursor.execute("""
                SELECT routine_name, routine_type 
                FROM information_schema.routines 
                WHERE routine_name = 'upsert_company_scores'
                AND routine_schema = 'public'
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"✅ Function exists: {result[0]} ({result[1]})")
            else:
                print("❌ Function does not exist")
                return
            
            # Test function call with minimal parameters
            print("Testing function call...")
            
            # Create test parameters
            test_params = (
                'TEST',  # ticker
                50.0,    # fundamental_health_score
                'C',     # fundamental_health_grade
                '{}',    # fundamental_health_components
                50.0,    # fundamental_risk_score
                'Moderate Risk',  # fundamental_risk_level
                '{}',    # fundamental_risk_components
                50.0,    # value_investment_score
                'Fair Value',  # value_rating
                '{}',    # value_components
                50.0,    # technical_health_score
                'C',     # technical_health_grade
                '{}',    # technical_health_components
                50.0,    # trading_signal_score
                'Neutral',  # trading_signal_rating
                '{}',    # trading_signal_components
                50.0,    # technical_risk_score
                'Moderate Risk',  # technical_risk_level
                '{}',    # technical_risk_components
                50.0,    # overall_score
                'C',     # overall_grade
                '[]',    # fundamental_red_flags
                '[]',    # fundamental_yellow_flags
                '[]',    # technical_red_flags
                '[]'     # technical_yellow_flags
            )
            
            print(f"Calling function with {len(test_params)} parameters...")
            
            cursor.execute("SELECT upsert_company_scores(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", test_params)
            
            print("✅ Function call successful!")
            
            # Check if data was inserted
            cursor.execute("SELECT ticker FROM company_scores_current WHERE ticker = 'TEST'")
            result = cursor.fetchone()
            if result:
                print("✅ Data was inserted into company_scores_current")
            else:
                print("❌ No data found in company_scores_current")
            
            cursor.execute("SELECT ticker FROM company_scores_historical WHERE ticker = 'TEST'")
            result = cursor.fetchone()
            if result:
                print("✅ Data was inserted into company_scores_historical")
            else:
                print("❌ No data found in company_scores_historical")
            
            # Clean up test data
            cursor.execute("DELETE FROM company_scores_current WHERE ticker = 'TEST'")
            cursor.execute("DELETE FROM company_scores_historical WHERE ticker = 'TEST'")
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
    test_function_exists() 