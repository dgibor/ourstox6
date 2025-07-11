#!/usr/bin/env python3
"""
Generate correct INSERT statement for company_fundamentals table
"""

from database import DatabaseManager

def generate_correct_insert():
    """Generate the correct INSERT statement for company_fundamentals"""
    db = DatabaseManager()
    
    try:
        # Get all columns with their nullability
        result = db.execute_query("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'company_fundamentals' 
            ORDER BY ordinal_position
        """)
        
        print("Company_fundamentals table structure:")
        print("=" * 50)
        
        all_columns = []
        required_columns = []
        
        for row in result:
            column_name, data_type, is_nullable, column_default = row
            all_columns.append(column_name)
            
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default = f" DEFAULT {column_default}" if column_default else ""
            
            print(f"  {column_name}: {data_type} ({nullable}){default}")
            
            # Check if column is required (NOT NULL and no default)
            if is_nullable == "NO" and not column_default:
                required_columns.append(column_name)
        
        print(f"\nTotal columns: {len(all_columns)}")
        print(f"Required columns (NOT NULL, no default): {len(required_columns)}")
        
        if required_columns:
            print("\nRequired columns:")
            for col in required_columns:
                print(f"  - {col}")
        
        # Generate the correct INSERT statement
        print("\n" + "=" * 50)
        print("CORRECT INSERT STATEMENT:")
        print("=" * 50)
        
        # For now, let's use a simple approach - just insert the columns we have data for
        # and let the database handle defaults for others
        insert_columns = [
            'ticker', 'report_date', 'period_type', 'fiscal_year', 'fiscal_quarter',
            'revenue', 'gross_profit', 'operating_income', 'net_income', 'ebitda',
            'total_assets', 'total_debt', 'total_equity', 'free_cash_flow', 'shares_outstanding',
            'price_to_earnings', 'price_to_book', 'debt_to_equity_ratio', 'current_ratio',
            'return_on_equity', 'return_on_assets', 'gross_margin', 'operating_margin', 'net_margin',
            'data_source', 'last_updated'
        ]
        
        # Check if all required columns are in our insert list
        missing_required = [col for col in required_columns if col not in insert_columns]
        
        if missing_required:
            print(f"WARNING: Missing required columns: {missing_required}")
            print("Adding missing required columns to insert...")
            insert_columns.extend(missing_required)
        
        # Generate the INSERT statement
        columns_str = ', '.join(insert_columns)
        placeholders = ', '.join(['%s'] * len(insert_columns))
        
        insert_sql = f"""INSERT INTO company_fundamentals (
    {columns_str}
) VALUES ({placeholders}) ON CONFLICT (ticker, report_date, period_type) DO UPDATE SET
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
    last_updated = EXCLUDED.last_updated"""
        
        print(insert_sql)
        
        print(f"\nNumber of placeholders: {len(insert_columns)}")
        print(f"Columns to insert: {insert_columns}")
        
        return insert_sql, insert_columns
        
    except Exception as e:
        print(f"Error generating INSERT statement: {e}")
        return None, None

if __name__ == "__main__":
    generate_correct_insert() 