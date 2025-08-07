#!/usr/bin/env python3
"""
Enhanced API Data Filler
Fetches missing fundamental data from multiple APIs to improve data confidence
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

from yahoo_finance_service import YahooFinanceService
from alpha_vantage_service import AlphaVantageService
from fmp_service import FMPService

class EnhancedAPIDataFiller:
    """Enhanced API integration for filling missing fundamental data"""
    
    def __init__(self):
        self.yahoo_api = YahooFinanceService()
        self.alpha_vantage_api = AlphaVantageService()
        self.fmp_api = FMPService()
        
        # Validation rules for fundamental ratios
        self.validation_rules = {
            'pe_ratio': (0, 1000),
            'pb_ratio': (0, 100),
            'roe': (-100, 100),
            'debt_to_equity': (0, 10),
            'current_ratio': (0, 10),
            'quick_ratio': (0, 10),
            'profit_margin': (-100, 100),
            'revenue_growth': (-100, 100),
            'earnings_growth': (-100, 100),
            'dividend_yield': (0, 50),
            'beta': (0, 5)
        }
        
        # API priority order (most reliable first)
        self.api_priority = ['yahoo', 'fmp', 'alpha_vantage']
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def fill_missing_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """Fill missing fundamental ratios using multiple APIs"""
        self.logger.info(f"Filling missing data for {ticker}")
        
        missing_data = {}
        
        # Get current fundamental data from database
        current_data = self.get_current_fundamental_data(ticker)
        
        # Identify missing metrics
        missing_metrics = self.identify_missing_metrics(current_data)
        
        if not missing_metrics:
            self.logger.info(f"No missing metrics for {ticker}")
            return missing_data
        
        self.logger.info(f"Missing metrics for {ticker}: {missing_metrics}")
        
        # Fill missing data from APIs
        for metric in missing_metrics:
            api_data = self.fetch_metric_from_apis(ticker, metric)
            if api_data:
                missing_data[metric] = api_data
                self.logger.info(f"Filled {metric} for {ticker}: {api_data}")
            else:
                self.logger.warning(f"Could not fill {metric} for {ticker}")
        
        return missing_data
    
    def get_current_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """Get current fundamental data from database"""
        # This would integrate with existing database queries
        # For now, return empty dict to simulate missing data
        return {}
    
    def identify_missing_metrics(self, current_data: Dict[str, Any]) -> List[str]:
        """Identify which fundamental metrics are missing"""
        required_metrics = [
            'pe_ratio', 'pb_ratio', 'roe', 'debt_to_equity', 
            'current_ratio', 'quick_ratio', 'profit_margin',
            'revenue_growth', 'earnings_growth', 'dividend_yield', 'beta'
        ]
        
        missing = []
        for metric in required_metrics:
            if metric not in current_data or current_data[metric] is None:
                missing.append(metric)
        
        return missing
    
    def fetch_metric_from_apis(self, ticker: str, metric: str) -> Optional[float]:
        """Fetch specific metric from multiple APIs with fallback"""
        apis = [
            (self.yahoo_api, 'yahoo'),
            (self.fmp_api, 'fmp'),
            (self.alpha_vantage_api, 'alpha_vantage')
        ]
        
        for api, source in self.api_priority:
            try:
                api_instance = next(api_obj for api_obj, name in apis if name == source)
                value = self.get_metric_from_api(api_instance, ticker, metric)
                
                if value and self.validate_ratio_value(value, metric):
                    self.logger.info(f"Successfully fetched {metric} from {source}: {value}")
                    return value
                    
            except Exception as e:
                self.logger.warning(f"Failed to fetch {metric} from {source}: {str(e)}")
                continue
        
        return None
    
    def get_metric_from_api(self, api_instance, ticker: str, metric: str) -> Optional[float]:
        """Get specific metric from API instance"""
        try:
            if hasattr(api_instance, f'get_{metric}'):
                method = getattr(api_instance, f'get_{metric}')
                return method(ticker)
            elif hasattr(api_instance, 'get_fundamental_ratio'):
                return api_instance.get_fundamental_ratio(ticker, metric)
            elif hasattr(api_instance, 'get_fundamental_data'):
                data = api_instance.get_fundamental_data(ticker)
                return data.get(metric)
            else:
                self.logger.warning(f"API instance does not have method for {metric}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting {metric} from API: {str(e)}")
            return None
    
    def validate_ratio_value(self, value: float, metric: str) -> bool:
        """Validate ratio values are within reasonable ranges"""
        if value is None:
            return False
        
        if metric in self.validation_rules:
            min_val, max_val = self.validation_rules[metric]
            if not (min_val <= value <= max_val):
                self.logger.warning(f"{metric} value {value} outside valid range [{min_val}, {max_val}]")
                return False
        
        return True
    
    def cross_validate_data(self, ticker: str, data_sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Cross-validate data between multiple sources"""
        validated_data = {}
        confidence_scores = {}
        
        for metric in self.validation_rules.keys():
            values = []
            sources = []
            
            # Collect values from all sources
            for source_name, source_data in data_sources.items():
                if metric in source_data and source_data[metric] is not None:
                    values.append(source_data[metric])
                    sources.append(source_name)
            
            if len(values) >= 2:
                # Calculate variance and confidence
                variance = self.calculate_variance(values)
                confidence = self.calculate_confidence(variance, len(values))
                
                # Use weighted average if variance is acceptable
                if variance <= 0.3:  # 30% variance threshold
                    validated_data[metric] = self.weighted_average(values, sources)
                    confidence_scores[metric] = confidence
                else:
                    # Use most reliable source
                    best_source_idx = self.select_best_source(sources)
                    validated_data[metric] = values[best_source_idx]
                    confidence_scores[metric] = 0.7  # Reduced confidence for variance
        
        return {
            'validated_data': validated_data,
            'confidence_scores': confidence_scores,
            'overall_confidence': sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        }
    
    def calculate_variance(self, values: List[float]) -> float:
        """Calculate coefficient of variation"""
        if not values or len(values) < 2:
            return float('inf')
        
        mean = sum(values) / len(values)
        if mean == 0:
            return float('inf')
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return (variance ** 0.5) / abs(mean)
    
    def calculate_confidence(self, variance: float, num_sources: int) -> float:
        """Calculate confidence score based on variance and number of sources"""
        base_confidence = 1.0 - min(variance, 1.0)
        source_bonus = min((num_sources - 1) * 0.1, 0.2)
        return min(base_confidence + source_bonus, 1.0)
    
    def weighted_average(self, values: List[float], sources: List[str]) -> float:
        """Calculate weighted average based on source reliability"""
        # Simple average for now - could be enhanced with source-specific weights
        return sum(values) / len(values)
    
    def select_best_source(self, sources: List[str]) -> int:
        """Select the most reliable source based on priority"""
        for priority_source in self.api_priority:
            if priority_source in sources:
                return sources.index(priority_source)
        return 0  # Default to first source
    
    def update_database_with_filled_data(self, ticker: str, filled_data: Dict[str, Any]) -> bool:
        """Update database with filled fundamental data"""
        try:
            # This would integrate with existing database update methods
            # For now, just log the update
            self.logger.info(f"Would update database for {ticker} with: {filled_data}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update database for {ticker}: {str(e)}")
            return False
    
    def get_data_quality_report(self, ticker: str) -> Dict[str, Any]:
        """Generate data quality report for a ticker"""
        current_data = self.get_current_fundamental_data(ticker)
        missing_metrics = self.identify_missing_metrics(current_data)
        
        total_metrics = len(self.validation_rules)
        filled_metrics = total_metrics - len(missing_metrics)
        confidence = filled_metrics / total_metrics
        
        return {
            'ticker': ticker,
            'total_metrics': total_metrics,
            'filled_metrics': filled_metrics,
            'missing_metrics': missing_metrics,
            'confidence': confidence,
            'data_quality': self.get_quality_grade(confidence)
        }
    
    def get_quality_grade(self, confidence: float) -> str:
        """Get quality grade based on confidence level"""
        if confidence >= 0.9:
            return 'Excellent'
        elif confidence >= 0.8:
            return 'Good'
        elif confidence >= 0.7:
            return 'Fair'
        elif confidence >= 0.6:
            return 'Poor'
        else:
            return 'Very Poor'

def main():
    """Test the enhanced API data filler"""
    filler = EnhancedAPIDataFiller()
    
    # Test with a few tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\n🔍 Testing {ticker}:")
        
        # Get data quality report
        report = filler.get_data_quality_report(ticker)
        print(f"  Data Quality: {report['data_quality']} ({report['confidence']:.1%})")
        print(f"  Missing Metrics: {len(report['missing_metrics'])}")
        
        # Try to fill missing data
        if report['missing_metrics']:
            filled_data = filler.fill_missing_fundamental_data(ticker)
            print(f"  Filled Data: {filled_data}")
        else:
            print("  No missing data to fill")

if __name__ == "__main__":
    main() 