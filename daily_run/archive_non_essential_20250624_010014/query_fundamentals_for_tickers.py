#!/usr/bin/env python3
"""
Query and display current fundamental data for a list of tickers
"""

from database import DatabaseManager
import sys

def query_fundamentals_for_tickers(tickers):
    print(f"Querying fundamentals for: {tickers}")
    db = DatabaseManager()
    db.connect()
    
    # Use only the columns that actually exist in the company_fundamentals table
    query = """
    SELECT ticker, report_date, period_type, fiscal_year, fiscal_quarter,
           revenue, gross_profit, operating_income, net_income, ebitda, eps_diluted,
           data_source, last_updated
    FROM company_fundamentals 
    WHERE ticker = ANY(%s)
    ORDER BY ticker, report_date DESC
    """
    
    try:
        results = db.execute_query(query, (tickers,))
        if results:
            print(f"Found {len(results)} records:")
            print("-" * 80)
            for row in results:
                ticker, report_date, period_type, fiscal_year, fiscal_quarter, \
                revenue, gross_profit, operating_income, net_income, ebitda, eps_diluted, \
                data_source, last_updated = row
                
                print(f"  {ticker} ({period_type} - {report_date}):")
                if fiscal_year:
                    print(f"    Fiscal Year: {fiscal_year}")
                if revenue:
                    print(f"    Revenue: ${revenue:,.0f}")
                if gross_profit:
                    print(f"    Gross Profit: ${gross_profit:,.0f}")
                if operating_income:
                    print(f"    Operating Income: ${operating_income:,.0f}")
                if net_income:
                    print(f"    Net Income: ${net_income:,.0f}")
                if ebitda:
                    print(f"    EBITDA: ${ebitda:,.0f}")
                if eps_diluted:
                    print(f"    EPS: ${eps_diluted:.2f}")
                print(f"    Data Source: {data_source}")
                print(f"    Last Updated: {last_updated}")
                print()
        else:
            print("No records found.")
    except Exception as e:
        print(f"Error querying fundamentals: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    # Accept tickers as command line args or use a default list
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    query_fundamentals_for_tickers(tickers) 