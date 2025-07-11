#!/usr/bin/env python3
"""
Debug SQL query generation
"""

from database import DatabaseManager
from datetime import datetime

def debug_sql_query():
    """Debug the SQL query being generated"""
    db = DatabaseManager()
    
    # Test values
    ticker = "NVDA"
    fiscal_year = 2024
    fiscal_quarter = 1
    
    # The SQL query from the fixed filler
    query = """
        INSERT INTO company_fundamentals (
            ticker, report_date, period_type, fiscal_year, fiscal_quarter,
            revenue, gross_profit, operating_income, net_income, ebitda,
            total_assets, total_debt, total_equity, free_cash_flow, shares_outstanding,
            price_to_earnings, price_to_book, debt_to_equity_ratio, current_ratio,
            return_on_equity, return_on_assets, gross_margin, operating_margin, net_margin,
            data_source, last_updated
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (ticker, report_date, period_type) DO UPDATE SET
            revenue = EXCLUDED.revenue,
            gross_profit = EXCLUDED.gross_profit,
            operating_income = EXCLUDED.operating_income,
            net_income = EXCLUDED.net_income,
            ebitda = EXCLUDED.ebitda,
            total_assets = EXCLUDED.total_assets,
            total_debt = EXCLUDED.total_debt,
            total_equity = EXCLUDED.total_equity,
            free_cash_flow = EXCLUDED.free_cash_flow,
            shares_outstanding = EXCLUDED.shares_outstanding,
            price_to_earnings = EXCLUDED.price_to_earnings,
            price_to_book = EXCLUDED.price_to_book,
            debt_to_equity_ratio = EXCLUDED.debt_to_equity_ratio,
            current_ratio = EXCLUDED.current_ratio,
            return_on_equity = EXCLUDED.return_on_equity,
            return_on_assets = EXCLUDED.return_on_assets,
            gross_margin = EXCLUDED.gross_margin,
            operating_margin = EXCLUDED.operating_margin,
            net_margin = EXCLUDED.net_margin,
            data_source = EXCLUDED.data_source,
            last_updated = EXCLUDED.last_updated
        )
    """
    
    # Test values
    values = (
        ticker,
        datetime.now().date(),  # report_date
        'TTM',  # period_type
        fiscal_year,
        fiscal_quarter,
        1000000000,  # revenue
        500000000,  # gross_profit
        200000000,  # operating_income
        150000000,  # net_income
        250000000,  # ebitda
        5000000000,  # total_assets
        1000000000,  # total_debt
        3000000000,  # total_equity
        100000000,  # free_cash_flow
        100000000,  # shares_outstanding
        15.0,  # price_to_earnings
        2.5,  # price_to_book
        0.33,  # debt_to_equity_ratio
        1.5,  # current_ratio
        0.05,  # return_on_equity
        0.03,  # return_on_assets
        0.50,  # gross_margin
        0.20,  # operating_margin
        0.15,  # net_margin
        'debug_test',  # data_source
        datetime.now()  # last_updated
    )
    
    print("SQL Query:")
    print(query)
    print()
    print("Values:")
    print(values)
    print()
    
    try:
        print("Executing query...")
        db.execute_query(query, values)
        print("✅ Query executed successfully!")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        
        # Try a simpler approach - just INSERT without ON CONFLICT
        print("\nTrying simple INSERT...")
        simple_query = """
            INSERT INTO company_fundamentals (
                ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                revenue, gross_profit, operating_income, net_income, ebitda,
                total_assets, total_debt, total_equity, free_cash_flow, shares_outstanding,
                price_to_earnings, price_to_book, debt_to_equity_ratio, current_ratio,
                return_on_equity, return_on_assets, gross_margin, operating_margin, net_margin,
                data_source, last_updated
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        try:
            db.execute_query(simple_query, values)
            print("✅ Simple INSERT worked!")
        except Exception as e2:
            print(f"❌ Simple INSERT also failed: {e2}")

if __name__ == "__main__":
    debug_sql_query() 