#!/usr/bin/env python3
"""
Isolated test for sentiment analysis to identify hanging issue
"""

import sys
import os
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_sentiment_analyzer():
    """Test sentiment analyzer initialization and basic functionality"""
    
    logger.info("Testing SentimentAnalyzer initialization...")
    
    try:
        # Add parent directory to path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        from sentiment_analyzer import SentimentAnalyzer
        
        logger.info("Successfully imported SentimentAnalyzer")
        
        # Initialize sentiment analyzer
        logger.info("Initializing SentimentAnalyzer...")
        sentiment_analyzer = SentimentAnalyzer()
        logger.info("Successfully initialized SentimentAnalyzer")
        
        # Test basic functionality
        logger.info("Testing basic sentiment functionality...")
        
        # Test market sentiment (should be fast)
        logger.info("Testing market sentiment...")
        market_sentiment = sentiment_analyzer.get_market_sentiment()
        logger.info(f"Market sentiment result: {market_sentiment}")
        
        # Test news sentiment for one ticker (this might be slow)
        logger.info("Testing news sentiment for AAPL...")
        news_sentiment = sentiment_analyzer.get_news_sentiment('AAPL', days_back=1)
        logger.info(f"News sentiment result: {news_sentiment}")
        
        logger.info("Sentiment analyzer test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in sentiment analyzer test: {e}")
        return False

def test_fundamental_calculator():
    """Test fundamental calculator with sentiment integration"""
    
    logger.info("Testing FundamentalScoreCalculator with sentiment...")
    
    try:
        # Add parent directory to path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        from calc_fundamental_scores import FundamentalScoreCalculator
        
        logger.info("Successfully imported FundamentalScoreCalculator")
        
        # Initialize calculator
        logger.info("Initializing FundamentalScoreCalculator...")
        fundamental_calc = FundamentalScoreCalculator()
        logger.info("Successfully initialized FundamentalScoreCalculator")
        
        # Test calculation for one ticker
        logger.info("Testing fundamental score calculation for AAPL...")
        start_time = time.time()
        
        scores = fundamental_calc.calculate_fundamental_scores('AAPL')
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Calculation completed in {duration:.2f} seconds")
        logger.info(f"Scores result: {scores}")
        
        if scores.get('error'):
            logger.error(f"Calculation failed: {scores['error']}")
            return False
        
        logger.info("Fundamental calculator test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in fundamental calculator test: {e}")
        return False

def main():
    """Main test function"""
    
    logger.info("Starting isolated sentiment analysis test")
    logger.info("=" * 60)
    
    # Test 1: Sentiment analyzer only
    logger.info("\nTEST 1: Sentiment Analyzer Only")
    success1 = test_sentiment_analyzer()
    
    if not success1:
        logger.error("Sentiment analyzer test failed. Stopping.")
        return False
    
    # Test 2: Fundamental calculator with sentiment
    logger.info("\nTEST 2: Fundamental Calculator with Sentiment")
    success2 = test_fundamental_calculator()
    
    if not success2:
        logger.error("Fundamental calculator test failed.")
        return False
    
    logger.info("\nAll tests completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

