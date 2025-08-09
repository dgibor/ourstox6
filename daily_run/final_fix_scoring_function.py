#!/usr/bin/env python3
"""
Final fix for the upsert_company_scores function - only use existing columns
"""

from database import DatabaseManager
import os

def final_fix_scoring_function():
    """Fix the upsert_company_scores function to only use existing columns"""
    try:
        db = DatabaseManager()
        print("Database connection successful")
        
        # Create a corrected function that only uses existing columns
        corrected_function = """
        CREATE OR REPLACE FUNCTION upsert_company_scores(
            p_ticker VARCHAR(10),
            p_fundamental_health_score DECIMAL(5,2),
            p_fundamental_health_grade VARCHAR(20),
            p_fundamental_health_components JSONB,
            p_fundamental_risk_score DECIMAL(5,2),
            p_fundamental_risk_level VARCHAR(20),
            p_fundamental_risk_components JSONB,
            p_value_investment_score DECIMAL(5,2),
            p_value_rating VARCHAR(20),
            p_value_components JSONB,
            p_technical_health_score DECIMAL(5,2),
            p_technical_health_grade VARCHAR(20),
            p_technical_health_components JSONB,
            p_trading_signal_score DECIMAL(5,2),
            p_trading_signal_rating VARCHAR(20),
            p_trading_signal_components JSONB,
            p_technical_risk_score DECIMAL(5,2),
            p_technical_risk_level VARCHAR(20),
            p_technical_risk_components JSONB,
            p_overall_score DECIMAL(5,2),
            p_overall_grade VARCHAR(20),
            p_fundamental_red_flags JSONB,
            p_fundamental_yellow_flags JSONB,
            p_technical_red_flags JSONB,
            p_technical_yellow_flags JSONB
        ) RETURNS VOID AS $$
        BEGIN
            -- Insert into historical table (only the columns that actually exist)
            INSERT INTO company_scores_historical (
                ticker, date_calculated,
                fundamental_health_score, fundamental_health_grade,
                fundamental_risk_score, fundamental_risk_level,
                value_investment_score, value_rating,
                technical_health_score, technical_health_grade,
                trading_signal_score, trading_signal_rating,
                technical_risk_score, technical_risk_level,
                overall_score, overall_grade
            ) VALUES (
                p_ticker, CURRENT_DATE,
                p_fundamental_health_score, p_fundamental_health_grade,
                p_fundamental_risk_score, p_fundamental_risk_level,
                p_value_investment_score, p_value_rating,
                p_technical_health_score, p_technical_health_grade,
                p_trading_signal_score, p_trading_signal_rating,
                p_technical_risk_score, p_technical_risk_level,
                p_overall_score, p_overall_grade
            )
            ON CONFLICT (ticker, date_calculated) DO UPDATE SET
                fundamental_health_score = EXCLUDED.fundamental_health_score,
                fundamental_health_grade = EXCLUDED.fundamental_health_grade,
                fundamental_risk_score = EXCLUDED.fundamental_risk_score,
                fundamental_risk_level = EXCLUDED.fundamental_risk_level,
                value_investment_score = EXCLUDED.value_investment_score,
                value_rating = EXCLUDED.value_rating,
                technical_health_score = EXCLUDED.technical_health_score,
                technical_health_grade = EXCLUDED.technical_health_grade,
                trading_signal_score = EXCLUDED.trading_signal_score,
                trading_signal_rating = EXCLUDED.trading_signal_rating,
                technical_risk_score = EXCLUDED.technical_risk_score,
                technical_risk_level = EXCLUDED.technical_risk_level,
                overall_score = EXCLUDED.overall_score,
                overall_grade = EXCLUDED.overall_grade,
                created_at = CURRENT_TIMESTAMP;
            
            -- Update current table (all columns)
            UPDATE company_scores_current SET
                date_calculated = CURRENT_DATE,
                fundamental_health_score = p_fundamental_health_score,
                fundamental_health_grade = p_fundamental_health_grade,
                fundamental_health_components = p_fundamental_health_components,
                fundamental_risk_score = p_fundamental_risk_score,
                fundamental_risk_level = p_fundamental_risk_level,
                fundamental_risk_components = p_fundamental_risk_components,
                value_investment_score = p_value_investment_score,
                value_rating = p_value_rating,
                value_components = p_value_components,
                technical_health_score = p_technical_health_score,
                technical_health_grade = p_technical_health_grade,
                technical_health_components = p_technical_health_components,
                trading_signal_score = p_trading_signal_score,
                trading_signal_rating = p_trading_signal_rating,
                trading_signal_components = p_trading_signal_components,
                technical_risk_score = p_technical_risk_score,
                technical_risk_level = p_technical_risk_level,
                technical_risk_components = p_technical_risk_components,
                overall_score = p_overall_score,
                overall_grade = p_overall_grade,
                fundamental_red_flags = p_fundamental_red_flags,
                fundamental_yellow_flags = p_fundamental_yellow_flags,
                technical_red_flags = p_technical_red_flags,
                technical_yellow_flags = p_technical_yellow_flags,
                updated_at = CURRENT_TIMESTAMP
            WHERE ticker = p_ticker;
            
            -- If no rows updated, insert new record
            IF NOT FOUND THEN
                INSERT INTO company_scores_current (
                    ticker, date_calculated,
                    fundamental_health_score, fundamental_health_grade, fundamental_health_components,
                    fundamental_risk_score, fundamental_risk_level, fundamental_risk_components,
                    value_investment_score, value_rating, value_components,
                    technical_health_score, technical_health_grade, technical_health_components,
                    trading_signal_score, trading_signal_rating, trading_signal_components,
                    technical_risk_score, technical_risk_level, technical_risk_components,
                    overall_score, overall_grade,
                    fundamental_red_flags, fundamental_yellow_flags,
                    technical_red_flags, technical_yellow_flags
                ) VALUES (
                    p_ticker, CURRENT_DATE,
                    p_fundamental_health_score, p_fundamental_health_grade, p_fundamental_health_components,
                    p_fundamental_risk_score, p_fundamental_risk_level, p_fundamental_risk_components,
                    p_value_investment_score, p_value_rating, p_value_components,
                    p_technical_health_score, p_technical_health_grade, p_technical_health_components,
                    p_trading_signal_score, p_trading_signal_rating, p_trading_signal_components,
                    p_technical_risk_score, p_technical_risk_level, p_technical_risk_components,
                    p_overall_score, p_overall_grade,
                    p_fundamental_red_flags, p_fundamental_yellow_flags,
                    p_technical_red_flags, p_technical_yellow_flags
                );
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        print("Installing final corrected upsert_company_scores function...")
        db.execute_update(corrected_function)
        
        print("Function updated successfully!")
        
        # Verify the function was updated
        function_exists = db.fetch_one("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_name = 'upsert_company_scores'
        """)
        
        if function_exists:
            print("✅ Function verification successful: upsert_company_scores is updated")
            return True
        else:
            print("❌ Function verification failed: upsert_company_scores not found")
            return False
            
    except Exception as e:
        print(f"Error fixing function: {e}")
        return False

if __name__ == "__main__":
    success = final_fix_scoring_function()
    if success:
        print("\n🎉 Final database function fix completed successfully!")
    else:
        print("\n❌ Final database function fix failed!")

