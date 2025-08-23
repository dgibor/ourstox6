#!/usr/bin/env python3
"""
Unit tests for AnalystScoringManager

Tests all functionality including edge cases and error conditions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyst_scoring_manager import AnalystScoringManager
from database import DatabaseManager


class TestAnalystScoringManager(unittest.TestCase):
    """Test cases for AnalystScoringManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock(spec=DatabaseManager)
        self.mock_db.connection = Mock()
        self.mock_db.execute_query = Mock()
        
        self.manager = AnalystScoringManager(db=self.mock_db)
    
    def test_init(self):
        """Test manager initialization"""
        self.assertIsNotNone(self.manager.db)
        self.assertIsNotNone(self.manager.analyst_scorer)
    
    def test_get_active_tickers_success(self):
        """Test successful retrieval of active tickers"""
        # Mock database response
        mock_results = [('AAPL',), ('MSFT',), ('NVDA',)]
        self.mock_db.execute_query.return_value = mock_results
        
        tickers = self.manager.get_active_tickers()
        
        self.assertEqual(tickers, ['AAPL', 'MSFT', 'NVDA'])
        self.mock_db.execute_query.assert_called_once()
    
    def test_get_active_tickers_empty(self):
        """Test handling of empty ticker list"""
        self.mock_db.execute_query.return_value = []
        
        tickers = self.manager.get_active_tickers()
        
        self.assertEqual(tickers, [])
    
    def test_get_active_tickers_database_error(self):
        """Test handling of database errors"""
        self.mock_db.execute_query.side_effect = Exception("Database error")
        
        tickers = self.manager.get_active_tickers()
        
        self.assertEqual(tickers, [])
    
    def test_check_api_rate_limits_with_service(self):
        """Test API rate limit checking with service manager"""
        mock_service_manager = Mock()
        mock_finnhub_service = Mock()
        mock_rate_limiter = Mock()
        
        mock_service_manager.get_service.return_value = mock_finnhub_service
        mock_finnhub_service.rate_limiter = mock_rate_limiter
        mock_rate_limiter.get_remaining_calls.return_value = 10
        
        result = self.manager.check_api_rate_limits(mock_service_manager)
        
        self.assertTrue(result)
        mock_service_manager.get_service.assert_called_once_with('finnhub')
        mock_rate_limiter.get_remaining_calls.assert_called_once_with('finnhub', 'stock/recommendation')
    
    def test_check_api_rate_limits_no_calls_remaining(self):
        """Test API rate limit checking when no calls remaining"""
        mock_service_manager = Mock()
        mock_finnhub_service = Mock()
        mock_rate_limiter = Mock()
        
        mock_service_manager.get_service.return_value = mock_finnhub_service
        mock_finnhub_service.rate_limiter = mock_rate_limiter
        mock_rate_limiter.get_remaining_calls.return_value = 0
        
        result = self.manager.check_api_rate_limits(mock_service_manager)
        
        self.assertFalse(result)
    
    def test_check_api_rate_limits_no_service_manager(self):
        """Test API rate limit checking without service manager"""
        result = self.manager.check_api_rate_limits(None)
        
        self.assertTrue(result)  # Should assume OK if we can't check
    
    def test_check_api_rate_limits_exception(self):
        """Test API rate limit checking with exception"""
        mock_service_manager = Mock()
        mock_service_manager.get_service.side_effect = Exception("Service error")
        
        result = self.manager.check_api_rate_limits(mock_service_manager)
        
        self.assertTrue(result)  # Should assume OK if we can't check
    
    @patch('analyst_scoring_manager.logger')
    def test_calculate_all_analyst_scores_no_tickers(self, mock_logger):
        """Test analyst scoring with no active tickers"""
        self.mock_db.execute_query.return_value = []
        
        result = self.manager.calculate_all_analyst_scores()
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'no_active_tickers')
        self.assertEqual(result['successful_calculations'], 0)
        self.assertEqual(result['failed_calculations'], 0)
    
    @patch('analyst_scoring_manager.logger')
    def test_calculate_all_analyst_scores_no_api_calls(self, mock_logger):
        """Test analyst scoring with no API calls remaining"""
        mock_results = [('AAPL',), ('MSFT',)]
        self.mock_db.execute_query.return_value = mock_results
        
        # Mock rate limit check to return False
        with patch.object(self.manager, 'check_api_rate_limits', return_value=False):
            result = self.manager.calculate_all_analyst_scores()
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'no_api_calls_remaining')
    
    @patch('analyst_scoring_manager.logger')
    def test_calculate_all_analyst_scores_success(self, mock_logger):
        """Test successful analyst scoring"""
        mock_results = [('AAPL',), ('MSFT',)]
        self.mock_db.execute_query.return_value = mock_results
        
        # Mock rate limit check to return True
        with patch.object(self.manager, 'check_api_rate_limits', return_value=True):
            # Mock successful processing
            with patch.object(self.manager, '_process_single_ticker') as mock_process:
                mock_process.return_value = {'success': True}
                
                result = self.manager.calculate_all_analyst_scores()
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['successful_calculations'], 2)
        self.assertEqual(result['failed_calculations'], 0)
        self.assertEqual(result['total_tickers'], 2)
    
    @patch('analyst_scoring_manager.logger')
    def test_calculate_all_analyst_scores_mixed_results(self, mock_logger):
        """Test analyst scoring with mixed success/failure"""
        mock_results = [('AAPL',), ('MSFT',), ('INVALID',)]
        self.mock_db.execute_query.return_value = mock_results
        
        # Mock rate limit check to return True
        with patch.object(self.manager, 'check_api_rate_limits', return_value=True):
            # Mock mixed processing results
            with patch.object(self.manager, '_process_single_ticker') as mock_process:
                mock_process.side_effect = [
                    {'success': True},   # AAPL
                    {'success': False},  # MSFT
                    {'success': True}    # INVALID
                ]
                
                result = self.manager.calculate_all_analyst_scores()
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['successful_calculations'], 2)
        self.assertEqual(result['failed_calculations'], 1)
        self.assertEqual(result['total_tickers'], 3)
    
    @patch('analyst_scoring_manager.logger')
    def test_calculate_all_analyst_scores_exception(self, mock_logger):
        """Test analyst scoring with exception"""
        # Mock get_active_tickers to raise an exception directly
        with patch.object(self.manager, 'get_active_tickers', side_effect=Exception("Database error")):
            result = self.manager.calculate_all_analyst_scores()
        
        self.assertEqual(result['status'], 'failed')
        self.assertIn('reason', result)
        self.assertEqual(result['reason'], 'Database error')
    
    def test_process_single_ticker_success(self):
        """Test successful processing of single ticker"""
        with patch.object(self.manager.analyst_scorer, 'calculate_analyst_score') as mock_calc:
            with patch.object(self.manager.analyst_scorer, 'store_analyst_score') as mock_store:
                mock_calc.return_value = {'calculation_status': 'success'}
                mock_store.return_value = True
                
                result = self.manager._process_single_ticker('AAPL', 1, 1)
        
        self.assertTrue(result['success'])
    
    def test_process_single_ticker_calculation_failed(self):
        """Test processing of ticker with failed calculation"""
        with patch.object(self.manager.analyst_scorer, 'calculate_analyst_score') as mock_calc:
            mock_calc.return_value = {'calculation_status': 'failed'}
            
            result = self.manager._process_single_ticker('AAPL', 1, 1)
        
        self.assertFalse(result['success'])
    
    def test_process_single_ticker_storage_failed(self):
        """Test processing of ticker with failed storage"""
        with patch.object(self.manager.analyst_scorer, 'calculate_analyst_score') as mock_calc:
            with patch.object(self.manager.analyst_scorer, 'store_analyst_score') as mock_store:
                mock_calc.return_value = {'calculation_status': 'success'}
                mock_store.return_value = False
                
                result = self.manager._process_single_ticker('AAPL', 1, 1)
        
        self.assertFalse(result['success'])
    
    def test_process_single_ticker_exception(self):
        """Test processing of ticker with exception"""
        with patch.object(self.manager.analyst_scorer, 'calculate_analyst_score') as mock_calc:
            mock_calc.side_effect = Exception("Calculation error")
            
            result = self.manager._process_single_ticker('AAPL', 1, 1)
        
        self.assertFalse(result['success'])
    
    def test_create_result_completed(self):
        """Test result creation for completed status"""
        result = self.manager._create_result(
            'completed', 
            start_time=100.0, 
            successful=5, 
            failed=1, 
            total=6
        )
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['successful_calculations'], 5)
        self.assertEqual(result['failed_calculations'], 1)
        self.assertEqual(result['total_tickers'], 6)
        self.assertIn('processing_time', result)
    
    def test_create_result_skipped(self):
        """Test result creation for skipped status"""
        result = self.manager._create_result('skipped', 'no_tickers')
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'no_tickers')
        self.assertNotIn('processing_time', result)


if __name__ == '__main__':
    unittest.main()
