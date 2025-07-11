#!/usr/bin/env python3
"""
Analyze Missing Data in Stocks and Company Fundamentals Tables
Identifies tickers with missing or incomplete data
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import pandas as pd

from database import DatabaseManager
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Analyze missing data in database tables"""
    
    def __init__(self):
        """Initialize the data analyzer"""
        self.db = DatabaseManager()
        
    def analyze_stocks_table(self) -> Dict[str, Any]:
        """Analyze the stocks table for missing data"""
        logger.info("Analyzing stocks table...")
        
        try:
            # Get total count
            total_query = "SELECT COUNT(*) FROM stocks WHERE ticker IS NOT NULL"
            total_result = self.db.execute_query(total_query)
            total_stocks = total_result[0][0] if total_result else 0
            
            # Check for missing company info
            missing_info_query = """
                SELECT ticker, company_name, sector, industry, market_cap
                FROM stocks 
                WHERE ticker IS NOT NULL 
                AND (company_name IS NULL OR company_name = '' OR 
                     sector IS NULL OR sector = '' OR 
                     industry IS NULL OR industry = '' OR
                     market_cap IS NULL OR market_cap = 0)
                ORDER BY market_cap DESC NULLS LAST
            """
            missing_info_result = self.db.execute_query(missing_info_query)
            
            # Check for stocks with no fundamental data
            no_fundamentals_query = """
                SELECT s.ticker, s.company_name, s.market_cap
                FROM stocks s
                LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
                WHERE s.ticker IS NOT NULL 
                AND cf.ticker IS NULL
                ORDER BY s.market_cap DESC NULLS LAST
            """
            no_fundamentals_result = self.db.execute_query(no_fundamentals_query)
            
            # Check for stale fundamental data (older than 7 days)
            stale_data_query = """
                SELECT s.ticker, s.company_name, cf.last_updated, s.market_cap
                FROM stocks s
                INNER JOIN company_fundamentals cf ON s.ticker = cf.ticker
                WHERE s.ticker IS NOT NULL 
                AND cf.last_updated < %s
                ORDER BY s.market_cap DESC NULLS LAST
            """
            cutoff_date = datetime.now() - timedelta(days=7)
            stale_data_result = self.db.execute_query(stale_data_query, (cutoff_date,))
            
            return {
                'total_stocks': total_stocks,
                'missing_company_info': [{'ticker': row[0], 'company_name': row[1], 'sector': row[2], 'industry': row[3], 'market_cap': row[4]} for row in missing_info_result],
                'no_fundamentals': [{'ticker': row[0], 'company_name': row[1], 'market_cap': row[2]} for row in no_fundamentals_result],
                'stale_fundamentals': [{'ticker': row[0], 'company_name': row[1], 'last_updated': row[2], 'market_cap': row[3]} for row in stale_data_result]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing stocks table: {e}")
            return {}
    
    def analyze_company_fundamentals_table(self) -> Dict[str, Any]:
        """Analyze the company_fundamentals table for missing data"""
        logger.info("Analyzing company_fundamentals table...")
        
        try:
            # Get total count
            total_query = "SELECT COUNT(*) FROM company_fundamentals WHERE ticker IS NOT NULL"
            total_result = self.db.execute_query(total_query)
            total_fundamentals = total_result[0][0] if total_result else 0
            
            # Check for missing key financial data
            missing_financials_query = """
                SELECT ticker, 
                       revenue_ttm, net_income_ttm, total_assets, total_equity,
                       total_debt, free_cash_flow, shares_outstanding,
                       pe_ratio, pb_ratio, debt_to_equity, current_ratio,
                       roe, roa, gross_margin, operating_margin, net_margin
                FROM company_fundamentals 
                WHERE ticker IS NOT NULL
                AND (revenue_ttm IS NULL OR revenue_ttm = 0 OR
                     net_income_ttm IS NULL OR net_income_ttm = 0 OR
                     total_assets IS NULL OR total_assets = 0 OR
                     total_equity IS NULL OR total_equity = 0 OR
                     shares_outstanding IS NULL OR shares_outstanding = 0)
                ORDER BY ticker
            """
            missing_financials_result = self.db.execute_query(missing_financials_query)
            
            # Check for missing ratios
            missing_ratios_query = """
                SELECT ticker, 
                       pe_ratio, pb_ratio, debt_to_equity, current_ratio,
                       roe, roa, gross_margin, operating_margin, net_margin
                FROM company_fundamentals 
                WHERE ticker IS NOT NULL
                AND (pe_ratio IS NULL OR pe_ratio = 0 OR
                     pb_ratio IS NULL OR pb_ratio = 0 OR
                     debt_to_equity IS NULL OR debt_to_equity = 0 OR
                     current_ratio IS NULL OR current_ratio = 0 OR
                     roe IS NULL OR roe = 0 OR
                     roa IS NULL OR roa = 0)
                ORDER BY ticker
            """
            missing_ratios_result = self.db.execute_query(missing_ratios_query)
            
            # Check data quality by counting non-null values
            quality_query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN revenue_ttm IS NOT NULL AND revenue_ttm != 0 THEN 1 END) as revenue_count,
                    COUNT(CASE WHEN net_income_ttm IS NOT NULL AND net_income_ttm != 0 THEN 1 END) as net_income_count,
                    COUNT(CASE WHEN total_assets IS NOT NULL AND total_assets != 0 THEN 1 END) as total_assets_count,
                    COUNT(CASE WHEN total_equity IS NOT NULL AND total_equity != 0 THEN 1 END) as total_equity_count,
                    COUNT(CASE WHEN pe_ratio IS NOT NULL AND pe_ratio != 0 THEN 1 END) as pe_ratio_count,
                    COUNT(CASE WHEN pb_ratio IS NOT NULL AND pb_ratio != 0 THEN 1 END) as pb_ratio_count,
                    COUNT(CASE WHEN roe IS NOT NULL AND roe != 0 THEN 1 END) as roe_count
                FROM company_fundamentals 
                WHERE ticker IS NOT NULL
            """
            quality_result = self.db.execute_query(quality_query)
            
            return {
                'total_fundamentals': total_fundamentals,
                'missing_financials': [{'ticker': row[0], 'revenue_ttm': row[1], 'net_income_ttm': row[2], 'total_assets': row[3], 'total_equity': row[4], 'total_debt': row[5], 'free_cash_flow': row[6], 'shares_outstanding': row[7], 'pe_ratio': row[8], 'pb_ratio': row[9], 'debt_to_equity': row[10], 'current_ratio': row[11], 'roe': row[12], 'roa': row[13], 'gross_margin': row[14], 'operating_margin': row[15], 'net_margin': row[16]} for row in missing_financials_result],
                'missing_ratios': [{'ticker': row[0], 'pe_ratio': row[1], 'pb_ratio': row[2], 'debt_to_equity': row[3], 'current_ratio': row[4], 'roe': row[5], 'roa': row[6], 'gross_margin': row[7], 'operating_margin': row[8], 'net_margin': row[9]} for row in missing_ratios_result],
                'data_quality': quality_result[0] if quality_result else {}
            }
            
        except Exception as e:
            logger.error(f"Error analyzing company_fundamentals table: {e}")
            return {}
    
    def get_tickers_needing_data(self) -> List[str]:
        """Get list of tickers that need data updates"""
        logger.info("Getting tickers needing data updates...")
        
        try:
            # Get tickers with missing fundamentals
            query = """
                SELECT DISTINCT s.ticker 
                FROM stocks s
                LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
                WHERE s.ticker IS NOT NULL
                AND (cf.ticker IS NULL OR 
                     cf.revenue_ttm IS NULL OR cf.revenue_ttm = 0 OR
                     cf.total_equity IS NULL OR cf.total_equity = 0 OR
                     cf.shares_outstanding IS NULL OR cf.shares_outstanding = 0 OR
                     cf.last_updated < %s)
                ORDER BY s.market_cap DESC NULLS LAST
            """
            cutoff_date = datetime.now() - timedelta(days=7)
            result = self.db.execute_query(query, (cutoff_date,))
            
            tickers = [row[0] for row in result if row[0]]
            logger.info(f"Found {len(tickers)} tickers needing data updates")
            return tickers
            
        except Exception as e:
            logger.error(f"Error getting tickers needing data: {e}")
            return []
    
    def generate_missing_data_report(self) -> Dict[str, Any]:
        """Generate comprehensive missing data report"""
        logger.info("Generating missing data report...")
        
        stocks_analysis = self.analyze_stocks_table()
        fundamentals_analysis = self.analyze_company_fundamentals_table()
        tickers_needing_data = self.get_tickers_needing_data()
        
        report = {
            'timestamp': datetime.now(),
            'stocks_analysis': stocks_analysis,
            'fundamentals_analysis': fundamentals_analysis,
            'tickers_needing_data': tickers_needing_data,
            'summary': {
                'total_stocks': stocks_analysis.get('total_stocks', 0),
                'stocks_missing_info': len(stocks_analysis.get('missing_company_info', [])),
                'stocks_no_fundamentals': len(stocks_analysis.get('no_fundamentals', [])),
                'stocks_stale_fundamentals': len(stocks_analysis.get('stale_fundamentals', [])),
                'total_fundamentals': fundamentals_analysis.get('total_fundamentals', 0),
                'fundamentals_missing_data': len(fundamentals_analysis.get('missing_financials', [])),
                'fundamentals_missing_ratios': len(fundamentals_analysis.get('missing_ratios', [])),
                'tickers_needing_updates': len(tickers_needing_data)
            }
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Print the missing data report"""
        print("📊 MISSING DATA ANALYSIS REPORT")
        print("=" * 60)
        print(f"Generated: {report['timestamp']}")
        print()
        
        # Stocks summary
        summary = report['summary']
        print("📈 STOCKS TABLE:")
        print(f"  Total stocks: {summary['total_stocks']}")
        print(f"  Missing company info: {summary['stocks_missing_info']}")
        print(f"  No fundamentals: {summary['stocks_no_fundamentals']}")
        print(f"  Stale fundamentals (>7 days): {summary['stocks_stale_fundamentals']}")
        print()
        
        # Fundamentals summary
        print("💰 COMPANY FUNDAMENTALS TABLE:")
        print(f"  Total records: {summary['total_fundamentals']}")
        print(f"  Missing financial data: {summary['fundamentals_missing_data']}")
        print(f"  Missing ratios: {summary['fundamentals_missing_ratios']}")
        print()
        
        # Data quality
        if 'data_quality' in report['fundamentals_analysis']:
            quality = report['fundamentals_analysis']['data_quality']
            if quality:
                total = quality[0] or 1
                print("📊 DATA QUALITY METRICS:")
                print(f"  Revenue data: {quality[1]}/{total} ({quality[1]/total*100:.1f}%)")
                print(f"  Net income data: {quality[2]}/{total} ({quality[2]/total*100:.1f}%)")
                print(f"  Total assets data: {quality[3]}/{total} ({quality[3]/total*100:.1f}%)")
                print(f"  Total equity data: {quality[4]}/{total} ({quality[4]/total*100:.1f}%)")
                print(f"  P/E ratio data: {quality[5]}/{total} ({quality[5]/total*100:.1f}%)")
                print(f"  P/B ratio data: {quality[6]}/{total} ({quality[6]/total*100:.1f}%)")
                print(f"  ROE data: {quality[7]}/{total} ({quality[7]/total*100:.1f}%)")
                print()
        
        # Tickers needing updates
        print(f"🔄 TICKERS NEEDING UPDATES: {summary['tickers_needing_updates']}")
        if report['tickers_needing_data']:
            print("  Top 20 tickers by market cap:")
            for i, ticker in enumerate(report['tickers_needing_data'][:20]):
                print(f"    {i+1:2d}. {ticker}")
            if len(report['tickers_needing_data']) > 20:
                print(f"    ... and {len(report['tickers_needing_data']) - 20} more")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if summary['tickers_needing_updates'] > 0:
            print(f"  - Process {min(summary['tickers_needing_updates'], 100)} tickers per batch")
            print(f"  - Focus on high market cap stocks first")
            print(f"  - Use FMP batch API calls for efficiency")
        else:
            print("  - All data appears to be up to date!")
        print()

def main():
    """Main function to run the analysis"""
    analyzer = DataAnalyzer()
    
    try:
        # Generate report
        report = analyzer.generate_missing_data_report()
        
        # Print report
        analyzer.print_report(report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"missing_data_report_{timestamp}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Report saved to: {filename}")
        
        return report
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return None

if __name__ == "__main__":
    main() 