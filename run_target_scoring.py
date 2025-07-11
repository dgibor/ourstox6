#!/usr/bin/env python3
"""
Run scoring for target tickers
"""

import logging
from datetime import date
from daily_run.score_calculator.score_orchestrator import ScoreOrchestrator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_target_scoring():
    """Run scoring for target tickers"""
    
    # Target tickers
    target_tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    
    print(f"Starting scoring for target tickers: {', '.join(target_tickers)}")
    
    # Initialize orchestrator
    orchestrator = ScoreOrchestrator()
    
    # Set calculation date to today
    calculation_date = date.today()
    
    # Run scoring batch
    print(f"Running scoring batch for {len(target_tickers)} tickers...")
    result = orchestrator.run_scoring_batch(
        tickers=target_tickers,
        calculation_date=calculation_date,
        force_recalculate=True,  # Force recalculation to ensure fresh data
        max_time_hours=2
    )
    
    # Print results
    print("\n=== SCORING RESULTS ===")
    print(f"Success: {result.get('success', False)}")
    print(f"Processed: {result.get('processed_count', 0)}/{result.get('total_count', 0)}")
    
    if 'technical_success_rate' in result:
        print(f"Technical Success Rate: {result['technical_success_rate']:.2%}")
        print(f"Fundamental Success Rate: {result['fundamental_success_rate']:.2%}")
        print(f"Analyst Success Rate: {result['analyst_success_rate']:.2%}")
        print(f"All Scores Success Rate: {result['all_scores_success_rate']:.2%}")
    
    if 'failed_tickers' in result and result['failed_tickers']:
        print(f"Failed Tickers: {', '.join(result['failed_tickers'])}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    
    # Clean up
    orchestrator.db.disconnect()
    
    return result

if __name__ == "__main__":
    run_target_scoring() 