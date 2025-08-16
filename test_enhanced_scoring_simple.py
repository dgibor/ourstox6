#!/usr/bin/env python3
"""
Simple test of Enhanced Full Spectrum Scoring with database connection
"""
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_scoring_with_db():
    """Test enhanced scoring with proper database connection"""
    try:
        logger.info("🧪 Testing Enhanced Full Spectrum Scoring with database")
        
        # Import database manager first
        from daily_run.database import DatabaseManager
        
        # Initialize database
        db = DatabaseManager()
        db.connect()
        logger.info("✅ Database connected successfully")
        
        # Import and initialize enhanced scoring
        from daily_run.enhanced_full_spectrum_scoring import EnhancedFullSpectrumScoring
        
        scoring_system = EnhancedFullSpectrumScoring(db=db)
        
        if not scoring_system.initialize():
            logger.error("Failed to initialize scoring system")
            return False
        
        logger.info("✅ Enhanced scoring system initialized")
        
        # Test with sample tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMD', 'SLB']
        logger.info(f"🎯 Testing with tickers: {test_tickers}")
        
        results = []
        for ticker in test_tickers:
            try:
                result = scoring_system.calculate_enhanced_scores(ticker)
                if result:
                    results.append(result)
                    logger.info(f"✅ {ticker}: {result['rating']} ({result['composite_score']:.1f})")
                else:
                    logger.warning(f"⚠️ {ticker}: No result")
            except Exception as e:
                logger.error(f"❌ {ticker}: Error - {e}")
        
        # Test batch processing
        if results:
            logger.info("🎯 Testing batch processing...")
            batch_results = scoring_system.calculate_scores_for_all_tickers(test_tickers)
            
            logger.info("📊 Batch Results:")
            logger.info(f"   Total: {batch_results.get('total_tickers', 0)}")
            logger.info(f"   Successful: {batch_results.get('successful_calculations', 0)}")
            logger.info(f"   Failed: {batch_results.get('failed_calculations', 0)}")
            
            if 'summary' in batch_results:
                summary = batch_results['summary']
                if 'rating_distribution' in summary:
                    logger.info("   Rating Distribution:")
                    for rating, count in summary['rating_distribution'].items():
                        logger.info(f"     {rating}: {count} stocks")
                
                full_spectrum = summary.get('full_spectrum_achieved', False)
                logger.info(f"   Full Spectrum: {'✅' if full_spectrum else '❌'}")
        
        # Cleanup
        db.disconnect()
        logger.info("✅ Database disconnected")
        
        success = len(results) > 0
        if success:
            logger.info("🎉 Enhanced scoring test PASSED!")
        else:
            logger.error("❌ Enhanced scoring test FAILED!")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test runner"""
    logger.info("🚀 Starting Enhanced Full Spectrum Scoring Database Test")
    
    if test_enhanced_scoring_with_db():
        logger.info("✅ Test completed successfully")
        return True
    else:
        logger.error("❌ Test failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
