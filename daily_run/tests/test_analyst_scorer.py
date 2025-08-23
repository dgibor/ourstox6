#!/usr/bin/env python3
"""
Unit tests for AnalystScorer

Tests all functionality including edge cases and error conditions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyst_scorer import AnalystScorer
from database import DatabaseManager


class TestAnalystScorer(unittest.TestCase):
    """Test cases for AnalystScorer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock(spec=DatabaseManager)
        self.mock_db.connection = Mock()
        self.mock_db.execute_query = Mock()
        
        # Mock cursor and connection
        self.mock_cursor = Mock()
        self.mock_db.connection.cursor.return_value = self.mock_cursor
        
        self.scorer = AnalystScorer(db=self.mock_db)
    
    def test_init(self):
        """Test scorer initialization"""
        self.assertIsNotNone(self.scorer.db)
        self.assertIsNotNone(self.scorer.industry_analyst_adjustments)
        self.assertIsNotNone(self.scorer.qualitative_analyst_bonuses)
    
    def test_ensure_database_schema_success(self):
        """Test successful database schema creation"""
        # Mock successful database operations
        self.mock_cursor.execute.return_value = None
        self.mock_db.connection.commit.return_value = None
        
        # Re-initialize to trigger schema creation
        scorer = AnalystScorer(db=self.mock_db)
        
        # Verify schema creation calls were made
        self.mock_cursor.execute.assert_called()
        self.mock_db.connection.commit.assert_called()
    
    def test_ensure_database_schema_failure(self):
        """Test database schema creation failure"""
        # Mock database operation failure
        self.mock_cursor.execute.side_effect = Exception("Schema error")
        
        # Should not raise exception, should handle gracefully
        try:
            scorer = AnalystScorer(db=self.mock_db)
        except Exception:
            self.fail("AnalystScorer should handle schema creation errors gracefully")
    
    def test_get_analyst_recommendations_fallback(self):
        """Test fallback to database when external service fails"""
        # Mock database fallback
        with patch.object(self.scorer, '_get_analyst_recommendations_from_db') as mock_db_fallback:
            mock_db_fallback.return_value = {'buy_count': 3, 'hold_count': 2}
            
            result = self.scorer.get_analyst_recommendations('AAPL')
            
            self.assertIsNotNone(result)
            mock_db_fallback.assert_called_once_with('AAPL')
    
    def test_get_analyst_recommendations_database_fallback(self):
        """Test database fallback data structure"""
        result = self.scorer._get_analyst_recommendations_from_db('AAPL')
        
        self.assertIsNotNone(result)
        self.assertIn('buy_count', result)
        self.assertIn('hold_count', result)
        self.assertIn('sell_count', result)
        self.assertIn('strong_buy_count', result)
        self.assertIn('strong_sell_count', result)
        self.assertIn('price_target', result)
        self.assertIn('revision_count', result)
    
    def test_calculate_earnings_proximity_score(self):
        """Test earnings proximity score calculation"""
        # Mock earnings calendar data
        mock_earnings_data = {
            'earnings_calendar': [
                {'date': '2024-01-15', 'quarter': 4, 'year': 2023},
                {'date': '2024-04-15', 'quarter': 1, 'year': 2024}
            ]
        }
        
        score = self.scorer.calculate_earnings_proximity_score(mock_earnings_data)
        
        # Should return a score between 0-100
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_earnings_proximity_score_no_data(self):
        """Test earnings proximity score with no data"""
        mock_earnings_data = {}
        
        score = self.scorer.calculate_earnings_proximity_score(mock_earnings_data)
        
        # Should return default score
        self.assertEqual(score, 50)
    
    def test_calculate_earnings_surprise_score(self):
        """Test earnings surprise score calculation"""
        # Mock earnings data
        mock_earnings_data = {
            'earnings_calendar': [
                {'actual': 1.50, 'estimate': 1.45, 'surprise': 0.05},
                {'actual': 1.20, 'estimate': 1.25, 'surprise': -0.05}
            ]
        }
        
        score = self.scorer.calculate_earnings_surprise_score(mock_earnings_data)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_analyst_sentiment_score(self):
        """Test analyst sentiment score calculation"""
        mock_recommendations = {
            'buy_count': 8,
            'hold_count': 2,
            'sell_count': 1,
            'strong_buy_count': 3,
            'strong_sell_count': 0
        }
        
        score = self.scorer.calculate_analyst_sentiment_score(mock_recommendations)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_price_target_score(self):
        """Test price target score calculation"""
        mock_recommendations = {
            'price_target': 150.0,
            'price_target_percent': 0.20
        }
        
        current_price = 125.0
        
        score = self.scorer.calculate_price_target_score(mock_recommendations, current_price)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_revision_score(self):
        """Test revision score calculation"""
        mock_recommendations = {
            'revision_count': 5
        }
        
        score = self.scorer.calculate_revision_score(mock_recommendations)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_composite_analyst_score(self):
        """Test composite analyst score calculation"""
        mock_scores = {
            'earnings_proximity': 75,
            'earnings_surprise': 80,
            'analyst_sentiment': 85,
            'price_target': 70,
            'revision': 90
        }
        
        score = self.scorer.calculate_composite_analyst_score(mock_scores)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_analyst_score_success(self):
        """Test successful analyst score calculation"""
        # Mock all the required methods
        with patch.object(self.scorer, 'get_analyst_recommendations') as mock_recs:
            with patch.object(self.scorer, 'get_earnings_calendar_data') as mock_earnings:
                with patch.object(self.scorer, 'get_current_price') as mock_price:
                    mock_recs.return_value = {
                        'buy_count': 5, 'hold_count': 2, 'sell_count': 1,
                        'price_target': 150.0, 'revision_count': 3
                    }
                    mock_earnings.return_value = {
                        'earnings_calendar': [
                            {'date': '2024-01-15', 'actual': 1.50, 'estimate': 1.45}
                        ]
                    }
                    mock_price.return_value = 125.0
                    
                    result = self.scorer.calculate_analyst_score('AAPL')
                    
                    self.assertIsNotNone(result)
                    self.assertEqual(result['calculation_status'], 'success')
                    self.assertIn('composite_analyst_score', result)
                    self.assertIn('earnings_proximity_score', result)
    
    def test_calculate_analyst_score_failure(self):
        """Test analyst score calculation failure"""
        # Mock failure in recommendations
        with patch.object(self.scorer, 'get_analyst_recommendations') as mock_recs:
            mock_recs.side_effect = Exception("Data error")
            
            result = self.scorer.calculate_analyst_score('AAPL')
            
            self.assertIsNotNone(result)
            self.assertEqual(result['calculation_status'], 'failed')
    
    def test_store_analyst_score_success(self):
        """Test successful analyst score storage"""
        mock_scores = {
            'analyst_score': 85.5,
            'analyst_components': {'component1': 80, 'component2': 90}
        }
        
        # Mock successful database operations
        self.mock_cursor.execute.return_value = None
        self.mock_db.connection.commit.return_value = None
        
        result = self.scorer.store_analyst_score('AAPL', mock_scores)
        
        self.assertTrue(result)
        self.mock_cursor.execute.assert_called()
        self.mock_db.connection.commit.assert_called()
    
    def test_store_analyst_score_failure(self):
        """Test analyst score storage failure"""
        mock_scores = {
            'analyst_score': 85.5,
            'analyst_components': {'component1': 80, 'component2': 90}
        }
        
        # Mock database operation failure
        self.mock_cursor.execute.side_effect = Exception("Storage error")
        
        result = self.scorer.store_analyst_score('AAPL', mock_scores)
        
        self.assertFalse(result)
    
    def test_get_industry_adjustment(self):
        """Test industry adjustment retrieval"""
        ticker = 'AAPL'
        
        adjustment = self.scorer._get_industry_adjustment(ticker)
        
        self.assertIsInstance(adjustment, int)
        self.assertGreaterEqual(adjustment, 0)
    
    def test_get_qualitative_bonus(self):
        """Test qualitative bonus retrieval"""
        ticker = 'AAPL'
        
        bonus = self.scorer._get_qualitative_bonus(ticker)
        
        self.assertIsInstance(bonus, int)
        self.assertGreaterEqual(bonus, 0)


if __name__ == '__main__':
    unittest.main()
