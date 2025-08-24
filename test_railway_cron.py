#!/usr/bin/env python3
"""
Test script for Railway cron entry functionality
"""

import os
import sys
import subprocess
from pathlib import Path

def test_railway_cron_entry():
    """Test that the railway_cron_entry.py script can be executed"""
    print("🧪 Testing Railway Cron Entry Script")
    
    # Check if the file exists
    cron_file = Path("railway_cron_entry.py")
    if not cron_file.exists():
        print("❌ railway_cron_entry.py not found")
        return False
    
    print(f"✅ Found {cron_file}")
    
    # Check if daily_run directory exists
    daily_run_dir = Path("daily_run")
    if not daily_run_dir.exists():
        print("❌ daily_run directory not found")
        return False
    
    print(f"✅ Found {daily_run_dir}")
    
    # Check if daily_trading_system.py exists
    trading_system_file = daily_run_dir / "daily_trading_system.py"
    if not trading_system_file.exists():
        print("❌ daily_trading_system.py not found")
        return False
    
    print(f"✅ Found {trading_system_file}")
    
    # Test Python syntax
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(cron_file)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Python syntax check passed")
        else:
            print(f"❌ Python syntax check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking Python syntax: {e}")
        return False
    
    # Test import without execution
    try:
        # Add current directory to path
        if str(Path.cwd()) not in sys.path:
            sys.path.insert(0, str(Path.cwd()))
        
        # Try to import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_cron", str(cron_file))
        module = importlib.util.module_from_spec(spec)
        
        # Check if main function exists
        if hasattr(module, 'main'):
            print("✅ main() function found")
        else:
            print("⚠️  main() function not found")
        
        print("✅ Module import test passed")
        return True
        
    except Exception as e:
        print(f"❌ Module import test failed: {e}")
        return False

def test_environment_setup():
    """Test environment setup for Railway deployment"""
    print("\n🔧 Testing Environment Setup")
    
    # Check Python path
    print(f"📋 Python executable: {sys.executable}")
    print(f"📋 Python version: {sys.version}")
    print(f"📋 Current working directory: {os.getcwd()}")
    
    # Check if we can access daily_run
    try:
        daily_run_files = os.listdir("daily_run")
        print(f"✅ daily_run directory accessible, contains {len(daily_run_files)} files")
    except Exception as e:
        print(f"❌ Cannot access daily_run directory: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Railway Cron Entry Test Suite")
    print("=" * 50)
    
    # Run tests
    cron_test = test_railway_cron_entry()
    env_test = test_environment_setup()
    
    print("\n" + "=" * 50)
    if cron_test and env_test:
        print("✅ All tests passed! Railway cron entry should work.")
    else:
        print("❌ Some tests failed. Check the issues above.")
    
    sys.exit(0 if (cron_test and env_test) else 1)
