#!/usr/bin/env python3
"""
Archive Remaining Non-Essential Files Script

This script archives the remaining testing, debugging, and development files
that weren't caught by the first archive script.
"""

import os
import shutil
import logging
import glob
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def archive_files_by_pattern(archive_dir, pattern, description):
    """Archive files matching a glob pattern"""
    archived_count = 0
    
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        try:
            source = filename
            destination = os.path.join(archive_dir, filename)
            shutil.move(source, destination)
            logger.info(f"Archived: {filename}")
            archived_count += 1
        except Exception as e:
            logger.error(f"Failed to archive {filename}: {e}")
    
    logger.info(f"Archived {archived_count} {description} files")
    return archived_count

def archive_specific_files(archive_dir, file_list, description):
    """Archive specific files by name"""
    archived_count = 0
    
    for filename in file_list:
        if os.path.exists(filename):
            try:
                source = filename
                destination = os.path.join(archive_dir, filename)
                shutil.move(source, destination)
                logger.info(f"Archived: {filename}")
                archived_count += 1
            except Exception as e:
                logger.error(f"Failed to archive {filename}: {e}")
    
    logger.info(f"Archived {archived_count} {description} files")
    return archived_count

def main():
    """Main archiving function"""
    logger.info("Starting archive of remaining non-essential files")
    
    # Use the existing archive directory
    archive_dirs = [d for d in os.listdir('.') if d.startswith('archive_non_essential_')]
    if archive_dirs:
        archive_dir = archive_dirs[0]  # Use the first archive directory
        logger.info(f"Using existing archive directory: {archive_dir}")
    else:
        # Create new archive directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = f"archive_non_essential_{timestamp}"
        os.makedirs(archive_dir, exist_ok=True)
        logger.info(f"Created new archive directory: {archive_dir}")
    
    total_archived = 0
    
    # Archive test files (using glob pattern)
    total_archived += archive_files_by_pattern(archive_dir, "test_*.py", "test")
    
    # Archive debug files (using glob pattern)
    total_archived += archive_files_by_pattern(archive_dir, "debug_*.py", "debug")
    
    # Archive check files (using glob pattern)
    total_archived += archive_files_by_pattern(archive_dir, "check_*.py", "check")
    
    # Archive fix files (using glob pattern)
    total_archived += archive_files_by_pattern(archive_dir, "fix_*.py", "fix")
    
    # Archive update files (using glob pattern)
    total_archived += archive_files_by_pattern(archive_dir, "update_*.py", "update")
    
    # Archive query files (using glob pattern)
    total_archived += archive_files_by_pattern(archive_dir, "query_*.py", "query")
    
    # Archive specific remaining files
    remaining_files = [
        'test_stability_improvements.py',
        'test_fundamentals_updater.py',
        'test_alpha_vantage_delayed.py',
        'test_fmp.py',
        'test_alpha_vantage.py',
        'test_fallback.py',
        'test_services.py',
        'test_integration.py',
        'debug_monitoring.py',
        'debug_shares_outstanding.py',
        'debug_raw_data.py',
        'debug_data_extraction.py',
        'debug_storage_issue.py',
        'debug_fundamental_storage.py',
        'check_fundamentals_structure.py',
        'check_table_structure.py',
        'check_price_columns.py',
        'check_missing_data.py',
        'check_all_fundamental_columns.py',
        'check_stocks_schema.py',
        'check_fmp_storage.py',
        'check_actual_fundamental_data.py',
        'check_stocks_fundamentals.py',
        'check_fundamentals_schema.py',
        'check_database_updates.py',
        'fix_with_calculations_fixed.py',
        'fix_with_calculations.py',
        'fix_missing_data_simple.py',
        'fix_missing_data.py',
        'fix_schema.py',
        'update_all_fundamentals_complete.py',
        'update_fundamentals_fixed.py',
        'update_fundamentals_for_tickers.py',
        'query_fundamentals_for_tickers.py',
        'cleanup_old_files.py'
    ]
    
    total_archived += archive_specific_files(archive_dir, remaining_files, "remaining")
    
    # Archive the archive script itself
    try:
        shutil.move('archive_non_essential_files.py', os.path.join(archive_dir, 'archive_non_essential_files.py'))
        shutil.move('archive_remaining_files.py', os.path.join(archive_dir, 'archive_remaining_files.py'))
        logger.info("Archived archive scripts")
    except Exception as e:
        logger.error(f"Failed to archive archive scripts: {e}")
    
    logger.info(f"Archive completed! Total files archived in this run: {total_archived}")
    logger.info(f"Archive location: {archive_dir}")
    logger.info("Production directory is now clean and ready for deployment.")

if __name__ == "__main__":
    main() 