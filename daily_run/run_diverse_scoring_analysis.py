#!/usr/bin/env python3
"""
Comprehensive scoring analysis with AI comparison for 20 diverse tickers
"""

import sys
import os
import logging
import time
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('diverse_scoring_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 20 diverse tickers across different sectors
DIVERSE_TICKERS = [
    # Technology
    'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA',
    # Healthcare
    'JNJ', 'UNH', 'LLY', 'PFE',
    # Financial
    'JPM', 'V', 'MA',
    # Consumer
    'AMZN', 'COST', 'HD',
    # Energy
    'CVX', 'XOM',
    # Industrial
    'CAT', 'BA',
    # Communication
    'META', 'NFLX'
]

def run_scoring_analysis():
    """Run scoring analysis on diverse tickers"""
    
    logger.info("Starting Diverse Ticker Scoring Analysis")
    logger.info("=" * 60)
    
    try:
        from daily_trading_system import DailyTradingSystem
        
        # Initialize the system
        trading_system = DailyTradingSystem()
        logger.info("Successfully initialized DailyTradingSystem")
        
        # Import scoring calculators
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        from calc_fundamental_scores import FundamentalScoreCalculator
        from calc_technical_scores import TechnicalScoreCalculator
        
        # Initialize scoring calculators
        fundamental_calc = FundamentalScoreCalculator()
        technical_calc = TechnicalScoreCalculator()
        
        # Results storage
        results = []
        
        logger.info(f"Processing {len(DIVERSE_TICKERS)} diverse tickers...")
        
        for i, ticker in enumerate(DIVERSE_TICKERS, 1):
            try:
                logger.info(f"[{i}/{len(DIVERSE_TICKERS)}] Calculating scores for {ticker}...")
                
                # Calculate fundamental scores
                fundamental_scores = fundamental_calc.calculate_fundamental_scores(ticker)
                if fundamental_scores.get('error'):
                    logger.error(f"Fundamental calculation failed for {ticker}: {fundamental_scores['error']}")
                    continue
                
                # Calculate technical scores
                technical_scores = technical_calc.calculate_technical_scores(ticker)
                if technical_scores.get('error'):
                    logger.error(f"Technical calculation failed for {ticker}: {technical_scores['error']}")
                    continue
                
                # Store combined scores
                success = trading_system._store_combined_scores(ticker, fundamental_scores, technical_scores)
                
                if success:
                    # Extract key metrics
                    result = {
                        'ticker': ticker,
                        'fundamental_health_score': fundamental_scores.get('fundamental_health_score', 0),
                        'fundamental_health_grade': fundamental_scores.get('fundamental_health_grade', 'N/A'),
                        'value_investment_score': fundamental_scores.get('value_investment_score', 0),
                        'value_rating': fundamental_scores.get('value_rating', 'N/A'),
                        'fundamental_risk_score': fundamental_scores.get('fundamental_risk_score', 0),
                        'fundamental_risk_level': fundamental_scores.get('fundamental_risk_level', 'N/A'),
                        'technical_health_score': technical_scores.get('technical_health_score', 0),
                        'technical_health_grade': technical_scores.get('technical_health_grade', 'N/A'),
                        'trading_signal_score': technical_scores.get('trading_signal_score', 0),
                        'trading_signal_rating': technical_scores.get('trading_signal_rating', 'N/A'),
                        'technical_risk_score': technical_scores.get('technical_risk_score', 0),
                        'technical_risk_level': technical_scores.get('technical_risk_level', 'N/A'),
                        'overall_score': fundamental_scores.get('overall_score', 0),
                        'overall_grade': fundamental_scores.get('overall_grade', 'N/A')
                    }
                    results.append(result)
                    logger.info(f"Successfully processed {ticker}")
                else:
                    logger.error(f"Failed to store scores for {ticker}")
                    
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        logger.info(f"Completed scoring analysis for {len(results)} tickers")
        return results
        
    except Exception as e:
        logger.error(f"Error in scoring analysis: {e}")
        return []

def perform_ai_analysis():
    """Perform AI analysis as a stock analyst and expert investor"""
    
    logger.info("Performing AI Analysis as Stock Analyst")
    logger.info("=" * 60)
    
    # AI analysis based on current market knowledge and fundamental analysis
    ai_analysis = {
        'AAPL': {
            'fundamental_health': 85, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 70, 'value_rating': 'Buy',
            'risk_level': 25, 'risk_grade': 'Buy',
            'technical_health': 80, 'technical_grade': 'Strong Buy',
            'trading_signal': 75, 'signal_rating': 'Buy',
            'technical_risk': 30, 'tech_risk_grade': 'Buy',
            'overall_score': 78, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Strong fundamentals, excellent cash flow, premium valuation justified by ecosystem'
        },
        'MSFT': {
            'fundamental_health': 90, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 65, 'value_rating': 'Buy',
            'risk_level': 20, 'risk_grade': 'Strong Buy',
            'technical_health': 85, 'technical_grade': 'Strong Buy',
            'trading_signal': 80, 'signal_rating': 'Strong Buy',
            'technical_risk': 25, 'tech_risk_grade': 'Strong Buy',
            'overall_score': 82, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Cloud leader, strong AI positioning, excellent financials, premium valuation'
        },
        'GOOGL': {
            'fundamental_health': 88, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 75, 'value_rating': 'Strong Buy',
            'risk_level': 15, 'risk_grade': 'Strong Buy',
            'technical_health': 75, 'technical_grade': 'Buy',
            'trading_signal': 70, 'signal_rating': 'Buy',
            'technical_risk': 35, 'tech_risk_grade': 'Buy',
            'overall_score': 80, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Advertising recovery, AI leadership, strong balance sheet, good value'
        },
        'NVDA': {
            'fundamental_health': 95, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 40, 'value_rating': 'Neutral',
            'risk_level': 35, 'risk_grade': 'Buy',
            'technical_health': 90, 'technical_grade': 'Strong Buy',
            'trading_signal': 85, 'signal_rating': 'Strong Buy',
            'technical_risk': 40, 'tech_risk_grade': 'Buy',
            'overall_score': 85, 'overall_grade': 'Strong Buy',
            'ai_notes': 'AI chip leader, exceptional growth, high valuation, execution risk'
        },
        'TSLA': {
            'fundamental_health': 70, 'fundamental_grade': 'Buy',
            'value_assessment': 50, 'value_rating': 'Neutral',
            'risk_level': 60, 'risk_grade': 'Sell',
            'technical_health': 65, 'technical_grade': 'Buy',
            'trading_signal': 60, 'signal_rating': 'Buy',
            'technical_risk': 55, 'tech_risk_grade': 'Neutral',
            'overall_score': 65, 'overall_grade': 'Buy',
            'ai_notes': 'EV leader, execution challenges, high volatility, growth potential'
        },
        'JNJ': {
            'fundamental_health': 85, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 75, 'value_rating': 'Strong Buy',
            'risk_level': 20, 'risk_grade': 'Strong Buy',
            'technical_health': 70, 'technical_grade': 'Buy',
            'trading_signal': 65, 'signal_rating': 'Buy',
            'technical_risk': 30, 'tech_risk_grade': 'Buy',
            'overall_score': 75, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Healthcare giant, stable earnings, good dividend, litigation risks'
        },
        'UNH': {
            'fundamental_health': 75, 'fundamental_grade': 'Buy',
            'value_assessment': 70, 'value_rating': 'Buy',
            'risk_level': 40, 'risk_grade': 'Buy',
            'technical_health': 70, 'technical_grade': 'Buy',
            'trading_signal': 65, 'signal_rating': 'Buy',
            'technical_risk': 35, 'tech_risk_grade': 'Buy',
            'overall_score': 70, 'overall_grade': 'Buy',
            'ai_notes': 'Healthcare insurance leader, regulatory risks, stable business model'
        },
        'LLY': {
            'fundamental_health': 90, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 45, 'value_rating': 'Neutral',
            'risk_level': 30, 'risk_grade': 'Buy',
            'technical_health': 75, 'technical_grade': 'Buy',
            'trading_signal': 70, 'signal_rating': 'Buy',
            'technical_risk': 35, 'tech_risk_grade': 'Buy',
            'overall_score': 75, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Pharma leader, strong pipeline, high valuation, patent risks'
        },
        'PFE': {
            'fundamental_health': 70, 'fundamental_grade': 'Buy',
            'value_assessment': 80, 'value_rating': 'Strong Buy',
            'risk_level': 45, 'risk_grade': 'Neutral',
            'technical_health': 60, 'technical_grade': 'Neutral',
            'trading_signal': 55, 'signal_rating': 'Neutral',
            'technical_risk': 45, 'tech_risk_grade': 'Neutral',
            'overall_score': 65, 'overall_grade': 'Buy',
            'ai_notes': 'Post-COVID decline, good value, pipeline concerns, dividend safety'
        },
        'JPM': {
            'fundamental_health': 80, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 75, 'value_rating': 'Strong Buy',
            'risk_level': 35, 'risk_grade': 'Buy',
            'technical_health': 75, 'technical_grade': 'Buy',
            'trading_signal': 70, 'signal_rating': 'Buy',
            'technical_risk': 40, 'tech_risk_grade': 'Buy',
            'overall_score': 75, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Banking leader, strong fundamentals, interest rate beneficiary'
        },
        'V': {
            'fundamental_health': 85, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 70, 'value_rating': 'Buy',
            'risk_level': 25, 'risk_grade': 'Strong Buy',
            'technical_health': 75, 'technical_grade': 'Buy',
            'trading_signal': 70, 'signal_rating': 'Buy',
            'technical_risk': 30, 'tech_risk_grade': 'Buy',
            'overall_score': 75, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Payment processing leader, strong moat, consistent growth'
        },
        'MA': {
            'fundamental_health': 80, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 65, 'value_rating': 'Buy',
            'risk_level': 30, 'risk_grade': 'Buy',
            'technical_health': 70, 'technical_grade': 'Buy',
            'trading_signal': 65, 'signal_rating': 'Buy',
            'technical_risk': 35, 'tech_risk_grade': 'Buy',
            'overall_score': 70, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Payment network, strong fundamentals, digital payment growth'
        },
        'AMZN': {
            'fundamental_health': 85, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 75, 'value_rating': 'Strong Buy',
            'risk_level': 30, 'risk_grade': 'Buy',
            'technical_health': 80, 'technical_grade': 'Strong Buy',
            'trading_signal': 75, 'signal_rating': 'Strong Buy',
            'technical_risk': 35, 'tech_risk_grade': 'Buy',
            'overall_score': 80, 'overall_grade': 'Strong Buy',
            'ai_notes': 'E-commerce and cloud leader, strong growth, improving profitability'
        },
        'COST': {
            'fundamental_health': 85, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 60, 'value_rating': 'Buy',
            'risk_level': 25, 'risk_grade': 'Strong Buy',
            'technical_health': 75, 'technical_grade': 'Buy',
            'trading_signal': 70, 'signal_rating': 'Buy',
            'technical_risk': 30, 'tech_risk_grade': 'Buy',
            'overall_score': 75, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Retail leader, strong membership model, consistent growth'
        },
        'HD': {
            'fundamental_health': 75, 'fundamental_grade': 'Buy',
            'value_assessment': 70, 'value_rating': 'Buy',
            'risk_level': 40, 'risk_grade': 'Buy',
            'technical_health': 70, 'technical_grade': 'Buy',
            'trading_signal': 65, 'signal_rating': 'Buy',
            'technical_risk': 40, 'tech_risk_grade': 'Buy',
            'overall_score': 70, 'overall_grade': 'Buy',
            'ai_notes': 'Home improvement leader, housing market dependent, strong brand'
        },
        'CVX': {
            'fundamental_health': 70, 'fundamental_grade': 'Buy',
            'value_assessment': 75, 'value_rating': 'Strong Buy',
            'risk_level': 50, 'risk_grade': 'Neutral',
            'technical_health': 65, 'technical_grade': 'Buy',
            'trading_signal': 60, 'signal_rating': 'Buy',
            'technical_risk': 50, 'tech_risk_grade': 'Neutral',
            'overall_score': 65, 'overall_grade': 'Buy',
            'ai_notes': 'Energy major, oil price dependent, good dividend, transition risks'
        },
        'XOM': {
            'fundamental_health': 75, 'fundamental_grade': 'Buy',
            'value_assessment': 80, 'value_rating': 'Strong Buy',
            'risk_level': 55, 'risk_grade': 'Neutral',
            'technical_health': 70, 'technical_grade': 'Buy',
            'trading_signal': 65, 'signal_rating': 'Buy',
            'technical_risk': 55, 'tech_risk_grade': 'Neutral',
            'overall_score': 70, 'overall_grade': 'Buy',
            'ai_notes': 'Oil major, strong cash flow, energy transition challenges'
        },
        'CAT': {
            'fundamental_health': 75, 'fundamental_grade': 'Buy',
            'value_assessment': 70, 'value_rating': 'Buy',
            'risk_level': 45, 'risk_grade': 'Neutral',
            'technical_health': 65, 'technical_grade': 'Buy',
            'trading_signal': 60, 'signal_rating': 'Buy',
            'technical_risk': 45, 'tech_risk_grade': 'Neutral',
            'overall_score': 65, 'overall_grade': 'Buy',
            'ai_notes': 'Construction equipment, cyclical business, infrastructure spending'
        },
        'BA': {
            'fundamental_health': 60, 'fundamental_grade': 'Neutral',
            'value_assessment': 65, 'value_rating': 'Buy',
            'risk_level': 70, 'risk_grade': 'Sell',
            'technical_health': 55, 'technical_grade': 'Neutral',
            'trading_signal': 50, 'signal_rating': 'Neutral',
            'technical_risk': 65, 'tech_risk_grade': 'Sell',
            'overall_score': 55, 'overall_grade': 'Neutral',
            'ai_notes': 'Aerospace leader, safety concerns, recovery potential, high risk'
        },
        'META': {
            'fundamental_health': 85, 'fundamental_grade': 'Strong Buy',
            'value_assessment': 70, 'value_rating': 'Buy',
            'risk_level': 35, 'risk_grade': 'Buy',
            'technical_health': 80, 'technical_grade': 'Strong Buy',
            'trading_signal': 75, 'signal_rating': 'Strong Buy',
            'technical_risk': 40, 'tech_risk_grade': 'Buy',
            'overall_score': 75, 'overall_grade': 'Strong Buy',
            'ai_notes': 'Social media leader, AI investments, regulatory risks, strong growth'
        },
        'NFLX': {
            'fundamental_health': 75, 'fundamental_grade': 'Buy',
            'value_assessment': 60, 'value_rating': 'Buy',
            'risk_level': 45, 'risk_grade': 'Neutral',
            'technical_health': 70, 'technical_grade': 'Buy',
            'trading_signal': 65, 'signal_rating': 'Buy',
            'technical_risk': 45, 'tech_risk_grade': 'Neutral',
            'overall_score': 65, 'overall_grade': 'Buy',
            'ai_notes': 'Streaming leader, content costs, competition, international growth'
        }
    }
    
    logger.info("AI analysis completed")
    return ai_analysis

def create_comparison_table(scoring_results, ai_analysis):
    """Create comparison table between calculated scores and AI analysis"""
    
    logger.info("Creating Comparison Table")
    logger.info("=" * 60)
    
    comparison_data = []
    
    for result in scoring_results:
        ticker = result['ticker']
        ai_data = ai_analysis.get(ticker, {})
        
        comparison_row = {
            'Ticker': ticker,
            # Fundamental Health
            'Calc_Fund_Health': f"{result['fundamental_health_score']:.1f}",
            'AI_Fund_Health': f"{ai_data.get('fundamental_health', 'N/A')}",
            'Fund_Health_Diff': f"{result['fundamental_health_score'] - ai_data.get('fundamental_health', 0):.1f}",
            'Calc_Fund_Grade': result['fundamental_health_grade'],
            'AI_Fund_Grade': ai_data.get('fundamental_grade', 'N/A'),
            # Value Assessment
            'Calc_Value': f"{result['value_investment_score']:.1f}",
            'AI_Value': f"{ai_data.get('value_assessment', 'N/A')}",
            'Value_Diff': f"{result['value_investment_score'] - ai_data.get('value_assessment', 0):.1f}",
            'Calc_Value_Grade': result['value_rating'],
            'AI_Value_Grade': ai_data.get('value_rating', 'N/A'),
            # Risk Assessment
            'Calc_Risk': f"{result['fundamental_risk_score']:.1f}",
            'AI_Risk': f"{ai_data.get('risk_level', 'N/A')}",
            'Risk_Diff': f"{result['fundamental_risk_score'] - ai_data.get('risk_level', 0):.1f}",
            'Calc_Risk_Grade': result['fundamental_risk_level'],
            'AI_Risk_Grade': ai_data.get('risk_grade', 'N/A'),
            # Technical Health
            'Calc_Tech_Health': f"{result['technical_health_score']:.1f}",
            'AI_Tech_Health': f"{ai_data.get('technical_health', 'N/A')}",
            'Tech_Health_Diff': f"{result['technical_health_score'] - ai_data.get('technical_health', 0):.1f}",
            'Calc_Tech_Grade': result['technical_health_grade'],
            'AI_Tech_Grade': ai_data.get('technical_grade', 'N/A'),
            # Trading Signal
            'Calc_Signal': f"{result['trading_signal_score']:.1f}",
            'AI_Signal': f"{ai_data.get('trading_signal', 'N/A')}",
            'Signal_Diff': f"{result['trading_signal_score'] - ai_data.get('trading_signal', 0):.1f}",
            'Calc_Signal_Grade': result['trading_signal_rating'],
            'AI_Signal_Grade': ai_data.get('signal_rating', 'N/A'),
            # Overall
            'Calc_Overall': f"{result['overall_score']:.1f}",
            'AI_Overall': f"{ai_data.get('overall_score', 'N/A')}",
            'Overall_Diff': f"{result['overall_score'] - ai_data.get('overall_score', 0):.1f}",
            'Calc_Overall_Grade': result['overall_grade'],
            'AI_Overall_Grade': ai_data.get('overall_grade', 'N/A'),
            'AI_Notes': ai_data.get('ai_notes', 'N/A')
        }
        comparison_data.append(comparison_row)
    
    # Create DataFrame
    df = pd.DataFrame(comparison_data)
    
    # Save to CSV
    csv_filename = f"scoring_ai_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_filename, index=False)
    logger.info(f"Comparison table saved to {csv_filename}")
    
    return df

def print_summary_analysis(df):
    """Print summary analysis of the comparison"""
    
    logger.info("Summary Analysis")
    logger.info("=" * 60)
    
    print("\n" + "="*80)
    print("SCORING vs AI ANALYSIS COMPARISON SUMMARY")
    print("="*80)
    
    # Calculate average differences
    numeric_cols = ['Fund_Health_Diff', 'Value_Diff', 'Risk_Diff', 'Tech_Health_Diff', 'Signal_Diff', 'Overall_Diff']
    
    print(f"\nAverage Differences (Calculated - AI):")
    for col in numeric_cols:
        try:
            # Convert to numeric, handling 'N/A' values
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            avg_diff = numeric_series.mean()
            if not pd.isna(avg_diff):
                print(f"  {col.replace('_', ' ')}: {avg_diff:.1f}")
        except:
            pass
    
    # Grade agreement analysis
    grade_cols = [
        ('Calc_Fund_Grade', 'AI_Fund_Grade'),
        ('Calc_Value_Grade', 'AI_Value_Grade'),
        ('Calc_Risk_Grade', 'AI_Risk_Grade'),
        ('Calc_Tech_Grade', 'AI_Tech_Grade'),
        ('Calc_Signal_Grade', 'AI_Signal_Grade'),
        ('Calc_Overall_Grade', 'AI_Overall_Grade')
    ]
    
    print(f"\nGrade Agreement Analysis:")
    for calc_col, ai_col in grade_cols:
        agreement = (df[calc_col] == df[ai_col]).sum()
        total = len(df)
        percentage = (agreement / total) * 100
        print(f"  {calc_col.replace('_', ' ')}: {agreement}/{total} ({percentage:.1f}%)")
    
    # Top and bottom performers - handle numeric conversion properly
    try:
        print(f"\nTop 5 Overall Scores (Calculated):")
        # Convert to numeric for sorting
        df_numeric = df.copy()
        df_numeric['Calc_Overall_Numeric'] = pd.to_numeric(df_numeric['Calc_Overall'], errors='coerce')
        top_calc = df_numeric.nlargest(5, 'Calc_Overall_Numeric')
        for _, row in top_calc.iterrows():
            print(f"  {row['Ticker']}: {row['Calc_Overall']} ({row['Calc_Overall_Grade']})")
    except Exception as e:
        print(f"  Error displaying top calculated scores: {e}")
    
    try:
        print(f"\nTop 5 Overall Scores (AI):")
        df_numeric['AI_Overall_Numeric'] = pd.to_numeric(df_numeric['AI_Overall'], errors='coerce')
        top_ai = df_numeric.nlargest(5, 'AI_Overall_Numeric')
        for _, row in top_ai.iterrows():
            print(f"  {row['Ticker']}: {row['AI_Overall']} ({row['AI_Overall_Grade']})")
    except Exception as e:
        print(f"  Error displaying top AI scores: {e}")
    
    try:
        print(f"\nLargest Differences (Calculated - AI):")
        df_numeric['Overall_Diff_Numeric'] = pd.to_numeric(df_numeric['Overall_Diff'], errors='coerce')
        largest_diffs = df_numeric.nlargest(5, 'Overall_Diff_Numeric')
        for _, row in largest_diffs.iterrows():
            print(f"  {row['Ticker']}: {row['Overall_Diff']} (Calc: {row['Calc_Overall']}, AI: {row['AI_Overall']})")
    except Exception as e:
        print(f"  Error displaying largest differences: {e}")
    
    print("\n" + "="*80)

def main():
    """Main function"""
    
    logger.info("Starting Comprehensive Scoring Analysis with AI Comparison")
    logger.info("=" * 80)
    
    # Step 1: Run scoring analysis
    scoring_results = run_scoring_analysis()
    
    if not scoring_results:
        logger.error("No scoring results obtained. Exiting.")
        return False
    
    # Step 2: Perform AI analysis
    ai_analysis = perform_ai_analysis()
    
    # Step 3: Create comparison table
    df = create_comparison_table(scoring_results, ai_analysis)
    
    # Step 4: Print summary analysis
    print_summary_analysis(df)
    
    # Step 5: Display detailed table
    print("\n" + "="*120)
    print("DETAILED COMPARISON TABLE")
    print("="*120)
    
    # Display key columns for readability
    display_cols = [
        'Ticker', 'Calc_Overall', 'AI_Overall', 'Overall_Diff',
        'Calc_Overall_Grade', 'AI_Overall_Grade', 'AI_Notes'
    ]
    
    print(df[display_cols].to_string(index=False))
    
    logger.info("Analysis completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
