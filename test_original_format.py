#!/usr/bin/env python3
"""
Test script using the original working cron format
"""

import os
import sys
import logging
from datetime import datetime

def main():
    """Test function using original format"""
    # Setup logging like the original script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - ORIGINAL FORMAT TEST - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🚀 ORIGINAL FORMAT CRON TEST STARTED")
    logger.info(f"⏰ Time: {datetime.now()}")
    logger.info(f"📁 Directory: {os.getcwd()}")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    logger.info("✅ ORIGINAL FORMAT CRON TEST COMPLETED")
    logger.info("=" * 60)
    
    # Force flush
    sys.stdout.flush()

if __name__ == "__main__":
    main() 