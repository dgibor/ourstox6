#!/usr/bin/env python3
"""
Recalculate Ratios for Failed Tickers
=====================================

This script re-calculates financial ratios for tickers that failed in the fundamental scoring.
It runs them through the FMP service to fetch fresh data and calculate ratios.

Author: AI Assistant
Date: 2025-01-26
"""

import sys
import os
from datetime import date, datetime
from typing import List, Dict, Optional
import logging

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_run.database import DatabaseManager
from daily_run.fmp_service import FMPService
from daily_run.ratio_calculator import calculate_ratios, validate_ratios

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RatioRecalculator:
    """Recalculate ratios for failed tickers"""
    
    def __init__(self):
        """Initialize the recalculator"""
        self.db = DatabaseManager()
        self.fmp_service = FMPService()
        
    def get_failed_tickers(self) -> List[str]:
        """Get the list of tickers that failed in the last update"""
        failed_tickers = ['AMD', 'AMZN', 'AVGO', 'INTC', 'MU', 'QCOM']
        return failed_tickers
    
    def check_current_data(self, ticker: str) -> Dict:
        """Check current data in company_fundamentals for a ticker"""
        try:
            query = """
            SELECT 
                last_updated,
                price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda,
                return_on_equity, return_on_assets, gross_margin, operating_margin, net_margin,
                debt_to_equity_ratio, current_ratio, revenue_growth_yoy, earnings_growth_yoy
            FROM company_fundamentals
            WHERE ticker = %s
            ORDER BY last_updated DESC
            LIMIT 1
            """
            result = self.db.execute_query(query, (ticker,))
            
            if not result:
                return {'has_data': False, 'quality_score': 0, 'last_updated': None}
            
            row = result[0]
            last_updated = row[0]
            
            # Count non-null key ratios
            key_ratios = row[1:15]  # Skip last_updated
            non_null_count = sum(1 for ratio in key_ratios if ratio is not None and ratio != 0)
            quality_score = int((non_null_count / len(key_ratios)) * 100)
            
            return {
                'has_data': True,
                'quality_score': quality_score,
                'last_updated': last_updated,
                'non_null_ratios': non_null_count,
                'total_ratios': len(key_ratios)
            }
            
        except Exception as e:
            logger.error(f"Error checking current data for {ticker}: {e}")
            return {'has_data': False, 'quality_score': 0, 'error': str(e)}
    
    def recalculate_single_ticker(self, ticker: str) -> Dict:
        """Recalculate ratios for a single ticker"""
        try:
            logger.info(f"Recalculating ratios for {ticker}")
            
            # Check current data quality
            current_data = self.check_current_data(ticker)
            logger.info(f"{ticker} current quality: {current_data['quality_score']}% ({current_data['non_null_ratios']}/{current_data['total_ratios']} ratios)")
            
            # Fetch fresh data from FMP
            logger.info(f"Fetching fresh FMP data for {ticker}")
            result = self.fmp_service.get_fundamental_data(ticker)
            
            if not result:
                return {
                    'ticker': ticker,
                    'status': 'failed',
                    'reason': 'Failed to fetch FMP data',
                    'old_quality': current_data['quality_score'],
                    'new_quality': 0
                }
            
            # Check new data quality
            new_data = self.check_current_data(ticker)
            
            return {
                'ticker': ticker,
                'status': 'success',
                'old_quality': current_data['quality_score'],
                'new_quality': new_data['quality_score'],
                'old_ratios': current_data['non_null_ratios'],
                'new_ratios': new_data['non_null_ratios'],
                'improvement': new_data['quality_score'] - current_data['quality_score']
            }
            
        except Exception as e:
            logger.error(f"Error recalculating {ticker}: {e}")
            return {
                'ticker': ticker,
                'status': 'error',
                'reason': str(e),
                'old_quality': 0,
                'new_quality': 0
            }
    
    def recalculate_all_failed(self) -> Dict:
        """Recalculate ratios for all failed tickers"""
        failed_tickers = self.get_failed_tickers()
        logger.info(f"Recalculating ratios for {len(failed_tickers)} failed tickers: {failed_tickers}")
        
        results = []
        success_count = 0
        failed_count = 0
        
        for i, ticker in enumerate(failed_tickers, 1):
            logger.info(f"Processing {i}/{len(failed_tickers)}: {ticker}")
            
            result = self.recalculate_single_ticker(ticker)
            results.append(result)
            
            if result['status'] == 'success':
                success_count += 1
            else:
                failed_count += 1
        
        # Compile summary
        summary = {
            'total_tickers': len(failed_tickers),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }
        
        logger.info(f"Recalculation complete: {success_count} success, {failed_count} failed")
        
        return summary
    
    def verify_improvements(self) -> Dict:
        """Verify that the recalculation improved data quality"""
        failed_tickers = self.get_failed_tickers()
        
        print("\n" + "="*60)
        print("VERIFICATION: Data Quality After Recalculation")
        print("="*60)
        
        for ticker in failed_tickers:
            data = self.check_current_data(ticker)
            print(f"{ticker}:")
            print(f"  Quality Score: {data['quality_score']}%")
            print(f"  Ratios Available: {data['non_null_ratios']}/{data['total_ratios']}")
            print(f"  Last Updated: {data['last_updated']}")
            print("-")
        
        return {'status': 'verification_complete'}

def main():
    """Main execution function"""
    try:
        logger.info("Starting ratio recalculation for failed tickers")
        
        # Initialize recalculator
        recalculator = RatioRecalculator()
        
        # Recalculate ratios
        summary = recalculator.recalculate_all_failed()
        
        # Print results
        print("\n" + "="*60)
        print("RATIO RECALCULATION SUMMARY")
        print("="*60)
        print(f"Total Tickers: {summary['total_tickers']}")
        print(f"Success: {summary['success_count']}")
        print(f"Failed: {summary['failed_count']}")
        
        print("\n" + "-"*60)
        print("DETAILED RESULTS")
        print("-"*60)
        for result in summary['results']:
            if result['status'] == 'success':
                print(f"  {result['ticker']}: SUCCESS")
                print(f"    Quality: {result['old_quality']}% → {result['new_quality']}% (Δ{result['improvement']:+d}%)")
                print(f"    Ratios: {result['old_ratios']} → {result['new_ratios']}")
            else:
                print(f"  {result['ticker']}: FAILED - {result.get('reason', 'Unknown error')}")
        
        # Verify improvements
        recalculator.verify_improvements()
        
        print("\n" + "="*60)
        logger.info("Ratio recalculation process completed")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 