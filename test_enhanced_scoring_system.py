import os
import sys
from datetime import date

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

from calc_fundamental_scores_enhanced import EnhancedFundamentalScoreCalculator
from calc_technical_scores import TechnicalScoreCalculator

def test_enhanced_scoring_system():
    """Test both enhanced fundamental and technical scoring systems"""
    
    # Test tickers including large and small cap
    test_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'PG', 'PFE', 'CSCO',
        'UAL', 'XOM', 'JPM', 'JNJ', 'V', 'HD', 'DIS', 'NFLX', 'ADBE', 'CRM'
    ]
    
    print("Enhanced Scoring System Test")
    print("=" * 60)
    print(f"Testing {len(test_tickers)} tickers on {date.today()}")
    print()
    
    # Initialize calculators
    fundamental_calc = EnhancedFundamentalScoreCalculator()
    technical_calc = TechnicalScoreCalculator()
    
    results = []
    
    for i, ticker in enumerate(test_tickers, 1):
        print(f"[{i:2d}/{len(test_tickers)}] Processing {ticker}...")
        
        # Calculate fundamental scores
        fundamental_scores = fundamental_calc.calculate_fundamental_scores_enhanced(ticker)
        
        # Calculate technical scores
        technical_scores = technical_calc.calculate_technical_scores(ticker)
        
        if 'error' in fundamental_scores:
            print(f"  ✗ Fundamental Error: {fundamental_scores['error']}")
            continue
        
        if 'error' in technical_scores:
            print(f"  ✗ Technical Error: {technical_scores['error']}")
            continue
        
        # Store fundamental scores
        try:
            fundamental_stored = fundamental_calc.store_fundamental_scores(ticker, fundamental_scores)
            if fundamental_stored:
                print(f"  Storage: ✓")
            else:
                print(f"  Storage: ✗")
        except Exception as e:
            print(f"  Storage: ✗ (Error: {e})")
            fundamental_stored = False
        
        # Store technical scores
        try:
            technical_stored = technical_calc.store_technical_scores(ticker, technical_scores)
        except Exception as e:
            print(f"  ✗ Technical Storage Error: {e}")
            technical_stored = False
        
        # Display results
        print(f"  Fundamental Health: {fundamental_scores['fundamental_health_score']:.1f} ({fundamental_scores['fundamental_health_grade']})")
        print(f"  Value Investment: {fundamental_scores['value_investment_score']:.1f} ({fundamental_scores['value_rating']})")
        print(f"  Risk Assessment: {fundamental_scores['fundamental_risk_score']:.1f} ({fundamental_scores['fundamental_risk_level']})")
        print(f"  Technical Health: {technical_scores['technical_health_score']:.1f} ({technical_scores['technical_health_grade']})")
        print(f"  Trading Signal: {technical_scores['trading_signal_score']:.1f} ({technical_scores['trading_signal_rating']})")
        print(f"  Technical Risk: {technical_scores['technical_risk_score']:.1f} ({technical_scores['technical_risk_level']})")
        print(f"  Data Confidence: {fundamental_scores['data_confidence']:.1%}")
        
        if fundamental_scores['missing_metrics']:
            print(f"  Missing Metrics: {len(fundamental_scores['missing_metrics'])}/{len(fundamental_calc.REQUIRED_METRICS)}")
        
        if fundamental_scores['data_warnings']:
            print(f"  Warnings: {len(fundamental_scores['data_warnings'])}")
        
        print(f"  Storage: {'✓' if fundamental_stored and technical_stored else '✗'}")
        print()
        
        # Collect results for analysis
        results.append({
            'ticker': ticker,
            'fundamental': fundamental_scores,
            'technical': technical_scores,
            'stored': fundamental_stored and technical_stored
        })
    
    # Close connections
    fundamental_calc.close()
    # technical_calc.close() # Removed as per edit hint
    
    # Provide professor's analysis
    print("=" * 60)
    print("PROFESSOR'S ANALYSIS")
    print("=" * 60)
    
    analyze_results(results)
    
    return results

