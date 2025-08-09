#!/usr/bin/env python3
"""
Railway Debug Script - Simple file and path checker
"""

import os
import sys
from datetime import datetime

print("🔍 RAILWAY DEBUG SCRIPT")
print("=" * 50)
print(f"⏰ Time: {datetime.now()}")
print(f"🐍 Python version: {sys.version}")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"📁 Script location: {__file__}")

print("\n📋 ENVIRONMENT VARIABLES:")
for key, value in os.environ.items():
    if any(keyword in key.upper() for keyword in ['PATH', 'PYTHON', 'APP', 'RAILWAY']):
        print(f"  {key}: {value}")

print("\n📁 CURRENT DIRECTORY CONTENTS:")
try:
    cwd = os.getcwd()
    for item in sorted(os.listdir(cwd)):
        item_path = os.path.join(cwd, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}/")
        elif item.endswith('.py'):
            print(f"  🐍 {item}")
        else:
            print(f"  📄 {item}")
except Exception as e:
    print(f"❌ Error listing directory: {e}")

print("\n🔍 LOOKING FOR KEY FILES:")
key_files = [
    'railway_cron_entry.py',
    'daily_run/daily_trading_system.py',
    'calc_technical_scores_enhanced.py',
    'requirements.txt',
    'railway.toml'
]

for file in key_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} (NOT FOUND)")

print("\n📁 DAILY_RUN DIRECTORY:")
daily_run_path = os.path.join(os.getcwd(), 'daily_run')
if os.path.exists(daily_run_path):
    try:
        print(f"✅ daily_run directory exists at: {daily_run_path}")
        for item in sorted(os.listdir(daily_run_path)):
            if item.endswith('.py'):
                print(f"  🐍 {item}")
    except Exception as e:
        print(f"❌ Error listing daily_run: {e}")
else:
    print(f"❌ daily_run directory not found")

print("\n🐍 PYTHON PATH:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

print("\n✅ DEBUG SCRIPT COMPLETED")
