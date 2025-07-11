#!/usr/bin/env python3
"""
Add ratio columns to company_fundamentals table
"""

import sys
sys.path.append('..')

from database import DatabaseManager

def add_ratio_columns():
    db = DatabaseManager()
    
    # Columns to add
    columns_to_add = [
        ('price_to_earnings', 'NUMERIC(10,4)'),
        ('price_to_book', 'NUMERIC(10,4)'),
        ('price_to_sales', 'NUMERIC(10,4)'),
        ('ev_to_ebitda', 'NUMERIC(10,4)'),
        ('return_on_equity', 'NUMERIC(10,4)'),
        ('return_on_assets', 'NUMERIC(10,4)'),
        ('debt_to_equity_ratio', 'NUMERIC(10,4)'),
        ('current_ratio', 'NUMERIC(10,4)'),
        ('gross_margin', 'NUMERIC(10,4)'),
        ('operating_margin', 'NUMERIC(10,4)'),
        ('net_margin', 'NUMERIC(10,4)'),
        ('peg_ratio', 'NUMERIC(10,4)'),
        ('return_on_invested_capital', 'NUMERIC(10,4)'),
        ('quick_ratio', 'NUMERIC(10,4)'),
        ('interest_coverage', 'NUMERIC(10,4)'),
        ('altman_z_score', 'NUMERIC(10,4)'),
        ('asset_turnover', 'NUMERIC(10,4)'),
        ('inventory_turnover', 'NUMERIC(10,4)'),
        ('receivables_turnover', 'NUMERIC(10,4)'),
        ('revenue_growth_yoy', 'NUMERIC(10,4)'),
        ('earnings_growth_yoy', 'NUMERIC(10,4)'),
        ('fcf_growth_yoy', 'NUMERIC(10,4)'),
        ('fcf_to_net_income', 'NUMERIC(10,4)'),
        ('cash_conversion_cycle', 'NUMERIC(10,4)'),
        ('market_cap', 'NUMERIC(20,2)'),
        ('enterprise_value', 'NUMERIC(20,2)'),
        ('graham_number', 'NUMERIC(10,4)')
    ]
    
    print("Adding ratio columns to company_fundamentals table...")
    
    for column_name, data_type in columns_to_add:
        try:
            # Check if column already exists
            result = db.execute_query("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'company_fundamentals' AND column_name = %s
            """, (column_name,))
            
            if not result:
                # Add the column using direct cursor execution
                with db.get_cursor() as cursor:
                    cursor.execute(f"""
                        ALTER TABLE company_fundamentals 
                        ADD COLUMN {column_name} {data_type}
                    """)
                print(f"✅ Added column: {column_name}")
            else:
                print(f"⏭️  Column already exists: {column_name}")
                
        except Exception as e:
            print(f"❌ Error adding column {column_name}: {e}")
    
    print("\n✅ Finished adding ratio columns to company_fundamentals table")

if __name__ == "__main__":
    add_ratio_columns() 