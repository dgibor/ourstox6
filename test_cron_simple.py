#!/usr/bin/env python3
"""
Ultra-simple cron test that writes to a file
"""

import os
import sys
from datetime import datetime

def main():
    """Write test output to a file"""
    timestamp = datetime.now().isoformat()
    
    # Write to a file in the current directory
    with open('cron_test_output.txt', 'a') as f:
        f.write(f"=== CRON TEST RUN AT {timestamp} ===\n")
        f.write(f"Current directory: {os.getcwd()}\n")
        f.write(f"Python version: {sys.version}\n")
        f.write(f"Files in directory: {len(os.listdir('.'))}\n")
        f.write(f"Environment variables:\n")
        f.write(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'NOT SET')}\n")
        f.write(f"  TZ: {os.getenv('TZ', 'NOT SET')}\n")
        f.write(f"  DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}\n")
        f.write("=== END CRON TEST ===\n\n")
    
    # Also try to print to stdout
    print(f"CRON TEST COMPLETED AT {timestamp}")
    sys.stdout.flush()

if __name__ == "__main__":
    main() 