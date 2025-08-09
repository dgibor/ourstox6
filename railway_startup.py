#!/usr/bin/env python3
"""
Railway Startup Script - Handles /app directory navigation and robust execution
"""

import os
import sys
import logging
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - RAILWAY STARTUP - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def find_and_execute():
    """Find the correct directory and execute the railway_cron_entry.py"""
    logger.info("🚀 RAILWAY STARTUP SCRIPT")
    logger.info(f"⏰ Time: {datetime.now()}")
    logger.info(f"📁 Initial working directory: {os.getcwd()}")
    
    # Possible directories where our code might be
    possible_dirs = [
        '/app',
        '/workspace', 
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__))
    ]
    
    target_file = 'railway_cron_entry.py'
    found_dir = None
    
    logger.info("🔍 Searching for railway_cron_entry.py in possible directories...")
    
    for directory in possible_dirs:
        if os.path.exists(directory):
            target_path = os.path.join(directory, target_file)
            logger.info(f"  Checking: {target_path}")
            
            if os.path.exists(target_path):
                found_dir = directory
                logger.info(f"✅ Found {target_file} in: {directory}")
                break
            else:
                logger.info(f"  ❌ Not found in: {directory}")
                # List contents of directory for debugging
                try:
                    contents = os.listdir(directory)[:10]  # First 10 files
                    logger.info(f"    Directory contents: {contents}")
                except Exception as e:
                    logger.error(f"    Error listing directory: {e}")
    
    if not found_dir:
        logger.error(f"❌ {target_file} not found in any expected directory!")
        logger.error("🔍 Listing all files in current directory for debugging:")
        try:
            for file in os.listdir(os.getcwd()):
                logger.error(f"  - {file}")
        except Exception as e:
            logger.error(f"Error listing current directory: {e}")
        return False
    
    # Change to the correct directory
    logger.info(f"📁 Changing to directory: {found_dir}")
    os.chdir(found_dir)
    logger.info(f"📁 New working directory: {os.getcwd()}")
    
    # Add the directory to Python path
    if found_dir not in sys.path:
        sys.path.insert(0, found_dir)
        logger.info(f"✅ Added {found_dir} to Python path")
    
    # Execute the main script
    logger.info(f"🚀 Executing {target_file}...")
    
    try:
        # Import the module properly
        import importlib.util
        spec = importlib.util.spec_from_file_location("railway_cron_entry", target_file)
        module = importlib.util.module_from_spec(spec)
        
        # Add module to sys.modules so imports work
        sys.modules["railway_cron_entry"] = module
        
        # Execute the module
        spec.loader.exec_module(module)
        
        # Call the main function if it exists
        if hasattr(module, 'main'):
            result = module.main()
            logger.info(f"✅ Script executed successfully, result: {result}")
            return result
        else:
            logger.info("✅ Script executed successfully (no main function)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error executing script: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = find_and_execute()
    sys.exit(0 if success else 1)
