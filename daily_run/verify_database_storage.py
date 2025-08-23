#!/usr/bin/env python3
"""
Database Storage Verification

Verifies that analyst scores are properly stored in the database.
"""

import logging
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get direct database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def verify_enhanced_scores_table():
    """Verify the enhanced_scores table structure and content"""
    logger.info("🔍 VERIFYING ENHANCED_SCORES TABLE")
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'enhanced_scores'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        logger.info(f"📋 Table structure ({len(columns)} columns):")
        for col in columns:
            logger.info(f"   {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Check if analyst columns exist
        analyst_columns = [col for col in columns if 'analyst' in col['column_name']]
        logger.info(f"📊 Analyst columns found: {len(analyst_columns)}")
        for col in analyst_columns:
            logger.info(f"   ✅ {col['column_name']}: {col['data_type']}")
        
        cursor.close()
        conn.close()
        return len(analyst_columns) > 0
        
    except Exception as e:
        logger.error(f"Error checking table structure: {e}")
        if conn:
            conn.close()
        return False

def verify_test_stocks_data():
    """Verify that our test stocks have analyst data"""
    logger.info("🔍 VERIFYING TEST STOCKS DATA")
    
    test_stocks = ["AAPL", "MSFT", "NVDA", "TSLA", "JPM", "JNJ", "XOM", "KO", "HD", "CAT"]
    
    conn = get_database_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        results = {}
        
        for ticker in test_stocks:
            # Check for analyst data
            cursor.execute("""
                SELECT 
                    ticker,
                    analyst_score,
                    analyst_components,
                    calculation_date,
                    id
                FROM enhanced_scores 
                WHERE ticker = %s AND analyst_score IS NOT NULL
                ORDER BY calculation_date DESC 
                LIMIT 5
            """, (ticker,))
            
            records = cursor.fetchall()
            
            if records:
                latest = records[0]
                components = json.loads(latest['analyst_components']) if latest['analyst_components'] else {}
                
                results[ticker] = {
                    'found': True,
                    'record_count': len(records),
                    'latest_score': float(latest['analyst_score']),
                    'latest_date': latest['calculation_date'].isoformat(),
                    'components': components,
                    'record_id': latest['id']
                }
                logger.info(f"   ✅ {ticker}: Score {latest['analyst_score']}, {len(records)} records")
            else:
                results[ticker] = {
                    'found': False,
                    'record_count': 0
                }
                logger.warning(f"   ❌ {ticker}: No analyst data found")
        
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        logger.error(f"Error verifying test stocks: {e}")
        if conn:
            conn.close()
        return {}

def get_overall_statistics():
    """Get overall database statistics"""
    logger.info("📊 GETTING OVERALL STATISTICS")
    
    conn = get_database_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        # Total records with analyst scores
        cursor.execute("SELECT COUNT(*) FROM enhanced_scores WHERE analyst_score IS NOT NULL")
        total_analyst_records = cursor.fetchone()[0]
        
        # Unique tickers with analyst scores
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM enhanced_scores WHERE analyst_score IS NOT NULL")
        unique_tickers = cursor.fetchone()[0]
        
        # Score distribution
        cursor.execute("""
            SELECT 
                MIN(analyst_score) as min_score,
                MAX(analyst_score) as max_score,
                AVG(analyst_score) as avg_score,
                COUNT(*) as total_records
            FROM enhanced_scores 
            WHERE analyst_score IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        
        # Recent records
        cursor.execute("""
            SELECT COUNT(*) 
            FROM enhanced_scores 
            WHERE analyst_score IS NOT NULL 
            AND calculation_date >= NOW() - INTERVAL '1 hour'
        """)
        recent_records = cursor.fetchone()[0]
        
        statistics = {
            'total_analyst_records': total_analyst_records,
            'unique_tickers_with_analyst_scores': unique_tickers,
            'min_score': float(stats[0]) if stats[0] else None,
            'max_score': float(stats[1]) if stats[1] else None,
            'avg_score': float(stats[2]) if stats[2] else None,
            'total_records': stats[3],
            'recent_records_last_hour': recent_records
        }
        
        logger.info(f"📊 Total analyst records: {total_analyst_records}")
        logger.info(f"📊 Unique tickers: {unique_tickers}")
        logger.info(f"📊 Score range: {stats[0]:.2f} - {stats[1]:.2f}" if stats[0] and stats[1] else "📊 No score data")
        logger.info(f"📊 Average score: {stats[2]:.2f}" if stats[2] else "📊 No average")
        logger.info(f"📊 Recent records (last hour): {recent_records}")
        
        cursor.close()
        conn.close()
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        if conn:
            conn.close()
        return {}

def main():
    """Run database verification"""
    logger.info("🚀 DATABASE STORAGE VERIFICATION")
    logger.info("=" * 50)
    
    # Check table structure
    table_ok = verify_enhanced_scores_table()
    
    if not table_ok:
        logger.error("❌ Table structure check failed")
        return False
    
    # Verify test stocks data
    test_results = verify_test_stocks_data()
    
    # Get overall statistics
    statistics = get_overall_statistics()
    
    # Summary
    logger.info("=" * 50)
    logger.info("📋 VERIFICATION SUMMARY")
    
    if test_results:
        found_count = sum(1 for r in test_results.values() if r['found'])
        logger.info(f"   Test Stocks Found: {found_count}/10")
        
        if found_count == 10:
            logger.info("   ✅ ALL TEST STOCKS HAVE ANALYST DATA")
        elif found_count >= 8:
            logger.info("   ✅ MOST TEST STOCKS HAVE ANALYST DATA")
        else:
            logger.warning("   ⚠️ SOME TEST STOCKS MISSING ANALYST DATA")
    
    if statistics:
        logger.info(f"   Total Records: {statistics.get('total_analyst_records', 0)}")
        logger.info(f"   Unique Tickers: {statistics.get('unique_tickers_with_analyst_scores', 0)}")
        logger.info(f"   Recent Records: {statistics.get('recent_records_last_hour', 0)}")
    
    # Generate report data
    report = {
        'verification_date': datetime.now().isoformat(),
        'table_structure_ok': table_ok,
        'test_stocks_results': test_results,
        'overall_statistics': statistics,
        'success': table_ok and len([r for r in test_results.values() if r['found']]) >= 8
    }
    
    # Save report
    with open('database_verification_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info("📄 Report saved to: database_verification_report.json")
    
    return report['success']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
