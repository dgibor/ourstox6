"""
Test the enhanced fundamental ratio calculator on 10 real tickers
"""

import logging
import sys
import os
import psycopg2.extras
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Add daily_run to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))

def test_real_tickers():
    """Test the enhanced fundamental ratio calculator on real tickers"""
    
    # Test tickers - mix of different sectors and market caps
    test_tickers = [
        'AAPL',   # Technology - Large Cap
        'MSFT',   # Technology - Large Cap  
        'GOOGL',  # Technology - Large Cap
        'AMZN',   # Consumer Discretionary - Large Cap
        'TSLA',   # Consumer Discretionary - Large Cap
        'JPM',    # Financial - Large Cap
        'JNJ',    # Healthcare - Large Cap
        'PG',     # Consumer Staples - Large Cap
        'XOM',    # Energy - Large Cap
        'NVDA'    # Technology - Large Cap
    ]
    
    try:
        # Import the enhanced calculator with fallback
        try:
            from improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
            from database import DatabaseManager
        except ImportError:
            # Fallback to relative imports
            from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
            from daily_run.database import DatabaseManager
        
        logger.info("✅ Successfully imported enhanced calculator")
        
        # Initialize calculator and database
        calculator = EnhancedRatioCalculatorV5()
        db = DatabaseManager()
        
        logger.info(f"Testing {len(test_tickers)} tickers: {', '.join(test_tickers)}")
        
        results = {}
        successful_calculations = 0
        failed_calculations = 0
        
        for ticker in test_tickers:
            logger.info(f"\n--- Processing {ticker} ---")
            
            try:
                # Get current price from daily_charts table - use dollar-format data
                current_price_query = """
                    SELECT close 
                    FROM daily_charts 
                    WHERE ticker = %s AND close > 1000
                    ORDER BY date DESC 
                    LIMIT 1
                """
                
                with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(current_price_query, (ticker,))
                    price_result = cursor.fetchone()
                    
                    if not price_result or not price_result['close']:
                        logger.warning(f"No current price found for {ticker}")
                        failed_calculations += 1
                        continue
                    
                    # Use dollar-format data directly (no conversion needed)
                    current_price = price_result['close']
                    logger.info(f"Current price: ${current_price:.2f}")
                
                # Get fundamental data from company_fundamentals table
                fundamental_query = """
                    SELECT 
                        revenue, net_income, total_assets, total_equity, shares_outstanding,
                        eps_diluted, book_value_per_share, ebitda, total_debt, 
                        cash_and_equivalents, gross_profit, operating_income, 
                        free_cash_flow, current_assets, current_liabilities, inventory,
                        accounts_receivable, cost_of_goods_sold, operating_cash_flow,
                        shares_float, accounts_payable, retained_earnings
                    FROM company_fundamentals 
                    WHERE ticker = %s 
                    ORDER BY report_date DESC 
                    LIMIT 1
                """
                
                with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(fundamental_query, (ticker,))
                    fundamental_result = cursor.fetchone()
                    
                    if not fundamental_result:
                        logger.warning(f"No fundamental data found for {ticker}")
                        failed_calculations += 1
                        continue
                    
                    fundamental_data = dict(fundamental_result)
                    logger.info(f"Found fundamental data with {len(fundamental_data)} fields")
                
                # Get historical data for growth calculations
                historical_query = """
                    SELECT 
                        revenue as revenue_previous, 
                        net_income as net_income_previous,
                        free_cash_flow as free_cash_flow_previous,
                        total_assets as total_assets_previous,
                        inventory as inventory_previous,
                        accounts_receivable as accounts_receivable_previous,
                        retained_earnings as retained_earnings_previous
                    FROM company_fundamentals 
                    WHERE ticker = %s 
                    ORDER BY report_date DESC 
                    LIMIT 1 OFFSET 1
                """
                
                with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(historical_query, (ticker,))
                    historical_result = cursor.fetchone()
                    historical_data = dict(historical_result) if historical_result else {}
                    
                    if historical_data:
                        logger.info(f"Found historical data with {len(historical_data)} fields")
                    else:
                        logger.info("No historical data available")
                
                # Calculate ratios
                ratios = calculator.calculate_all_ratios(
                    ticker, 
                    fundamental_data, 
                    current_price, 
                    historical_data
                )
                
                if ratios:
                    results[ticker] = {
                        'current_price': current_price,
                        'ratios': ratios,
                        'ratio_count': len(ratios)
                    }
                    
                    successful_calculations += 1
                    logger.info(f"✅ {ticker}: Calculated {len(ratios)} ratios")
                    
                    # Show key ratios
                    key_ratios = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'roe', 'roa', 'debt_to_equity']
                    for ratio in key_ratios:
                        if ratio in ratios:
                            logger.info(f"  {ratio}: {ratios[ratio]:.2f}")
                else:
                    logger.warning(f"❌ {ticker}: No ratios calculated")
                    failed_calculations += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {ticker}: {e}")
                failed_calculations += 1
        
        # Summary
        logger.info(f"\n--- SUMMARY ---")
        logger.info(f"Successful calculations: {successful_calculations}")
        logger.info(f"Failed calculations: {failed_calculations}")
        logger.info(f"Success rate: {successful_calculations/(successful_calculations+failed_calculations)*100:.1f}%")
        
        # Show detailed results
        logger.info(f"\n--- DETAILED RESULTS ---")
        for ticker, result in results.items():
            logger.info(f"\n{ticker} (${result['current_price']:.2f}):")
            logger.info(f"  Ratios calculated: {result['ratio_count']}")
            
            # Group ratios by category
            categories = {
                'Valuation': ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda'],
                'Profitability': ['roe', 'roa', 'roic', 'gross_margin', 'operating_margin', 'net_margin'],
                'Financial Health': ['debt_to_equity', 'current_ratio', 'quick_ratio'],
                'Efficiency': ['asset_turnover', 'inventory_turnover', 'receivables_turnover'],
                'Growth': ['revenue_growth_yoy', 'earnings_growth_yoy', 'fcf_growth_yoy'],
                'Quality': ['fcf_to_net_income'],
                'Market': ['market_cap', 'enterprise_value'],
                'Intrinsic': ['graham_number']
            }
            
            for category, ratio_names in categories.items():
                category_ratios = {name: result['ratios'][name] for name in ratio_names if name in result['ratios']}
                if category_ratios:
                    logger.info(f"  {category}:")
                    for ratio_name, value in category_ratios.items():
                        logger.info(f"    {ratio_name}: {value:.2f}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    logger.info("Starting enhanced fundamental ratio calculation test on real tickers")
    results = test_real_tickers()
    
    if results:
        logger.info("✅ Test completed successfully!")
    else:
        logger.error("❌ Test failed!")
        sys.exit(1) 