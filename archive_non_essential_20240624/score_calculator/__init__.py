"""
Score Calculator Package

A comprehensive scoring system for stock analysis that calculates:
- Technical scores using existing indicators from daily_charts
- Fundamental scores using existing ratios from financial_ratios  
- Analyst scores using earnings calendar and analyst data

The system prioritizes stocks by earnings proximity and maintains
100 days of historical scores with data quality tracking.
"""

from .database_manager import ScoreDatabaseManager
from .schema_manager import ScoreSchemaManager
from .technical_scorer import TechnicalScorer
from .fundamental_scorer import FundamentalScorer
from .analyst_scorer import AnalystScorer
from .score_orchestrator import ScoreOrchestrator

__all__ = [
    'ScoreDatabaseManager',
    'ScoreSchemaManager', 
    'TechnicalScorer',
    'FundamentalScorer',
    'AnalystScorer',
    'ScoreOrchestrator'
]

__version__ = '1.0.0' 