#!/usr/bin/env python3
"""
Comprehensive Analyst Data Service
Integrates FMP, Yahoo Finance, and Finnhub for analyst target prices and ratings
"""
import logging
import requests
import time
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

try:
    from daily_run.database import DatabaseManager
except ImportError:
    from database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalystDataService:
    """
    Comprehensive analyst data service with FMP primary, Yahoo Finance secondary, Finnhub tertiary
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        
        # API configurations
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY', 'sandbox_c0q2hr748v6s25vl8nq0')
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        
        # Rate limiting
        self.fmp_delay = 0.5  # 2 calls per second max
        self.yahoo_delay = 1.0  # Conservative for Yahoo
        self.finnhub_delay = 1.0  # 60 calls per minute = 1 per second
        
        self.last_fmp_call = 0
        self.last_yahoo_call = 0
        self.last_finnhub_call = 0
        
        if not self.fmp_api_key:
            logger.warning("FMP_API_KEY not found. FMP service will be unavailable.")
    
    def get_comprehensive_analyst_data(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive analyst data using priority fallback system:
        1. FMP (Primary)
        2. Yahoo Finance (Secondary) 
        3. Finnhub (Tertiary)
        """
        try:
            logger.info(f"🎯 Fetching comprehensive analyst data for {ticker}")
            
            result = {
                'ticker': ticker,
                'target_data': None,
                'rating_data': None,
                'actions_data': None,
                'data_sources': [],
                'success': False
            }
            
            # Try FMP first (Primary)
            if self.fmp_api_key:
                logger.info(f"📊 Attempting FMP for {ticker}")
                fmp_data = self._get_fmp_analyst_data(ticker)
                if fmp_data and fmp_data.get('success'):
                    result['target_data'] = fmp_data.get('targets')
                    result['rating_data'] = fmp_data.get('ratings')
                    result['actions_data'] = fmp_data.get('actions')
                    result['data_sources'].append('fmp')
                    result['success'] = True
                    logger.info(f"✅ FMP data successful for {ticker}")
                    return result
                else:
                    logger.warning(f"⚠️ FMP failed for {ticker}, trying Yahoo Finance")
            
            # Try Yahoo Finance (Secondary)
            logger.info(f"🔍 Attempting Yahoo Finance for {ticker}")
            yahoo_data = self._get_yahoo_analyst_data(ticker)
            if yahoo_data and yahoo_data.get('success'):
                result['target_data'] = yahoo_data.get('targets')
                result['rating_data'] = yahoo_data.get('ratings')
                result['data_sources'].append('yahoo')
                result['success'] = True
                logger.info(f"✅ Yahoo Finance data successful for {ticker}")
                return result
            else:
                logger.warning(f"⚠️ Yahoo Finance failed for {ticker}, trying Finnhub")
            
            # Try Finnhub (Tertiary)
            if self.finnhub_api_key:
                logger.info(f"🔧 Attempting Finnhub for {ticker}")
                finnhub_data = self._get_finnhub_analyst_data(ticker)
                if finnhub_data and finnhub_data.get('success'):
                    result['target_data'] = finnhub_data.get('targets')
                    result['rating_data'] = finnhub_data.get('ratings')
                    result['data_sources'].append('finnhub')
                    result['success'] = True
                    logger.info(f"✅ Finnhub data successful for {ticker}")
                    return result
                else:
                    logger.warning(f"⚠️ Finnhub failed for {ticker}")
            
            logger.error(f"❌ All analyst data sources failed for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting analyst data for {ticker}: {e}")
            return {'ticker': ticker, 'success': False, 'error': str(e)}
    
    def _get_fmp_analyst_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get analyst data from Financial Modeling Prep"""
        try:
            self._rate_limit_fmp()
            
            result = {'success': False, 'targets': None, 'ratings': None, 'actions': None}
            
            # 1. Get Price Target Summary
            targets_url = f"{self.fmp_base_url}/price-target-summary/{ticker}"
            targets_params = {'apikey': self.fmp_api_key}
            
            logger.debug(f"FMP Targets URL: {targets_url}")
            targets_response = requests.get(targets_url, params=targets_params, timeout=30)
            
            if targets_response.status_code == 200:
                targets_data = targets_response.json()
                if targets_data and len(targets_data) > 0:
                    target_info = targets_data[0]
                    result['targets'] = {
                        'avg_target_price': target_info.get('lastMonthAvgPriceTarget'),
                        'high_target_price': target_info.get('lastMonthHighPriceTarget'),
                        'low_target_price': target_info.get('lastMonthLowPriceTarget'),
                        'num_analysts': target_info.get('lastMonthNumberOfAnalysts'),
                        'data_source': 'fmp'
                    }
                    logger.debug(f"FMP targets data: {result['targets']}")
            
            # 2. Get Analyst Estimates/Ratings
            estimates_url = f"{self.fmp_base_url}/analyst-estimates/{ticker}"
            estimates_params = {'apikey': self.fmp_api_key}
            
            estimates_response = requests.get(estimates_url, params=estimates_params, timeout=30)
            
            if estimates_response.status_code == 200:
                estimates_data = estimates_response.json()
                if estimates_data and len(estimates_data) > 0:
                    # Get most recent quarter data
                    recent_estimate = estimates_data[0]
                    result['ratings'] = {
                        'consensus_rating': self._convert_fmp_rating(recent_estimate.get('analystRatingsbuy', 0), 
                                                                   recent_estimate.get('analystRatingsHold', 0),
                                                                   recent_estimate.get('analystRatingsSell', 0)),
                        'strong_buy_count': recent_estimate.get('analystRatingStrongBuy', 0),
                        'buy_count': recent_estimate.get('analystRatingsbuy', 0),
                        'hold_count': recent_estimate.get('analystRatingsHold', 0),
                        'sell_count': recent_estimate.get('analystRatingsSell', 0),
                        'strong_sell_count': recent_estimate.get('analystRatingStrongSell', 0),
                        'total_analysts': (recent_estimate.get('analystRatingStrongBuy', 0) + 
                                         recent_estimate.get('analystRatingsbuy', 0) + 
                                         recent_estimate.get('analystRatingsHold', 0) + 
                                         recent_estimate.get('analystRatingsSell', 0) + 
                                         recent_estimate.get('analystRatingStrongSell', 0)),
                        'data_source': 'fmp'
                    }
            
            # 3. Get Upgrades/Downgrades
            actions_url = f"{self.fmp_base_url}/upgrades-downgrades/{ticker}"
            actions_params = {'apikey': self.fmp_api_key}
            
            actions_response = requests.get(actions_url, params=actions_params, timeout=30)
            
            if actions_response.status_code == 200:
                actions_data = actions_response.json()
                if actions_data:
                    # Get recent actions (last 30 days)
                    recent_actions = []
                    cutoff_date = datetime.now() - timedelta(days=30)
                    
                    for action in actions_data[:10]:  # Limit to recent 10
                        action_date = datetime.strptime(action.get('publishedDate', ''), '%Y-%m-%d %H:%M:%S')
                        if action_date >= cutoff_date:
                            recent_actions.append({
                                'analyst_firm': action.get('analystCompany'),
                                'action_date': action.get('publishedDate')[:10],  # Just the date part
                                'action_type': action.get('gradeType', '').lower(),
                                'new_rating': action.get('newGrade'),
                                'previous_rating': action.get('previousGrade'),
                                'new_target': action.get('priceTarget'),
                                'data_source': 'fmp'
                            })
                    
                    result['actions'] = recent_actions
            
            # Check if we got any useful data
            if result['targets'] or result['ratings'] or result['actions']:
                result['success'] = True
                logger.info(f"✅ FMP successfully retrieved data for {ticker}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ FMP error for {ticker}: {e}")
            return None
    
    def _get_yahoo_analyst_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get analyst data from Yahoo Finance using yfinance"""
        try:
            self._rate_limit_yahoo()
            
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            
            result = {'success': False, 'targets': None, 'ratings': None}
            
            # Get target price data
            avg_target = info.get('targetMeanPrice')
            high_target = info.get('targetHighPrice')
            low_target = info.get('targetLowPrice')
            recommendation_mean = info.get('recommendationMean')
            
            if avg_target and avg_target > 0:
                result['targets'] = {
                    'avg_target_price': float(avg_target),
                    'high_target_price': float(high_target) if high_target else None,
                    'low_target_price': float(low_target) if low_target else None,
                    'num_analysts': info.get('numberOfAnalystOpinions', 0),
                    'data_source': 'yahoo'
                }
            
            # Get rating data
            if recommendation_mean:
                consensus_rating = self._convert_yahoo_rating(float(recommendation_mean))
                result['ratings'] = {
                    'consensus_rating': consensus_rating,
                    'consensus_score': float(recommendation_mean),
                    'total_analysts': info.get('numberOfAnalystOpinions', 0),
                    'data_source': 'yahoo'
                }
            
            # Try to get recommendations history
            try:
                recommendations = stock.recommendations
                if recommendations is not None and not recommendations.empty:
                    # Use the most recent recommendation data
                    latest_rec = recommendations.iloc[-1] if len(recommendations) > 0 else None
                    if latest_rec is not None:
                        result['ratings'].update({
                            'strong_buy_count': int(latest_rec.get('strongBuy', 0)),
                            'buy_count': int(latest_rec.get('buy', 0)),
                            'hold_count': int(latest_rec.get('hold', 0)),
                            'sell_count': int(latest_rec.get('sell', 0)),
                            'strong_sell_count': int(latest_rec.get('strongSell', 0)),
                        })
            except Exception as rec_error:
                logger.debug(f"Yahoo recommendations error for {ticker}: {rec_error}")
            
            if result['targets'] or result['ratings']:
                result['success'] = True
                logger.info(f"✅ Yahoo Finance successfully retrieved data for {ticker}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Yahoo Finance error for {ticker}: {e}")
            return None
    
    def _get_finnhub_analyst_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get analyst data from Finnhub"""
        try:
            self._rate_limit_finnhub()
            
            result = {'success': False, 'targets': None, 'ratings': None}
            
            # 1. Get Price Target
            target_url = f"{self.finnhub_base_url}/stock/price-target"
            target_params = {'symbol': ticker, 'token': self.finnhub_api_key}
            
            target_response = requests.get(target_url, params=target_params, timeout=30)
            
            if target_response.status_code == 200:
                target_data = target_response.json()
                if target_data and target_data.get('targetMean'):
                    result['targets'] = {
                        'avg_target_price': float(target_data.get('targetMean')),
                        'high_target_price': float(target_data.get('targetHigh')) if target_data.get('targetHigh') else None,
                        'low_target_price': float(target_data.get('targetLow')) if target_data.get('targetLow') else None,
                        'num_analysts': int(target_data.get('lastUpdated', 0)),  # Finnhub doesn't provide analyst count
                        'data_source': 'finnhub'
                    }
            
            # 2. Get Recommendation Trends
            rec_url = f"{self.finnhub_base_url}/stock/recommendation"
            rec_params = {'symbol': ticker, 'token': self.finnhub_api_key}
            
            rec_response = requests.get(rec_url, params=rec_params, timeout=30)
            
            if rec_response.status_code == 200:
                rec_data = rec_response.json()
                if rec_data and len(rec_data) > 0:
                    # Get most recent recommendation
                    latest_rec = rec_data[0]
                    result['ratings'] = {
                        'strong_buy_count': int(latest_rec.get('strongBuy', 0)),
                        'buy_count': int(latest_rec.get('buy', 0)),
                        'hold_count': int(latest_rec.get('hold', 0)),
                        'sell_count': int(latest_rec.get('sell', 0)),
                        'strong_sell_count': int(latest_rec.get('strongSell', 0)),
                        'total_analysts': (int(latest_rec.get('strongBuy', 0)) + 
                                         int(latest_rec.get('buy', 0)) + 
                                         int(latest_rec.get('hold', 0)) + 
                                         int(latest_rec.get('sell', 0)) + 
                                         int(latest_rec.get('strongSell', 0))),
                        'consensus_rating': self._calculate_consensus_rating(
                            int(latest_rec.get('strongBuy', 0)),
                            int(latest_rec.get('buy', 0)),
                            int(latest_rec.get('hold', 0)),
                            int(latest_rec.get('sell', 0)),
                            int(latest_rec.get('strongSell', 0))
                        ),
                        'data_source': 'finnhub'
                    }
            
            if result['targets'] or result['ratings']:
                result['success'] = True
                logger.info(f"✅ Finnhub successfully retrieved data for {ticker}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Finnhub error for {ticker}: {e}")
            return None
    
    def _rate_limit_fmp(self):
        """Rate limiting for FMP API (2 calls per second)"""
        current_time = time.time()
        time_since_last = current_time - self.last_fmp_call
        if time_since_last < self.fmp_delay:
            time.sleep(self.fmp_delay - time_since_last)
        self.last_fmp_call = time.time()
    
    def _rate_limit_yahoo(self):
        """Rate limiting for Yahoo Finance (1 call per second)"""
        current_time = time.time()
        time_since_last = current_time - self.last_yahoo_call
        if time_since_last < self.yahoo_delay:
            time.sleep(self.yahoo_delay - time_since_last)
        self.last_yahoo_call = time.time()
    
    def _rate_limit_finnhub(self):
        """Rate limiting for Finnhub API (1 call per second)"""
        current_time = time.time()
        time_since_last = current_time - self.last_finnhub_call
        if time_since_last < self.finnhub_delay:
            time.sleep(self.finnhub_delay - time_since_last)
        self.last_finnhub_call = time.time()
    
    def _convert_fmp_rating(self, buy_count: int, hold_count: int, sell_count: int) -> str:
        """Convert FMP rating counts to consensus rating"""
        total = buy_count + hold_count + sell_count
        if total == 0:
            return "Hold"
        
        buy_pct = buy_count / total
        sell_pct = sell_count / total
        
        if buy_pct >= 0.7:
            return "Strong Buy"
        elif buy_pct >= 0.5:
            return "Buy"
        elif sell_pct >= 0.5:
            return "Sell"
        elif sell_pct >= 0.7:
            return "Strong Sell"
        else:
            return "Hold"
    
    def _convert_yahoo_rating(self, recommendation_mean: float) -> str:
        """Convert Yahoo's numerical rating (1-5 scale) to text"""
        if recommendation_mean <= 1.5:
            return "Strong Buy"
        elif recommendation_mean <= 2.5:
            return "Buy"
        elif recommendation_mean <= 3.5:
            return "Hold"
        elif recommendation_mean <= 4.5:
            return "Sell"
        else:
            return "Strong Sell"
    
    def _calculate_consensus_rating(self, strong_buy: int, buy: int, hold: int, sell: int, strong_sell: int) -> str:
        """Calculate consensus rating from individual counts"""
        total = strong_buy + buy + hold + sell + strong_sell
        if total == 0:
            return "Hold"
        
        # Calculate weighted score (1 = Strong Buy, 5 = Strong Sell)
        weighted_score = (strong_buy * 1 + buy * 2 + hold * 3 + sell * 4 + strong_sell * 5) / total
        
        if weighted_score <= 1.5:
            return "Strong Buy"
        elif weighted_score <= 2.5:
            return "Buy"
        elif weighted_score <= 3.5:
            return "Hold"
        elif weighted_score <= 4.5:
            return "Sell"
        else:
            return "Strong Sell"

def test_analyst_data_service():
    """Test the analyst data service with sample tickers"""
    logger.info("🧪 Testing Analyst Data Service")
    
    service = AnalystDataService()
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for ticker in test_tickers:
        logger.info(f"\n🎯 Testing {ticker}...")
        result = service.get_comprehensive_analyst_data(ticker)
        
        if result.get('success'):
            logger.info(f"✅ {ticker} - Success with sources: {result['data_sources']}")
            
            if result.get('target_data'):
                targets = result['target_data']
                logger.info(f"   Target: ${targets.get('avg_target_price', 'N/A')} (Analysts: {targets.get('num_analysts', 'N/A')})")
            
            if result.get('rating_data'):
                ratings = result['rating_data']
                logger.info(f"   Rating: {ratings.get('consensus_rating', 'N/A')} (Total: {ratings.get('total_analysts', 'N/A')})")
        else:
            logger.warning(f"⚠️ {ticker} - Failed to get data")

if __name__ == "__main__":
    test_analyst_data_service()


