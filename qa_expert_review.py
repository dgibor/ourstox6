#!/usr/bin/env python3
"""
QA Expert Review - Scoring System Implementation
Comprehensive review to identify and fix issues in the scoring system
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAExpertReview:
    """QA Expert Review for scoring system implementation"""
    
    def __init__(self):
        self.issues_found = []
        self.warnings = []
        self.recommendations = []
        self.test_results = {}
        
    def review_environment_setup(self) -> bool:
        """Review environment variables and configuration"""
        logger.info("🔍 Reviewing environment setup...")
        
        issues = []
        warnings = []
        
        # Check required environment variables
        required_vars = [
            'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
            'news_api_key', 'fred_api_key', 'openai_api_key'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                issues.append(f"Missing environment variable: {var}")
            else:
                logger.info(f"✅ {var} is configured")
        
        # Check file existence
        required_files = [
            'calc_fundamental_scores.py',
            'calc_technical_scores.py',
            'enhanced_sentiment_analyzer.py',
            '.env'
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                issues.append(f"Missing required file: {file}")
            else:
                file_size = os.path.getsize(file)
                if file_size < 1000:  # Less than 1KB
                    warnings.append(f"File {file} is very small ({file_size} bytes) - may be corrupted")
                logger.info(f"✅ {file} exists ({file_size} bytes)")
        
        self.issues_found.extend(issues)
        self.warnings.extend(warnings)
        
        return len(issues) == 0
    
    def review_database_connection(self) -> bool:
        """Review database connection and schema"""
        logger.info("🔍 Reviewing database connection...")
        
        try:
            import psycopg2
            from dotenv import load_dotenv
            
            load_dotenv()
            
            db_config = {
                'host': os.getenv('DB_HOST'),
                'database': os.getenv('DB_NAME'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'port': os.getenv('DB_PORT', '5432')
            }
            
            # Test connection
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Check required tables
            required_tables = [
                'daily_charts',
                'financial_ratios', 
                'company_scores_current',
                'company_scores_historical'
            ]
            
            for table in required_tables:
                cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                exists = cursor.fetchone()[0]
                if exists:
                    logger.info(f"✅ Table {table} exists")
                else:
                    self.issues_found.append(f"Missing table: {table}")
            
            # Check sentiment columns in scoring tables
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'company_scores_current' 
                AND column_name IN ('sentiment_analysis', 'sentiment_score', 'sentiment_grade', 'sentiment_source')
            """)
            sentiment_columns = [row[0] for row in cursor.fetchall()]
            
            if len(sentiment_columns) == 4:
                logger.info("✅ Sentiment columns exist in company_scores_current")
            else:
                self.issues_found.append(f"Missing sentiment columns in company_scores_current: found {sentiment_columns}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.issues_found.append(f"Database connection failed: {e}")
            return False
    
    def review_code_quality(self) -> bool:
        """Review code quality and potential issues"""
        logger.info("🔍 Reviewing code quality...")
        
        issues = []
        warnings = []
        
        # Check for common issues in fundamental scores
        try:
            with open('calc_fundamental_scores.py', 'r') as f:
                content = f.read()
                
            # Check for calibration factors
            if 'score_calibration' in content:
                logger.info("✅ Score calibration factors found")
            else:
                issues.append("Missing score calibration factors in fundamental scores")
            
            # Check for sentiment integration
            if 'EnhancedSentimentAnalyzer' in content:
                logger.info("✅ Enhanced sentiment analyzer integration found")
            else:
                issues.append("Missing enhanced sentiment analyzer integration")
                
        except Exception as e:
            issues.append(f"Error reading calc_fundamental_scores.py: {e}")
        
        # Check technical scores
        try:
            with open('calc_technical_scores.py', 'r') as f:
                content = f.read()
                
            if 'TechnicalScoreCalculator' in content:
                logger.info("✅ TechnicalScoreCalculator class found")
            else:
                issues.append("Missing TechnicalScoreCalculator class")
                
            if 'score_calibration' in content:
                logger.info("✅ Technical score calibration found")
            else:
                issues.append("Missing technical score calibration")
                
        except Exception as e:
            issues.append(f"Error reading calc_technical_scores.py: {e}")
        
        # Check sentiment analyzer
        try:
            with open('enhanced_sentiment_analyzer.py', 'r') as f:
                content = f.read()
                
            if 'EnhancedSentimentAnalyzer' in content:
                logger.info("✅ EnhancedSentimentAnalyzer class found")
            else:
                issues.append("Missing EnhancedSentimentAnalyzer class")
                
            if 'openai' in content.lower():
                logger.info("✅ OpenAI integration found")
            else:
                issues.append("Missing OpenAI integration")
                
        except Exception as e:
            issues.append(f"Error reading enhanced_sentiment_analyzer.py: {e}")
        
        self.issues_found.extend(issues)
        self.warnings.extend(warnings)
        
        return len(issues) == 0
    
    def test_imports(self) -> bool:
        """Test that all modules can be imported"""
        logger.info("🔍 Testing module imports...")
        
        issues = []
        
        try:
            from calc_fundamental_scores import FundamentalScoreCalculator
            logger.info("✅ FundamentalScoreCalculator imported successfully")
        except Exception as e:
            issues.append(f"Failed to import FundamentalScoreCalculator: {e}")
        
        try:
            from calc_technical_scores import TechnicalScoreCalculator
            logger.info("✅ TechnicalScoreCalculator imported successfully")
        except Exception as e:
            issues.append(f"Failed to import TechnicalScoreCalculator: {e}")
        
        try:
            from enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer
            logger.info("✅ EnhancedSentimentAnalyzer imported successfully")
        except Exception as e:
            issues.append(f"Failed to import EnhancedSentimentAnalyzer: {e}")
        
        self.issues_found.extend(issues)
        
        return len(issues) == 0
    
    def test_simple_calculation(self) -> bool:
        """Test simple calculation without database or API calls"""
        logger.info("🔍 Testing simple calculation...")
        
        try:
            from calc_fundamental_scores import FundamentalScoreCalculator
            from calc_technical_scores import TechnicalScoreCalculator
            
            # Test initialization
            fundamental_calc = FundamentalScoreCalculator()
            technical_calc = TechnicalScoreCalculator()
            
            logger.info("✅ Calculators initialized successfully")
            
            # Test calibration factors
            if hasattr(fundamental_calc, 'score_calibration'):
                logger.info("✅ Fundamental score calibration found")
                logger.info(f"  Calibration factors: {fundamental_calc.score_calibration}")
            else:
                self.issues_found.append("Missing score_calibration in FundamentalScoreCalculator")
            
            if hasattr(technical_calc, 'score_calibration'):
                logger.info("✅ Technical score calibration found")
                logger.info(f"  Calibration factors: {technical_calc.score_calibration}")
            else:
                self.issues_found.append("Missing score_calibration in TechnicalScoreCalculator")
            
            return True
            
        except Exception as e:
            self.issues_found.append(f"Simple calculation test failed: {e}")
            return False
    
    def generate_recommendations(self):
        """Generate recommendations based on findings"""
        logger.info("🔍 Generating recommendations...")
        
        recommendations = []
        
        if self.issues_found:
            recommendations.append("CRITICAL: Fix all identified issues before proceeding")
        
        # Performance recommendations
        recommendations.append("Consider implementing caching for API calls to reduce rate limiting")
        recommendations.append("Add timeout handling for database connections")
        recommendations.append("Implement retry logic for failed API calls")
        
        # Monitoring recommendations
        recommendations.append("Add comprehensive logging for debugging")
        recommendations.append("Implement metrics collection for performance monitoring")
        recommendations.append("Add health checks for all external dependencies")
        
        # Testing recommendations
        recommendations.append("Create unit tests for individual scoring components")
        recommendations.append("Implement integration tests for the complete pipeline")
        recommendations.append("Add regression tests for score calibration")
        
        self.recommendations = recommendations
        
        for rec in recommendations:
            logger.info(f"💡 Recommendation: {rec}")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive QA report"""
        logger.info("📊 Generating QA report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': len(self.issues_found),
                'total_warnings': len(self.warnings),
                'total_recommendations': len(self.recommendations),
                'overall_status': 'PASS' if len(self.issues_found) == 0 else 'FAIL'
            },
            'issues': self.issues_found,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'test_results': self.test_results
        }
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'qa_expert_review_report_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 QA report saved to: {filename}")
        
        return report
    
    def run_full_review(self) -> Dict:
        """Run complete QA review"""
        logger.info("🚀 Starting QA Expert Review...")
        logger.info("=" * 60)
        
        # Run all review steps
        steps = [
            ("Environment Setup", self.review_environment_setup),
            ("Database Connection", self.review_database_connection),
            ("Code Quality", self.review_code_quality),
            ("Module Imports", self.test_imports),
            ("Simple Calculation", self.test_simple_calculation)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}")
            logger.info("-" * 40)
            success = step_func()
            self.test_results[step_name] = success
            
            if success:
                logger.info(f"✅ {step_name} - PASSED")
            else:
                logger.info(f"❌ {step_name} - FAILED")
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Generate final report
        report = self.generate_report()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 QA EXPERT REVIEW SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Issues: {len(self.issues_found)}")
        logger.info(f"Total Warnings: {len(self.warnings)}")
        logger.info(f"Total Recommendations: {len(self.recommendations)}")
        logger.info(f"Overall Status: {report['summary']['overall_status']}")
        
        if self.issues_found:
            logger.info("\n❌ CRITICAL ISSUES FOUND:")
            for issue in self.issues_found:
                logger.info(f"  • {issue}")
        
        if self.warnings:
            logger.info("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                logger.info(f"  • {warning}")
        
        return report

def main():
    """Main function to run QA review"""
    qa_review = QAExpertReview()
    report = qa_review.run_full_review()
    
    if report['summary']['overall_status'] == 'PASS':
        print("\n🎉 QA Review PASSED! Ready for final testing.")
    else:
        print("\n💥 QA Review FAILED! Issues need to be fixed before proceeding.")
        print("Please review the issues above and fix them before continuing.")

if __name__ == "__main__":
    main()

