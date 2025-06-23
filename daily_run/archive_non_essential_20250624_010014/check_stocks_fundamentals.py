#!/usr/bin/env python3
"""
Check if fundamental data was stored in the stocks table for the updated tickers
"""

from database import DatabaseManager

def check_stocks_fundamentals(tickers):
    print(f"Checking stocks table for fundamental data: {tickers}")
    print("=" * 60)
    
    db = DatabaseManager()
    db.connect()
    
    # Check what columns exist in stocks table
    print("1. Checking stocks table schema:")
    print("-" * 40)
    
    schema_query = """
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_name = 'stocks'
    ORDER BY ordinal_position
    """
    
    try:
        schema_results = db.execute_query(schema_query)
        fundamental_columns = []
        for row in schema_results:
            column_name, data_type = row
            if any(keyword in column_name.lower() for keyword in ['revenue', 'income', 'debt', 'equity', 'market', 'shares', 'eps', 'book']):
                fundamental_columns.append(column_name)
                print(f"  {column_name}: {data_type}")
    except Exception as e:
        print(f"Error checking schema: {e}")
    
    # Query fundamental data from stocks table
    print(f"\n2. Fundamental data in stocks table:")
    print("-" * 40)
    
    if fundamental_columns:
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
                print(f"Found {len(results)} records:")
                for row in results:
                    ticker = row[0]
                    print(f"\n  {ticker}:")
                    for i, column in enumerate(fundamental_columns, 1):
                        value = row[i]
                        if value is not None:
                            if 'revenue' in column.lower() or 'income' in column.lower() or 'debt' in column.lower() or 'equity' in column.lower() or 'market' in column.lower():
                                print(f"    {column}: ${value:,.0f}")
                            elif 'ratio' in column.lower():
                                print(f"    {column}: {value:.2f}")
                            else:
                                print(f"    {column}: {value}")
            else:
                print("No records found in stocks table.")
        except Exception as e:
            print(f"Error querying stocks table: {e}")
    else:
        print("No fundamental columns found in stocks table.")
    
    # Also check company_fundamentals table again with a simpler query
    print(f"\n3. Checking company_fundamentals table:")
    print("-" * 40)
    
    simple_query = """
    SELECT ticker, COUNT(*) as record_count
    FROM company_fundamentals 
    WHERE ticker = ANY(%s)
    GROUP BY ticker
    ORDER BY ticker
    """
    
    try:
        results = db.execute_query(simple_query, (tickers,))
        if results:
            print("Records found in company_fundamentals:")
            for row in results:
                ticker, count = row
                print(f"  {ticker}: {count} records")
        else:
            print("No records found in company_fundamentals table.")
    except Exception as e:
        print(f"Error querying company_fundamentals: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    check_stocks_fundamentals(tickers) 