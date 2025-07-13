#!/usr/bin/env python3
"""
Railway Deployment Verification Script

This script verifies that all required files and dependencies are available
for the Railway deployment.
"""

import os
import sys
import importlib

def check_file_exists(filepath, description):
    """Check if a file exists and log the result"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_module_import(module_name, description):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} - {e}")
        return False

def main():
    """Verify Railway deployment setup"""
    print("🔍 RAILWAY DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    # Check current directory
    cwd = os.getcwd()
    print(f"📁 Current working directory: {cwd}")
    
    # Check required files
    print("\n📋 Checking required files:")
    files_to_check = [
        ("railway_cron_entry.py", "Railway cron entry script"),
        ("run_cron_only.py", "Original cron entry script"),
        ("railway.toml", "Railway configuration"),
        ("requirements.txt", "Python dependencies"),
        ("daily_run/daily_trading_system.py", "Daily trading system"),
        ("daily_run/config.py", "Configuration file"),
        ("daily_run/database.py", "Database module"),
    ]
    
    file_checks = []
    for filepath, description in files_to_check:
        file_checks.append(check_file_exists(filepath, description))
    
    # Check Python modules
    print("\n📦 Checking Python modules:")
    modules_to_check = [
        ("yfinance", "Yahoo Finance API"),
        ("pandas", "Data manipulation"),
        ("requests", "HTTP requests"),
        ("sqlite3", "SQLite database"),
        ("logging", "Logging system"),
    ]
    
    module_checks = []
    for module_name, description in modules_to_check:
        module_checks.append(check_module_import(module_name, description))
    
    # Check project-specific imports
    print("\n🔧 Checking project-specific imports:")
    try:
        sys.path.insert(0, cwd)
        sys.path.insert(0, os.path.join(cwd, 'daily_run'))
        
        # Try importing the main trading system
        try:
            from daily_run.daily_trading_system import DailyTradingSystem
            print("✅ DailyTradingSystem: Successfully imported")
            project_imports_ok = True
        except ImportError as e:
            print(f"❌ DailyTradingSystem: {e}")
            project_imports_ok = False
            
    except Exception as e:
        print(f"❌ Project imports failed: {e}")
        project_imports_ok = False
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_files_ok = all(file_checks)
    all_modules_ok = all(module_checks)
    
    print(f"Files: {'✅ All OK' if all_files_ok else '❌ Some missing'}")
    print(f"Modules: {'✅ All OK' if all_modules_ok else '❌ Some missing'}")
    print(f"Project imports: {'✅ OK' if project_imports_ok else '❌ Failed'}")
    
    if all_files_ok and all_modules_ok and project_imports_ok:
        print("\n🎉 DEPLOYMENT READY!")
        print("All required files and dependencies are available.")
        return True
    else:
        print("\n⚠️  DEPLOYMENT ISSUES DETECTED")
        print("Please fix the issues above before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 