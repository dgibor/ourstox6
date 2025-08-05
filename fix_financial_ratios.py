#!/usr/bin/env python3
"""
Fix Missing Financial Ratios
Calculate missing financial ratios from available fundamental data
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialRatioCalculator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '38837')  # Railway port
        }
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def get_companies_with_fundamentals(self):
        """Get all companies that have fundamental data but missing ratios"""
        query = """
        SELECT DISTINCT cf.ticker, cf.last_updated, cf.revenue, cf.net_income, 
               cf.total_assets, cf.total_equity, cf.total_debt, cf.current_assets, 
               cf.current_liabilities, cf.book_value_per_share, cf.earnings_per_share,
               dc.close as current_price
        FROM company_fundamentals cf
        LEFT JOIN daily_charts dc ON cf.ticker = dc.ticker 
            AND dc.date = (SELECT MAX(date) FROM daily_charts WHERE ticker = cf.ticker)
        WHERE cf.last_updated = (SELECT MAX(last_updated) FROM company_fundamentals WHERE ticker = cf.ticker)
        AND (cf.revenue IS NOT NULL OR cf.net_income IS NOT NULL)
        ORDER BY cf.ticker
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
    
    def calculate_ratios(self, company_data):
        """Calculate financial ratios for a company"""
        ratios = {}
        
        try:
            # Extract data
            revenue = company_data.get('revenue', 0)
            net_income = company_data.get('net_income', 0)
            total_assets = company_data.get('total_assets', 0)
            total_equity = company_data.get('total_equity', 0)
            total_debt = company_data.get('total_debt', 0)
            current_assets = company_data.get('current_assets', 0)
            current_liabilities = company_data.get('current_liabilities', 0)
            book_value_per_share = company_data.get('book_value_per_share', 0)
            earnings_per_share = company_data.get('earnings_per_share', 0)
            current_price = company_data.get('current_price', 0)
            
            # Calculate ratios
            if earnings_per_share and earnings_per_share > 0 and current_price:
                ratios['pe_ratio'] = current_price / earnings_per_share
            else:
                ratios['pe_ratio'] = None
            
            if book_value_per_share and book_value_per_share > 0 and current_price:
                ratios['pb_ratio'] = current_price / book_value_per_share
            else:
                ratios['pb_ratio'] = None
            
            if total_equity and total_equity > 0:
                ratios['roe'] = (net_income / total_equity) * 100
            else:
                ratios['roe'] = None
            
            if total_assets and total_assets > 0:
                ratios['roa'] = (net_income / total_assets) * 100
            else:
                ratios['roa'] = None
            
            if total_equity and total_equity > 0 and total_debt:
                ratios['debt_to_equity'] = total_debt / total_equity
            else:
                ratios['debt_to_equity'] = None
            
            if current_liabilities and current_liabilities > 0 and current_assets:
                ratios['current_ratio'] = current_assets / current_liabilities
            else:
                ratios['current_ratio'] = None
            
            # Calculate EV/EBITDA (simplified - using net income as proxy for EBITDA)
            if net_income and net_income > 0:
                # Enterprise Value = Market Cap + Total Debt - Cash (simplified)
                # Using net income as proxy for EBITDA
                ev_ebitda = None
                if current_price and earnings_per_share and earnings_per_share > 0:
                    # Estimate shares outstanding from EPS and net income
                    shares_outstanding = net_income / earnings_per_share
                    market_cap = current_price * shares_outstanding
                    enterprise_value = market_cap + total_debt
                    ev_ebitda = enterprise_value / net_income
                ratios['ev_ebitda'] = ev_ebitda
            else:
                ratios['ev_ebitda'] = None
            
            # Calculate PEG ratio (simplified - would need earnings growth data)
            ratios['peg_ratio'] = None  # Need earnings growth data
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating ratios for {company_data.get('ticker', 'Unknown')}: {e}")
            return {}
    
    def store_ratios(self, ticker, ratios):
        """Store calculated ratios in the database"""
        query = """
        INSERT INTO financial_ratios (
            ticker, calculation_date, pe_ratio, pb_ratio, peg_ratio, roe, roa, 
            debt_to_equity, current_ratio, ev_ebitda, quick_ratio, interest_coverage,
            asset_turnover, inventory_turnover, receivables_turnover, 
            gross_margin, operating_margin, net_margin, fcf_margin, 
            revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
            debt_to_ebitda, net_debt_to_ebitda, interest_coverage_ratio,
            cash_conversion_cycle, working_capital_turnover, 
            fixed_asset_turnover, total_asset_turnover, equity_turnover,
            return_on_capital, return_on_invested_capital, economic_value_added,
            graham_number, piotroski_score, altman_z_score, beneish_score,
            price_to_fcf, price_to_ocf, price_to_book_ratio, price_to_sales_ratio,
            enterprise_value_to_revenue, enterprise_value_to_ebitda,
            dividend_yield, dividend_payout_ratio, dividend_growth_rate,
            share_repurchase_yield, total_shareholder_yield,
            capex_to_revenue, capex_to_operating_cash_flow,
            research_development_to_revenue, advertising_to_revenue,
            general_administrative_to_revenue, operating_expenses_to_revenue,
            effective_tax_rate, tax_burden, interest_burden, operating_margin_ebit,
            asset_turnover_ratio, equity_multiplier, dupont_roe_breakdown
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (ticker, calculation_date) 
        DO UPDATE SET
            pe_ratio = EXCLUDED.pe_ratio,
            pb_ratio = EXCLUDED.pb_ratio,
            roe = EXCLUDED.roe,
            roa = EXCLUDED.roa,
            debt_to_equity = EXCLUDED.debt_to_equity,
            current_ratio = EXCLUDED.current_ratio,
            ev_ebitda = EXCLUDED.ev_ebitda
        """
        
        params = (
            ticker, datetime.now().date(), 
            ratios.get('pe_ratio'), ratios.get('pb_ratio'), ratios.get('peg_ratio'),
            ratios.get('roe'), ratios.get('roa'), ratios.get('debt_to_equity'),
            ratios.get('current_ratio'), ratios.get('ev_ebitda'),
            None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None
        )
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error storing ratios for {ticker}: {e}")
            return False
    
    def process_all_companies(self):
        """Process all companies and calculate missing ratios"""
        logger.info("Starting financial ratio calculation...")
        
        companies = self.get_companies_with_fundamentals()
        logger.info(f"Found {len(companies)} companies with fundamental data")
        
        successful = 0
        failed = 0
        
        for i, company in enumerate(companies, 1):
            ticker = company['ticker']
            logger.info(f"[{i}/{len(companies)}] Processing {ticker}...")
            
            try:
                # Calculate ratios
                ratios = self.calculate_ratios(company)
                
                if ratios:
                    # Store ratios
                    if self.store_ratios(ticker, ratios):
                        successful += 1
                        logger.info(f"✅ {ticker}: PE={ratios.get('pe_ratio', 'N/A'):.2f}, "
                                  f"PB={ratios.get('pb_ratio', 'N/A'):.2f}, "
                                  f"ROE={ratios.get('roe', 'N/A'):.1f}%")
                    else:
                        failed += 1
                        logger.error(f"❌ Failed to store ratios for {ticker}")
                else:
                    failed += 1
                    logger.warning(f"⚠️ No ratios calculated for {ticker}")
                    
            except Exception as e:
                failed += 1
                logger.error(f"❌ Error processing {ticker}: {e}")
        
        logger.info(f"\n📋 SUMMARY:")
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📊 Success Rate: {successful/(successful+failed)*100:.1f}%")
        
        return successful, failed

def main():
    """Main function"""
    calculator = FinancialRatioCalculator()
    successful, failed = calculator.process_all_companies()
    
    print(f"\n🏁 Financial ratio calculation completed!")
    print(f"✅ Successfully processed: {successful} companies")
    print(f"❌ Failed: {failed} companies")

if __name__ == "__main__":
    main() 