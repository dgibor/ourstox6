"""
Test script for daily fundamental ratio calculation integration
"""

import logging
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from daily_run.calculate_fundamental_ratios import DailyFundamentalRatioCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MockDatabase:
    """Mock database for testing"""
    
    def __init__(self):
        self.companies_data = [
            {
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'current_price': 150.0,
                'fundamentals_last_update': date.today(),
                'next_earnings_date': date.today() + timedelta(days=30),
                'data_priority': 1,
                'last_ratio_calculation': None
            },
            {
                'ticker': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'current_price': 300.0,
                'fundamentals_last_update': date.today(),
                'next_earnings_date': date.today() + timedelta(days=45),
                'data_priority': 1,
                'last_ratio_calculation': date.today() - timedelta(days=2)
            }
        ]
        
        self.fundamental_data = {
            'AAPL': {
                'ticker': 'AAPL',
                'report_date': date.today(),
                'period_type': 'annual',
                'revenue': 394328000000,
                'gross_profit': 170782000000,
                'operating_income': 114301000000,
                'net_income': 96995000000,
                'ebitda': 120000000000,
                'eps_diluted': 6.84,
                'book_value_per_share': 4.25,
                'total_assets': 352755000000,
                'total_debt': 95000000000,
                'total_equity': 80600000000,
                'cash_and_equivalents': 48000000000,
                'operating_cash_flow': 110000000000,
                'free_cash_flow': 90000000000,
                'shares_outstanding': 15700000000,
                'current_price': 150.0
            },
            'MSFT': {
                'ticker': 'MSFT',
                'report_date': date.today(),
                'period_type': 'annual',
                'revenue': 198270000000,
                'gross_profit': 135000000000,
                'operating_income': 88000000000,
                'net_income': 72000000000,
                'ebitda': 95000000000,
                'eps_diluted': 9.60,
                'book_value_per_share': 12.50,
                'total_assets': 411000000000,
                'total_debt': 60000000000,
                'total_equity': 238000000000,
                'cash_and_equivalents': 35000000000,
                'operating_cash_flow': 85000000000,
                'free_cash_flow': 65000000000,
                'shares_outstanding': 7500000000,
                'current_price': 300.0
            }
        }
        
        self.historical_data = {
            'AAPL': {
                'revenue_previous': 365817000000,
                'total_assets_previous': 346747000000,
                'inventory_previous': 4946000000,
                'accounts_receivable_previous': 29508000000,
                'retained_earnings_previous': 50000000000
            },
            'MSFT': {
                'revenue_previous': 176000000000,
                'total_assets_previous': 380000000000,
                'inventory_previous': 2500000000,
                'accounts_receivable_previous': 20000000000,
                'retained_earnings_previous': 80000000000
            }
        }
    
    def cursor(self, cursor_factory=None):
        return MockCursor(self, cursor_factory)
    
    def commit(self):
        pass
    
    def rollback(self):
        pass

