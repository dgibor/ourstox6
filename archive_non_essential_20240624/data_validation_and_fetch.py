#!/usr/bin/env python3
"""
Data Validation and Fetch Module
================================

This module validates the completeness of fundamental data in the company_fundamentals table,
identifies missing critical fields, and fetches missing data using batch API calls before
running ratio calculations.

Author: AI Assistant
Date: 2025-01-26
"""

import sys
import os
from datetime import date, datetime
from typing import List, Dict, Optional, Set, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_run.database import DatabaseManager
from daily_run.fmp_service import FMPService
from daily_run.ratio_calculator import calculate_ratios, validate_ratios

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates and fetches missing fundamental data"""
    
    def __init__(self):
        """Initialize the data validator"""
        self.db = DatabaseManager()
        self.fmp_service = None  # Initialize lazily to avoid connection issues
        
        # Critical fields required for ratio calculation
        self.critical_fields = {
            'financial': [
                'revenue', 'net_income', 'ebitda', 'total_equity', 
                'total_assets', 'total_debt', 'gross_profit', 
                'operating_income', 'free_cash_flow'
            ],
            'market': [
                'shares_outstanding', 'market_cap', 'enterprise_value'
            ]
        }
        
        # Fields that should not be zero or null for meaningful ratios
        self.non_zero_fields = [
            'revenue', 'net_income', 'total_equity', 'shares_outstanding'
        ]
    
    def _get_fmp_service(self):
        """Get FMP service instance with proper error handling"""
        if self.fmp_service is None:
            try:
                self.fmp_service = FMPService()
            except Exception as e:
                logger.error(f"Failed to initialize FMP service: {e}")
                return None
        return self.fmp_service
    
    def validate_ticker_data(self, ticker: str) -> Dict[str, any]:
        """
        Validate data completeness for a specific ticker
        
        Returns:
            Dict with validation results including missing fields and data quality issues
        """
        print(f"\n🔍 Validating data for {ticker}...")
        
        try:
            # Get the most recent fundamental data
            query = """
            SELECT 
                revenue, net_income, ebitda, total_equity, total_assets,
                total_debt, gross_profit, operating_income, free_cash_flow,
                shares_outstanding, market_cap, enterprise_value,
                data_source, last_updated
            FROM company_fundamentals
            WHERE ticker = %s
            ORDER BY last_updated DESC
            LIMIT 1
            """
            
            result = self.db.execute_query(query, (ticker,))
            
            if not result:
                return {
                    'ticker': ticker,
                    'has_data': False,
                    'missing_fields': self.critical_fields['financial'] + self.critical_fields['market'],
                    'zero_fields': [],
                    'data_quality_score': 0,
                    'needs_fetch': True,
                    'last_updated': None
                }
            
            row = result[0]
            field_names = [
                'revenue', 'net_income', 'ebitda', 'total_equity', 'total_assets',
                'total_debt', 'gross_profit', 'operating_income', 'free_cash_flow',
                'shares_outstanding', 'market_cap', 'enterprise_value'
            ]
            
            # Check for missing fields
            missing_fields = []
            zero_fields = []
            
            for i, field_name in enumerate(field_names):
                value = row[i]
                if value is None:
                    missing_fields.append(field_name)
                elif value == 0 and field_name in self.non_zero_fields:
                    zero_fields.append(field_name)
            
            # Calculate data quality score (0-100)
            total_fields = len(field_names)
            available_fields = total_fields - len(missing_fields)
            data_quality_score = int((available_fields / total_fields) * 100)
            
            # Determine if we need to fetch data
            needs_fetch = len(missing_fields) > 0 or len(zero_fields) > 0
            
            validation_result = {
                'ticker': ticker,
                'has_data': True,
                'missing_fields': missing_fields,
                'zero_fields': zero_fields,
                'data_quality_score': data_quality_score,
                'needs_fetch': needs_fetch,
                'last_updated': row[13],  # last_updated field
                'data_source': row[12]    # data_source field
            }
            
            # Print validation summary
            print(f"  📊 Data Quality Score: {data_quality_score}%")
            if missing_fields:
                print(f"  ❌ Missing fields: {', '.join(missing_fields)}")
            if zero_fields:
                print(f"  ⚠️  Zero fields: {', '.join(zero_fields)}")
            if not needs_fetch:
                print(f"  ✅ Data is complete and ready for ratio calculation")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating data for {ticker}: {e}")
            return {
                'ticker': ticker,
                'has_data': False,
                'missing_fields': self.critical_fields['financial'] + self.critical_fields['market'],
                'zero_fields': [],
                'data_quality_score': 0,
                'needs_fetch': True,
                'last_updated': None,
                'error': str(e)
            }
    
    def validate_all_tickers(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Validate data for all tickers
        
        Returns:
            Dict mapping ticker to validation results
        """
        print(f"\n🔍 VALIDATING DATA FOR {len(tickers)} TICKERS")
        print("=" * 60)
        
        validation_results = {}
        
        for ticker in tickers:
            validation_results[ticker] = self.validate_ticker_data(ticker)
        
        return validation_results
    
    def identify_tickers_needing_fetch(self, validation_results: Dict[str, Dict]) -> List[str]:
        """
        Identify tickers that need data fetching
        
        Returns:
            List of tickers that need data fetching
        """
        tickers_needing_fetch = []
        
        for ticker, result in validation_results.items():
            if result.get('needs_fetch', False):
                tickers_needing_fetch.append(ticker)
        
        return tickers_needing_fetch
    
    def fetch_missing_data_batch(self, tickers: List[str], max_workers: int = 1) -> Dict[str, bool]:
        """
        Fetch missing data for multiple tickers using batch processing
        
        Args:
            tickers: List of tickers to fetch data for
            max_workers: Maximum number of concurrent workers (default 1 to avoid rate limiting)
            
        Returns:
            Dict mapping ticker to success status
        """
        print(f"\n📥 FETCHING MISSING DATA FOR {len(tickers)} TICKERS")
        print("=" * 60)
        
        results = {}
        
        def fetch_single_ticker(ticker: str) -> Tuple[str, bool]:
            """Fetch data for a single ticker"""
            try:
                print(f"  📥 Fetching data for {ticker}...")
                
                # Get FMP service with proper error handling
                fmp_service = self._get_fmp_service()
                if not fmp_service:
                    print(f"    ❌ FMP service not available for {ticker}")
                    return ticker, False
                
                # Add delay between requests to avoid rate limiting
                time.sleep(2)
                
                # Fetch financial statements
                financial_data = fmp_service.fetch_financial_statements(ticker)
                if not financial_data:
                    print(f"    ❌ Failed to fetch financial statements for {ticker}")
                    return ticker, False
                
                # Add delay between requests
                time.sleep(1)
                
                # Fetch key statistics
                key_stats = fmp_service.fetch_key_statistics(ticker)
                if not key_stats:
                    print(f"    ⚠️  No key statistics for {ticker}, proceeding with financial data only")
                
                # Store the data
                success = fmp_service.store_fundamental_data(ticker, financial_data, key_stats or {})
                
                if success:
                    print(f"    ✅ Successfully fetched and stored data for {ticker}")
                else:
                    print(f"    ❌ Failed to store data for {ticker}")
                
                return ticker, success
                
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
                print(f"    ❌ Error fetching data for {ticker}: {e}")
                return ticker, False
        
        # Use ThreadPoolExecutor for concurrent fetching (but with limited workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(fetch_single_ticker, ticker): ticker 
                for ticker in tickers
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_ticker):
                ticker, success = future.result()
                results[ticker] = success
        
        return results
    
    def run_complete_validation_and_fetch(self, tickers: List[str]) -> Dict[str, any]:
        """
        Run complete validation and fetch workflow
        
        Args:
            tickers: List of tickers to process
            
        Returns:
            Summary of the entire process
        """
        print(f"\n🚀 STARTING COMPLETE DATA VALIDATION AND FETCH WORKFLOW")
        print("=" * 80)
        
        start_time = time.time()
        
        # Step 1: Validate all tickers
        print(f"\n📋 STEP 1: VALIDATING DATA COMPLETENESS")
        validation_results = self.validate_all_tickers(tickers)
        
        # Step 2: Identify tickers needing fetch
        print(f"\n📋 STEP 2: IDENTIFYING TICKERS NEEDING DATA FETCH")
        tickers_needing_fetch = self.identify_tickers_needing_fetch(validation_results)
        
        if not tickers_needing_fetch:
            print("  ✅ All tickers have complete data - no fetching needed!")
            return {
                'status': 'success',
                'tickers_processed': len(tickers),
                'tickers_fetched': 0,
                'validation_results': validation_results,
                'fetch_results': {},
                'execution_time': time.time() - start_time
            }
        
        print(f"  📥 Found {len(tickers_needing_fetch)} tickers needing data fetch: {', '.join(tickers_needing_fetch)}")
        
        # Step 3: Fetch missing data (with limited concurrency to avoid rate limiting)
        print(f"\n📋 STEP 3: FETCHING MISSING DATA")
        fetch_results = self.fetch_missing_data_batch(tickers_needing_fetch, max_workers=1)
        
        # Step 4: Re-validate after fetch
        print(f"\n📋 STEP 4: RE-VALIDATING AFTER DATA FETCH")
        post_fetch_validation = self.validate_all_tickers(tickers)
        
        # Step 5: Calculate ratios for all tickers
        print(f"\n📋 STEP 5: CALCULATING RATIOS")
        ratio_results = self.calculate_ratios_for_all_tickers(tickers)
        
        execution_time = time.time() - start_time
        
        # Prepare summary
        summary = {
            'status': 'success',
            'tickers_processed': len(tickers),
            'tickers_fetched': len(tickers_needing_fetch),
            'fetch_success_count': sum(1 for success in fetch_results.values() if success),
            'validation_results': validation_results,
            'post_fetch_validation': post_fetch_validation,
            'fetch_results': fetch_results,
            'ratio_results': ratio_results,
            'execution_time': execution_time
        }
        
        # Print final summary
        self.print_workflow_summary(summary)
        
        return summary
    
    def calculate_ratios_for_all_tickers(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Calculate ratios for all tickers after data validation and fetch
        
        Returns:
            Dict mapping ticker to ratio calculation success status
        """
        print(f"\n🧮 CALCULATING RATIOS FOR {len(tickers)} TICKERS")
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
                self.store_calculated_ratios(ticker, calculated_ratios)
                
                print(f"    ✅ Successfully calculated ratios for {ticker}")
                ratio_results[ticker] = True
                
            except Exception as e:
                logger.error(f"Error calculating ratios for {ticker}: {e}")
                print(f"    ❌ Error calculating ratios for {ticker}: {e}")
                ratio_results[ticker] = False
        
        return ratio_results
    
    def store_calculated_ratios(self, ticker: str, ratios: Dict[str, float]):
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
    
    def print_workflow_summary(self, summary: Dict[str, any]):
        """Print a comprehensive summary of the workflow results"""
        print(f"\n📊 WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"  🕒 Execution Time: {summary['execution_time']:.2f} seconds")
        print(f"  📈 Tickers Processed: {summary['tickers_processed']}")
        print(f"  📥 Tickers Fetched: {summary['tickers_fetched']}")
        print(f"  ✅ Successful Fetches: {summary['fetch_success_count']}")
        
        # Data quality improvement
        pre_avg_quality = sum(r['data_quality_score'] for r in summary['validation_results'].values()) / len(summary['validation_results'])
        post_avg_quality = sum(r['data_quality_score'] for r in summary['post_fetch_validation'].values()) / len(summary['post_fetch_validation'])
        
        print(f"  📊 Average Data Quality: {pre_avg_quality:.1f}% → {post_avg_quality:.1f}%")
        
        # Ratio calculation results
        successful_ratios = sum(1 for success in summary['ratio_results'].values() if success)
        print(f"  🧮 Successful Ratio Calculations: {successful_ratios}/{len(summary['ratio_results'])}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for ticker in summary['validation_results'].keys():
            pre_quality = summary['validation_results'][ticker]['data_quality_score']
            post_quality = summary['post_fetch_validation'][ticker]['data_quality_score']
            fetch_success = summary['fetch_results'].get(ticker, False)
            ratio_success = summary['ratio_results'].get(ticker, False)
            
            status_icons = []
            if fetch_success:
                status_icons.append("📥")
            if ratio_success:
                status_icons.append("🧮")
            
            status_str = " ".join(status_icons) if status_icons else "❌"
            
            print(f"  {ticker}: {pre_quality}% → {post_quality}% {status_str}")
    
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
    
    validator = DataValidator()
    
    try:
        # Run the complete workflow
        summary = validator.run_complete_validation_and_fetch(test_tickers)
        
        print(f"\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"Check the summary above for detailed results.")
        
    except Exception as e:
        logger.error(f"Error in main workflow: {e}")
        print(f"❌ Error in main workflow: {e}")
    
    finally:
        validator.cleanup()

if __name__ == "__main__":
    main() 