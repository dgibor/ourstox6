#!/usr/bin/env python3
"""
Test script to debug Railway path issues
"""

import os
import sys

def main():
    print("=== RAILWAY PATH DEBUG ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
    
    # Check if run_cron_only.py exists
    cron_file = "run_cron_only.py"
    if os.path.exists(cron_file):
        print(f"✅ {cron_file} exists in current directory")
    else:
        print(f"❌ {cron_file} NOT found in current directory")
    
    # List files in current directory
    print("\n=== Files in current directory ===")
    for file in os.listdir("."):
        if file.endswith(".py"):
            print(f"  {file}")
    
    # Check daily_run directory
    daily_run_dir = "daily_run"
    if os.path.exists(daily_run_dir):
        print(f"\n✅ {daily_run_dir} directory exists")
        if os.path.exists(os.path.join(daily_run_dir, "daily_trading_system.py")):
            print(f"✅ daily_trading_system.py exists in {daily_run_dir}")
        else:
            print(f"❌ daily_trading_system.py NOT found in {daily_run_dir}")
    else:
        print(f"❌ {daily_run_dir} directory NOT found")

if __name__ == "__main__":
    main() 