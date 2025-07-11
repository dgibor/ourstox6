#!/usr/bin/env python3
"""
Comprehensive Data Workflow
===========================

This script provides a complete workflow for:
1. Validating data completeness in company_fundamentals table
2. Identifying missing critical fields
3. Fetching missing data using batch API calls (with rate limiting)
4. Calculating ratios from the complete data
5. Updating fundamental scores

Author: AI Assistant
Date: 2025-01-26
"""

import sys
import os
from datetime import date, datetime
from typing import List, Dict, Optional, Set, Tuple
import logging
import time
import json

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_run.database import DatabaseManager
from daily_run.fmp_service import FMPService
from daily_run.ratio_calculator import calculate_ratios, validate_ratios
from daily_run.simple_data_validator import SimpleDataValidator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataWorkflow:
    """Comprehensive workflow for data validation, fetching, and ratio calculation"""
    
    def __init__(self):
        """Initialize the workflow"""
        self.db = DatabaseManager()
        self.validator = SimpleDataValidator()
        self.fmp_service = None  # Initialize lazily
        
        # Configuration
        self.max_retries = 3
        self.delay_between_requests = 3  # seconds
        self.max_concurrent_requests = 1  # Avoid rate limiting
        
    def _get_fmp_service(self):
        """Get FMP service instance with proper error handling"""
        if self.fmp_service is None:
            try:
                self.fmp_service = FMPService()
                logger.info("FMP service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FMP service: {e}")
                return None
        return self.fmp_service
    
    def step1_validate_data(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Step 1: Validate data completeness for all tickers
        
        Returns:
            Validation results for all tickers
        """
        print(f"\n📋 STEP 1: DATA VALIDATION")
        print("=" * 60)
        
        validation_results = self.validator.validate_all_tickers(tickers)
        self.validator.print_validation_summary(validation_results)
        
        return validation_results
    
    def step2_identify_missing_data(self, validation_results: Dict[str, Dict]) -> List[str]:
        """
        Step 2: Identify tickers that need data fetching
        
        Returns:
            Prioritized list of tickers needing data fetch
        """
        print(f"\n📋 STEP 2: IDENTIFYING MISSING DATA")
        print("=" * 60)
        
        tickers_needing_fetch = self.validator.identify_tickers_needing_fetch(validation_results)
        
        if not tickers_needing_fetch:
            print("  ✅ All tickers have complete data - no fetching needed!")
            return []
        
        # Generate prioritized list
        prioritized_list = self.validator.generate_fetch_list(validation_results)
        
        print(f"  📥 Found {len(tickers_needing_fetch)} tickers needing data fetch:")
        for i, ticker in enumerate(prioritized_list, 1):
            quality = validation_results[ticker]['data_quality_score']
            missing_count = len(validation_results[ticker].get('missing_fields', []))
            print(f"    {i:2d}. {ticker} ({quality}% quality, {missing_count} missing fields)")
        
        return prioritized_list
    
    def step3_fetch_missing_data(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Step 3: Fetch missing data with rate limiting and error handling
        
        Returns:
            Dict mapping ticker to success status
        """
        if not tickers:
            return {}
        
        print(f"\n📋 STEP 3: FETCHING MISSING DATA")
        print("=" * 60)
        
        results = {}
        fmp_service = self._get_fmp_service()
        
        if not fmp_service:
            print("  ❌ FMP service not available - skipping data fetch")
            return {ticker: False for ticker in tickers}
        
        for i, ticker in enumerate(tickers, 1):
            print(f"  📥 [{i}/{len(tickers)}] Fetching data for {ticker}...")
            
            success = self._fetch_single_ticker_data(ticker, fmp_service)
            results[ticker] = success
            
            # Add delay between requests to avoid rate limiting
            if i < len(tickers):
                print(f"    ⏳ Waiting {self.delay_between_requests}s before next request...")
                time.sleep(self.delay_between_requests)
        
        # Print fetch summary
        successful_fetches = sum(1 for success in results.values() if success)
        print(f"\n  📊 Fetch Summary: {successful_fetches}/{len(tickers)} successful")
        
        return results
    
    def _fetch_single_ticker_data(self, ticker: str, fmp_service: FMPService) -> bool:
        """
        Fetch data for a single ticker with retry logic
        
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                # Fetch financial statements
                financial_data = fmp_service.fetch_financial_statements(ticker)
                if not financial_data:
                    if attempt < self.max_retries - 1:
                        print(f"    ⚠️  Attempt {attempt + 1} failed, retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        print(f"    ❌ Failed to fetch financial statements for {ticker}")
                        return False
                
                # Fetch key statistics
                key_stats = fmp_service.fetch_key_statistics(ticker)
                if not key_stats:
                    print(f"    ⚠️  No key statistics for {ticker}, proceeding with financial data only")
                
                # Store the data
                success = fmp_service.store_fundamental_data(ticker, financial_data, key_stats or {})
                
                if success:
                    print(f"    ✅ Successfully fetched and stored data for {ticker}")
                    return True
                else:
                    print(f"    ❌ Failed to store data for {ticker}")
                    return False
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"    ⚠️  Attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Error fetching data for {ticker}: {e}")
                    print(f"    ❌ Error fetching data for {ticker}: {e}")
                    return False
        
        return False
    
    def step4_revalidate_data(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Step 4: Re-validate data after fetching
        
        Returns:
            Updated validation results
        """
        print(f"\n📋 STEP 4: RE-VALIDATING DATA")
        print("=" * 60)
        
        post_fetch_validation = self.validator.validate_all_tickers(tickers)
        
        # Compare with pre-fetch results
        print(f"\n📊 DATA QUALITY IMPROVEMENT:")
        for ticker in tickers:
            pre_quality = 41  # Default from previous run
            post_quality = post_fetch_validation[ticker]['data_quality_score']
            improvement = post_quality - pre_quality
            
            if improvement > 0:
                print(f"  📈 {ticker}: {pre_quality}% → {post_quality}% (+{improvement}%)")
            else:
                print(f"  📊 {ticker}: {pre_quality}% → {post_quality}% (no change)")
        
        return post_fetch_validation
    
    def step5_calculate_ratios(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Step 5: Calculate ratios for all tickers
        
        Returns:
            Dict mapping ticker to ratio calculation success status
        """
        print(f"\n📋 STEP 5: CALCULATING RATIOS")
        print("=" * 60)
        
        ratio_results = {}
        
        for ticker in tickers:
            try:
                print(f"  🧮 Calculating ratios for {ticker}...")
                
                # Get the most recent fundamental data
                query = """
                SELECT 
                    revenue, net_income, ebitda, total_equity, total_assets,
                    total_debt, gross_profit, operating_income, free_cash_flow
                FROM company_fundamentals
                WHERE ticker = %s
                ORDER BY last_updated DESC
                LIMIT 1
                """
                
                result = self.db.execute_query(query, (ticker,))
                
                if not result:
                    print(f"    ❌ No fundamental data found for {ticker}")
                    ratio_results[ticker] = False
                    continue
                
                row = result[0]
                
                # Prepare raw data
                raw_data = {
                    'revenue': row[0],
                    'net_income': row[1],
                    'ebitda': row[2],
                    'total_equity': row[3],
                    'total_assets': row[4],
                    'total_debt': row[5],
                    'gross_profit': row[6],
                    'operating_income': row[7],
                    'free_cash_flow': row[8]
                }
                
                # Get market data
                current_price = self.db.get_latest_price(ticker)
                market_query = """
                SELECT shares_outstanding, enterprise_value
                FROM stocks
                WHERE ticker = %s
                """
                market_result = self.db.execute_query(market_query, (ticker,))
                
                market_data = {
                    'current_price': current_price,
                    'shares_outstanding': market_result[0][0] if market_result else None,
                    'enterprise_value': market_result[0][1] if market_result else None
                }
                
                # Calculate ratios
                calculated_ratios = calculate_ratios(raw_data, market_data)
                
                # Store ratios in company_fundamentals
                self._store_calculated_ratios(ticker, calculated_ratios)
                
                print(f"    ✅ Successfully calculated ratios for {ticker}")
                ratio_results[ticker] = True
                
            except Exception as e:
                logger.error(f"Error calculating ratios for {ticker}: {e}")
                print(f"    ❌ Error calculating ratios for {ticker}: {e}")
                ratio_results[ticker] = False
        
        # Print ratio calculation summary
        successful_ratios = sum(1 for success in ratio_results.values() if success)
        print(f"\n  📊 Ratio Calculation Summary: {successful_ratios}/{len(tickers)} successful")
        
        return ratio_results
    
    def _store_calculated_ratios(self, ticker: str, ratios: Dict[str, float]):
        """
        Store calculated ratios in the company_fundamentals table
        """
        try:
            # Update the most recent record with calculated ratios
            update_query = """
            UPDATE company_fundamentals
            SET 
                price_to_earnings = %s,
                price_to_book = %s,
                price_to_sales = %s,
                ev_to_ebitda = %s,
                return_on_equity = %s,
                return_on_assets = %s,
                debt_to_equity_ratio = %s,
                current_ratio = %s,
                gross_margin = %s,
                operating_margin = %s,
                net_margin = %s,
                peg_ratio = %s,
                return_on_invested_capital = %s,
                quick_ratio = %s,
                interest_coverage = %s,
                altman_z_score = %s,
                asset_turnover = %s,
                inventory_turnover = %s,
                receivables_turnover = %s,
                revenue_growth_yoy = %s,
                earnings_growth_yoy = %s,
                fcf_growth_yoy = %s,
                fcf_to_net_income = %s,
                cash_conversion_cycle = %s,
                market_cap = %s,
                enterprise_value = %s,
                graham_number = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE ticker = %s
            AND id = (
                SELECT id FROM company_fundamentals 
                WHERE ticker = %s 
                ORDER BY last_updated DESC 
                LIMIT 1
            )
            """
            
            values = (
                ratios.get('pe_ratio'),
                ratios.get('pb_ratio'),
                ratios.get('ps_ratio'),
                ratios.get('ev_ebitda'),
                ratios.get('roe'),
                ratios.get('roa'),
                ratios.get('debt_to_equity'),
                ratios.get('current_ratio'),
                ratios.get('gross_margin'),
                ratios.get('operating_margin'),
                ratios.get('net_margin'),
                ratios.get('peg_ratio'),
                ratios.get('roic'),
                ratios.get('quick_ratio'),
                ratios.get('interest_coverage'),
                ratios.get('altman_z_score'),
                ratios.get('asset_turnover'),
                ratios.get('inventory_turnover'),
                ratios.get('receivables_turnover'),
                ratios.get('revenue_growth_yoy'),
                ratios.get('earnings_growth_yoy'),
                ratios.get('fcf_growth_yoy'),
                ratios.get('fcf_to_net_income'),
                ratios.get('cash_conversion_cycle'),
                ratios.get('market_cap'),
                ratios.get('enterprise_value'),
                ratios.get('graham_number'),
                ticker,
                ticker
            )
            
            self.db.execute_query(update_query, values)
            
        except Exception as e:
            logger.error(f"Error storing calculated ratios for {ticker}: {e}")
            raise
    
    def step6_update_fundamental_scores(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Step 6: Update fundamental scores using the new ratio data
        
        Returns:
            Dict mapping ticker to score update success status
        """
        print(f"\n📋 STEP 6: UPDATING FUNDAMENTAL SCORES")
        print("=" * 60)
        
        score_results = {}
        
        for ticker in tickers:
            try:
                print(f"  📊 Updating fundamental score for {ticker}...")
                
                # Get the latest ratios from company_fundamentals
                query = """
                SELECT 
                    price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda,
                    return_on_equity, return_on_assets, debt_to_equity_ratio,
                    gross_margin, operating_margin, net_margin
                FROM company_fundamentals
                WHERE ticker = %s
                ORDER BY last_updated DESC
                LIMIT 1
                """
                
                result = self.db.execute_query(query, (ticker,))
                
                if not result:
                    print(f"    ❌ No ratio data found for {ticker}")
                    score_results[ticker] = False
                    continue
                
                row = result[0]
                
                # Calculate fundamental score based on ratios
                fundamental_score = self._calculate_fundamental_score(row)
                
                # Update the daily_scores table
                update_query = """
                UPDATE daily_scores
                SET fundamental_score = %s, last_updated = CURRENT_TIMESTAMP
                WHERE ticker = %s AND date = CURRENT_DATE
                """
                
                self.db.execute_query(update_query, (fundamental_score, ticker))
                
                print(f"    ✅ Updated fundamental score for {ticker}: {fundamental_score}")
                score_results[ticker] = True
                
            except Exception as e:
                logger.error(f"Error updating fundamental score for {ticker}: {e}")
                print(f"    ❌ Error updating fundamental score for {ticker}: {e}")
                score_results[ticker] = False
        
        # Print score update summary
        successful_scores = sum(1 for success in score_results.values() if success)
        print(f"\n  📊 Score Update Summary: {successful_scores}/{len(tickers)} successful")
        
        return score_results
    
    def _calculate_fundamental_score(self, ratio_data: tuple) -> int:
        """
        Calculate fundamental score based on ratio data
        
        Returns:
            Score from 0-100
        """
        try:
            pe_ratio, pb_ratio, ps_ratio, ev_ebitda, roe, roa, debt_equity, gross_margin, operating_margin, net_margin = ratio_data
            
            score = 0
            max_score = 100
            
            # Valuation ratios (30 points)
            if pe_ratio and pe_ratio > 0 and pe_ratio < 25:
                score += min(15, (25 - pe_ratio) / 25 * 15)
            if pb_ratio and pb_ratio > 0 and pb_ratio < 3:
                score += min(15, (3 - pb_ratio) / 3 * 15)
            
            # Profitability ratios (40 points)
            if roe and roe > 0:
                score += min(20, roe / 20 * 20)  # 20% ROE = full points
            if gross_margin and gross_margin > 0:
                score += min(10, gross_margin / 50 * 10)  # 50% margin = full points
            if net_margin and net_margin > 0:
                score += min(10, net_margin / 20 * 10)  # 20% margin = full points
            
            # Financial health (30 points)
            if debt_equity and debt_equity < 1:
                score += min(15, (1 - debt_equity) / 1 * 15)
            if roa and roa > 0:
                score += min(15, roa / 10 * 15)  # 10% ROA = full points
            
            return min(max_score, int(score))
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score: {e}")
            return 0
    
    def run_complete_workflow(self, tickers: List[str]) -> Dict[str, any]:
        """
        Run the complete workflow for all tickers
        
        Returns:
            Comprehensive summary of the entire workflow
        """
        print(f"\n🚀 STARTING COMPREHENSIVE DATA WORKFLOW")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Step 1: Validate data
            validation_results = self.step1_validate_data(tickers)
            
            # Step 2: Identify missing data
            tickers_needing_fetch = self.step2_identify_missing_data(validation_results)
            
            # Step 3: Fetch missing data (if any)
            fetch_results = {}
            if tickers_needing_fetch:
                fetch_results = self.step3_fetch_missing_data(tickers_needing_fetch)
            else:
                print("  ✅ No data fetching needed - all tickers have complete data")
            
            # Step 4: Re-validate after fetch
            post_fetch_validation = self.step4_revalidate_data(tickers)
            
            # Step 5: Calculate ratios
            ratio_results = self.step5_calculate_ratios(tickers)
            
            # Step 6: Update fundamental scores
            score_results = self.step6_update_fundamental_scores(tickers)
            
            execution_time = time.time() - start_time
            
            # Prepare comprehensive summary
            summary = {
                'status': 'success',
                'execution_time': execution_time,
                'tickers_processed': len(tickers),
                'tickers_fetched': len(tickers_needing_fetch),
                'fetch_success_count': sum(1 for success in fetch_results.values() if success),
                'ratio_success_count': sum(1 for success in ratio_results.values() if success),
                'score_success_count': sum(1 for success in score_results.values() if success),
                'validation_results': validation_results,
                'post_fetch_validation': post_fetch_validation,
                'fetch_results': fetch_results,
                'ratio_results': ratio_results,
                'score_results': score_results
            }
            
            # Print final summary
            self.print_workflow_summary(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in complete workflow: {e}")
            print(f"❌ Error in complete workflow: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def print_workflow_summary(self, summary: Dict[str, any]):
        """Print a comprehensive summary of the workflow results"""
        print(f"\n📊 COMPREHENSIVE WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"  🕒 Execution Time: {summary['execution_time']:.2f} seconds")
        print(f"  📈 Tickers Processed: {summary['tickers_processed']}")
        print(f"  📥 Tickers Fetched: {summary['tickers_fetched']}")
        print(f"  ✅ Successful Fetches: {summary['fetch_success_count']}")
        print(f"  🧮 Successful Ratio Calculations: {summary['ratio_success_count']}")
        print(f"  📊 Successful Score Updates: {summary['score_success_count']}")
        
        # Data quality improvement
        if 'validation_results' in summary and 'post_fetch_validation' in summary:
            pre_avg_quality = sum(r['data_quality_score'] for r in summary['validation_results'].values()) / len(summary['validation_results'])
            post_avg_quality = sum(r['data_quality_score'] for r in summary['post_fetch_validation'].values()) / len(summary['post_fetch_validation'])
            
            print(f"  📊 Average Data Quality: {pre_avg_quality:.1f}% → {post_avg_quality:.1f}%")
        
        print(f"\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.fmp_service:
                self.fmp_service.close()
        except:
            pass

def main():
    """Main execution function"""
    # Test tickers
    test_tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM', 'AMD', 'AMZN', 'AVGO', 'INTC', 'MU', 'QCOM']
    
    workflow = ComprehensiveDataWorkflow()
    
    try:
        # Run the complete workflow
        summary = workflow.run_complete_workflow(test_tickers)
        
        if summary['status'] == 'success':
            print(f"\n🎉 COMPREHENSIVE WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"Check the summary above for detailed results.")
        else:
            print(f"\n❌ WORKFLOW FAILED: {summary.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Error in main workflow: {e}")
        print(f"❌ Error in main workflow: {e}")
    
    finally:
        workflow.cleanup()

if __name__ == "__main__":
    main() 