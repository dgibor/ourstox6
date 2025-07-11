#!/usr/bin/env python3
"""
QA Testing for Daily Trading System
Comprehensive test suite to identify and verify fixes for critical issues
"""

import sys
import logging
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class DailyTradingSystemQA:
    """Comprehensive QA testing for the daily trading system"""
    
    def __init__(self):
        self.issues_found = []
        self.tests_passed = 0
        self.tests_failed = 0
        self.critical_issues = []
        
    def run_comprehensive_qa(self):
        """Run comprehensive QA testing"""
        print("🔍 DAILY TRADING SYSTEM - QA EXPERT REVIEW")
        print("=" * 60)
        
        self.test_imports_and_dependencies()
        self.test_database_integration()
        self.test_service_manager_integration()
        self.test_priority_logic()
        self.test_error_handling_robustness()
        self.test_api_rate_limiting()
        self.test_data_validation()
        self.test_earnings_calendar_integration()
        self.test_system_integration()
        
        return self.generate_qa_report()
        
    def test_imports_and_dependencies(self):
        """Test 1: Import and Dependency Validation"""
        print("\n🧪 TEST 1: IMPORTS AND DEPENDENCIES")
        print("-" * 50)
        
        try:
            from daily_trading_system import DailyTradingSystem
            self.record_success("✅ Main class import successful")
            
            # Test critical dependencies
            dependencies = [
                ('database', 'DatabaseManager'),
                ('enhanced_multi_service_manager', 'get_multi_service_manager'),
                ('batch_price_processor', 'BatchPriceProcessor'),
                ('earnings_based_fundamental_processor', 'EarningsBasedFundamentalProcessor'),
                ('error_handler', 'ErrorHandler'),
                ('monitoring', 'SystemMonitor'),
                ('data_validator', 'data_validator'),
                ('circuit_breaker', 'circuit_manager')
            ]
            
            for module_name, class_name in dependencies:
                try:
                    module = __import__(module_name)
                    if hasattr(module, class_name):
                        self.record_success(f"✅ {module_name}.{class_name} available")
                    else:
                        self.record_issue(f"❌ {module_name}.{class_name} not found", "CRITICAL")
                except ImportError as e:
                    self.record_issue(f"❌ Import failed: {module_name} - {e}", "CRITICAL")
                    
        except Exception as e:
            self.record_issue(f"❌ Daily trading system import failed: {e}", "CRITICAL")
    
    def test_database_integration(self):
        """Test 2: Database Integration"""
        print("\n🧪 TEST 2: DATABASE INTEGRATION")
        print("-" * 50)
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            # Test connection
            if db.test_connection():
                self.record_success("✅ Database connection successful")
            else:
                self.record_issue("❌ Database connection failed", "CRITICAL")
                return
            
            # Test required methods existence
            required_methods = [
                'execute_query', 'execute_update', 'get_tickers',
                'get_price_data_for_technicals', 'update_technical_indicators'
            ]
            
            for method in required_methods:
                if hasattr(db, method):
                    self.record_success(f"✅ DatabaseManager.{method}() exists")
                else:
                    self.record_issue(f"❌ DatabaseManager.{method}() missing", "HIGH")
            
            # Test critical queries
            try:
                # Test stocks table access
                query = "SELECT COUNT(*) FROM stocks LIMIT 1"
                result = db.execute_query(query)
                self.record_success(f"✅ Stocks table accessible ({result[0][0] if result else 0} records)")
                
                # Test daily_charts table access
                query = "SELECT COUNT(*) FROM daily_charts LIMIT 1"
                result = db.execute_query(query)
                self.record_success(f"✅ Daily_charts table accessible ({result[0][0] if result else 0} records)")
                
                # Test company_fundamentals table access
                query = "SELECT COUNT(*) FROM company_fundamentals LIMIT 1"
                result = db.execute_query(query)
                self.record_success(f"✅ Company_fundamentals table accessible ({result[0][0] if result else 0} records)")
                
            except Exception as e:
                self.record_issue(f"❌ Database table access failed: {e}", "HIGH")
                
        except Exception as e:
            self.record_issue(f"❌ Database integration test failed: {e}", "CRITICAL")
    
    def test_service_manager_integration(self):
        """Test 3: Service Manager Integration"""
        print("\n🧪 TEST 3: SERVICE MANAGER INTEGRATION")
        print("-" * 50)
        
        try:
            from enhanced_multi_service_manager import get_multi_service_manager
            
            service_manager = get_multi_service_manager()
            if service_manager:
                self.record_success("✅ Service manager initialization successful")
                
                # Test critical methods
                if hasattr(service_manager, 'fetch_data_with_fallback'):
                    self.record_success("✅ fetch_data_with_fallback method exists")
                else:
                    self.record_issue("❌ fetch_data_with_fallback method missing", "CRITICAL")
                
                # Check for get_service method (used in daily_trading_system.py)
                if hasattr(service_manager, 'get_service'):
                    self.record_success("✅ get_service method exists")
                else:
                    self.record_issue("❌ CRITICAL: get_service method missing - used in _get_historical_data_to_minimum() and _update_single_ticker_fundamentals()", "CRITICAL")
                
                # Test service availability
                if hasattr(service_manager, 'service_instances'):
                    available_services = len(service_manager.service_instances)
                    self.record_success(f"✅ {available_services} services initialized")
                    
                    if available_services == 0:
                        self.record_issue("⚠️ No API services available - may impact functionality", "MEDIUM")
                else:
                    self.record_issue("❌ service_instances attribute missing", "HIGH")
                    
            else:
                self.record_issue("❌ Service manager initialization failed", "CRITICAL")
                
        except Exception as e:
            self.record_issue(f"❌ Service manager integration test failed: {e}", "CRITICAL")
    
    def test_priority_logic(self):
        """Test 4: Priority Logic Implementation"""
        print("\n🧪 TEST 4: PRIORITY LOGIC VALIDATION")
        print("-" * 50)
        
        try:
            from daily_trading_system import DailyTradingSystem
            
            system = DailyTradingSystem()
            
            # Test priority method existence
            priority_methods = [
                '_calculate_technical_indicators_priority1',
                '_update_earnings_announcement_fundamentals',
                '_ensure_minimum_historical_data',
                '_fill_missing_fundamental_data'
            ]
            
            for method in priority_methods:
                if hasattr(system, method):
                    self.record_success(f"✅ {method}() method exists")
                else:
                    self.record_issue(f"❌ {method}() method missing", "CRITICAL")
            
            # Test helper methods
            helper_methods = [
                '_get_earnings_announcement_tickers',
                '_get_tickers_needing_100_days_history',
                '_get_tickers_missing_fundamental_data',
                '_get_historical_data_to_minimum',
                '_update_single_ticker_fundamentals',
                '_calculate_fundamental_ratios'
            ]
            
            for method in helper_methods:
                if hasattr(system, method):
                    self.record_success(f"✅ {method}() helper method exists")
                else:
                    self.record_issue(f"❌ {method}() helper method missing", "HIGH")
            
            # Test API rate limiting
            if hasattr(system, 'api_calls_used') and hasattr(system, 'max_api_calls_per_day'):
                self.record_success("✅ API rate limiting attributes present")
            else:
                self.record_issue("❌ API rate limiting attributes missing", "MEDIUM")
                
        except Exception as e:
            self.record_issue(f"❌ Priority logic test failed: {e}", "HIGH")
    
    def test_error_handling_robustness(self):
        """Test 5: Error Handling Robustness"""
        print("\n🧪 TEST 5: ERROR HANDLING ROBUSTNESS")
        print("-" * 50)
        
        try:
            from daily_trading_system import DailyTradingSystem
            
            system = DailyTradingSystem()
            
            # Test invalid ticker handling
            try:
                result = system._get_earnings_announcement_tickers()
                if isinstance(result, list):
                    self.record_success("✅ _get_earnings_announcement_tickers() returns list (robust)")
                else:
                    self.record_issue("❌ _get_earnings_announcement_tickers() doesn't return list", "MEDIUM")
            except Exception as e:
                self.record_issue(f"❌ _get_earnings_announcement_tickers() throws exception: {e}", "HIGH")
            
            # Test empty database handling
            try:
                result = system._get_tickers_needing_100_days_history()
                if isinstance(result, list):
                    self.record_success("✅ _get_tickers_needing_100_days_history() returns list (robust)")
                else:
                    self.record_issue("❌ _get_tickers_needing_100_days_history() doesn't return list", "MEDIUM")
            except Exception as e:
                self.record_issue(f"❌ _get_tickers_needing_100_days_history() throws exception: {e}", "HIGH")
            
            # Test missing fundamental data handling
            try:
                result = system._get_tickers_missing_fundamental_data()
                if isinstance(result, list):
                    self.record_success("✅ _get_tickers_missing_fundamental_data() returns list (robust)")
                else:
                    self.record_issue("❌ _get_tickers_missing_fundamental_data() doesn't return list", "MEDIUM")
            except Exception as e:
                self.record_issue(f"❌ _get_tickers_missing_fundamental_data() throws exception: {e}", "HIGH")
            
            # Test individual ticker failure handling
            try:
                result = system._update_single_ticker_fundamentals("INVALID_TICKER_12345")
                if isinstance(result, bool):
                    self.record_success("✅ _update_single_ticker_fundamentals() handles invalid ticker gracefully")
                else:
                    self.record_issue("❌ _update_single_ticker_fundamentals() doesn't return boolean", "MEDIUM")
            except Exception as e:
                # This is actually good - it should handle errors internally
                self.record_issue(f"⚠️ _update_single_ticker_fundamentals() throws exception (should handle internally): {e}", "LOW")
                
        except Exception as e:
            self.record_issue(f"❌ Error handling robustness test failed: {e}", "HIGH")
    
    def test_api_rate_limiting(self):
        """Test 6: API Rate Limiting Logic"""
        print("\n🧪 TEST 6: API RATE LIMITING LOGIC")
        print("-" * 50)
        
        try:
            from daily_trading_system import DailyTradingSystem
            
            system = DailyTradingSystem()
            
            # Test initial state
            if system.api_calls_used == 0:
                self.record_success("✅ API calls counter initialized to 0")
            else:
                self.record_issue(f"⚠️ API calls counter not initialized to 0 (current: {system.api_calls_used})", "LOW")
            
            if system.max_api_calls_per_day > 0:
                self.record_success(f"✅ API call limit set ({system.max_api_calls_per_day} calls/day)")
            else:
                self.record_issue("❌ API call limit not set or invalid", "MEDIUM")
            
            # Test rate limiting logic in priority methods
            methods_with_rate_limiting = [
                '_update_earnings_announcement_fundamentals',
                '_ensure_minimum_historical_data', 
                '_fill_missing_fundamental_data'
            ]
            
            # This is a static analysis - we can't easily test the logic without API calls
            for method in methods_with_rate_limiting:
                if hasattr(system, method):
                    import inspect
                    source = inspect.getsource(getattr(system, method))
                    if 'api_calls_used' in source and 'max_api_calls_per_day' in source:
                        self.record_success(f"✅ {method}() implements API rate limiting")
                    else:
                        self.record_issue(f"❌ {method}() missing API rate limiting logic", "HIGH")
                        
        except Exception as e:
            self.record_issue(f"❌ API rate limiting test failed: {e}", "MEDIUM")
    
    def test_data_validation(self):
        """Test 7: Data Validation and Safe Operations"""
        print("\n🧪 TEST 7: DATA VALIDATION AND SAFE OPERATIONS")
        print("-" * 50)
        
        try:
            from daily_trading_system import DailyTradingSystem
            
            system = DailyTradingSystem()
            
            # Test safe_divide usage in ratio calculations
            try:
                import inspect
                ratio_method = getattr(system, '_calculate_fundamental_ratios')
                source = inspect.getsource(ratio_method)
                
                if 'safe_divide' in source:
                    self.record_success("✅ _calculate_fundamental_ratios() uses safe_divide for zero-division protection")
                else:
                    self.record_issue("❌ _calculate_fundamental_ratios() doesn't use safe_divide - potential division by zero", "HIGH")
                
                # Check for fallback safe_divide implementation
                if 'def safe_divide(' in source:
                    self.record_success("✅ Fallback safe_divide implementation present")
                else:
                    self.record_issue("⚠️ No fallback safe_divide implementation", "MEDIUM")
                    
            except Exception as e:
                self.record_issue(f"❌ Could not analyze ratio calculation method: {e}", "MEDIUM")
            
            # Test data extraction patterns
            try:
                store_method = getattr(system, '_store_fundamental_data')
                source = inspect.getsource(store_method)
                
                if '.get(' in source and 'or 0' in source:
                    self.record_success("✅ _store_fundamental_data() uses safe data extraction patterns")
                else:
                    self.record_issue("⚠️ _store_fundamental_data() may not handle missing data safely", "MEDIUM")
                    
            except Exception as e:
                self.record_issue(f"❌ Could not analyze data storage method: {e}", "MEDIUM")
                
        except Exception as e:
            self.record_issue(f"❌ Data validation test failed: {e}", "MEDIUM")
    
    def test_earnings_calendar_integration(self):
        """Test 8: Earnings Calendar Integration"""
        print("\n🧪 TEST 8: EARNINGS CALENDAR INTEGRATION")
        print("-" * 50)
        
        try:
            from daily_trading_system import DailyTradingSystem
            
            system = DailyTradingSystem()
            
            # Test earnings calendar service initialization
            if hasattr(system, 'earnings_processor'):
                self.record_success("✅ Earnings processor initialized")
                
                # Test earnings calendar table fallback
                try:
                    tickers = system._get_earnings_announcement_tickers()
                    if isinstance(tickers, list):
                        self.record_success(f"✅ Earnings announcement detection works (found {len(tickers)} tickers)")
                        
                        if len(tickers) == 0:
                            self.record_issue("ℹ️ No earnings announcements found for today (this may be normal)", "INFO")
                    else:
                        self.record_issue("❌ _get_earnings_announcement_tickers() doesn't return list", "HIGH")
                        
                except Exception as e:
                    self.record_issue(f"❌ Earnings announcement detection failed: {e}", "HIGH")
            else:
                self.record_issue("❌ Earnings processor not initialized", "HIGH")
                
        except Exception as e:
            self.record_issue(f"❌ Earnings calendar integration test failed: {e}", "HIGH")
    
    def test_system_integration(self):
        """Test 9: System Integration"""
        print("\n🧪 TEST 9: SYSTEM INTEGRATION")
        print("-" * 50)
        
        try:
            from daily_trading_system import DailyTradingSystem
            
            system = DailyTradingSystem()
            
            # Test main method structure
            if hasattr(system, 'run_daily_trading_process'):
                self.record_success("✅ Main entry point exists")
                
                # Test force run capability
                try:
                    import inspect
                    signature = inspect.signature(system.run_daily_trading_process)
                    if 'force_run' in signature.parameters:
                        self.record_success("✅ Force run parameter available")
                    else:
                        self.record_issue("❌ Force run parameter missing", "MEDIUM")
                except Exception as e:
                    self.record_issue(f"⚠️ Could not analyze main method signature: {e}", "LOW")
            else:
                self.record_issue("❌ Main entry point missing", "CRITICAL")
            
            # Test component integration
            components = ['db', 'error_handler', 'monitoring', 'batch_price_processor', 'service_manager']
            for component in components:
                if hasattr(system, component):
                    self.record_success(f"✅ {component} component integrated")
                else:
                    self.record_issue(f"❌ {component} component missing", "HIGH")
            
            # Test method call chain integrity
            try:
                import inspect
                main_method = getattr(system, 'run_daily_trading_process')
                source = inspect.getsource(main_method)
                
                expected_calls = [
                    '_check_trading_day',
                    '_update_daily_prices',
                    '_calculate_technical_indicators_priority1',
                    '_update_earnings_announcement_fundamentals',
                    '_ensure_minimum_historical_data',
                    '_fill_missing_fundamental_data'
                ]
                
                missing_calls = []
                for call in expected_calls:
                    if call not in source:
                        missing_calls.append(call)
                
                if not missing_calls:
                    self.record_success("✅ All priority methods called in main process")
                else:
                    self.record_issue(f"❌ Missing method calls: {missing_calls}", "CRITICAL")
                    
            except Exception as e:
                self.record_issue(f"❌ Could not analyze method call chain: {e}", "HIGH")
                
        except Exception as e:
            self.record_issue(f"❌ System integration test failed: {e}", "CRITICAL")
    
    def record_success(self, message: str):
        """Record a successful test"""
        print(f"  {message}")
        self.tests_passed += 1
    
    def record_issue(self, message: str, severity: str = "MEDIUM"):
        """Record an issue found"""
        print(f"  {message}")
        self.issues_found.append({
            'message': message,
            'severity': severity,
            'timestamp': datetime.now()
        })
        self.tests_failed += 1
        
        if severity == "CRITICAL":
            self.critical_issues.append(message)
    
    def generate_qa_report(self):
        """Generate comprehensive QA report"""
        print("\n" + "=" * 60)
        print("📊 QA REPORT SUMMARY")
        print("=" * 60)
        
        total_tests = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Categorize issues by severity
        critical = [i for i in self.issues_found if i['severity'] == 'CRITICAL']
        high = [i for i in self.issues_found if i['severity'] == 'HIGH']
        medium = [i for i in self.issues_found if i['severity'] == 'MEDIUM']
        low = [i for i in self.issues_found if i['severity'] == 'LOW']
        info = [i for i in self.issues_found if i['severity'] == 'INFO']
        
        print(f"\n🚨 ISSUES BY SEVERITY:")
        print(f"   🔴 Critical: {len(critical)}")
        print(f"   🟠 High: {len(high)}")
        print(f"   🟡 Medium: {len(medium)}")
        print(f"   🔵 Low: {len(low)}")
        print(f"   ℹ️  Info: {len(info)}")
        
        # Show critical issues
        if critical:
            print(f"\n🔴 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for i, issue in enumerate(critical, 1):
                print(f"   {i}. {issue['message'].replace('❌ ', '')}")
        
        # Show high priority issues
        if high:
            print(f"\n🟠 HIGH PRIORITY ISSUES:")
            for i, issue in enumerate(high, 1):
                print(f"   {i}. {issue['message'].replace('❌ ', '').replace('⚠️ ', '')}")
        
        # Overall assessment
        print(f"\n🎯 ASSESSMENT:")
        if len(critical) == 0 and len(high) <= 2:
            print("   ✅ SYSTEM IS PRODUCTION READY")
            print("   📋 Minor issues can be addressed in next iteration")
        elif len(critical) == 0:
            print("   ⚠️  SYSTEM NEEDS IMPROVEMENTS BEFORE PRODUCTION")
            print("   📋 Address high priority issues first")
        else:
            print("   🚨 SYSTEM NOT READY FOR PRODUCTION")
            print("   📋 Critical issues must be fixed before deployment")
        
        print("\n" + "=" * 60)
        return {
            'total_tests': total_tests,
            'passed': self.tests_passed,
            'failed': self.tests_failed,
            'success_rate': success_rate,
            'critical_issues': len(critical),
            'high_issues': len(high),
            'issues': self.issues_found
        }


def main():
    """Run QA testing"""
    qa = DailyTradingSystemQA()
    results = qa.run_comprehensive_qa()
    
    # Return appropriate exit code
    if results['critical_issues'] > 0:
        return 1  # Critical issues found
    elif results['high_issues'] > 3:
        return 2  # Too many high priority issues
    else:
        return 0  # System acceptable


if __name__ == "__main__":
    exit(main()) 