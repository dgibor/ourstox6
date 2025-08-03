#!/usr/bin/env python3
"""
Check MSFT ratios
"""

import sys
sys.path.insert(0, 'daily_run')

from database import DatabaseManager

def check_msft_ratios():
    """Check MSFT ratios in financial_ratios table"""
    db = DatabaseManager()
    
    try:
        result = db.fetch_all_dict(
            "SELECT * FROM financial_ratios WHERE ticker = %s ORDER BY calculation_date DESC LIMIT 3",
            ('MSFT',)
        )
        
        print("MSFT ratios in financial_ratios:")
        for r in result:
            print(f"  {r['calculation_date']}: gross_margin={r['gross_margin']}, operating_margin={r['operating_margin']}, net_margin={r['net_margin']}, fcf_to_net_income={r['fcf_to_net_income']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_msft_ratios() 