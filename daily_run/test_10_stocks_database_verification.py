#!/usr/bin/env python3
"""
10 Stocks Database Verification Test

Tests analyst scoring for 10 stocks and verifies data storage in database tables.
Generates a comprehensive report of results.
"""

import logging
import sys
import os
import json
from datetime import date, datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_test_stocks() -> List[str]:
    """Get 10 diverse test stocks"""
    return [
        "AAPL",  # Technology - Large cap
        "MSFT",  # Technology - Large cap
        "NVDA",  # Technology - AI leader
        "TSLA",  # Technology - EV
        "JPM",   # Financial - Banking
        "JNJ",   # Healthcare - Pharma
        "XOM",   # Energy - Oil
        "KO",    # Consumer - Beverages
        "HD",    # Consumer - Home improvement
        "CAT"    # Industrial - Machinery
    ]

def run_analyst_scoring_test(test_stocks: List[str]) -> Dict:
    """Run analyst scoring for test stocks"""
    logger.info(f"🧪 TESTING ANALYST SCORING FOR {len(test_stocks)} STOCKS")
    
    try:
        from analyst_scorer import AnalystScorer
        from database import DatabaseManager
        
        # Initialize
        db = DatabaseManager()
        analyst_scorer = AnalystScorer(db=db)
        
        results = {}
        successful = 0
        failed = 0
        
        for i, ticker in enumerate(test_stocks, 1):
            logger.info(f"📊 [{i}/{len(test_stocks)}] Testing {ticker}")
            
            try:
                # Calculate analyst scores
                scores = analyst_scorer.calculate_analyst_score(ticker)
                
                if scores and scores.get('calculation_status') != 'failed':
                    # Store in database
                    storage_success = analyst_scorer.store_analyst_score(ticker, scores)
                    
                    results[ticker] = {
                        'calculation_success': True,
                        'storage_success': storage_success,
                        'composite_score': scores.get('composite_analyst_score'),
                        'earnings_proximity': scores.get('earnings_proximity_score'),
                        'earnings_surprise': scores.get('earnings_surprise_score'),
                        'analyst_sentiment': scores.get('analyst_sentiment_score'),
                        'price_target': scores.get('price_target_score'),
                        'revision_score': scores.get('revision_score'),
                        'data_quality': scores.get('data_quality_score'),
                        'calculation_status': scores.get('calculation_status'),
                        'industry_adjustment': scores.get('industry_adjustment', 0),
                        'qualitative_bonus': scores.get('qualitative_bonus', 0),
                        'error_message': scores.get('error_message')
                    }
                    
                    if storage_success:
                        successful += 1
                        logger.info(f"   ✅ {ticker}: Score {scores.get('composite_analyst_score')} - Stored successfully")
                    else:
                        failed += 1
                        logger.warning(f"   ⚠️ {ticker}: Score calculated but storage failed")
                else:
                    failed += 1
                    results[ticker] = {
                        'calculation_success': False,
                        'storage_success': False,
                        'error_message': scores.get('error_message') if scores else 'Failed to calculate'
                    }
                    logger.error(f"   ❌ {ticker}: Calculation failed")
                    
            except Exception as e:
                failed += 1
                results[ticker] = {
                    'calculation_success': False,
                    'storage_success': False,
                    'error_message': str(e)
                }
                logger.error(f"   ❌ {ticker}: Exception - {e}")
        
        summary = {
            'total_stocks': len(test_stocks),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / len(test_stocks)) * 100,
            'results': results
        }
        
        logger.info(f"📊 SCORING SUMMARY: {successful}/{len(test_stocks)} successful ({summary['success_rate']:.1f}%)")
        return summary
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return {'error': str(e)}

