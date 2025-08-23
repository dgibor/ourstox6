#!/usr/bin/env python3
"""
Test Analyst Integration

Tests the integration of the analyst scorer into the daily run trading system.
"""

import logging
import sys
import os
from datetime import date

# Add the daily_run directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_analyst_scorer():
    """Test the analyst scorer functionality"""
    try:
        logger.info("🧪 Testing Analyst Scorer Integration")
        
        # Test import
        from analyst_scorer import AnalystScorer
        logger.info("✅ AnalystScorer imported successfully")
        
        # Test initialization
        from database import DatabaseManager
        db = DatabaseManager()
        analyst_scorer = AnalystScorer(db=db)
        logger.info("✅ AnalystScorer initialized successfully")
        
        # Test with a sample ticker
        test_ticker = "AAPL"
        logger.info(f"🧪 Testing analyst scoring for {test_ticker}")
        
        # Calculate analyst score
        analyst_scores = analyst_scorer.calculate_analyst_score(test_ticker)
        
        if analyst_scores:
            logger.info(f"✅ Analyst scores calculated for {test_ticker}")
            logger.info(f"   Composite Score: {analyst_scores.get('composite_analyst_score', 'N/A')}")
            logger.info(f"   Earnings Proximity: {analyst_scores.get('earnings_proximity_score', 'N/A')}")
            logger.info(f"   Earnings Surprise: {analyst_scores.get('earnings_surprise_score', 'N/A')}")
            logger.info(f"   Analyst Sentiment: {analyst_scores.get('analyst_sentiment_score', 'N/A')}")
            logger.info(f"   Price Target: {analyst_scores.get('price_target_score', 'N/A')}")
            logger.info(f"   Revision Score: {analyst_scores.get('revision_score', 'N/A')}")
            logger.info(f"   Data Quality: {analyst_scores.get('data_quality_score', 'N/A')}")
            logger.info(f"   Status: {analyst_scores.get('calculation_status', 'N/A')}")
            
            # Test storage
            logger.info(f"🧪 Testing storage for {test_ticker}")
            storage_success = analyst_scorer.store_analyst_score(test_ticker, analyst_scores)
            
            if storage_success:
                logger.info(f"✅ Analyst scores stored successfully for {test_ticker}")
            else:
                logger.warning(f"⚠️ Failed to store analyst scores for {test_ticker}")
        else:
            logger.error(f"❌ Failed to calculate analyst scores for {test_ticker}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_daily_trading_system_integration():
    """Test the integration with the daily trading system"""
    try:
        logger.info("🧪 Testing Daily Trading System Integration")
        
        # Test import
        from daily_trading_system import DailyTradingSystem
        logger.info("✅ DailyTradingSystem imported successfully")
        
        # Test initialization
        trading_system = DailyTradingSystem()
        logger.info("✅ DailyTradingSystem initialized successfully")
        
        # Test the analyst scoring method
        logger.info("🧪 Testing _calculate_analyst_scores method")
        
        # Get active tickers
        tickers = trading_system._get_active_tickers()
        logger.info(f"📊 Found {len(tickers)} active tickers")
        
        if tickers:
            # Test with first few tickers
            test_tickers = tickers[:3]
            logger.info(f"🧪 Testing with tickers: {test_tickers}")
            
            for ticker in test_tickers:
                logger.info(f"🧪 Testing analyst scoring for {ticker}")
                
                # Import analyst scorer
                from analyst_scorer import AnalystScorer
                analyst_scorer = AnalystScorer(db=trading_system.db)
                
                # Calculate scores
                scores = analyst_scorer.calculate_analyst_score(ticker)
                
                if scores:
                    logger.info(f"   ✅ {ticker}: Score {scores.get('composite_analyst_score', 'N/A')}")
                else:
                    logger.warning(f"   ⚠️ {ticker}: No scores calculated")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Analyst Integration Tests")
    
    # Test 1: Analyst Scorer
    test1_success = test_analyst_scorer()
    
    # Test 2: Daily Trading System Integration
    test2_success = test_daily_trading_system_integration()
    
    # Summary
    logger.info("📊 Test Results Summary")
    logger.info(f"   Analyst Scorer: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    logger.info(f"   Daily Trading Integration: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        logger.info("🎉 All tests passed! Analyst integration is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
