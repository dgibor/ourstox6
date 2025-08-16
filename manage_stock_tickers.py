#!/usr/bin/env python3
"""
Stock Ticker Management Script

This script manages stock tickers in the database by:
1. Deleting specified obsolete tickers
2. Changing ticker symbols (e.g., ABCM to TXNM)
3. Maintaining database integrity with transactions
4. Logging all operations for audit purposes
"""

import logging
import sys
from typing import List, Tuple
from datetime import datetime

# Add the daily_run directory to the path to import DatabaseManager
sys.path.append('daily_run')

try:
    from database import DatabaseManager
    from config import Config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/ticker_management_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StockTickerManager:
    """Manages stock ticker operations in the database"""
    
    def __init__(self):
        """Initialize the ticker manager"""
        self.db = DatabaseManager()
        self.tickers_to_delete = [
            'PBCT', 'PLAN', 'QTS', 'RXN', 'SAI', 'SC', 'SHI', 'SHLX', 
            'SNP', 'SYNC', 'AFTY', 'TIF', 'PTR'
        ]
        self.ticker_changes = [('ABCM', 'TXNM')]
        
    def verify_tickers_exist(self, tickers: List[str]) -> Tuple[List[str], List[str]]:
        """
        Verify which tickers exist in the database
        
        Args:
            tickers: List of ticker symbols to check
            
        Returns:
            Tuple of (existing_tickers, missing_tickers)
        """
        logger.info(f"Verifying existence of {len(tickers)} tickers...")
        
        try:
            # Get all existing tickers
            existing_tickers = self.db.get_tickers()
            logger.info(f"Found {len(existing_tickers)} total tickers in database")
            
            # Check which ones exist
            found_tickers = [t for t in tickers if t in existing_tickers]
            missing_tickers = [t for t in tickers if t not in existing_tickers]
            
            if found_tickers:
                logger.info(f"Found {len(found_tickers)} tickers to delete: {found_tickers}")
            if missing_tickers:
                logger.warning(f"Missing {len(missing_tickers)} tickers: {missing_tickers}")
                
            return found_tickers, missing_tickers
            
        except Exception as e:
            logger.error(f"Error verifying tickers: {e}")
            raise
    
    def check_foreign_key_references(self, ticker: str) -> List[str]:
        """
        Check if a ticker is referenced in other tables
        
        Args:
            ticker: Ticker symbol to check
            
        Returns:
            List of tables that reference this ticker
        """
        try:
            # Common tables that might reference tickers
            reference_tables = [
                'daily_charts', 'technical_indicators', 'company_fundamentals',
                'financial_ratios', 'investor_scores'
            ]
            
            referenced_tables = []
            for table in reference_tables:
                try:
                    # Check if table exists and has ticker column
                    check_query = f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'ticker'
                    )
                    """
                    table_exists = self.db.fetch_one(check_query, (table,))
                    
                    if table_exists and table_exists[0]:
                        # Check for references
                        ref_query = f"SELECT COUNT(*) FROM {table} WHERE ticker = %s"
                        ref_count = self.db.fetch_one(ref_query, (ticker,))
                        
                        if ref_count and ref_count[0] > 0:
                            referenced_tables.append(f"{table} ({ref_count[0]} rows)")
                            
                except Exception as e:
                    logger.warning(f"Could not check table {table}: {e}")
                    continue
            
            return referenced_tables
            
        except Exception as e:
            logger.error(f"Error checking foreign key references for {ticker}: {e}")
            return []

    def delete_tickers(self, tickers: List[str]) -> int:
        """
        Delete specified tickers from the stocks table
        
        Args:
            tickers: List of ticker symbols to delete
            
        Returns:
            Number of tickers successfully deleted
        """
        if not tickers:
            logger.info("No tickers to delete")
            return 0
            
        logger.info(f"Deleting {len(tickers)} tickers: {tickers}")
        
        try:
            # Start transaction
            self.db.begin_transaction()
            
            deleted_count = 0
            failed_tickers = []
            
            for ticker in tickers:
                try:
                    # Check for foreign key references
                    references = self.check_foreign_key_references(ticker)
                    if references:
                        logger.warning(f"Ticker {ticker} has references in: {references}")
                        logger.warning(f"Skipping deletion of {ticker} due to foreign key references")
                        failed_tickers.append(ticker)
                        continue
                    
                    # Delete from stocks table
                    delete_query = "DELETE FROM stocks WHERE ticker = %s"
                    result = self.db.execute_update(delete_query, (ticker,))
                    
                    if result > 0:
                        deleted_count += 1
                        logger.info(f"Successfully deleted ticker: {ticker}")
                    else:
                        logger.warning(f"No rows deleted for ticker: {ticker}")
                        
                except Exception as e:
                    logger.error(f"Error deleting ticker {ticker}: {e}")
                    failed_tickers.append(ticker)
                    # Continue with other tickers
            
            if failed_tickers:
                logger.warning(f"Failed to delete {len(failed_tickers)} tickers: {failed_tickers}")
                logger.warning("Rolling back transaction due to failures")
                self.db.rollback()
                return 0
            
            # Commit transaction only if all deletions succeeded
            self.db.commit()
            logger.info(f"Successfully deleted {deleted_count} out of {len(tickers)} tickers")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during ticker deletion: {e}")
            self.db.rollback()
            raise
    
    def change_ticker_symbol(self, old_ticker: str, new_ticker: str) -> bool:
        """
        Change a ticker symbol from old to new
        
        Args:
            old_ticker: Current ticker symbol
            new_ticker: New ticker symbol
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Changing ticker symbol from {old_ticker} to {new_ticker}")
        
        try:
            # Start transaction
            self.db.begin_transaction()
            
            # Check if old ticker exists
            check_query = "SELECT ticker FROM stocks WHERE ticker = %s"
            old_exists = self.db.fetch_one(check_query, (old_ticker,))
            
            if not old_exists:
                logger.error(f"Old ticker {old_ticker} not found in database")
                self.db.rollback()
                return False
            
            # Check if new ticker already exists
            new_exists = self.db.fetch_one(check_query, (new_ticker,))
            if new_exists:
                logger.error(f"New ticker {new_ticker} already exists in database")
                self.db.rollback()
                return False
            
            # Check for foreign key references that need updating
            reference_tables = [
                'daily_charts', 'technical_indicators', 'company_fundamentals',
                'financial_ratios', 'investor_scores'
            ]
            
            tables_to_update = []
            for table in reference_tables:
                try:
                    # Check if table exists and has ticker column
                    check_query = f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = 'ticker'
                    )
                    """
                    table_exists = self.db.fetch_one(check_query, (table,))
                    
                    if table_exists and table_exists[0]:
                        # Check for references
                        ref_query = f"SELECT COUNT(*) FROM {table} WHERE ticker = %s"
                        ref_count = self.db.fetch_one(ref_query, (old_ticker,))
                        
                        if ref_count and ref_count[0] > 0:
                            tables_to_update.append((table, ref_count[0]))
                            
                except Exception as e:
                    logger.warning(f"Could not check table {table}: {e}")
                    continue
            
            # Temporarily disable foreign key constraints
            logger.info("Temporarily disabling foreign key constraints...")
            self.db.execute_update("SET session_replication_role = replica")
            
            try:
                # Update the main stocks table first
                update_query = "UPDATE stocks SET ticker = %s WHERE ticker = %s"
                result = self.db.execute_update(update_query, (new_ticker, old_ticker))
                
                if result == 0:
                    logger.error(f"No rows updated for ticker change {old_ticker} -> {new_ticker}")
                    raise Exception("No rows updated in stocks table")
                
                # Now update foreign key references
                for table, row_count in tables_to_update:
                    try:
                        update_ref_query = f"UPDATE {table} SET ticker = %s WHERE ticker = %s"
                        ref_result = self.db.execute_update(update_ref_query, (new_ticker, old_ticker))
                        logger.info(f"Updated {ref_result} rows in {table} table")
                    except Exception as e:
                        logger.error(f"Error updating {table} table: {e}")
                        raise
                
                logger.info(f"Successfully changed ticker from {old_ticker} to {new_ticker}")
                if tables_to_update:
                    logger.info(f"Updated {len(tables_to_update)} reference tables")
                
            finally:
                # Re-enable foreign key constraints
                logger.info("Re-enabling foreign key constraints...")
                self.db.execute_update("SET session_replication_role = DEFAULT")
            
            self.db.commit()
            return True
                
        except Exception as e:
            logger.error(f"Error changing ticker symbol: {e}")
            self.db.rollback()
            raise
    
    def verify_changes(self) -> bool:
        """
        Verify that all changes were applied correctly
        
        Returns:
            True if verification passes, False otherwise
        """
        logger.info("Verifying database changes...")
        
        try:
            # Check that deleted tickers are gone
            existing_tickers = self.db.get_tickers()
            
            for ticker in self.tickers_to_delete:
                if ticker in existing_tickers:
                    logger.error(f"Ticker {ticker} still exists after deletion")
                    return False
            
            # Check that ABCM was changed to TXNM
            if 'ABCM' in existing_tickers:
                logger.error("Ticker ABCM still exists after change")
                return False
                
            if 'TXNM' not in existing_tickers:
                logger.error("Ticker TXNM not found after change")
                return False
            
            logger.info("All changes verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return False
    
    def run_management(self) -> bool:
        """
        Run the complete ticker management process
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting stock ticker management process")
        
        try:
            # Step 1: Verify tickers exist
            existing_to_delete, missing_to_delete = self.verify_tickers_exist(self.tickers_to_delete)
            
            # Step 2: Delete tickers
            deleted_count = self.delete_tickers(existing_to_delete)
            
            # Step 3: Change ticker symbols
            for old_ticker, new_ticker in self.ticker_changes:
                success = self.change_ticker_symbol(old_ticker, new_ticker)
                if not success:
                    logger.error(f"Failed to change ticker {old_ticker} to {new_ticker}")
                    return False
            
            # Step 4: Verify changes
            if not self.verify_changes():
                logger.error("Verification failed")
                return False
            
            logger.info("Stock ticker management completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Stock ticker management failed: {e}")
            return False
        finally:
            self.db.disconnect()


def main():
    """Main execution function"""
    print("🔄 Stock Ticker Management Script")
    print("=" * 50)
    
    try:
        # Create manager and run process
        manager = StockTickerManager()
        success = manager.run_management()
        
        if success:
            print("\n✅ Stock ticker management completed successfully!")
            print(f"   - Deleted {len(manager.tickers_to_delete)} tickers")
            print(f"   - Changed {len(manager.ticker_changes)} ticker symbols")
        else:
            print("\n❌ Stock ticker management failed!")
            print("   Check the logs for detailed error information")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
