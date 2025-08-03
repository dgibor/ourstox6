#!/usr/bin/env python3
"""
Analyze the actual ratio calculation results vs reported success
"""
import sys
sys.path.insert(0, 'daily_run')

from database import DatabaseManager

def analyze_ratio_calculations():
    """Analyze the actual ratio calculation results"""
    db = DatabaseManager()
    
    tickers = ['PG', 'AZN', 'COST', 'XOM', 'ORCL', 'LLY', 'TSM', 'AVGO', 'WFC', 'AMD', 'CVX', 'IBM', 'CSCO']
    
    print("🔍 COMPREHENSIVE RATIO ANALYSIS")
    print("=" * 80)
    
    total_ratios_possible = 27  # Total number of ratios we try to calculate
    all_results = {}
    
    for ticker in tickers:
        print(f"\n📊 Analyzing {ticker}:")
        print("-" * 50)
        
        # Get the latest fundamental data
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ticker, last_updated,
                    -- Valuation ratios (5)
                    price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda, peg_ratio,
                    -- Profitability ratios (6)
                    return_on_equity, return_on_assets, return_on_invested_capital,
                    gross_margin, operating_margin, net_margin,
                    -- Financial health ratios (5)
                    debt_to_equity_ratio, current_ratio, quick_ratio, interest_coverage, altman_z_score,
                    -- Efficiency ratios (3)
                    asset_turnover, inventory_turnover, receivables_turnover,
                    -- Growth ratios (3)
                    revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
                    -- Quality ratios (2)
                    fcf_to_net_income, cash_conversion_cycle,
                    -- Market ratios (3)
                    market_cap, enterprise_value, graham_number
                FROM company_fundamentals 
                WHERE ticker = %s AND period_type = 'ttm' 
                ORDER BY last_updated DESC 
                LIMIT 1
            """, (ticker,))
            
            result = cursor.fetchone()
            
            if result:
                # Extract values
                values = result[2:]  # Skip ticker and last_updated
                
                # Count calculated vs null ratios
                calculated_ratios = sum(1 for val in values if val is not None)
                null_ratios = sum(1 for val in values if val is None)
                
                # Categorize by ratio type
                valuation_ratios = values[0:5]  # 5 ratios
                profitability_ratios = values[5:11]  # 6 ratios
                financial_health_ratios = values[11:16]  # 5 ratios
                efficiency_ratios = values[16:19]  # 3 ratios
                growth_ratios = values[19:22]  # 3 ratios
                quality_ratios = values[22:24]  # 2 ratios
                market_ratios = values[24:27]  # 3 ratios
                
                # Count by category
                categories = {
                    'Valuation': (valuation_ratios, 5),
                    'Profitability': (profitability_ratios, 6),
                    'Financial Health': (financial_health_ratios, 5),
                    'Efficiency': (efficiency_ratios, 3),
                    'Growth': (growth_ratios, 3),
                    'Quality': (quality_ratios, 2),
                    'Market': (market_ratios, 3)
                }
                
                print(f"Last Updated: {result[1]}")
                print(f"Overall: {calculated_ratios}/{total_ratios_possible} ratios calculated ({calculated_ratios/total_ratios_possible*100:.1f}%)")
                print(f"Null ratios: {null_ratios}")
                
                print("\n📋 Breakdown by Category:")
                for category, (ratios, total) in categories.items():
                    calculated = sum(1 for r in ratios if r is not None)
                    percentage = calculated / total * 100 if total > 0 else 0
                    status = "✅" if calculated == total else "⚠️" if calculated > 0 else "❌"
                    print(f"  {status} {category}: {calculated}/{total} ({percentage:.1f}%)")
                
                # Store results
                all_results[ticker] = {
                    'calculated': calculated_ratios,
                    'total': total_ratios_possible,
                    'percentage': calculated_ratios / total_ratios_possible * 100,
                    'categories': categories
                }
                
                # Show specific missing ratios
                print("\n❌ Missing Ratios:")
                ratio_names = [
                    'P/E Ratio', 'P/B Ratio', 'P/S Ratio', 'EV/EBITDA', 'PEG Ratio',
                    'ROE', 'ROA', 'ROIC', 'Gross Margin', 'Operating Margin', 'Net Margin',
                    'Debt/Equity', 'Current Ratio', 'Quick Ratio', 'Interest Coverage', 'Altman Z-Score',
                    'Asset Turnover', 'Inventory Turnover', 'Receivables Turnover',
                    'Revenue Growth YoY', 'Earnings Growth YoY', 'FCF Growth YoY',
                    'FCF to Net Income', 'Cash Conversion Cycle',
                    'Market Cap', 'Enterprise Value', 'Graham Number'
                ]
                
                missing_count = 0
                for i, (name, value) in enumerate(zip(ratio_names, values)):
                    if value is None:
                        print(f"    • {name}")
                        missing_count += 1
                        if missing_count >= 10:  # Limit output
                            print(f"    • ... and {len(ratio_names) - i - 1} more")
                            break
            else:
                print(f"❌ No data found for {ticker}")
                all_results[ticker] = {
                    'calculated': 0,
                    'total': total_ratios_possible,
                    'percentage': 0,
                    'categories': {}
                }
    
    # Summary
    print(f"\n📊 OVERALL SUMMARY")
    print("=" * 80)
    
    total_companies = len(tickers)
    total_calculated = sum(r['calculated'] for r in all_results.values())
    total_possible = total_companies * total_ratios_possible
    overall_percentage = total_calculated / total_possible * 100
    
    print(f"Total Companies: {total_companies}")
    print(f"Total Ratios Calculated: {total_calculated}/{total_possible} ({overall_percentage:.1f}%)")
    
    print(f"\n📋 Company Performance:")
    print("-" * 60)
    print(f"{'Ticker':<6} {'Calculated':<10} {'Percentage':<12} {'Status'}")
    print("-" * 60)
    
    for ticker in sorted(tickers):
        result = all_results[ticker]
        percentage = result['percentage']
        status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
        print(f"{ticker:<6} {result['calculated']:<10} {percentage:<11.1f}% {status}")
    
    # Category analysis
    print(f"\n📊 CATEGORY ANALYSIS")
    print("=" * 80)
    
    category_totals = {}
    for ticker, result in all_results.items():
        for category, (ratios, total) in result['categories'].items():
            if category not in category_totals:
                category_totals[category] = {'calculated': 0, 'total': 0}
            category_totals[category]['calculated'] += sum(1 for r in ratios if r is not None)
            category_totals[category]['total'] += total
    
    for category, totals in category_totals.items():
        percentage = totals['calculated'] / totals['total'] * 100 if totals['total'] > 0 else 0
        status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
        print(f"{status} {category}: {totals['calculated']}/{totals['total']} ({percentage:.1f}%)")

if __name__ == "__main__":
    analyze_ratio_calculations() 