def verify_database_storage(test_stocks: List[str]) -> Dict:
    """Verify that data was actually stored in database tables"""
    logger.info("🔍 VERIFYING DATABASE STORAGE")
    
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        conn = db.connection
        cursor = conn.cursor()
        
        # Check enhanced_scores table
        logger.info("📋 Checking enhanced_scores table...")
        
        verification_results = {}
        
        for ticker in test_stocks:
            logger.info(f"   🔍 Checking {ticker}")
            
            # Query for the ticker
            query = """
            SELECT ticker, analyst_score, analyst_components, calculation_date
            FROM enhanced_scores 
            WHERE ticker = %s 
            ORDER BY calculation_date DESC 
            LIMIT 1
            """
            
            cursor.execute(query, (ticker,))
            result = cursor.fetchone()
            
            if result:
                ticker_db, analyst_score, analyst_components, calc_date = result
                
                # Parse JSON components
                try:
                    components = json.loads(analyst_components) if analyst_components else {}
                except:
                    components = {}
                
                verification_results[ticker] = {
                    'stored_in_db': True,
                    'analyst_score': float(analyst_score) if analyst_score else None,
                    'calculation_date': calc_date.isoformat() if calc_date else None,
                    'components': components
                }
                
                logger.info(f"      ✅ Found: Score {analyst_score}, Date {calc_date}")
            else:
                verification_results[ticker] = {
                    'stored_in_db': False,
                    'analyst_score': None,
                    'calculation_date': None,
                    'components': {}
                }
                logger.warning(f"      ❌ Not found in database")
        
        # Get table statistics
        cursor.execute("SELECT COUNT(*) FROM enhanced_scores WHERE analyst_score IS NOT NULL")
        total_analyst_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM enhanced_scores WHERE analyst_score IS NOT NULL")
        unique_tickers_with_analyst_scores = cursor.fetchone()[0]
        
        cursor.close()
        
        stored_count = sum(1 for r in verification_results.values() if r['stored_in_db'])
        
        database_summary = {
            'total_test_stocks': len(test_stocks),
            'stored_successfully': stored_count,
            'storage_rate': (stored_count / len(test_stocks)) * 100,
            'total_analyst_records_in_db': total_analyst_records,
            'unique_tickers_with_analyst_scores': unique_tickers_with_analyst_scores,
            'verification_results': verification_results
        }
        
        logger.info(f"📊 DATABASE VERIFICATION: {stored_count}/{len(test_stocks)} stocks stored ({database_summary['storage_rate']:.1f}%)")
        logger.info(f"📊 TOTAL RECORDS: {total_analyst_records} analyst records, {unique_tickers_with_analyst_scores} unique tickers")
        
        return database_summary
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return {'error': str(e)}

def generate_comprehensive_report(scoring_results: Dict, database_results: Dict) -> Dict:
    """Generate comprehensive report of all results"""
    logger.info("📝 GENERATING COMPREHENSIVE REPORT")
    
    report = {
        'test_info': {
            'test_date': datetime.now().isoformat(),
            'test_type': '10 Stocks Analyst Integration Test',
            'purpose': 'Verify analyst scoring calculation and database storage'
        },
        'scoring_results': scoring_results,
        'database_verification': database_results,
        'detailed_analysis': {},
        'recommendations': []
    }
    
    # Detailed analysis
    if 'results' in scoring_results and 'verification_results' in database_results:
        analysis = {}
        
        for ticker in scoring_results['results']:
            scoring_data = scoring_results['results'][ticker]
            db_data = database_results['verification_results'].get(ticker, {})
            
            analysis[ticker] = {
                'calculation_success': scoring_data.get('calculation_success', False),
                'storage_success': scoring_data.get('storage_success', False),
                'database_verified': db_data.get('stored_in_db', False),
                'composite_score': scoring_data.get('composite_score'),
                'database_score': db_data.get('analyst_score'),
                'scores_match': (
                    scoring_data.get('composite_score') == db_data.get('analyst_score')
                    if scoring_data.get('composite_score') and db_data.get('analyst_score') else False
                ),
                'component_breakdown': {
                    'earnings_proximity': scoring_data.get('earnings_proximity'),
                    'earnings_surprise': scoring_data.get('earnings_surprise'),
                    'analyst_sentiment': scoring_data.get('analyst_sentiment'),
                    'price_target': scoring_data.get('price_target'),
                    'revision_score': scoring_data.get('revision_score')
                },
                'adjustments': {
                    'industry_adjustment': scoring_data.get('industry_adjustment', 0),
                    'qualitative_bonus': scoring_data.get('qualitative_bonus', 0)
                },
                'data_quality': scoring_data.get('data_quality'),
                'status': 'SUCCESS' if (
                    scoring_data.get('calculation_success') and 
                    scoring_data.get('storage_success') and 
                    db_data.get('stored_in_db')
                ) else 'FAILED'
            }
        
        report['detailed_analysis'] = analysis
        
        # Calculate success metrics
        total_success = sum(1 for a in analysis.values() if a['status'] == 'SUCCESS')
        calculation_success = sum(1 for a in analysis.values() if a['calculation_success'])
        storage_success = sum(1 for a in analysis.values() if a['storage_success'])
        db_verified = sum(1 for a in analysis.values() if a['database_verified'])
        
        report['summary_metrics'] = {
            'total_stocks_tested': len(analysis),
            'end_to_end_success': total_success,
            'calculation_success': calculation_success,
            'storage_success': storage_success,
            'database_verified': db_verified,
            'end_to_end_success_rate': (total_success / len(analysis)) * 100,
            'calculation_success_rate': (calculation_success / len(analysis)) * 100,
            'storage_success_rate': (storage_success / len(analysis)) * 100,
            'database_verification_rate': (db_verified / len(analysis)) * 100
        }
        
        # Generate recommendations
        if total_success == len(analysis):
            report['recommendations'].append("✅ EXCELLENT: All stocks processed successfully. System is production-ready.")
        elif total_success >= len(analysis) * 0.8:
            report['recommendations'].append("✅ GOOD: Most stocks processed successfully. Minor issues may need attention.")
        else:
            report['recommendations'].append("⚠️ ATTENTION: Significant issues detected. Review failed cases.")
        
        if calculation_success < storage_success:
            report['recommendations'].append("🔍 REVIEW: Some calculations failed but storage succeeded - investigate data flow.")
        
        if storage_success < db_verified:
            report['recommendations'].append("🔍 REVIEW: Storage reports success but database verification failed - check storage logic.")
    
    return report