def analyze_results(results):
    """Provide professor's analysis of the scoring results"""
    
    if not results:
        print("No results to analyze.")
        return
    
    # Calculate statistics
    total_tickers = len(results)
    successful_storage = sum(1 for r in results if r['stored'])
    
    # Fundamental score statistics
    fundamental_health_scores = [r['fundamental']['fundamental_health_score'] for r in results]
    value_scores = [r['fundamental']['value_investment_score'] for r in results]
    risk_scores = [r['fundamental']['fundamental_risk_score'] for r in results]
    
    # Technical score statistics
    technical_health_scores = [r['technical']['technical_health_score'] for r in results]
    trading_signal_scores = [r['technical']['trading_signal_score'] for r in results]
    technical_risk_scores = [r['technical']['technical_risk_score'] for r in results]
    
    # Confidence statistics
    confidence_scores = [r['fundamental']['data_confidence'] for r in results]
    
    print(f"ANALYSIS SUMMARY:")
    print(f"  Total tickers analyzed: {total_tickers}")
    print(f"  Successfully stored: {successful_storage}/{total_tickers} ({successful_storage/total_tickers:.1%})")
    print()
    
    print(f"FUNDAMENTAL SCORES:")
    print(f"  Health Score Range: {min(fundamental_health_scores):.1f} - {max(fundamental_health_scores):.1f}")
    print(f"  Value Score Range: {min(value_scores):.1f} - {max(value_scores):.1f}")
    print(f"  Risk Score Range: {min(risk_scores):.1f} - {max(risk_scores):.1f}")
    print()
    
    print(f"TECHNICAL SCORES:")
    print(f"  Health Score Range: {min(technical_health_scores):.1f} - {max(technical_health_scores):.1f}")
    print(f"  Trading Signal Range: {min(trading_signal_scores):.1f} - {max(trading_signal_scores):.1f}")
    print(f"  Technical Risk Range: {min(technical_risk_scores):.1f} - {max(technical_risk_scores):.1f}")
    print()
    
    print(f"DATA QUALITY:")
    print(f"  Average Confidence: {sum(confidence_scores)/len(confidence_scores):.1%}")
    print(f"  Confidence Range: {min(confidence_scores):.1%} - {max(confidence_scores):.1%}")
    print()
    
    # Grade distribution analysis
    print(f"GRADE DISTRIBUTION:")
    
    fundamental_grades = {}
    value_grades = {}
    risk_levels = {}
    technical_grades = {}
    trading_grades = {}
    
    for r in results:
        # Fundamental grades
        grade = r['fundamental']['fundamental_health_grade']
        fundamental_grades[grade] = fundamental_grades.get(grade, 0) + 1
        
        grade = r['fundamental']['value_rating']
        value_grades[grade] = value_grades.get(grade, 0) + 1
        
        level = r['fundamental']['fundamental_risk_level']
        risk_levels[level] = risk_levels.get(level, 0) + 1
        
        # Technical grades
        grade = r['technical']['technical_health_grade']
        technical_grades[grade] = technical_grades.get(grade, 0) + 1
        
        grade = r['technical']['trading_signal_rating']
        trading_grades[grade] = trading_grades.get(grade, 0) + 1
    
    print(f"  Fundamental Health: {dict(fundamental_grades)}")
    print(f"  Value Investment: {dict(value_grades)}")
    print(f"  Risk Assessment: {dict(risk_levels)}")
    print(f"  Technical Health: {dict(technical_grades)}")
    print(f"  Trading Signal: {dict(trading_grades)}")
    print()
    
    # Professor's insights
    print(f"PROFESSOR'S INSIGHTS:")
    
    # Check for data quality issues
    low_confidence_count = sum(1 for c in confidence_scores if c < 0.6)
    if low_confidence_count > 0:
        print(f"  ⚠️  {low_confidence_count} tickers have low confidence (<60%) - consider improving data quality")
    
    # Check for score differentiation
    fundamental_range = max(fundamental_health_scores) - min(fundamental_health_scores)
    if fundamental_range < 30:
        print(f"  ⚠️  Limited fundamental score differentiation (range: {fundamental_range:.1f})")
    else:
        print(f"  ✓ Good fundamental score differentiation (range: {fundamental_range:.1f})")
    
    technical_range = max(technical_health_scores) - min(technical_health_scores)
    if technical_range < 30:
        print(f"  ⚠️  Limited technical score differentiation (range: {technical_range:.1f})")
    else:
        print(f"  ✓ Good technical score differentiation (range: {technical_range:.1f})")
    
    # Check for realistic risk assessment
    high_risk_count = sum(1 for r in risk_scores if r > 70)
    low_risk_count = sum(1 for r in risk_scores if r < 30)
    
    if high_risk_count == 0:
        print(f"  ⚠️  No companies identified as high risk - may need risk assessment adjustment")
    if low_risk_count == 0:
        print(f"  ⚠️  No companies identified as low risk - may need risk assessment adjustment")
    
    # Check for value opportunities
    strong_buy_value = value_grades.get('Strong Buy', 0)
    buy_value = value_grades.get('Buy', 0)
    
    if strong_buy_value + buy_value > total_tickers * 0.7:
        print(f"  ⚠️  High number of Buy/Strong Buy ratings ({strong_buy_value + buy_value}/{total_tickers}) - may be too optimistic")
    elif strong_buy_value + buy_value < total_tickers * 0.2:
        print(f"  ⚠️  Low number of Buy/Strong Buy ratings ({strong_buy_value + buy_value}/{total_tickers}) - may be too conservative")
    else:
        print(f"  ✓ Reasonable value assessment distribution ({strong_buy_value + buy_value}/{total_tickers} Buy/Strong Buy)")
    
    print()
    print(f"RECOMMENDATIONS:")
    print(f"  1. Monitor data quality and confidence levels")
    print(f"  2. Validate risk assessments against market expectations")
    print(f"  3. Review scoring thresholds for better differentiation")
    print(f"  4. Consider sector-specific adjustments")
    print(f"  5. Implement regular validation against external sources")

if __name__ == "__main__":
    test_enhanced_scoring_system() 