#!/usr/bin/env python3
"""
Test Enhanced Full Spectrum Scoring with 20 additional tickers
Validates performance and rating distribution across different sectors
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

def test_enhanced_scoring_20_more():
    """Test enhanced scoring with 20 additional diverse tickers"""
    try:
        logger.info("🧪 Testing Enhanced Full Spectrum Scoring with 20 Additional Tickers")
        
        # Import database manager and enhanced scoring
        from daily_run.database import DatabaseManager
        from daily_run.enhanced_full_spectrum_scoring import EnhancedFullSpectrumScoring
        
        # Initialize database
        db = DatabaseManager()
        db.connect()
        logger.info("✅ Database connected")
        
        # Initialize enhanced scoring system
        scoring_system = EnhancedFullSpectrumScoring(db=db)
        
        if not scoring_system.initialize():
            logger.error("Failed to initialize scoring system")
            return False
        
        logger.info("✅ Enhanced Full Spectrum Scoring initialized")
        
        # Test with 20 additional diverse tickers across sectors
        test_tickers = [
            # Additional Technology
            'AVGO', 'TXN', 'MU', 'AMAT', 'LRCX',
            
            # Additional Healthcare 
            'LLY', 'MRK', 'BMY', 'GILD', 'BIIB',
            
            # Additional Financial
            'C', 'V', 'MA', 'AXP', 'SPGI',
            
            # Additional Consumer & Retail
            'AMZN', 'WMT', 'COST', 'TGT', 'LOW'
        ]
        
        logger.info(f"🎯 Testing with 20 additional tickers:")
        logger.info(f"   Tickers: {', '.join(test_tickers)}")
        
        # Run enhanced scoring on all tickers
        logger.info("🧮 Starting enhanced scoring calculations...")
        
        results = scoring_system.calculate_scores_for_all_tickers(test_tickers)
        
        # Display results
        logger.info("=" * 80)
        logger.info("📊 ENHANCED SCORING RESULTS - 20 ADDITIONAL TICKERS")
        logger.info("=" * 80)
        
        logger.info(f"Total Tickers Processed: {results.get('total_tickers', 0)}")
        logger.info(f"Successful Calculations: {results.get('successful_calculations', 0)}")
        logger.info(f"Failed Calculations: {results.get('failed_calculations', 0)}")
        
        if results.get('successful_calculations', 0) > 0:
            success_rate = (results['successful_calculations'] / results['total_tickers']) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
        
        # Display detailed results
        if 'results' in results and results['results']:
            logger.info("\n📈 DETAILED SCORING RESULTS:")
            logger.info("   Ticker | Rating      | Score | Sector")
            logger.info("   " + "-" * 45)
            
            for stock in sorted(results['results'], key=lambda x: x['composite_score'], reverse=True):
                logger.info(f"   {stock['ticker']:6} | {stock['rating']:11} | {stock['composite_score']:5.1f} | {stock['sector']}")
        
        # Display summary statistics
        if 'summary' in results:
            summary = results['summary']
            
            logger.info("\n📊 RATING DISTRIBUTION:")
            rating_dist = summary.get('rating_distribution', {})
            total_successful = results.get('successful_calculations', 1)
            
            rating_order = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
            for rating in rating_order:
                count = rating_dist.get(rating, 0)
                pct = (count / total_successful * 100) if total_successful > 0 else 0
                logger.info(f"   {rating:11}: {count:2d} stocks ({pct:5.1f}%)")
            
            # Score statistics
            if 'score_statistics' in summary:
                stats = summary['score_statistics']
                logger.info("\n📊 SCORE STATISTICS:")
                logger.info(f"   Min Score: {stats.get('min_score', 0):.1f}")
                logger.info(f"   Max Score: {stats.get('max_score', 0):.1f}")
                logger.info(f"   Avg Score: {stats.get('avg_score', 0):.1f}")
                logger.info(f"   Score Range: {stats.get('max_score', 0) - stats.get('min_score', 0):.1f} points")
            
            # Full spectrum check
            full_spectrum = summary.get('full_spectrum_achieved', False)
            spectrum_status = "✅ ACHIEVED" if full_spectrum else "❌ NOT ACHIEVED"
            logger.info(f"\n🎯 Full Spectrum Ratings: {spectrum_status}")
            
            unique_ratings = len(rating_dist)
            logger.info(f"   Unique Rating Levels: {unique_ratings}/5")
            
            if full_spectrum:
                logger.info("   🌈 System is producing diverse ratings across the full spectrum!")
            else:
                logger.info(f"   ⚠️ Only {unique_ratings} different rating levels produced")
        
        # Sector breakdown
        if 'results' in results and results['results']:
            logger.info("\n🏢 SECTOR BREAKDOWN:")
            sector_performance = {}
            sector_counts = {}
            
            for stock in results['results']:
                sector = stock.get('sector', 'Unknown')
                if sector not in sector_performance:
                    sector_performance[sector] = []
                    sector_counts[sector] = {'Strong Buy': 0, 'Buy': 0, 'Hold': 0, 'Sell': 0, 'Strong Sell': 0}
                
                sector_performance[sector].append(stock['composite_score'])
                sector_counts[sector][stock['rating']] += 1
            
            for sector, scores in sector_performance.items():
                avg_score = sum(scores) / len(scores)
                logger.info(f"   {sector:20} | Avg Score: {avg_score:5.1f} | Count: {len(scores)}")
                
                # Show rating distribution for this sector
                sector_ratings = sector_counts[sector]
                top_rating = max(sector_ratings.items(), key=lambda x: x[1])
                if top_rating[1] > 0:
                    logger.info(f"   {'':22} | Top Rating: {top_rating[0]} ({top_rating[1]} stocks)")
        
        # Performance assessment
        logger.info("\n🎯 PERFORMANCE ASSESSMENT:")
        
        success_rate = (results.get('successful_calculations', 0) / results.get('total_tickers', 1)) * 100
        
        if success_rate >= 95:
            logger.info("   🎉 EXCELLENT: 95%+ success rate")
        elif success_rate >= 85:
            logger.info("   👍 GOOD: 85%+ success rate")
        elif success_rate >= 75:
            logger.info("   ⚠️ ACCEPTABLE: 75%+ success rate")
        else:
            logger.info("   ❌ POOR: <75% success rate")
        
        if 'summary' in results:
            unique_ratings = len(results['summary'].get('rating_distribution', {}))
            if unique_ratings >= 4:
                logger.info("   🌈 EXCELLENT: Full spectrum diversity (4+ rating levels)")
            elif unique_ratings >= 3:
                logger.info("   👍 GOOD: Moderate diversity (3 rating levels)")
            else:
                logger.info("   ⚠️ LIMITED: Low diversity (<3 rating levels)")
        
        # Cleanup
        db.disconnect()
        logger.info("\n✅ Database disconnected")
        
        # Final assessment
        success = results.get('successful_calculations', 0) >= len(test_tickers) * 0.8  # 80% success rate
        
        if success:
            logger.info("🎉 Enhanced scoring test with 20 additional tickers PASSED!")
            logger.info("✅ System maintains performance across diverse ticker sets")
        else:
            logger.error("❌ Enhanced scoring test FAILED!")
            logger.error("🔧 System may need additional tuning")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test runner"""
    logger.info("🚀 Enhanced Full Spectrum Scoring - Additional 20 Ticker Test")
    logger.info("   Testing system robustness across diverse sectors")
    logger.info("   Validating rating distribution and performance consistency")
    logger.info("")
    
    success = test_enhanced_scoring_20_more()
    
    if success:
        logger.info("\n🎯 ADDITIONAL TESTING COMPLETE!")
        logger.info("Enhanced scoring system validated across expanded ticker set")
        logger.info("System is robust and ready for production use")
    else:
        logger.error("\n❌ ADDITIONAL TESTING ISSUES DETECTED")
        logger.error("Please review and address issues before production deployment")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
