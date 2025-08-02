#!/usr/bin/env python3
"""
Simple Railway Test - Minimal script to verify deployment
"""

import os
import sys
import logging
from datetime import datetime

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - RAILWAY SIMPLE TEST - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("=" * 50)
print("🚀 RAILWAY SIMPLE TEST STARTED")
print(f"⏰ Time: {datetime.now()}")
print(f"📁 Directory: {os.getcwd()}")
print(f"🐍 Python: {sys.version}")
print("=" * 50)

# Test environment variables
print("🔧 Environment:")
print(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'NOT SET')}")
print(f"  TZ: {os.getenv('TZ', 'NOT SET')}")
print(f"  DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")

# Test basic imports
print("📦 Testing imports:")
try:
    import psycopg2
    print("✅ psycopg2 OK")
except Exception as e:
    print(f"❌ psycopg2 failed: {e}")

try:
    import pandas
    print("✅ pandas OK")
except Exception as e:
    print(f"❌ pandas failed: {e}")

# Test file access
print("📋 Files in current directory:")
try:
    files = os.listdir('.')
    for file in files[:5]:
        print(f"  - {file}")
    if len(files) > 5:
        print(f"  ... and {len(files) - 5} more")
except Exception as e:
    print(f"❌ File listing failed: {e}")

print("✅ RAILWAY SIMPLE TEST COMPLETED")
print("=" * 50) 