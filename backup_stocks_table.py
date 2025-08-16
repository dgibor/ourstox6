#!/usr/bin/env python3
"""
Backup Script for Stocks Table

This script creates a backup of the stocks table before making any changes
to ensure data safety and recovery capability.
"""

import sys
import logging
from datetime import datetime
import os

# Add the daily_run directory to the path
sys.path.append('daily_run')

try:
    from database import DatabaseManager
    from config import Config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_backup():
    """Create a backup of the stocks table"""
    print("💾 Creating backup of stocks table...")
    
    try:
        db = DatabaseManager()
        db.connect()
        
        # Create backup directory if it doesn't exist
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            print(f"Created backup directory: {backup_dir}")
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/stocks_backup_{timestamp}.sql"
        
        # Get all data from stocks table
        query = """
        SELECT ticker, company_name, exchange, sector, industry, country, 
               logo_url, last_updated, market_cap, revenue_ttm, net_income_ttm,
               total_assets, total_debt, shareholders_equity, current_assets,
               current_liabilities, operating_income, cash_and_equivalents,
               free_cash_flow, shares_outstanding, diluted_eps_ttm,
               book_value_per_share, ebitda_ttm, enterprise_value,
               peer_1_ticker, peer_2_ticker, peer_3_ticker, sector_etf_ticker,
               peers_last_updated, industry_classification, gics_sector,
               gics_industry, market_cap_category, fundamentals_last_update,
               next_earnings_date, data_priority
        FROM stocks 
        ORDER BY ticker
        """
        
        results = db.execute_query(query)
        
        if not results:
            print("❌ No data found in stocks table")
            return False
        
        # Write backup to SQL file
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("-- Stocks Table Backup\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n")
            f.write(f"-- Total Records: {len(results)}\n\n")
            
            f.write("-- Backup data for recovery\n")
            f.write("INSERT INTO stocks (\n")
            f.write("    ticker, company_name, exchange, sector, industry, country,\n")
            f.write("    logo_url, last_updated, market_cap, revenue_ttm, net_income_ttm,\n")
            f.write("    total_assets, total_debt, shareholders_equity, current_assets,\n")
            f.write("    current_liabilities, operating_income, cash_and_equivalents,\n")
            f.write("    free_cash_flow, shares_outstanding, diluted_eps_ttm,\n")
            f.write("    book_value_per_share, ebitda_ttm, enterprise_value,\n")
            f.write("    peer_1_ticker, peer_2_ticker, peer_3_ticker, sector_etf_ticker,\n")
            f.write("    peers_last_updated, industry_classification, gics_sector,\n")
            f.write("    gics_industry, market_cap_category, fundamentals_last_update,\n")
            f.write("    next_earnings_date, data_priority\n")
            f.write(") VALUES\n")
            
            for i, row in enumerate(results):
                # Format the row data safely
                formatted_row = []
                for value in row:
                    if value is None:
                        formatted_row.append('NULL')
                    elif isinstance(value, str):
                        # Escape single quotes in strings
                        escaped_value = value.replace("'", "''")
                        formatted_row.append(f"'{escaped_value}'")
                    else:
                        formatted_row.append(str(value))
                
                f.write(f"    ({', '.join(formatted_row)})")
                if i < len(results) - 1:
                    f.write(",")
                f.write("\n")
            
            f.write(";\n\n")
            f.write("-- End of backup\n")
        
        print(f"✅ Backup created successfully: {backup_file}")
        print(f"   - Total records: {len(results)}")
        print(f"   - File size: {os.path.getsize(backup_file)} bytes")
        
        # Also create a CSV backup for easy viewing
        csv_backup_file = f"{backup_dir}/stocks_backup_{timestamp}.csv"
        import csv
        
        with open(csv_backup_file, 'w', newline='', encoding='utf-8') as csvfile:
            # Get column names
            column_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            ORDER BY ordinal_position
            """
            columns = db.execute_query(column_query)
            column_names = [col[0] for col in columns]
            
            writer = csv.writer(csvfile)
            writer.writerow(column_names)
            
            for row in results:
                writer.writerow(row)
        
        print(f"✅ CSV backup created: {csv_backup_file}")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        logger.error(f"Backup failed: {e}")
        return False

def verify_backup(backup_file):
    """Verify the backup file exists and has content"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    file_size = os.path.getsize(backup_file)
    if file_size == 0:
        print(f"❌ Backup file is empty: {backup_file}")
        return False
    
    print(f"✅ Backup verification passed: {backup_file} ({file_size} bytes)")
    return True

def main():
    """Main backup function"""
    print("💾 Stocks Table Backup Script")
    print("=" * 40)
    
    # Create backup
    if create_backup():
        print("\n🎉 Backup completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Verify the backup files in the 'backups' directory")
        print("   2. Run: python manage_stock_tickers.py")
        print("   3. If anything goes wrong, you can restore from the backup")
    else:
        print("\n❌ Backup failed! Do not proceed with ticker management.")
        sys.exit(1)

if __name__ == "__main__":
    main()
