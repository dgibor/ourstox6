#!/usr/bin/env python3
"""
Debug Monitoring Issues
"""

from monitoring import system_monitor
import traceback

def debug_monitoring():
    """Debug monitoring issues step by step"""
    print("🔍 Debugging Monitoring System")
    print("=" * 40)
    
    try:
        print("1. Testing system metrics...")
        metrics = system_monitor.get_system_metrics()
        print(f"   ✅ System metrics: CPU {metrics.cpu_percent:.1f}%")
    except Exception as e:
        print(f"   ❌ System metrics failed: {e}")
        traceback.print_exc()
        return
    
    try:
        print("2. Testing database health...")
        db_health = system_monitor.check_database_health()
        print(f"   ✅ Database health: {db_health.status}")
    except Exception as e:
        print(f"   ❌ Database health failed: {e}")
        traceback.print_exc()
        return
    
    try:
        print("3. Testing stocks data quality...")
        stocks_quality = system_monitor.check_data_quality('stocks')
        print(f"   ✅ Stocks quality: {stocks_quality.total_records} records")
    except Exception as e:
        print(f"   ❌ Stocks quality failed: {e}")
        traceback.print_exc()
        return
    
    try:
        print("4. Testing fundamentals data quality...")
        fundamentals_quality = system_monitor.check_data_quality('company_fundamentals')
        print(f"   ✅ Fundamentals quality: {fundamentals_quality.total_records} records")
    except Exception as e:
        print(f"   ❌ Fundamentals quality failed: {e}")
        traceback.print_exc()
        return
    
    try:
        print("5. Testing system health summary...")
        health_summary = system_monitor.get_system_health_summary()
        print(f"   ✅ Health summary: {health_summary['overall_status']}")
        print("   ✅ All monitoring tests passed!")
    except Exception as e:
        print(f"   ❌ Health summary failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_monitoring() 