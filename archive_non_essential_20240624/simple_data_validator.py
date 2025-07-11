#!/usr/bin/env python3
"""
Simple Data Validator
=====================

This script validates the completeness of fundamental data in the company_fundamentals table
and identifies missing critical fields without attempting to fetch data.

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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleDataValidator:
    """Simple validator that identifies missing data without fetching"""
    
    def __init__(self):
        """Initialize the data validator"""
        self.db = DatabaseManager()
        
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
    
    def print_validation_summary(self, validation_results: Dict[str, Dict]):
        """Print a comprehensive summary of validation results"""
        print(f"\n📊 VALIDATION SUMMARY")
        print("=" * 80)
        
        # Calculate statistics
        total_tickers = len(validation_results)
        tickers_with_data = sum(1 for r in validation_results.values() if r['has_data'])
        tickers_needing_fetch = len(self.identify_tickers_needing_fetch(validation_results))
        
        avg_quality = sum(r['data_quality_score'] for r in validation_results.values()) / total_tickers
        
        print(f"  📈 Total Tickers: {total_tickers}")
        print(f"  📊 Tickers with Data: {tickers_with_data}")
        print(f"  📥 Tickers Needing Fetch: {tickers_needing_fetch}")
        print(f"  📊 Average Data Quality: {avg_quality:.1f}%")
        
        # Group by data quality
        excellent = sum(1 for r in validation_results.values() if r['data_quality_score'] >= 90)
        good = sum(1 for r in validation_results.values() if 70 <= r['data_quality_score'] < 90)
        fair = sum(1 for r in validation_results.values() if 50 <= r['data_quality_score'] < 70)
        poor = sum(1 for r in validation_results.values() if r['data_quality_score'] < 50)
        
        print(f"\n📋 DATA QUALITY BREAKDOWN:")
        print(f"  🟢 Excellent (90%+): {excellent} tickers")
        print(f"  🟡 Good (70-89%): {good} tickers")
        print(f"  🟠 Fair (50-69%): {fair} tickers")
        print(f"  🔴 Poor (<50%): {poor} tickers")
        
        # Most common missing fields
        all_missing_fields = []
        for result in validation_results.values():
            all_missing_fields.extend(result.get('missing_fields', []))
        
        if all_missing_fields:
            from collections import Counter
            field_counts = Counter(all_missing_fields)
            print(f"\n📋 MOST COMMON MISSING FIELDS:")
            for field, count in field_counts.most_common(5):
                print(f"  ❌ {field}: {count} tickers")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for ticker in sorted(validation_results.keys()):
            result = validation_results[ticker]
            quality = result['data_quality_score']
            missing_count = len(result.get('missing_fields', []))
            zero_count = len(result.get('zero_fields', []))
            
            status = "✅" if quality >= 90 else "🟡" if quality >= 70 else "🟠" if quality >= 50 else "🔴"
            
            print(f"  {ticker}: {quality}% {status} (missing: {missing_count}, zero: {zero_count})")
    
    def generate_fetch_list(self, validation_results: Dict[str, Dict]) -> List[str]:
        """
        Generate a prioritized list of tickers that need data fetching
        
        Returns:
            List of tickers prioritized by data quality (worst first)
        """
        tickers_needing_fetch = self.identify_tickers_needing_fetch(validation_results)
        
        # Sort by data quality (worst first) and then by ticker name
        sorted_tickers = sorted(
            tickers_needing_fetch,
            key=lambda t: (validation_results[t]['data_quality_score'], t)
        )
        
        return sorted_tickers
    
    def export_validation_report(self, validation_results: Dict[str, Dict], filename: str = None):
        """
        Export validation results to a CSV file
        
        Args:
            validation_results: Results from validation
            filename: Output filename (optional)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_validation_report_{timestamp}.csv"
        
        try:
            import csv
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = [
                    'ticker', 'has_data', 'data_quality_score', 'missing_fields_count',
                    'zero_fields_count', 'needs_fetch', 'data_source', 'last_updated'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for ticker, result in validation_results.items():
                    writer.writerow({
                        'ticker': ticker,
                        'has_data': result['has_data'],
                        'data_quality_score': result['data_quality_score'],
                        'missing_fields_count': len(result.get('missing_fields', [])),
                        'zero_fields_count': len(result.get('zero_fields', [])),
                        'needs_fetch': result['needs_fetch'],
                        'data_source': result.get('data_source', ''),
                        'last_updated': result.get('last_updated', '')
                    })
            
            print(f"\n📄 Validation report exported to: {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting validation report: {e}")
            print(f"❌ Error exporting validation report: {e}")

def main():
    """Main execution function"""
    # Test tickers
    test_tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM', 'AMD', 'AMZN', 'AVGO', 'INTC', 'MU', 'QCOM']
    
    validator = SimpleDataValidator()
    
    try:
        print(f"\n🚀 STARTING DATA VALIDATION")
        print("=" * 80)
        
        # Validate all tickers
        validation_results = validator.validate_all_tickers(test_tickers)
        
        # Print summary
        validator.print_validation_summary(validation_results)
        
        # Generate fetch list
        fetch_list = validator.generate_fetch_list(validation_results)
        if fetch_list:
            print(f"\n📥 TICKERS NEEDING DATA FETCH (prioritized):")
            for i, ticker in enumerate(fetch_list, 1):
                quality = validation_results[ticker]['data_quality_score']
                print(f"  {i:2d}. {ticker} ({quality}% quality)")
        
        # Export report
        validator.export_validation_report(validation_results)
        
        print(f"\n🎉 VALIDATION COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        logger.error(f"Error in main validation: {e}")
        print(f"❌ Error in main validation: {e}")

if __name__ == "__main__":
    main() 