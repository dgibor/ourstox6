"""
Test Script for Score Calculator

This script tests the scoring system implementation to ensure all components
work correctly before integration into the daily run pipeline.
"""

import logging
import sys
from datetime import date
from ..database import DatabaseManager
from .score_orchestrator import ScoreOrchestrator
from .schema_manager import ScoreSchemaManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_database_setup():
    """Test database schema setup"""
    try:
        logger.info("Testing database setup...")
        
        db = DatabaseManager()
        schema_manager = ScoreSchemaManager(db)
        
        # Test table creation
        success = schema_manager.create_tables()
        
        if success:
            logger.info("✅ Database setup test passed")
            return True
        else:
            logger.error("❌ Database setup test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database setup test error: {e}")
        return False


def test_single_ticker_scoring():
    """Test scoring for a single ticker"""
    try:
        logger.info("Testing single ticker scoring...")
        
        # Use a well-known ticker that should have data
        test_ticker = 'AAPL'
        calculation_date = date.today()
        
        orchestrator = ScoreOrchestrator()
        
        # Test single ticker processing
        result = orchestrator.process_single_ticker(test_ticker, calculation_date)
        
        if result['technical_success'] or result['fundamental_success'] or result['analyst_success']:
            logger.info(f"✅ Single ticker scoring test passed for {test_ticker}")
            logger.info(f"   Technical: {result['technical_success']}")
            logger.info(f"   Fundamental: {result['fundamental_success']}")
            logger.info(f"   Analyst: {result['analyst_success']}")
            return True
        else:
            logger.error(f"❌ Single ticker scoring test failed for {test_ticker}")
            logger.error(f"   Errors: {result['errors']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Single ticker scoring test error: {e}")
        return False


def test_system_status():
    """Test system status functionality"""
    try:
        logger.info("Testing system status...")
        
        orchestrator = ScoreOrchestrator()
        status = orchestrator.get_scoring_status()
        
        if status['system_status'] == 'operational':
            logger.info("✅ System status test passed")
            logger.info(f"   Total active tickers: {status['total_active_tickers']}")
            return True
        else:
            logger.error(f"❌ System status test failed: {status['system_status']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ System status test error: {e}")
        return False


def test_batch_scoring():
    """Test batch scoring with a small number of tickers"""
    try:
        logger.info("Testing batch scoring...")
        
        orchestrator = ScoreOrchestrator()
        
        # Test with just 5 tickers and 1 hour time limit
        result = orchestrator.run_daily_scoring(
            max_tickers=5,
            max_time_hours=1,
            force_recalculate=False
        )
        
        if result['success']:
            batch_result = result['batch_result']
            logger.info("✅ Batch scoring test passed")
            logger.info(f"   Processed: {batch_result['processed_count']}/{batch_result['total_count']} tickers")
            logger.info(f"   Technical success rate: {batch_result['technical_success_rate']:.1%}")
            logger.info(f"   Fundamental success rate: {batch_result['fundamental_success_rate']:.1%}")
            logger.info(f"   Analyst success rate: {batch_result['analyst_success_rate']:.1%}")
            return True
        else:
            logger.error(f"❌ Batch scoring test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Batch scoring test error: {e}")
        return False


def test_data_retrieval():
    """Test data retrieval from existing tables"""
    try:
        logger.info("Testing data retrieval...")
        
        db = DatabaseManager()
        
        # Test daily_charts data
        charts_query = "SELECT COUNT(*) FROM daily_charts WHERE ticker = 'AAPL'"
        charts_result = db.execute_query(charts_query)
        charts_count = charts_result[0][0] if charts_result else 0
        
        # Test financial_ratios data
        ratios_query = "SELECT COUNT(*) FROM financial_ratios WHERE ticker = 'AAPL'"
        ratios_result = db.execute_query(ratios_query)
        ratios_count = ratios_result[0][0] if ratios_result else 0
        
        # Test earnings_calendar data
        earnings_query = "SELECT COUNT(*) FROM earnings_calendar WHERE ticker = 'AAPL'"
        earnings_result = db.execute_query(earnings_query)
        earnings_count = earnings_result[0][0] if earnings_result else 0
        
        logger.info(f"   Daily charts records for AAPL: {charts_count}")
        logger.info(f"   Financial ratios records for AAPL: {ratios_count}")
        logger.info(f"   Earnings calendar records for AAPL: {earnings_count}")
        
        if charts_count > 0 or ratios_count > 0 or earnings_count > 0:
            logger.info("✅ Data retrieval test passed")
            return True
        else:
            logger.error("❌ Data retrieval test failed - no data found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Data retrieval test error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("Starting comprehensive test suite...")
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Data Retrieval", test_data_retrieval),
        ("System Status", test_system_status),
        ("Single Ticker Scoring", test_single_ticker_scoring),
        ("Batch Scoring", test_batch_scoring)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"TEST SUMMARY: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 All tests passed! The scoring system is ready for use.")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed. Please fix issues before deployment.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1) 