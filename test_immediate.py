#!/usr/bin/env python3
"""
Immediate test script for Railway cron
"""

import sys
from datetime import datetime

def main():
    print("=" * 50)
    print("🚀 IMMEDIATE RAILWAY CRON TEST")
    print(f"⏰ Time: {datetime.now()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print("✅ This should appear in Railway logs immediately")
    print("=" * 50)
    sys.stdout.flush()

if __name__ == "__main__":
    main() 