class MockCursor:
    """Mock cursor for testing"""
    
    def __init__(self, db, cursor_factory=None):
        self.db = db
        self.cursor_factory = cursor_factory
        self.execute_calls = []
        self.fetch_results = []
    
    def execute(self, query, params=None):
        self.execute_calls.append((query, params))
        print(f"DEBUG: Query: {query[:100]}...")
        print(f"DEBUG: Params: {params}")
        
        # Mock different query responses
        if 'companies_needing_ratio_updates' in query or 'stocks s' in query:
            self.fetch_results = self.db.companies_data
        elif 'company_fundamentals cf' in query:
            print(f"DEBUG: Found company_fundamentals query with params: {params}")
            if params and params[0] in self.db.fundamental_data:
                # Convert to RealDictCursor format
                result = self.db.fundamental_data[params[0]]
                print(f"DEBUG: Found fundamental data for {params[0]}: {list(result.keys())}")
                if self.cursor_factory:
                    # Simulate RealDictCursor behavior
                    class MockRow:
                        def __init__(self, data):
                            self._data = data
                        def __getitem__(self, key):
                            return self._data[key]
                        def __contains__(self, key):
                            return key in self._data
                        def keys(self):
                            return self._data.keys()
                        def values(self):
                            return self._data.values()
                        def items(self):
                            return self._data.items()
                        def get(self, key, default=None):
                            return self._data.get(key, default)
                        def __iter__(self):
                            return iter(self._data)
                        def __len__(self):
                            return len(self._data)
                        def __repr__(self):
                            return f"MockRow({self._data})"
                    
                    self.fetch_results = [MockRow(result)]
                else:
                    self.fetch_results = [result]
            else:
                print(f"DEBUG: No fundamental data found for {params}")
                self.fetch_results = []
        elif 'historical' in query:
            if params and params[0] in self.db.historical_data:
                result = self.db.historical_data[params[0]]
                if self.cursor_factory:
                    class MockRow:
                        def __init__(self, data):
                            self._data = data
                        def __getitem__(self, key):
                            return self._data[key]
                        def __contains__(self, key):
                            return key in self._data
                        def keys(self):
                            return self._data.keys()
                        def values(self):
                            return self._data.values()
                        def items(self):
                            return self._data.items()
                        def get(self, key, default=None):
                            return self._data.get(key, default)
                        def __iter__(self):
                            return iter(self._data)
                        def __len__(self):
                            return len(self._data)
                        def __repr__(self):
                            return f"MockRow({self._data})"
                    
                    self.fetch_results = [MockRow(result)]
                else:
                    self.fetch_results = [result]
            else:
                self.fetch_results = []
        elif 'DELETE FROM financial_ratios' in query:
            self.fetch_results = []
        elif 'INSERT INTO financial_ratios' in query:
            self.fetch_results = []
    
    def fetchall(self):
        return self.fetch_results
    
    def fetchone(self):
        if self.fetch_results:
            return self.fetch_results[0]
        return None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def test_daily_fundamental_ratio_calculator():
    """Test the daily fundamental ratio calculator"""
    
    logger.info("Testing Daily Fundamental Ratio Calculator")
    
    # Create mock database
    mock_db = MockDatabase()
    
    # Create calculator with mock database
    calculator = DailyFundamentalRatioCalculator(mock_db)
    
    # Test getting companies needing updates
    logger.info("Testing get_companies_needing_ratio_updates...")
    companies = calculator.get_companies_needing_ratio_updates()
    
    assert len(companies) == 2, f"Expected 2 companies, got {len(companies)}"
    assert companies[0]['ticker'] == 'AAPL', f"Expected AAPL, got {companies[0]['ticker']}"
    assert companies[1]['ticker'] == 'MSFT', f"Expected MSFT, got {companies[1]['ticker']}"
    
    logger.info("✓ get_companies_needing_ratio_updates test passed")
    
    # Test getting fundamental data
    logger.info("Testing get_latest_fundamental_data...")
    aapl_data = calculator.get_latest_fundamental_data('AAPL')
    
    assert aapl_data is not None, "Expected fundamental data for AAPL"
    logger.info(f"AAPL data keys: {list(aapl_data.keys())}")
    assert aapl_data['ticker'] == 'AAPL', f"Expected AAPL ticker, got {aapl_data['ticker']}"
    assert aapl_data['revenue'] == 394328000000, f"Expected revenue, got {aapl_data['revenue']}"
    
    logger.info("✓ get_latest_fundamental_data test passed")
    
    # Test getting historical data
    logger.info("Testing get_historical_fundamental_data...")
    aapl_historical = calculator.get_historical_fundamental_data('AAPL')
    
    assert aapl_historical is not None, "Expected historical data for AAPL"
    assert aapl_historical['revenue_previous'] == 365817000000, f"Expected previous revenue, got {aapl_historical['revenue_previous']}"
    
    logger.info("✓ get_historical_fundamental_data test passed")
    
    # Test calculating ratios for a company
    logger.info("Testing calculate_ratios_for_company...")
    company_data = companies[0]  # AAPL
    result = calculator.calculate_ratios_for_company(company_data)
    
    assert result['status'] == 'success', f"Expected success, got {result['status']}"
    assert result['ratios_calculated'] > 0, f"Expected ratios calculated, got {result['ratios_calculated']}"
    assert 'ratios' in result, "Expected ratios in result"
    
    # Check that key ratios were calculated
    ratios = result['ratios']
    assert 'pe_ratio' in ratios, "Expected P/E ratio"
    assert 'pb_ratio' in ratios, "Expected P/B ratio"
    assert 'roe' in ratios, "Expected ROE"
    assert 'roa' in ratios, "Expected ROA"
    
    logger.info("✓ calculate_ratios_for_company test passed")
    
    # Test processing all companies
    logger.info("Testing process_all_companies...")
    results = calculator.process_all_companies()
    
    assert results['total_processed'] == 2, f"Expected 2 processed, got {results['total_processed']}"
    assert results['successful'] == 2, f"Expected 2 successful, got {results['successful']}"
    assert results['failed'] == 0, f"Expected 0 failed, got {results['failed']}"
    
    logger.info("✓ process_all_companies test passed")
    
    logger.info("All tests passed! ✅")

def test_error_handling():
    """Test error handling scenarios"""
    
    logger.info("Testing error handling...")
    
    # Create mock database that raises errors
    mock_db = Mock()
    mock_db.cursor.side_effect = Exception("Database connection failed")
    
    calculator = DailyFundamentalRatioCalculator(mock_db)
    
    # Test error handling in get_companies_needing_ratio_updates
    companies = calculator.get_companies_needing_ratio_updates()
    assert companies == [], "Expected empty list on database error"
    
    logger.info("✓ Error handling test passed")

def main():
    """Main test function"""
    logger.info("Starting Daily Fundamental Ratio Calculator tests")
    
    try:
        # Test normal operation
        test_daily_fundamental_ratio_calculator()
        
        # Test error handling
        test_error_handling()
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 