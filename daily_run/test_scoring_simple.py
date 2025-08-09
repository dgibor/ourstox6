#!/usr/bin/env python3
"""
Simple test script for scoring integration in daily trading system
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_scoring_simple.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_database_scoring_function():
    """Test the database scoring function"""
    
    logger.info("Testing Database Scoring Function")
    logger.info("=" * 40)
    
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Test the upsert_company_scores method
        test_score_data = {
            'fundamental_health_score': 75.0,
            'fundamental_health_grade': 'Buy',
            'fundamental_health_components': {'test': 'data'},
            'fundamental_risk_score': 25.0,
            'fundamental_risk_level': 'Buy',
            'fundamental_risk_components': {'test': 'data'},
            'value_investment_score': 80.0,
            'value_rating': 'Buy',
            'value_components': {'test': 'data'},
            'technical_health_score': 70.0,
            'technical_health_grade': 'Buy',
            'technical_health_components': {'test': 'data'},
            'trading_signal_score': 65.0,
            'trading_signal_rating': 'Buy',
            'trading_signal_components': {'test': 'data'},
            'technical_risk_score': 30.0,
            'technical_risk_level': 'Buy',
            'technical_risk_components': {'test': 'data'},
            'composite_score': 72.5,
            'composite_grade': 'Buy',
            'fundamental_red_flags': [],
            'fundamental_yellow_flags': [],
            'technical_red_flags': [],
            'technical_yellow_flags': []
        }
        
        # Test with a real ticker that exists in the stocks table
        success = db.upsert_company_scores('AAPL', test_score_data)
        
        if success:
            logger.info("Database scoring function test PASSED")
            return True
        else:
            logger.error("Database scoring function test FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False

def test_scoring_method():
    """Test the scoring calculation method with limited tickers"""
    
    logger.info("Testing Scoring Calculation Method (Limited to 3 tickers)")
    logger.info("=" * 40)
    
    try:
        from daily_trading_system import DailyTradingSystem
        
        logger.info("Successfully imported DailyTradingSystem")
        
        # Initialize the system
        trading_system = DailyTradingSystem()
        logger.info("Successfully initialized DailyTradingSystem")
        
        # Import scoring calculators directly
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        from calc_fundamental_scores import FundamentalScoreCalculator
        from calc_technical_scores import TechnicalScoreCalculator
        
        # Initialize scoring calculators
        fundamental_calc = FundamentalScoreCalculator()
        technical_calc = TechnicalScoreCalculator()
        
        # Test with only 3 tickers to make it fast
        logger.info("Testing scoring calculation method with limited tickers...")
        
        # Get a small subset of tickers for testing
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']  # Only 3 tickers for fast testing
        
        # Calculate scores for limited tickers
        successful_calculations = 0
        failed_calculations = 0
        
        for ticker in test_tickers:
            try:
                logger.info(f"Calculating scores for {ticker}...")
                
                # Calculate fundamental scores
                fundamental_scores = fundamental_calc.calculate_fundamental_scores(ticker)
                if fundamental_scores.get('error'):
                    logger.error(f"Fundamental calculation failed for {ticker}: {fundamental_scores['error']}")
                    failed_calculations += 1
                    continue
                
                # Calculate technical scores
                technical_scores = technical_calc.calculate_technical_scores(ticker)
                if technical_scores.get('error'):
                    logger.error(f"Technical calculation failed for {ticker}: {technical_scores['error']}")
                    failed_calculations += 1
                    continue
                
                # Store combined scores using the trading system's method
                success = trading_system._store_combined_scores(ticker, fundamental_scores, technical_scores)
                
                if success:
                    logger.info(f"Successfully calculated and stored scores for {ticker}")
                    successful_calculations += 1
                else:
                    logger.error(f"Failed to store scores for {ticker}")
                    failed_calculations += 1
                    
            except Exception as e:
                logger.error(f"Error calculating scores for {ticker}: {e}")
                failed_calculations += 1
        
        logger.info(f"Scoring Results (Limited Test):")
        logger.info(f"   - Tickers processed: {len(test_tickers)}")
        logger.info(f"   - Successful calculations: {successful_calculations}")
        logger.info(f"   - Failed calculations: {failed_calculations}")
        
        if successful_calculations > 0:
            logger.info("Scoring integration test PASSED")
            return True
        else:
            logger.warning("No successful scoring calculations")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

def main():
    """Main test function"""
    
    logger.info("Starting Simple Scoring Integration Tests (Limited)")
    logger.info("=" * 60)
    
    # Test 1: Database scoring function
    db_test_passed = test_database_scoring_function()
    
    # Test 2: Scoring method (limited)
    scoring_test_passed = test_scoring_method()
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Database Scoring Function: {'PASSED' if db_test_passed else 'FAILED'}")
    logger.info(f"Scoring Method (Limited): {'PASSED' if scoring_test_passed else 'FAILED'}")
    
    overall_passed = db_test_passed and scoring_test_passed
    
    if overall_passed:
        logger.info("ALL TESTS PASSED - Scoring integration is working!")
    else:
        logger.error("SOME TESTS FAILED - Please check the logs for details")
    
    return overall_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
