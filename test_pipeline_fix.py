#!/usr/bin/env python3
"""
Test script to verify pipeline fixes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

from integrated_daily_runner_v2 import IntegratedDailyRunnerV2

def test_pipeline_fixes():
    """Test the fixed pipeline"""
    print("🧪 Testing Pipeline Fixes")
    print("=" * 50)
    
    try:
        # Test with minimal tickers
        runner = IntegratedDailyRunnerV2()
        
        result = runner.run_complete_daily_pipeline(
            test_mode=True,
            max_price_tickers=2,
            max_fundamental_tickers=1
        )
        
        print(f"\n📊 PIPELINE RESULTS:")
        print(f"Overall Status: {result.get('overall_status')}")
        
        price_update = result.get('price_update', {})
        print(f"Price Updates: {price_update.get('successful', 0)}/{price_update.get('total_tickers', 0)} successful")
        
        fundamentals_update = result.get('fundamentals_update', {})
        print(f"Fundamentals Updates: {fundamentals_update.get('successful', 0)}/{fundamentals_update.get('total_tickers', 0)} successful")
        
        technical_indicators = result.get('technical_indicators', {})
        print(f"Technical Indicators: {technical_indicators.get('successful', 0)}/{technical_indicators.get('total_tickers', 0)} successful")
        
        if result.get('overall_status') == 'success':
            print("\n✅ Pipeline test completed successfully!")
        else:
            print("\n❌ Pipeline test completed with issues")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline_fixes() 