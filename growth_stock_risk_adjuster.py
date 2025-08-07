#!/usr/bin/env python3
"""
Growth Stock Risk Adjuster
Properly identifies and adjusts risk scores for high-risk growth stocks
"""

import os
import sys
from typing import Dict, List, Any, Optional
import logging

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

class GrowthStockRiskAdjuster:
    """Adjusts risk scores for growth stocks with high PE ratios and volatility"""
    
    def __init__(self):
        # Growth stock indicators and thresholds
        self.growth_stock_indicators = {
            'high_pe_threshold': 30,
            'very_high_pe_threshold': 50,
            'high_volatility_threshold': 0.4,
            'very_high_volatility_threshold': 0.6,
            'growth_sector_multipliers': {
                'Technology': 1.5,
                'Communication Services': 1.3,
                'Consumer Discretionary': 1.2,
                'Healthcare': 1.1
            },
            'high_growth_indicators': {
                'revenue_growth_threshold': 0.20,  # 20% annual growth
                'earnings_growth_threshold': 0.15,  # 15% annual growth
                'high_beta_threshold': 1.5
            }
        }
        
        # Known high-risk growth stocks
        self.known_growth_stocks = {
            'NVDA': {
                'sector': 'Technology',
                'typical_pe': 80,
                'typical_beta': 1.8,
                'risk_multiplier': 2.0
            },
            'TSLA': {
                'sector': 'Consumer Discretionary',
                'typical_pe': 60,
                'typical_beta': 2.2,
                'risk_multiplier': 2.2
            },
            'UBER': {
                'sector': 'Technology',
                'typical_pe': 45,
                'typical_beta': 1.6,
                'risk_multiplier': 1.8
            },
            'AMD': {
                'sector': 'Technology',
                'typical_pe': 35,
                'typical_beta': 1.9,
                'risk_multiplier': 1.7
            },
            'NFLX': {
                'sector': 'Communication Services',
                'typical_pe': 40,
                'typical_beta': 1.4,
                'risk_multiplier': 1.6
            },
            'SNAP': {
                'sector': 'Communication Services',
                'typical_pe': 50,
                'typical_beta': 2.0,
                'risk_multiplier': 2.1
            },
            'PLTR': {
                'sector': 'Technology',
                'typical_pe': 70,
                'typical_beta': 2.5,
                'risk_multiplier': 2.3
            }
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def adjust_risk_for_growth_stocks(self, ticker: str, base_risk_score: float, 
                                    fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply growth stock risk multipliers and return detailed adjustment info"""
        self.logger.info(f"Adjusting risk for {ticker} - Base score: {base_risk_score}")
        
        adjusted_risk = base_risk_score
        adjustments = []
        
        # Check if it's a known growth stock
        if ticker in self.known_growth_stocks:
            known_data = self.known_growth_stocks[ticker]
            multiplier = known_data['risk_multiplier']
            adjusted_risk *= multiplier
            adjustments.append(f"Known growth stock multiplier: {multiplier}x")
            self.logger.info(f"Applied known growth stock multiplier for {ticker}: {multiplier}x")
        
        # Check for high PE ratio
        pe_ratio = fundamental_data.get('pe_ratio')
        if pe_ratio and pe_ratio > self.growth_stock_indicators['high_pe_threshold']:
            pe_multiplier = self.calculate_pe_multiplier(pe_ratio)
            adjusted_risk *= pe_multiplier
            adjustments.append(f"High PE multiplier: {pe_multiplier:.2f}x (PE: {pe_ratio:.1f})")
            self.logger.info(f"Applied PE multiplier for {ticker}: {pe_multiplier:.2f}x")
        
        # Check for high volatility (beta)
        beta = fundamental_data.get('beta', 1.0)
        if beta > self.growth_stock_indicators['high_volatility_threshold']:
            vol_multiplier = self.calculate_volatility_multiplier(beta)
            adjusted_risk *= vol_multiplier
            adjustments.append(f"High volatility multiplier: {vol_multiplier:.2f}x (Beta: {beta:.2f})")
            self.logger.info(f"Applied volatility multiplier for {ticker}: {vol_multiplier:.2f}x")
        
        # Apply sector-specific multipliers
        sector = self.get_stock_sector(ticker)
        if sector in self.growth_stock_indicators['growth_sector_multipliers']:
            sector_multiplier = self.growth_stock_indicators['growth_sector_multipliers'][sector]
            adjusted_risk *= sector_multiplier
            adjustments.append(f"Sector multiplier: {sector_multiplier:.2f}x ({sector})")
            self.logger.info(f"Applied sector multiplier for {ticker}: {sector_multiplier:.2f}x")
        
        # Check for high growth indicators
        growth_multiplier = self.calculate_growth_multiplier(fundamental_data)
        if growth_multiplier > 1.0:
            adjusted_risk *= growth_multiplier
            adjustments.append(f"Growth indicator multiplier: {growth_multiplier:.2f}x")
            self.logger.info(f"Applied growth multiplier for {ticker}: {growth_multiplier:.2f}x")
        
        # Ensure risk score stays within bounds (0-100)
        adjusted_risk = min(max(adjusted_risk, 0), 100)
        
        # Determine risk level
        risk_level = self.determine_risk_level(adjusted_risk)
        
        result = {
            'original_risk_score': base_risk_score,
            'adjusted_risk_score': adjusted_risk,
            'risk_level': risk_level,
            'adjustments': adjustments,
            'total_multiplier': adjusted_risk / base_risk_score if base_risk_score > 0 else 1.0,
            'is_growth_stock': self.is_growth_stock(ticker, fundamental_data)
        }
        
        self.logger.info(f"Risk adjustment complete for {ticker}: {base_risk_score:.1f} → {adjusted_risk:.1f} ({risk_level})")
        
        return result
    
    def calculate_pe_multiplier(self, pe_ratio: float) -> float:
        """Calculate risk multiplier based on PE ratio"""
        if pe_ratio <= self.growth_stock_indicators['high_pe_threshold']:
            return 1.0
        elif pe_ratio <= self.growth_stock_indicators['very_high_pe_threshold']:
            # Linear increase from 1.0 to 1.5
            ratio = (pe_ratio - self.growth_stock_indicators['high_pe_threshold']) / \
                   (self.growth_stock_indicators['very_high_pe_threshold'] - self.growth_stock_indicators['high_pe_threshold'])
            return 1.0 + (0.5 * ratio)
        else:
            # Very high PE - exponential increase
            excess_ratio = pe_ratio / self.growth_stock_indicators['very_high_pe_threshold']
            return min(1.5 + (excess_ratio - 1.0) * 0.5, 2.5)
    
    def calculate_volatility_multiplier(self, beta: float) -> float:
        """Calculate risk multiplier based on beta (volatility)"""
        if beta <= 1.0:
            return 1.0
        elif beta <= self.growth_stock_indicators['high_volatility_threshold']:
            # Linear increase from 1.0 to 1.3
            ratio = (beta - 1.0) / (self.growth_stock_indicators['high_volatility_threshold'] - 1.0)
            return 1.0 + (0.3 * ratio)
        elif beta <= self.growth_stock_indicators['very_high_volatility_threshold']:
            # Linear increase from 1.3 to 1.6
            ratio = (beta - self.growth_stock_indicators['high_volatility_threshold']) / \
                   (self.growth_stock_indicators['very_high_volatility_threshold'] - self.growth_stock_indicators['high_volatility_threshold'])
            return 1.3 + (0.3 * ratio)
        else:
            # Very high volatility - exponential increase
            excess_ratio = beta / self.growth_stock_indicators['very_high_volatility_threshold']
            return min(1.6 + (excess_ratio - 1.0) * 0.4, 2.0)
    
    def calculate_growth_multiplier(self, fundamental_data: Dict[str, Any]) -> float:
        """Calculate risk multiplier based on growth indicators"""
        multiplier = 1.0
        
        # Revenue growth
        revenue_growth = fundamental_data.get('revenue_growth', 0)
        if revenue_growth > self.growth_stock_indicators['high_growth_indicators']['revenue_growth_threshold']:
            growth_ratio = revenue_growth / self.growth_stock_indicators['high_growth_indicators']['revenue_growth_threshold']
            multiplier *= min(1.0 + (growth_ratio - 1.0) * 0.2, 1.3)
        
        # Earnings growth
        earnings_growth = fundamental_data.get('earnings_growth', 0)
        if earnings_growth > self.growth_stock_indicators['high_growth_indicators']['earnings_growth_threshold']:
            growth_ratio = earnings_growth / self.growth_stock_indicators['high_growth_indicators']['earnings_growth_threshold']
            multiplier *= min(1.0 + (growth_ratio - 1.0) * 0.15, 1.2)
        
        return multiplier
    
    def get_stock_sector(self, ticker: str) -> str:
        """Get stock sector for risk adjustment"""
        # Check known stocks first
        if ticker in self.known_growth_stocks:
            return self.known_growth_stocks[ticker]['sector']
        
        # Sector mapping for common stocks
        sector_map = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'AMZN': 'Consumer Discretionary', 'META': 'Technology',
            'JPM': 'Financial Services', 'JNJ': 'Healthcare', 'PG': 'Consumer Staples',
            'HD': 'Consumer Discretionary', 'V': 'Financial Services', 'UNH': 'Healthcare',
            'ADBE': 'Technology', 'CRM': 'Technology'
        }
        
        return sector_map.get(ticker, 'Unknown')
    
    def is_growth_stock(self, ticker: str, fundamental_data: Dict[str, Any]) -> bool:
        """Determine if a stock should be classified as a growth stock"""
        # Check if it's a known growth stock
        if ticker in self.known_growth_stocks:
            return True
        
        # Check PE ratio
        pe_ratio = fundamental_data.get('pe_ratio')
        if pe_ratio and pe_ratio > self.growth_stock_indicators['high_pe_threshold']:
            return True
        
        # Check volatility
        beta = fundamental_data.get('beta', 1.0)
        if beta > self.growth_stock_indicators['high_volatility_threshold']:
            return True
        
        # Check growth indicators
        revenue_growth = fundamental_data.get('revenue_growth', 0)
        if revenue_growth > self.growth_stock_indicators['high_growth_indicators']['revenue_growth_threshold']:
            return True
        
        # Check sector
        sector = self.get_stock_sector(ticker)
        if sector in ['Technology', 'Communication Services']:
            return True
        
        return False
    
    def determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on adjusted risk score"""
        if risk_score <= 30:
            return 'Low'
        elif risk_score <= 50:
            return 'Medium'
        elif risk_score <= 70:
            return 'High'
        else:
            return 'Very High'
    
    def get_growth_stock_report(self, ticker: str, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive growth stock analysis report"""
        is_growth = self.is_growth_stock(ticker, fundamental_data)
        sector = self.get_stock_sector(ticker)
        
        report = {
            'ticker': ticker,
            'is_growth_stock': is_growth,
            'sector': sector,
            'indicators': {
                'pe_ratio': fundamental_data.get('pe_ratio'),
                'beta': fundamental_data.get('beta'),
                'revenue_growth': fundamental_data.get('revenue_growth'),
                'earnings_growth': fundamental_data.get('earnings_growth')
            },
            'thresholds': {
                'high_pe': self.growth_stock_indicators['high_pe_threshold'],
                'high_volatility': self.growth_stock_indicators['high_volatility_threshold'],
                'high_revenue_growth': self.growth_stock_indicators['high_growth_indicators']['revenue_growth_threshold']
            },
            'risk_factors': []
        }
        
        # Identify specific risk factors
        if fundamental_data.get('pe_ratio', 0) > self.growth_stock_indicators['high_pe_threshold']:
            report['risk_factors'].append('High PE Ratio')
        
        if fundamental_data.get('beta', 1.0) > self.growth_stock_indicators['high_volatility_threshold']:
            report['risk_factors'].append('High Volatility')
        
        if fundamental_data.get('revenue_growth', 0) > self.growth_stock_indicators['high_growth_indicators']['revenue_growth_threshold']:
            report['risk_factors'].append('High Growth Rate')
        
        if sector in self.growth_stock_indicators['growth_sector_multipliers']:
            report['risk_factors'].append(f'{sector} Sector')
        
        return report

def main():
    """Test the growth stock risk adjuster"""
    adjuster = GrowthStockRiskAdjuster()
    
    # Test with known growth stocks
    test_cases = [
        {
            'ticker': 'NVDA',
            'base_risk': 30,
            'fundamental_data': {
                'pe_ratio': 80,
                'beta': 1.8,
                'revenue_growth': 0.25,
                'earnings_growth': 0.20
            }
        },
        {
            'ticker': 'TSLA',
            'base_risk': 25,
            'fundamental_data': {
                'pe_ratio': 60,
                'beta': 2.2,
                'revenue_growth': 0.30,
                'earnings_growth': 0.15
            }
        },
        {
            'ticker': 'JPM',
            'base_risk': 40,
            'fundamental_data': {
                'pe_ratio': 12,
                'beta': 1.1,
                'revenue_growth': 0.05,
                'earnings_growth': 0.08
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n🔍 Testing {case['ticker']}:")
        
        # Get growth stock report
        report = adjuster.get_growth_stock_report(case['ticker'], case['fundamental_data'])
        print(f"  Growth Stock: {report['is_growth_stock']}")
        print(f"  Risk Factors: {report['risk_factors']}")
        
        # Adjust risk
        result = adjuster.adjust_risk_for_growth_stocks(
            case['ticker'], 
            case['base_risk'], 
            case['fundamental_data']
        )
        
        print(f"  Risk Adjustment: {result['original_risk_score']:.1f} → {result['adjusted_risk_score']:.1f}")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Total Multiplier: {result['total_multiplier']:.2f}x")
        print(f"  Adjustments: {result['adjustments']}")

if __name__ == "__main__":
    main() 