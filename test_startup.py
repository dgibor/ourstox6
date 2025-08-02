#!/usr/bin/env python3
"""
Test script to run during Railway startup
"""

import os
import sys
from datetime import datetime

def main():
    """Test function that runs during startup"""
    timestamp = datetime.now().isoformat()
    
    # Write to a file
    with open('startup_test_output.txt', 'a') as f:
        f.write(f"=== STARTUP TEST RUN AT {timestamp} ===\n")
        f.write(f"Current directory: {os.getcwd()}\n")
        f.write(f"Python version: {sys.version}\n")
        f.write(f"Files in directory: {len(os.listdir('.'))}\n")
        f.write(f"Environment variables:\n")
        f.write(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'NOT SET')}\n")
        f.write(f"  TZ: {os.getenv('TZ', 'NOT SET')}\n")
        f.write(f"  DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}\n")
        f.write("=== END STARTUP TEST ===\n\n")
    
    # Print to stdout
    print(f"STARTUP TEST COMPLETED AT {timestamp}")
    sys.stdout.flush()

if __name__ == "__main__":
    main() 