#!/usr/bin/env python3
"""
Archive non-essential scripts from daily_run folder
"""

import os
import shutil
from pathlib import Path

def archive_non_essential_scripts():
    """Move non-essential scripts to archive folder"""
    
    # Essential scripts to keep in daily_run
    essential_scripts = {
        # Core services
        'fmp_service.py',
        'alpha_vantage_service.py', 
        'database.py',
        'config.py',
        'common_imports.py',
        'error_handler.py',
        'exceptions.py',
        
        # Daily update logic
        'earnings_based_fundamental_processor.py',
        'earnings_calendar_service.py',
        'daily_trading_system.py',
        
        # Technical indicators (entire folder)
        'indicators/',
        
        # Logs folder
        'logs/',
        'daily_run/',
        
        # Archive folders
        'archive_temp_files/',
        'archive_non_essential_20250624_010014/',
        'archive_non_essential_20240624/',
        
        # Cache
        '__pycache__/',
        
        # Documentation
        'README.md',
        'SYSTEM_DOCUMENTATION.md',
        'PRODUCTION_FILES_LIST.md',
        'IMPLEMENTATION_STATUS.md',
        'BATCH_PROCESSING_LOGIC.md',
        'DAILY_RUN_FOLDER_SUMMARY.md',
        'ARCHIVE_SUMMARY.md'
    }
    
    # Essential file patterns (keep files matching these patterns)
    essential_patterns = [
        'earnings_',
        'daily_',
        'update_',
        'service_',
        'base_',
        'enhanced_',
        'monitoring',
        'system_health'
    ]
    
    daily_run_path = Path('daily_run')
    archive_path = Path('archive_non_essential_20240624')
    
    if not daily_run_path.exists():
        print("❌ daily_run folder not found")
        return
    
    if not archive_path.exists():
        archive_path.mkdir()
        print(f"📁 Created archive folder: {archive_path}")
    
    moved_count = 0
    kept_count = 0
    
    print("🔄 Starting archive process...")
    print(f"📁 Moving non-essential files to: {archive_path}")
    print()
    
    # Process all files in daily_run
    for item in daily_run_path.iterdir():
        item_name = item.name
        
        # Skip if it's the archive folder itself
        if item_name.startswith('archive_'):
            continue
            
        # Check if it's essential
        is_essential = False
        
        # Check exact matches
        if item_name in essential_scripts:
            is_essential = True
        # Check if it's a folder that should be kept
        elif item.is_dir() and item_name in essential_scripts:
            is_essential = True
        # Check patterns
        else:
            for pattern in essential_patterns:
                if pattern in item_name.lower():
                    is_essential = True
                    break
        
        if is_essential:
            print(f"✅ KEEP: {item_name}")
            kept_count += 1
        else:
            try:
                # Move to archive
                destination = archive_path / item_name
                if item.is_file():
                    shutil.move(str(item), str(destination))
                elif item.is_dir():
                    shutil.move(str(item), str(destination))
                print(f"📦 ARCHIVE: {item_name}")
                moved_count += 1
            except Exception as e:
                print(f"❌ ERROR moving {item_name}: {e}")
    
    print()
    print("📋 Archive Summary:")
    print(f"   - Files kept: {kept_count}")
    print(f"   - Files archived: {moved_count}")
    print(f"   - Archive location: {archive_path}")
    
    # Show what's left in daily_run
    print()
    print("📁 Remaining files in daily_run:")
    remaining_files = list(daily_run_path.iterdir())
    if remaining_files:
        for item in sorted(remaining_files):
            if item.is_file():
                print(f"   📄 {item.name}")
            elif item.is_dir():
                print(f"   📁 {item.name}/")
    else:
        print("   (empty)")

if __name__ == "__main__":
    archive_non_essential_scripts() 