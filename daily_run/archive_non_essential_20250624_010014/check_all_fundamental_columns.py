#!/usr/bin/env python3
"""
Check all fundamental columns for the 10 tickers
"""

from database import DatabaseManager

def check_all_fundamental_columns(tickers):
    print(f"Checking all fundamental columns for: {tickers}")
    print("=" * 80)
    
    db = DatabaseManager()
    db.connect()
    
    # Get all fundamental columns
    fundamental_columns = [
        'market_cap', 'revenue_ttm', 'net_income_ttm', 'total_assets', 'total_debt',
        'shareholders_equity', 'current_assets', 'current_liabilities', 'operating_income',
        'cash_and_equivalents', 'free_cash_flow', 'shares_outstanding', 'diluted_eps_ttm',
        'book_value_per_share', 'ebitda_ttm', 'enterprise_value'
    ]
    
    columns_str = ', '.join(fundamental_columns)
    query = f"""
    SELECT ticker, {columns_str}
    FROM stocks 
    WHERE ticker = ANY(%s)
    ORDER BY ticker
    """
    
    try:
        results = db.execute_query(query, (tickers,))
        if results:
            print("Current fundamental data:")
            print("-" * 80)
            
            for row in results:
                ticker = row[0]
                print(f"\n{ticker}:")
                
                null_count = 0
                for i, column in enumerate(fundamental_columns, 1):
                    value = row[i]
                    if value is None:
                        print(f"  ❌ {column}: NULL")
                        null_count += 1
                    else:
                        if 'ratio' in column.lower() or 'eps' in column.lower():
                            print(f"  ✅ {column}: {value:.2f}")
                        elif 'cap' in column.lower() or 'revenue' in column.lower() or 'income' in column.lower() or 'debt' in column.lower() or 'equity' in column.lower() or 'assets' in column.lower() or 'cash' in column.lower() or 'flow' in column.lower():
                            print(f"  ✅ {column}: ${value:,.0f}")
                        else:
                            print(f"  ✅ {column}: {value}")
                
                print(f"  Summary: {len(fundamental_columns) - null_count}/{len(fundamental_columns)} columns filled")
        else:
            print("No records found")
    except Exception as e:
        print(f"Error querying data: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    check_all_fundamental_columns(tickers) 