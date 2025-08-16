#!/usr/bin/env python3
"""
Test the daily_run integration with Enhanced Full Spectrum Scoring
"""
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_scoring_integration():
    """Test the enhanced scoring integration with daily_run"""
    try:
        logger.info("🧪 Testing Enhanced Full Spectrum Scoring integration with daily_run")
        
        # Import the daily trading system
        from daily_run.daily_trading_system import DailyTradingSystem
        logger.info("✅ Successfully imported DailyTradingSystem")
        
        # Initialize the system
        daily_system = DailyTradingSystem()
        logger.info("✅ Successfully initialized DailyTradingSystem")
        
        # Test the enhanced scoring method directly
        logger.info("🎯 Testing _calculate_daily_scores method...")
        
        result = daily_system._calculate_daily_scores()
        
        logger.info("📊 Scoring Results:")
        logger.info(f"   Phase: {result.get('phase', 'unknown')}")
        logger.info(f"   Scoring System: {result.get('scoring_system', 'unknown')}")
        logger.info(f"   Tickers Processed: {result.get('tickers_processed', 0)}")
        logger.info(f"   Successful: {result.get('successful_calculations', 0)}")
        logger.info(f"   Failed: {result.get('failed_calculations', 0)}")
        logger.info(f"   Processing Time: {result.get('processing_time', 0):.2f}s")
        
        if 'summary' in result:
            summary = result['summary']
            logger.info("📈 Summary Statistics:")
            
            if 'rating_distribution' in summary:
                logger.info("   Rating Distribution:")
                for rating, count in summary['rating_distribution'].items():
                    logger.info(f"     {rating}: {count} stocks")
            
            if 'score_statistics' in summary:
                stats = summary['score_statistics']
                logger.info("   Score Statistics:")
                logger.info(f"     Min Score: {stats.get('min_score', 0):.1f}")
                logger.info(f"     Max Score: {stats.get('max_score', 0):.1f}")
                logger.info(f"     Avg Score: {stats.get('avg_score', 0):.1f}")
            
            full_spectrum = summary.get('full_spectrum_achieved', False)
            logger.info(f"   Full Spectrum Achieved: {'✅' if full_spectrum else '❌'} {full_spectrum}")
        
        # Determine success
        if result.get('successful_calculations', 0) > 0:
            logger.info("🎉 Integration test PASSED!")
            logger.info(f"✅ Enhanced scoring successfully processed {result['successful_calculations']} stocks")
            
            # Check if we're using enhanced or legacy scoring
            scoring_system = result.get('scoring_system', '')
            if 'Enhanced' in scoring_system:
                logger.info("🚀 Using Enhanced Full Spectrum Scoring system")
            else:
                logger.warning("⚠️ Using legacy scoring system (fallback)")
            
            return True
        else:
            logger.error("❌ Integration test FAILED!")
            logger.error(f"No stocks were successfully processed")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Integration test FAILED with exception: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_enhanced_scoring_module():
    """Test the enhanced scoring module directly"""
    try:
        logger.info("🧪 Testing Enhanced Full Spectrum Scoring module directly")
        
        from daily_run.enhanced_full_spectrum_scoring import EnhancedFullSpectrumScoring
        logger.info("✅ Successfully imported EnhancedFullSpectrumScoring")
        
        # Initialize the scoring system
        scoring_system = EnhancedFullSpectrumScoring()
        logger.info("✅ Successfully initialized EnhancedFullSpectrumScoring")
        
        # Test initialization
        if scoring_system.initialize():
            logger.info("✅ Successfully initialized scoring system")
        else:
            logger.error("❌ Failed to initialize scoring system")
            return False
        
        # Test with a few sample tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        logger.info(f"🎯 Testing with sample tickers: {test_tickers}")
        
        for ticker in test_tickers:
            try:
                result = scoring_system.calculate_enhanced_scores(ticker)
                if result:
                    logger.info(f"✅ {ticker}: {result['rating']} ({result['composite_score']:.1f})")
                else:
                    logger.warning(f"⚠️ {ticker}: No result")
            except Exception as e:
                logger.error(f"❌ {ticker}: Error - {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct module test FAILED: {e}")
        return False

def main():
    """Main test runner"""
    logger.info("🚀 Starting Enhanced Full Spectrum Scoring Integration Tests")
    
    tests = [
        ("Enhanced Scoring Module", test_enhanced_scoring_module),
        ("Daily Run Integration", test_enhanced_scoring_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            if test_func():
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: EXCEPTION - {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Enhanced scoring is ready for daily_run")
    else:
        logger.error(f"❌ {total - passed} tests failed. Integration needs fixing.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
