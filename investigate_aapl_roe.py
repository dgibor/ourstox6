"""
Investigate AAPL ROE calculation and compare to Yahoo Finance
"""

import logging
import sys
import os
import psycopg2.extras
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def get_yahoo_finance_stats(ticker):
    """Get key statistics from Yahoo Finance"""
    try:
        # Using Yahoo Finance API
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # For key stats, we'll use a different approach
        stats_url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=financialData,defaultKeyStatistics"
        stats_response = requests.get(stats_url, timeout=10)
        stats_response.raise_for_status()
        
        data = stats_response.json()
        
        if 'quoteSummary' in data and 'result' in data['quoteSummary'] and data['quoteSummary']['result']:
            result = data['quoteSummary']['result'][0]
            
            financial_data = result.get('financialData', {})
            default_key_stats = result.get('defaultKeyStatistics', {})
            
            return {
                'current_price': financial_data.get('currentPrice'),
                'return_on_equity': financial_data.get('returnOnEquity'),
                'return_on_assets': financial_data.get('returnOnAssets'),
                'profit_margins': financial_data.get('profitMargins'),
                'operating_margins': financial_data.get('operatingMargins'),
                'ebitda_margins': financial_data.get('ebitdaMargins'),
                'revenue_growth': financial_data.get('revenueGrowth'),
                'earnings_growth': financial_data.get('earningsGrowth'),
                'revenue_per_share': financial_data.get('revenuePerShare'),
                'return_on_capital': financial_data.get('returnOnCapital'),
                'book_value': default_key_stats.get('bookValue'),
                'price_to_book': default_key_stats.get('priceToBook'),
                'enterprise_value': default_key_stats.get('enterpriseValue'),
                'market_cap': financial_data.get('marketCap')
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data: {e}")
        return None

def get_aapl_fundamental_data():
    """Get AAPL fundamental data from our database"""
    try:
        # Import with fallback
        try:
            from daily_run.database import DatabaseManager
        except ImportError:
            # Add daily_run to path and try again
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))
            from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Get current price
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT close 
                FROM daily_charts 
                WHERE ticker = 'AAPL' AND close > 1000
                ORDER BY date DESC 
                LIMIT 1
            """)
            price_result = cursor.fetchone()
            current_price = price_result['close'] if price_result else None
            
            # Get fundamental data
            cursor.execute("""
                SELECT 
                    revenue, net_income, total_assets, total_equity, shares_outstanding,
                    eps_diluted, book_value_per_share, ebitda, total_debt, 
                    cash_and_equivalents, gross_profit, operating_income, 
                    free_cash_flow, current_assets, current_liabilities, inventory,
                    accounts_receivable, cost_of_goods_sold, operating_cash_flow,
                    shares_float, accounts_payable, retained_earnings
                FROM company_fundamentals 
                WHERE ticker = 'AAPL' 
                ORDER BY report_date DESC 
                LIMIT 1
            """)
            fundamental_result = cursor.fetchone()
            
            if fundamental_result:
                return {
                    'current_price': current_price,
                    'fundamental_data': dict(fundamental_result)
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching database data: {e}")
        return None

def calculate_roe_manually(net_income, total_equity):
    """Calculate ROE manually"""
    if net_income and total_equity and total_equity > 0:
        roe = (net_income / total_equity) * 100
        return roe
    return None

def investigate_aapl_roe():
    """Investigate AAPL ROE calculation"""
    
    logger.info("=== AAPL ROE INVESTIGATION ===")
    
    # Get our database data
    logger.info("\n1. OUR DATABASE DATA:")
    db_data = get_aapl_fundamental_data()
    
    if db_data:
        current_price = db_data['current_price']
        fundamental_data = db_data['fundamental_data']
        
        logger.info(f"Current Price: ${current_price:,.2f}")
        logger.info(f"Net Income: ${fundamental_data.get('net_income', 'N/A'):,.0f}" if fundamental_data.get('net_income') else "Net Income: N/A")
        logger.info(f"Total Equity: ${fundamental_data.get('total_equity', 'N/A'):,.0f}" if fundamental_data.get('total_equity') else "Total Equity: N/A")
        logger.info(f"Shares Outstanding: {fundamental_data.get('shares_outstanding', 'N/A'):,.0f}" if fundamental_data.get('shares_outstanding') else "Shares Outstanding: N/A")
        
        # Calculate ROE manually
        net_income = fundamental_data.get('net_income')
        total_equity = fundamental_data.get('total_equity')
        
        if net_income and total_equity:
            manual_roe = calculate_roe_manually(net_income, total_equity)
            logger.info(f"Manual ROE Calculation: {manual_roe:.2f}%")
            
            # Check if values make sense
            logger.info(f"\nROE Components Analysis:")
            logger.info(f"  Net Income: ${net_income:,.0f}")
            logger.info(f"  Total Equity: ${total_equity:,.0f}")
            logger.info(f"  ROE = (${net_income:,.0f} / ${total_equity:,.0f}) * 100 = {manual_roe:.2f}%")
            
            # Check if values are reasonable
            if manual_roe > 100:
                logger.warning(f"⚠️  ROE > 100% - This seems unusually high!")
                logger.info(f"   Possible issues:")
                logger.info(f"   - Net Income might be too high")
                logger.info(f"   - Total Equity might be too low")
                logger.info(f"   - Data might be from different periods")
                
                # Check if it's trailing 12 months vs annual
                logger.info(f"\nData Period Check:")
                logger.info(f"  If Net Income is TTM and Total Equity is end-of-period:")
                logger.info(f"  ROE = TTM Net Income / End-of-Period Equity")
                logger.info(f"  This can be higher than annual ROE")
        
        # Show all fundamental data for debugging
        logger.info(f"\nAll Fundamental Data:")
        for key, value in fundamental_data.items():
            if value is not None:
                if isinstance(value, (int, float)) and value > 1000000:
                    logger.info(f"  {key}: ${value:,.0f}")
                else:
                    logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {key}: None")
    
    # Get Yahoo Finance data
    logger.info(f"\n2. YAHOO FINANCE DATA:")
    yahoo_data = get_yahoo_finance_stats('AAPL')
    
    if yahoo_data:
        logger.info(f"Current Price: ${yahoo_data.get('current_price', 'N/A')}")
        logger.info(f"ROE (Yahoo): {yahoo_data.get('return_on_equity', 'N/A')}")
        logger.info(f"ROA (Yahoo): {yahoo_data.get('return_on_assets', 'N/A')}")
        logger.info(f"Profit Margins (Yahoo): {yahoo_data.get('profit_margins', 'N/A')}")
        logger.info(f"Operating Margins (Yahoo): {yahoo_data.get('operating_margins', 'N/A')}")
        logger.info(f"Book Value (Yahoo): {yahoo_data.get('book_value', 'N/A')}")
        logger.info(f"Market Cap (Yahoo): ${yahoo_data.get('market_cap', 'N/A'):,.0f}" if yahoo_data.get('market_cap') else "Market Cap (Yahoo): N/A")
        
        # Compare ROE
        if db_data and yahoo_data.get('return_on_equity'):
            our_roe = calculate_roe_manually(net_income, total_equity)
            yahoo_roe = yahoo_data.get('return_on_equity')
            
            logger.info(f"\n3. ROE COMPARISON:")
            logger.info(f"Our Calculation: {our_roe:.2f}%")
            logger.info(f"Yahoo Finance: {yahoo_roe:.2f}%")
            logger.info(f"Difference: {abs(our_roe - yahoo_roe):.2f} percentage points")
            
            if abs(our_roe - yahoo_roe) > 10:
                logger.error(f"❌ Large discrepancy detected!")
                logger.info(f"Possible causes:")
                logger.info(f"1. Different time periods (TTM vs Annual)")
                logger.info(f"2. Different accounting standards")
                logger.info(f"3. Data quality issues")
                logger.info(f"4. Calculation methodology differences")
    
    # Additional analysis
    logger.info(f"\n4. ADDITIONAL ANALYSIS:")
    if db_data:
        fundamental_data = db_data['fundamental_data']
        
        # Check if we have multiple periods of data
        try:
            from daily_run.database import DatabaseManager
            db = DatabaseManager()
            
            with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT report_date, net_income, total_equity
                    FROM company_fundamentals 
                    WHERE ticker = 'AAPL' 
                    ORDER BY report_date DESC 
                    LIMIT 5
                """)
                
                results = cursor.fetchall()
                if results:
                    logger.info(f"Historical Data (Last 5 periods):")
                    for row in results:
                        roe = calculate_roe_manually(row['net_income'], row['total_equity'])
                        logger.info(f"  {row['report_date']}: Net Income=${row['net_income']:,.0f}, Equity=${row['total_equity']:,.0f}, ROE={roe:.2f}%")
        
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")

if __name__ == "__main__":
    investigate_aapl_roe() 