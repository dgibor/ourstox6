#!/usr/bin/env python3
"""
Diagnostic script to identify why overall scores are always 0.0
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def diagnose_overall_score_issue():
    """Diagnose the overall score calculation issue"""
    
    logger.info("Diagnosing Overall Score Calculation Issue")
    logger.info("=" * 60)
    
    try:
        # Import scoring calculators
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        from calc_fundamental_scores import FundamentalScoreCalculator
        from calc_technical_scores import TechnicalScoreCalculator
        
        # Initialize calculators
        fundamental_calc = FundamentalScoreCalculator()
        technical_calc = TechnicalScoreCalculator()
        
        # Test with a few tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        for ticker in test_tickers:
            logger.info(f"\nAnalyzing {ticker}:")
            logger.info("-" * 40)
            
            # Calculate fundamental scores
            fundamental_scores = fundamental_calc.calculate_fundamental_scores(ticker)
            
            if fundamental_scores.get('error'):
                logger.error(f"Fundamental calculation failed: {fundamental_scores['error']}")
                continue
            
            # Calculate technical scores
            technical_scores = technical_calc.calculate_technical_scores(ticker)
            
            if technical_scores.get('error'):
                logger.error(f"Technical calculation failed: {technical_scores['error']}")
                continue
            
            # Log individual scores
            logger.info("Individual Scores:")
            logger.info(f"  Fundamental Health: {fundamental_scores.get('fundamental_health_score', 'N/A')}")
            logger.info(f"  Value Investment: {fundamental_scores.get('value_investment_score', 'N/A')}")
            logger.info(f"  Fundamental Risk: {fundamental_scores.get('fundamental_risk_score', 'N/A')}")
            logger.info(f"  Technical Health: {technical_scores.get('technical_health_score', 'N/A')}")
            logger.info(f"  Trading Signal: {technical_scores.get('trading_signal_score', 'N/A')}")
            logger.info(f"  Technical Risk: {technical_scores.get('technical_risk_score', 'N/A')}")
            logger.info(f"  Overall Score: {fundamental_scores.get('overall_score', 'N/A')}")
            logger.info(f"  Overall Grade: {fundamental_scores.get('overall_grade', 'N/A')}")
            
            # Check if any scores are None or 0
            scores_to_check = [
                ('fundamental_health_score', fundamental_scores),
                ('value_investment_score', fundamental_scores),
                ('fundamental_risk_score', fundamental_scores),
                ('technical_health_score', technical_scores),
                ('trading_signal_score', technical_scores),
                ('technical_risk_score', technical_scores),
                ('overall_score', fundamental_scores)
            ]
            
            logger.info("\nScore Analysis:")
            for score_name, score_dict in scores_to_check:
                score_value = score_dict.get(score_name)
                if score_value is None:
                    logger.warning(f"  {score_name}: None (missing)")
                elif score_value == 0:
                    logger.warning(f"  {score_name}: 0 (zero)")
                else:
                    logger.info(f"  {score_name}: {score_value} (OK)")
            
            # Check the overall score calculation logic
            logger.info("\nOverall Score Calculation Analysis:")
            
            # Get the individual components
            fh_score = fundamental_scores.get('fundamental_health_score', 0)
            vi_score = fundamental_scores.get('value_investment_score', 0)
            fr_score = fundamental_scores.get('fundamental_risk_score', 0)
            th_score = technical_scores.get('technical_health_score', 0)
            ts_score = technical_scores.get('trading_signal_score', 0)
            tr_score = technical_scores.get('technical_risk_score', 0)
            
            # Calculate what the overall score should be
            if all(isinstance(x, (int, float)) for x in [fh_score, vi_score, fr_score, th_score, ts_score, tr_score]):
                # Match the actual implementation: fundamental-only weighted average
                overall_calc = (
                    fh_score * 0.4 +
                    vi_score * 0.3 +
                    (100 - fr_score) * 0.3  # Invert risk score (lower risk = higher score)
                )
                
                logger.info(f"  Calculated Overall Score: {overall_calc:.2f}")
                logger.info(f"  Actual Overall Score: {fundamental_scores.get('overall_score', 'N/A')}")
                
                if overall_calc != fundamental_scores.get('overall_score', 0):
                    logger.error(f"  MISMATCH: Calculated {overall_calc:.2f} vs Actual {fundamental_scores.get('overall_score', 'N/A')}")
                else:
                    logger.info("  MATCH: Overall score calculation is correct")
            else:
                logger.error("  ERROR: Cannot calculate overall score due to non-numeric components")
        
        logger.info("\n" + "="*60)
        logger.info("Diagnosis Complete")
        
    except Exception as e:
        logger.error(f"Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_overall_score_issue()
