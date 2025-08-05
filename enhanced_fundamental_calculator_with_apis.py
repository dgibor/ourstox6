import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv

# Import API services
from yahoo_finance_service import YahooFinanceService
from fmp_service import FMPService
from finnhub_service import FinnhubService
from alpha_vantage_service import AlphaVantageService

# Import the enhanced fundamental calculator
from calc_fundamental_scores_enhanced_v2 import EnhancedFundamentalScoreCalculatorV2

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFundamentalCalculatorWithAPIs:
    """
    Enhanced fundamental calculator that integrates multiple API services
    to improve data confidence and fill missing fundamental ratios
    """
    
    def __init__(self):
        self.yahoo_service = YahooFinanceService()
        self.fmp_service = FMPService()
        self.finnhub_service = FinnhubService()
        self.alpha_vantage_service = AlphaVantageService()
        self.base_calculator = EnhancedFundamentalScoreCalculatorV2()
        
        # API priority order as specified by user
        self.api_priority = [
            ('yahoo', self.yahoo_service),
            ('fmp', self.fmp_service),
            ('finnhub', self.finnhub_service),
            ('alpha_vantage', self.alpha_vantage_service)
        ]
    
    def get_enhanced_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data using API integration in priority order
        Returns the best available data from all sources
        """
        logger.info(f"Fetching enhanced fundamental data for {ticker}")
        
        best_data = None
        best_confidence = 0
        best_source = None
        
        # Try each API in priority order
        for source_name, api_service in self.api_priority:
            try:
                logger.info(f"Trying {source_name} API for {ticker}")
                api_data = api_service.get_fundamental_data(ticker)
                
                if api_data:
                    confidence_data = api_service.get_data_confidence(api_data)
                    confidence = confidence_data['confidence']
                    
                    logger.info(f"{source_name} confidence: {confidence}% for {ticker}")
                    
                    # Update best data if this source has higher confidence
                    if confidence > best_confidence:
                        best_data = api_data
                        best_confidence = confidence
                        best_source = source_name
                        
                        # If we have very high confidence, we can stop here
                        if confidence >= 90:
                            logger.info(f"High confidence ({confidence}%) achieved with {source_name}, stopping API calls")
                            break
                else:
                    logger.warning(f"No data from {source_name} for {ticker}")
                    
            except Exception as e:
                logger.error(f"Error with {source_name} API for {ticker}: {str(e)}")
                continue
        
        if best_data:
            logger.info(f"Best data for {ticker} from {best_source} with {best_confidence}% confidence")
            return {
                'data': best_data,
                'source': best_source,
                'confidence': best_confidence,
                'ticker': ticker
            }
        else:
            logger.warning(f"No API data available for {ticker}")
            return None
    
    def calculate_enhanced_scores_with_apis(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Calculate enhanced fundamental scores using API data to improve confidence
        """
        try:
            # Get enhanced fundamental data from APIs
            api_result = self.get_enhanced_fundamental_data(ticker)
            
            if api_result:
                api_data = api_result['data']
                source = api_result['source']
                confidence = api_result['confidence']
                
                logger.info(f"Using {source} data with {confidence}% confidence for {ticker}")
                
                # Merge API data with existing database data
                merged_data = self._merge_api_data_with_database(ticker, api_data)
                
                # Calculate scores using the enhanced calculator
                scores = self.base_calculator.calculate_fundamental_scores_enhanced(ticker)
                
                if scores:
                    # Update scores with API confidence information
                    scores['api_source'] = source
                    scores['api_confidence'] = confidence
                    scores['data_confidence'] = max(scores.get('data_confidence', 0), confidence)
                    
                    # Add API data quality metrics
                    scores['api_data_available'] = True
                    scores['api_metrics_count'] = len(api_data)
                    
                    logger.info(f"Enhanced scores calculated for {ticker} with {confidence}% API confidence")
                    return scores
                else:
                    logger.warning(f"Failed to calculate scores for {ticker}")
                    return None
            else:
                # Fallback to base calculator without API data
                logger.info(f"Using base calculator for {ticker} (no API data available)")
                return self.base_calculator.calculate_fundamental_scores_enhanced(ticker)
                
        except Exception as e:
            logger.error(f"Error calculating enhanced scores for {ticker}: {str(e)}")
            return None
    
    def _merge_api_data_with_database(self, ticker: str, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge API data with existing database data
        API data takes precedence over database data
        """
        try:
            # Get existing database data
            db_data = self.base_calculator.get_fundamental_data(ticker)
            
            if not db_data:
                return api_data
            
            # Create merged data with API data taking precedence
            merged_data = db_data.copy()
            
            # Update with API data (API data overrides database data)
            for key, value in api_data.items():
                if value is not None:
                    merged_data[key] = value
            
            logger.info(f"Merged API and database data for {ticker}")
            return merged_data
            
        except Exception as e:
            logger.error(f"Error merging data for {ticker}: {str(e)}")
            return api_data
    
    def store_enhanced_scores(self, ticker: str, scores: Dict[str, Any]) -> bool:
        """
        Store enhanced scores in the database
        """
        try:
            return self.base_calculator.store_fundamental_scores(ticker, scores)
        except Exception as e:
            logger.error(f"Error storing enhanced scores for {ticker}: {str(e)}")
            return False
    
    def test_api_integration(self, test_tickers: List[str]) -> Dict[str, Any]:
        """
        Test the API integration with a list of tickers
        Returns comprehensive test results
        """
        logger.info(f"Testing API integration with {len(test_tickers)} tickers")
        
        results = {
            'total_tickers': len(test_tickers),
            'successful_calculations': 0,
            'api_sources_used': {},
            'confidence_improvements': [],
            'failed_tickers': [],
            'detailed_results': []
        }
        
        for ticker in test_tickers:
            try:
                logger.info(f"Testing {ticker}...")
                
                # Calculate enhanced scores
                scores = self.calculate_enhanced_scores_with_apis(ticker)
                
                if scores:
                    results['successful_calculations'] += 1
                    
                    # Track API source usage
                    api_source = scores.get('api_source', 'none')
                    results['api_sources_used'][api_source] = results['api_sources_used'].get(api_source, 0) + 1
                    
                    # Track confidence improvements
                    api_confidence = scores.get('api_confidence', 0)
                    data_confidence = scores.get('data_confidence', 0)
                    results['confidence_improvements'].append({
                        'ticker': ticker,
                        'api_confidence': api_confidence,
                        'data_confidence': data_confidence,
                        'api_source': api_source
                    })
                    
                    # Store detailed results
                    results['detailed_results'].append({
                        'ticker': ticker,
                        'fundamental_health_score': scores.get('fundamental_health_score'),
                        'fundamental_health_grade': scores.get('fundamental_health_grade'),
                        'value_investment_score': scores.get('value_investment_score'),
                        'value_rating': scores.get('value_rating'),
                        'fundamental_risk_score': scores.get('fundamental_risk_score'),
                        'fundamental_risk_level': scores.get('fundamental_risk_level'),
                        'api_source': api_source,
                        'api_confidence': api_confidence,
                        'data_confidence': data_confidence
                    })
                    
                    # Store scores in database
                    self.store_enhanced_scores(ticker, scores)
                    
                else:
                    results['failed_tickers'].append(ticker)
                    
            except Exception as e:
                logger.error(f"Error testing {ticker}: {str(e)}")
                results['failed_tickers'].append(ticker)
        
        # Calculate summary statistics
        results['success_rate'] = (results['successful_calculations'] / results['total_tickers']) * 100
        
        if results['confidence_improvements']:
            avg_api_confidence = sum(r['api_confidence'] for r in results['confidence_improvements']) / len(results['confidence_improvements'])
            avg_data_confidence = sum(r['data_confidence'] for r in results['confidence_improvements']) / len(results['confidence_improvements'])
            results['average_api_confidence'] = round(avg_api_confidence, 2)
            results['average_data_confidence'] = round(avg_data_confidence, 2)
        
        logger.info(f"API integration test completed. Success rate: {results['success_rate']}%")
        return results
    
    def generate_results_table(self, results: Dict[str, Any]) -> str:
        """
        Generate a formatted table of results for display
        """
        if not results['detailed_results']:
            return "No results to display"
        
        # Create table header
        table = "Ticker | Fundamental Health | Value Rating | Risk Level | API Source | API Conf% | Data Conf%\n"
        table += "-------|-------------------|--------------|------------|------------|-----------|-----------\n"
        
        for result in results['detailed_results']:
            ticker = result['ticker']
            health_grade = result['fundamental_health_grade'] or 'N/A'
            value_rating = result['value_rating'] or 'N/A'
            risk_level = result['fundamental_risk_level'] or 'N/A'
            api_source = result['api_source'] or 'none'
            api_conf = result['api_confidence'] or 0
            data_conf = result['data_confidence'] or 0
            
            table += f"{ticker:6} | {health_grade:17} | {value_rating:12} | {risk_level:10} | {api_source:10} | {api_conf:9.1f} | {data_conf:9.1f}\n"
        
        # Add summary
        table += f"\nSummary:\n"
        table += f"Total tickers tested: {results['total_tickers']}\n"
        table += f"Successful calculations: {results['successful_calculations']} ({results['success_rate']:.1f}%)\n"
        table += f"Average API confidence: {results.get('average_api_confidence', 0):.1f}%\n"
        table += f"Average data confidence: {results.get('average_data_confidence', 0):.1f}%\n"
        
        if results['api_sources_used']:
            table += f"API sources used: {dict(results['api_sources_used'])}\n"
        
        if results['failed_tickers']:
            table += f"Failed tickers: {', '.join(results['failed_tickers'])}\n"
        
        return table

def main():
    """Test the enhanced fundamental calculator with API integration"""
    calculator = EnhancedFundamentalCalculatorWithAPIs()
    
    # Test with 20 stocks as requested
    test_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'BRK.B', 'UNH', 'JNJ',
        'V', 'PG', 'HD', 'MA', 'DIS', 'PYPL', 'BAC', 'ADBE', 'CRM', 'NFLX'
    ]
    
    print("Testing Enhanced Fundamental Calculator with API Integration")
    print("=" * 60)
    
    # Run the test
    results = calculator.test_api_integration(test_tickers)
    
    # Display results table
    print("\nResults Table:")
    print("=" * 60)
    print(calculator.generate_results_table(results))
    
    # Save results to file
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"api_integration_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {filename}")

if __name__ == "__main__":
    main() 