def save_report_to_file(report: Dict) -> str:
    """Save report to JSON and markdown files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON report
    json_filename = f"analyst_test_report_{timestamp}.json"
    with open(json_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Save markdown report
    md_filename = f"analyst_test_report_{timestamp}.md"
    with open(md_filename, 'w') as f:
        f.write("# Analyst Integration Test Report\n\n")
        f.write(f"**Test Date**: {report['test_info']['test_date']}\n")
        f.write(f"**Test Type**: {report['test_info']['test_type']}\n\n")
        
        if 'summary_metrics' in report:
            metrics = report['summary_metrics']
            f.write("## Summary Metrics\n\n")
            f.write(f"- **Total Stocks Tested**: {metrics['total_stocks_tested']}\n")
            f.write(f"- **End-to-End Success**: {metrics['end_to_end_success']}/{metrics['total_stocks_tested']} ({metrics['end_to_end_success_rate']:.1f}%)\n")
            f.write(f"- **Calculation Success**: {metrics['calculation_success']}/{metrics['total_stocks_tested']} ({metrics['calculation_success_rate']:.1f}%)\n")
            f.write(f"- **Storage Success**: {metrics['storage_success']}/{metrics['total_stocks_tested']} ({metrics['storage_success_rate']:.1f}%)\n")
            f.write(f"- **Database Verified**: {metrics['database_verified']}/{metrics['total_stocks_tested']} ({metrics['database_verification_rate']:.1f}%)\n\n")
        
        if 'detailed_analysis' in report:
            f.write("## Detailed Results\n\n")
            f.write("| Ticker | Status | Calc Score | DB Score | Match | Data Quality |\n")
            f.write("|--------|--------|------------|----------|-------|-------------|\n")
            
            for ticker, analysis in report['detailed_analysis'].items():
                status_emoji = "✅" if analysis['status'] == 'SUCCESS' else "❌"
                calc_score = analysis['composite_score'] or 'N/A'
                db_score = analysis['database_score'] or 'N/A'
                match_emoji = "✅" if analysis['scores_match'] else "❌"
                data_quality = analysis['data_quality'] or 'N/A'
                
                f.write(f"| {ticker} | {status_emoji} {analysis['status']} | {calc_score} | {db_score} | {match_emoji} | {data_quality} |\n")
        
        if 'recommendations' in report:
            f.write("\n## Recommendations\n\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")
    
    logger.info(f"📝 Reports saved: {json_filename}, {md_filename}")
    return md_filename

def main():
    """Run the complete test"""
    logger.info("🚀 STARTING 10 STOCKS DATABASE VERIFICATION TEST")
    logger.info("=" * 60)
    
    # Get test stocks
    test_stocks = get_test_stocks()
    logger.info(f"📋 Test Stocks: {', '.join(test_stocks)}")
    
    # Run analyst scoring test
    scoring_results = run_analyst_scoring_test(test_stocks)
    
    # Verify database storage
    database_results = verify_database_storage(test_stocks)
    
    # Generate comprehensive report
    report = generate_comprehensive_report(scoring_results, database_results)
    
    # Save report to file
    report_file = save_report_to_file(report)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("📊 FINAL RESULTS SUMMARY")
    
    if 'summary_metrics' in report:
        metrics = report['summary_metrics']
        logger.info(f"   End-to-End Success: {metrics['end_to_end_success']}/{metrics['total_stocks_tested']} ({metrics['end_to_end_success_rate']:.1f}%)")
        logger.info(f"   Calculation Success: {metrics['calculation_success']}/{metrics['total_stocks_tested']} ({metrics['calculation_success_rate']:.1f}%)")
        logger.info(f"   Storage Success: {metrics['storage_success']}/{metrics['total_stocks_tested']} ({metrics['storage_success_rate']:.1f}%)")
        logger.info(f"   Database Verified: {metrics['database_verified']}/{metrics['total_stocks_tested']} ({metrics['database_verification_rate']:.1f}%)")
    
    if 'recommendations' in report:
        logger.info("\n📋 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            logger.info(f"   {rec}")
    
    logger.info(f"\n📄 Full report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    report = main()
    
    # Exit with appropriate code
    if 'summary_metrics' in report:
        success_rate = report['summary_metrics']['end_to_end_success_rate']
        sys.exit(0 if success_rate >= 80 else 1)
    else:
        sys.exit(1)
