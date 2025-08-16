#!/usr/bin/env python3
"""
Enhanced Stock Scoring System with VWAP & Support/Resistance
Implements the updated scoring methodology including VWAP analysis and support/resistance positioning
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add daily_run to path for imports
sys.path.append('daily_run')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedStockScorer:
    """Enhanced stock scoring system with VWAP and support/resistance analysis"""
    
    def __init__(self):
        self.db = None
        self.sector_averages = {}
        
    def connect_db(self):
        """Connect to database"""
        try:
            from daily_run.database import DatabaseManager
            self.db = DatabaseManager()
            self.db.connect()
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect_db(self):
        """Disconnect from database"""
        if self.db:
            self.db.disconnect()
            logger.info("Database disconnected")
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive stock data for scoring"""
        try:
            cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
            
            # Get latest fundamental data
            cursor.execute("""
                SELECT * FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            fundamental_data = cursor.fetchone()
            
            if not fundamental_data:
                logger.warning(f"No fundamental data found for {ticker}")
                return None
            
            # Get latest technical data
            cursor.execute("""
                SELECT * FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """, (ticker,))
            technical_data = cursor.fetchone()
            
            if not technical_data:
                logger.warning(f"No technical data found for {ticker}")
                return None
            
            # Get historical price data for support/resistance
            cursor.execute("""
                SELECT date, open, high, low, close, volume 
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 100
            """, (ticker,))
            price_history = cursor.fetchall()
            
            cursor.close()
            
            return {
                'fundamental': fundamental_data,
                'technical': technical_data,
                'price_history': price_history
            }
            
        except Exception as e:
            logger.error(f"Error getting stock data for {ticker}: {e}")
            return None
    
    def calculate_vwap_sr_score(self, stock_data: Dict) -> Tuple[float, Dict]:
        """Calculate VWAP and Support/Resistance score (0-100)"""
        try:
            technical = stock_data['technical']
            price_history = stock_data['price_history']
            
            if not price_history:
                return 50.0, {'error': 'No price history available'}
            
            # Database stores prices as 100x (bigint format)
            # Convert back to actual prices by dividing by 100
            current_price = technical['close'] / 100.0
            vwap = technical.get('vwap')
            if vwap and not pd.isna(vwap):
                vwap = vwap / 100.0
            
            # Convert price history to DataFrame
            df = pd.DataFrame(price_history)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Convert all price columns to actual prices
            df['close'] = df['close'] / 100.0
            df['open'] = df['open'] / 100.0
            df['high'] = df['high'] / 100.0
            df['low'] = df['low'] / 100.0
            
            # Calculate VWAP if not available
            if not vwap or pd.isna(vwap):
                if 'volume' in df.columns and not df['volume'].isna().all():
                    vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
                else:
                    vwap = df['close'].mean()
            
            # VWAP Analysis (40% weight)
            vwap_score = 0
            if current_price > vwap:
                vwap_score = 85  # Price above VWAP
            elif abs(current_price - vwap) / vwap < 0.02:  # Within 2% of VWAP
                vwap_score = 70
            else:
                vwap_score = 40  # Price below VWAP
            
            # Support Analysis (30% weight)
            support_score = 0
            support_1 = technical.get('support_1')
            support_2 = technical.get('support_2')
            support_3 = technical.get('support_3')
            
            # Convert support levels to actual prices (divide by 100)
            if support_1 and not pd.isna(support_1):
                support_1 = support_1 / 100.0
            if support_2 and not pd.isna(support_2):
                support_2 = support_2 / 100.0
            if support_3 and not pd.isna(support_3):
                support_3 = support_3 / 100.0
            
            if support_1 and not pd.isna(support_1):
                # Find closest support level
                supports = [s for s in [support_1, support_2, support_3] if s and not pd.isna(s)]
                if supports:
                    closest_support = min(supports, key=lambda x: abs(current_price - x))
                    distance_to_support = abs(current_price - closest_support) / closest_support
                    
                    if distance_to_support < 0.02:  # Within 2%
                        support_score = 100
                    elif distance_to_support < 0.05:  # Within 5%
                        support_score = 85
                    elif distance_to_support < 0.10:  # Within 10%
                        support_score = 70
                    elif distance_to_support < 0.15:  # Within 15%
                        support_score = 50
                    else:
                        support_score = 30
                else:
                    support_score = 50
            else:
                support_score = 50
            
            # Resistance Analysis (30% weight)
            resistance_score = 0
            resistance_1 = technical.get('resistance_1')
            resistance_2 = technical.get('resistance_2')
            resistance_3 = technical.get('resistance_3')
            
            # Convert resistance levels to actual prices (divide by 100)
            if resistance_1 and not pd.isna(resistance_1):
                resistance_1 = resistance_1 / 100.0
            if resistance_2 and not pd.isna(resistance_2):
                resistance_2 = resistance_2 / 100.0
            if resistance_3 and not pd.isna(resistance_3):
                resistance_3 = resistance_3 / 100.0
            
            if resistance_1 and not pd.isna(resistance_1):
                # Find closest resistance level
                resistances = [r for r in [resistance_1, resistance_2, resistance_3] if r and not pd.isna(r)]
                if resistances:
                    closest_resistance = min(resistances, key=lambda x: abs(current_price - x))
                    distance_to_resistance = abs(current_price - closest_resistance) / closest_resistance
                    
                    if distance_to_resistance < 0.02:  # Within 2%
                        resistance_score = 20
                    elif distance_to_resistance < 0.05:  # Within 5%
                        resistance_score = 40
                    elif distance_to_resistance < 0.10:  # Within 10%
                        resistance_score = 60
                    elif distance_to_resistance < 0.15:  # Within 15%
                        resistance_score = 80
                    else:
                        resistance_score = 100
                else:
                    resistance_score = 50
            else:
                resistance_score = 50
            
            # Calculate final score
            final_score = (vwap_score * 0.4) + (support_score * 0.3) + (resistance_score * 0.3)
            
            breakdown = {
                'vwap_score': vwap_score,
                'support_score': support_score,
                'resistance_score': resistance_score,
                'current_price': current_price,
                'vwap': vwap,
                'closest_support': support_1,
                'closest_resistance': resistance_1
            }
            
            return final_score, breakdown
            
        except Exception as e:
            logger.error(f"Error calculating VWAP/SR score: {e}")
            return 50.0, {'error': str(e)}
    
    def calculate_fundamental_health_score(self, stock_data: Dict) -> Tuple[float, Dict]:
        """Calculate fundamental health score (0-100)"""
        try:
            fundamental = stock_data['fundamental']
            
            # Core financial ratios (70% weight)
            core_score = 0
            ratios = {}
            
            # PE Ratio (15%)
            pe_ratio = fundamental.get('pe_ratio')
            if pe_ratio and not pd.isna(pe_ratio) and pe_ratio > 0:
                if pe_ratio < 15:
                    ratios['pe_score'] = 100
                elif pe_ratio < 25:
                    ratios['pe_score'] = 80
                elif pe_ratio < 40:
                    ratios['pe_score'] = 60
                elif pe_ratio < 60:
                    ratios['pe_score'] = 40
                else:
                    ratios['pe_score'] = 20
                core_score += ratios['pe_score'] * 0.15
            else:
                ratios['pe_score'] = 50
                core_score += 25
            
            # ROE (12%)
            roe = fundamental.get('roe')
            if roe and not pd.isna(roe):
                if roe > 20:
                    ratios['roe_score'] = 100
                elif roe > 15:
                    ratios['roe_score'] = 85
                elif roe > 10:
                    ratios['roe_score'] = 70
                elif roe > 5:
                    ratios['roe_score'] = 55
                else:
                    ratios['roe_score'] = 30
                core_score += ratios['roe_score'] * 0.12
            else:
                ratios['roe_score'] = 50
                core_score += 30
            
            # Debt-to-Equity (10%)
            debt_equity = fundamental.get('debt_to_equity')
            if debt_equity and not pd.isna(debt_equity):
                if debt_equity < 0.5:
                    ratios['debt_score'] = 100
                elif debt_equity < 1.0:
                    ratios['debt_score'] = 80
                elif debt_equity < 1.5:
                    ratios['debt_score'] = 60
                elif debt_equity < 2.0:
                    ratios['debt_score'] = 40
                else:
                    ratios['debt_score'] = 20
                core_score += ratios['debt_score'] * 0.10
            else:
                ratios['debt_score'] = 50
                core_score += 25
            
            # Growth metrics (30% weight)
            growth_score = 0
            
            # Revenue growth
            revenue_growth = fundamental.get('revenue_growth')
            if revenue_growth and not pd.isna(revenue_growth):
                if revenue_growth > 20:
                    ratios['revenue_growth_score'] = 100
                elif revenue_growth > 10:
                    ratios['revenue_growth_score'] = 80
                elif revenue_growth > 5:
                    ratios['revenue_growth_score'] = 60
                elif revenue_growth > 0:
                    ratios['revenue_growth_score'] = 40
                else:
                    ratios['revenue_growth_score'] = 20
                growth_score += ratios['revenue_growth_score'] * 0.5
            else:
                ratios['revenue_growth_score'] = 50
                growth_score += 25
            
            # Earnings growth
            earnings_growth = fundamental.get('earnings_growth')
            if earnings_growth and not pd.isna(earnings_growth):
                if earnings_growth > 20:
                    ratios['earnings_growth_score'] = 100
                elif earnings_growth > 10:
                    ratios['earnings_growth_score'] = 80
                elif earnings_growth > 5:
                    ratios['earnings_growth_score'] = 60
                elif earnings_growth > 0:
                    ratios['earnings_growth_score'] = 40
                else:
                    ratios['earnings_growth_score'] = 20
                growth_score += ratios['earnings_growth_score'] * 0.5
            else:
                ratios['earnings_growth_score'] = 50
                growth_score += 25
            
            final_score = (core_score * 0.7) + (growth_score * 0.3)
            
            return final_score, ratios
            
        except Exception as e:
            logger.error(f"Error calculating fundamental health score: {e}")
            return 50.0, {'error': str(e)}
    
    def calculate_technical_health_score(self, stock_data: Dict) -> Tuple[float, Dict]:
        """Calculate technical health score (0-100)"""
        try:
            technical = stock_data['technical']
            
            # Trend indicators (50% weight)
            trend_score = 0
            
            # RSI (15%)
            rsi = technical.get('rsi_14')
            if rsi and not pd.isna(rsi):
                if 30 <= rsi <= 70:
                    trend_score += 100 * 0.15
                elif 20 <= rsi <= 80:
                    trend_score += 70 * 0.15
                else:
                    trend_score += 30 * 0.15
            else:
                trend_score += 50 * 0.15
            
            # MACD (15%)
            macd = technical.get('macd')
            if macd and not pd.isna(macd):
                if macd > 0:
                    trend_score += 80 * 0.15
                else:
                    trend_score += 40 * 0.15
            else:
                trend_score += 50 * 0.15
            
            # Moving averages (20%)
            ma_20 = technical.get('ma_20')
            ma_50 = technical.get('ma_50')
            if ma_20 and ma_50 and not pd.isna(ma_20) and not pd.isna(ma_50):
                if ma_20 > ma_50:
                    trend_score += 100 * 0.20
                else:
                    trend_score += 30 * 0.20
            else:
                trend_score += 50 * 0.20
            
            # Support/Resistance (30% weight) - already calculated in VWAP/SR score
            sr_score = 50  # Placeholder, will be replaced by actual calculation
            
            # Momentum indicators (20% weight)
            momentum_score = 0
            
            # Price momentum
            current_price = technical['close'] / 100.0  # Convert to actual price
            if len(stock_data['price_history']) > 1:
                prev_price = stock_data['price_history'][1]['close'] / 100.0  # Convert to actual price
                if prev_price > 0:
                    momentum = (current_price - prev_price) / prev_price
                    if momentum > 0.02:  # 2% gain
                        momentum_score += 100 * 0.10
                    elif momentum > 0:
                        momentum_score += 70 * 0.10
                    else:
                        momentum_score += 30 * 0.10
                else:
                    momentum_score += 50 * 0.10
            else:
                momentum_score += 50 * 0.10
            
            # Volume analysis
            volume = technical.get('volume')
            if volume and not pd.isna(volume):
                momentum_score += 70 * 0.10
            else:
                momentum_score += 50 * 0.10
            
            final_score = (trend_score * 0.5) + (sr_score * 0.3) + (momentum_score * 0.2)
            
            return final_score, {
                'trend_score': trend_score,
                'sr_score': sr_score,
                'momentum_score': momentum_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical health score: {e}")
            return 50.0, {'error': str(e)}
    
    def calculate_composite_score(self, scores: Dict) -> float:
        """Calculate composite score using updated weights"""
        try:
            fundamental = scores.get('fundamental_health', 50)
            technical = scores.get('technical_health', 50)
            vwap_sr = scores.get('vwap_sr', 50)
            
            # Using updated weights from methodology
            composite = (fundamental * 0.25) + (technical * 0.20) + (vwap_sr * 0.15)
            
            return composite
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 50.0
    
    def score_stock(self, ticker: str) -> Dict:
        """Score a single stock using enhanced methodology"""
        try:
            logger.info(f"Scoring stock: {ticker}")
            
            # Get stock data
            stock_data = self.get_stock_data(ticker)
            if not stock_data:
                return {'ticker': ticker, 'error': 'No data available'}
            
            # Calculate individual scores
            fundamental_score, fundamental_breakdown = self.calculate_fundamental_health_score(stock_data)
            technical_score, technical_breakdown = self.calculate_technical_health_score(stock_data)
            vwap_sr_score, vwap_sr_breakdown = self.calculate_vwap_sr_score(stock_data)
            
            # Calculate composite score
            composite_score = self.calculate_composite_score({
                'fundamental_health': fundamental_score,
                'technical_health': technical_score,
                'vwap_sr': vwap_sr_score
            })
            
            # Determine rating
            if composite_score >= 90:
                rating = "Strong Buy"
            elif composite_score >= 70:
                rating = "Buy"
            elif composite_score >= 50:
                rating = "Neutral"
            elif composite_score >= 30:
                rating = "Sell"
            else:
                rating = "Strong Sell"
            
            return {
                'ticker': ticker,
                'composite_score': round(composite_score, 2),
                'rating': rating,
                'fundamental_health': round(fundamental_score, 2),
                'technical_health': round(technical_score, 2),
                'vwap_sr_score': round(vwap_sr_score, 2),
                'breakdown': {
                    'fundamental': fundamental_breakdown,
                    'technical': technical_breakdown,
                    'vwap_sr': vwap_sr_breakdown
                }
            }
            
        except Exception as e:
            logger.error(f"Error scoring stock {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def score_multiple_stocks(self, tickers: List[str]) -> List[Dict]:
        """Score multiple stocks"""
        results = []
        
        for ticker in tickers:
            try:
                result = self.score_stock(ticker)
                results.append(result)
                logger.info(f"Completed scoring for {ticker}")
            except Exception as e:
                logger.error(f"Failed to score {ticker}: {e}")
                results.append({'ticker': ticker, 'error': str(e)})
        
        return results

def main():
    """Main function to test the enhanced scoring system"""
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
    
    scorer = EnhancedStockScorer()
    
    if not scorer.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting enhanced stock scoring test...")
        
        # Score all test tickers
        results = scorer.score_multiple_stocks(test_tickers)
        
        # Display results
        print("\n" + "="*80)
        print("ENHANCED STOCK SCORING RESULTS WITH VWAP & SUPPORT/RESISTANCE")
        print("="*80)
        
        for result in results:
            if 'error' in result:
                print(f"\n{result['ticker']}: ERROR - {result['error']}")
            else:
                print(f"\n{result['ticker']}:")
                print(f"  Composite Score: {result['composite_score']}/100")
                print(f"  Rating: {result['rating']}")
                print(f"  Fundamental Health: {result['fundamental_health']}/100")
                print(f"  Technical Health: {result['technical_health']}/100")
                print(f"  VWAP & S/R Score: {result['vwap_sr_score']}/100")
                
                # Show VWAP/SR breakdown
                vwap_sr = result['breakdown']['vwap_sr']
                if 'error' not in vwap_sr:
                    print(f"    VWAP Score: {vwap_sr['vwap_score']}/100")
                    print(f"    Support Score: {vwap_sr['support_score']}/100")
                    print(f"    Resistance Score: {vwap_sr['resistance_score']}/100")
                    print(f"    Current Price: ${vwap_sr['current_price']:.2f}")
                    print(f"    VWAP: ${vwap_sr['vwap']:.2f}")
        
        print("\n" + "="*80)
        print("SCORING COMPLETED")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        scorer.disconnect_db()

if __name__ == "__main__":
    main()
