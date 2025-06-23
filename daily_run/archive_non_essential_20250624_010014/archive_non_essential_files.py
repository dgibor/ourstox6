#!/usr/bin/env python3
"""
Archive Non-Essential Files Script

This script archives all testing, debugging, and development files
to declutter the production directory.
"""

import os
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_archive_directory():
    """Create archive directory with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = f"archive_non_essential_{timestamp}"
    os.makedirs(archive_dir, exist_ok=True)
    return archive_dir

def archive_files(archive_dir, file_patterns, description):
    """Archive files matching patterns"""
    archived_count = 0
    
    for pattern in file_patterns:
        for filename in os.listdir('.'):
            if filename.endswith(pattern):
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
    logger.info("Starting archive of non-essential files")
    
    # Create archive directory
    archive_dir = create_archive_directory()
    logger.info(f"Created archive directory: {archive_dir}")
    
    total_archived = 0
    
    # Archive test files
    test_patterns = ['test_*.py', 'quick_test.py', 'quick_stability_test.py']
    total_archived += archive_files(archive_dir, test_patterns, "test")
    
    # Archive debug files
    debug_patterns = ['debug_*.py']
    total_archived += archive_files(archive_dir, debug_patterns, "debug")
    
    # Archive check files
    check_patterns = ['check_*.py']
    total_archived += archive_files(archive_dir, check_patterns, "check")
    
    # Archive fix files
    fix_patterns = ['fix_*.py']
    total_archived += archive_files(archive_dir, fix_patterns, "fix")
    
    # Archive update files
    update_patterns = ['update_*.py']
    total_archived += archive_files(archive_dir, update_patterns, "update")
    
    # Archive query files
    query_patterns = ['query_*.py']
    total_archived += archive_files(archive_dir, query_patterns, "query")
    
    # Archive specific legacy files
    legacy_files = [
        'integrated_daily_runner_v2.py',
        'integrated_daily_runner_v3.py',
        'main_daily_runner.py',
        'price_service.py',
        'fundamental_service.py',
        'ratios_calculator.py',
        'daily_fundamentals_updater.py',
        'batch_processor.py'
    ]
    total_archived += archive_specific_files(archive_dir, legacy_files, "legacy")
    
    # Archive summary files
    summary_files = [
        'final_summary.py',
        'system_status_summary_fixed.py',
        'system_status_summary.py',
        'final_test_complete_system.py'
    ]
    total_archived += archive_specific_files(archive_dir, summary_files, "summary")
    
    # Archive documentation files
    doc_files = [
        'CLEANUP_PLAN.md',
        'DESIGN_DOCUMENT.md',
        'trading_indicators_spec.md',
        'Technical Indicators Calculator - LLM Implementation Instructions.pdf',
        'Stock Data Collection System - LLM Development Guide.pdf'
    ]
    total_archived += archive_specific_files(archive_dir, doc_files, "documentation")
    
    # Archive migration files
    migration_files = [
        'migrate_add_technicals_columns.py'
    ]
    total_archived += archive_specific_files(archive_dir, migration_files, "migration")
    
    # Create README for archive
    readme_content = f"""# Non-Essential Files Archive

This directory contains files that were archived to declutter the production directory.

## Archive Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Contents:
- Test files (test_*.py, quick_test.py, etc.)
- Debug files (debug_*.py)
- Check/validation files (check_*.py)
- Fix/update scripts (fix_*.py, update_*.py)
- Query scripts (query_*.py)
- Legacy files (superseded by newer implementations)
- Summary files (final_summary.py, etc.)
- Documentation files (CLEANUP_PLAN.md, etc.)
- Migration scripts

## Total Files Archived: {total_archived}

## Production Files Remaining:
- daily_trading_system.py (main production entry point)
- cron_setup.py (production cron setup)
- system_health_check.py (health monitoring)
- batch_price_processor.py (batch processing)
- earnings_based_fundamental_processor.py (fundamentals)
- All service files (yahoo_finance_service.py, etc.)
- All infrastructure files (database.py, error_handler.py, etc.)
- All technical indicators (indicators/ directory)
- All documentation (IMPLEMENTATION_STATUS.md, etc.)

## Note:
These files are kept for reference and can be restored if needed.
"""
    
    readme_path = os.path.join(archive_dir, "README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    logger.info(f"Archive completed! Total files archived: {total_archived}")
    logger.info(f"Archive location: {archive_dir}")
    logger.info("Production directory is now clean and ready for deployment.")

if __name__ == "__main__":
    main() 