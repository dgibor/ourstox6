#!/usr/bin/env python3
"""
Batch CSV Import Workflow Script
================================

This script runs the complete workflow for importing and managing stock data from batch CSV files.
It executes all tasks in sequence with proper error handling and reporting.

Tasks:
1. Update stocks table schema to accommodate batch CSV columns
2. Upload all four batch CSV files to stocks table
3. Remove duplicate records from stocks table
4. Verify stocks table has all information from batch files
5. Find tickers in stocks table not covered by batch files
6. Generate summary report

Usage:
    python run_batch_import_workflow.py
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Import our custom modules
from update_stocks_schema import update_stocks_schema
from upload_batch_csvs import upload_batch_csvs
from remove_duplicates import remove_duplicates
from check_stocks_table import check_stocks_table
from find_missing_tickers import find_missing_tickers

load_dotenv()

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step_num, step_name):
    """Print a formatted step header"""
    print(f"\n📋 STEP {step_num}: {step_name}")
    print("-" * 40)

def run_workflow():
    """Run the complete batch import workflow"""
    
    start_time = time.time()
    workflow_start = datetime.now()
    
    print_header("BATCH CSV IMPORT WORKFLOW")
    print(f"Started at: {workflow_start.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track results
    results = {
        'schema_updated': False,
        'files_uploaded': False,
        'duplicates_removed': False,
        'verification_completed': False,
        'missing_tickers_found': False,
        'errors': []
    }
    
    try:
        # Step 1: Update stocks table schema
        print_step(1, "UPDATE STOCKS TABLE SCHEMA")
        try:
            update_stocks_schema()
            results['schema_updated'] = True
            print("✅ Schema update completed successfully")
        except Exception as e:
            error_msg = f"Schema update failed: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            raise
        
        # Step 2: Upload batch CSV files
        print_step(2, "UPLOAD BATCH CSV FILES")
        try:
            upload_batch_csvs()
            results['files_uploaded'] = True
            print("✅ Batch file upload completed successfully")
        except Exception as e:
            error_msg = f"Batch file upload failed: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            raise
        
        # Step 3: Remove duplicates
        print_step(3, "REMOVE DUPLICATE RECORDS")
        try:
            remove_duplicates()
            results['duplicates_removed'] = True
            print("✅ Duplicate removal completed successfully")
        except Exception as e:
            error_msg = f"Duplicate removal failed: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            # Don't raise here - duplicates might not exist
        
        # Step 4: Verify stocks table
        print_step(4, "VERIFY STOCKS TABLE DATA")
        try:
            check_stocks_table()
            results['verification_completed'] = True
            print("✅ Data verification completed successfully")
        except Exception as e:
            error_msg = f"Data verification failed: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            # Don't raise here - verification can fail without stopping workflow
        
        # Step 5: Find missing tickers
        print_step(5, "FIND MISSING TICKERS")
        try:
            missing_df = find_missing_tickers()
            results['missing_tickers_found'] = True
            if missing_df is not None:
                print(f"✅ Missing tickers analysis completed - found {len(missing_df)} missing tickers")
            else:
                print("✅ No missing tickers found - all stocks are covered by batch files")
        except Exception as e:
            error_msg = f"Missing tickers analysis failed: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            # Don't raise here - analysis can fail without stopping workflow
        
        # Generate summary report
        print_header("WORKFLOW SUMMARY REPORT")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Workflow Duration: {duration:.2f} seconds")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📊 Task Results:")
        print(f"   ✅ Schema Update: {'SUCCESS' if results['schema_updated'] else 'FAILED'}")
        print(f"   ✅ File Upload: {'SUCCESS' if results['files_uploaded'] else 'FAILED'}")
        print(f"   ✅ Duplicate Removal: {'SUCCESS' if results['duplicates_removed'] else 'FAILED'}")
        print(f"   ✅ Data Verification: {'SUCCESS' if results['verification_completed'] else 'FAILED'}")
        print(f"   ✅ Missing Tickers Analysis: {'SUCCESS' if results['missing_tickers_found'] else 'FAILED'}")
        
        if results['errors']:
            print(f"\n⚠️  Errors encountered:")
            for i, error in enumerate(results['errors'], 1):
                print(f"   {i}. {error}")
        
        # Determine overall success
        critical_tasks = ['schema_updated', 'files_uploaded']
        critical_success = all(results[task] for task in critical_tasks)
        
        if critical_success:
            print(f"\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"   All critical tasks completed. Check the generated files for detailed results.")
        else:
            print(f"\n❌ WORKFLOW FAILED!")
            print(f"   Critical tasks failed. Please review the errors above.")
            sys.exit(1)
        
        # List generated files
        print(f"\n📁 Generated Files:")
        files_to_check = [
            'missing_tickers_from_batch_files.csv'
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   ✅ {file_path} ({file_size:,} bytes)")
            else:
                print(f"   ❌ {file_path} (not found)")
        
        print(f"\n📝 Next Steps:")
        print(f"   1. Review the generated CSV files")
        print(f"   2. Check the console output for any warnings")
        print(f"   3. Verify data quality in the database")
        print(f"   4. Run additional analysis as needed")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Workflow failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_workflow() 