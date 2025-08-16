#!/usr/bin/env python3
"""
IMPROVED ALIGNMENT SCORING
Adjusts thresholds and scoring logic to better align with AI sentiment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_ai_comparison_table import ComprehensiveAIComparison
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class ImprovedAlignmentScoring(ComprehensiveAIComparison):
    def __init__(self):
        super().__init__()
    
    def calculate_fundamental_health(self, data, sector_weights):
        """Enhanced fundamental health calculation with more conservative scoring"""
        try:
            # More conservative base score
            base_score = sector_weights.get('base_score_fundamental', 45)  # Reduced from 50
            score = base_score
            factors = 0
            
            # Market Cap Analysis (0-12 points) - Reduced from 15
            if pd.notna(data['market_cap']) and data['market_cap'] > 0:
                market_cap_b = data['market_cap'] / 1_000_000_000
                if market_cap_b > 500:  # Mega cap
                    score += 12
                elif market_cap_b > 100:  # Large cap
                    score += 10
                elif market_cap_b > 10:  # Mid cap
                    score += 7
                elif market_cap_b > 2:  # Small cap
                    score += 4
                else:  # Micro cap
                    score += 2
                factors += 1
                
            # Revenue Growth & Profitability (0-18 points) - More conservative
            if pd.notna(data['revenue_ttm']) and pd.notna(data['net_income_ttm']):
                if data['revenue_ttm'] > 0 and data['net_income_ttm'] > 0:
                    profit_margin = data['net_income_ttm'] / data['revenue_ttm']
                    if profit_margin > 0.30:  # 30%+ margin (raised bar)
                        score += 18
                    elif profit_margin > 0.20:  # 20%+ margin
                        score += 14
                    elif profit_margin > 0.15:  # 15%+ margin
                        score += 10
                    elif profit_margin > 0.10:  # 10%+ margin
                        score += 6
                    elif profit_margin > 0.05:  # 5%+ margin
                        score += 3
                    else:  # Low margin
                        score += 0
                elif data['revenue_ttm'] > 0:  # Revenue positive but loss
                    score += 1  # Reduced penalty
                factors += 1
                
            # Debt Management (0-12 points) - More conservative
            if pd.notna(data['total_debt']) and pd.notna(data['revenue_ttm']):
                if data['revenue_ttm'] > 0:
                    debt_to_revenue = data['total_debt'] / data['revenue_ttm']
                    if debt_to_revenue < 0.3:  # Very low debt (raised bar)
                        score += 12
                    elif debt_to_revenue < 0.6:  # Low debt
                        score += 8
                    elif debt_to_revenue < 1.0:  # Moderate debt
                        score += 5
                    elif debt_to_revenue < 1.5:  # High debt
                        score += 2
                    else:  # Very high debt
                        score += 0
                factors += 1
                
            # Cash Flow Analysis (0-8 points) - More conservative
            if pd.notna(data['free_cash_flow']):
                if data['free_cash_flow'] > 1_000_000_000:  # Strong FCF (>$1B)
                    score += 8
                elif data['free_cash_flow'] > 0:  # Positive FCF
                    score += 5
                elif data['free_cash_flow'] > -500_000_000:  # Minor negative FCF
                    score += 2
                else:  # Significant negative FCF
                    score += 0
                factors += 1
            
            # Apply normalization with lower max
            if factors > 0:
                max_possible_score = base_score + 50  # Reduced from 60
                score = min(score, max_possible_score)
                
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating fundamental health: {e}")
            return 45  # More conservative neutral score
    
    def calculate_technical_health(self, data, sector_weights):
        """Enhanced technical health with more conservative scoring"""
        try:
            # More conservative base score
            base_score = sector_weights.get('base_score_technical', 35)  # Reduced from 40
            score = base_score
            factors = 0
            
            # RSI Analysis (0-18 points) - More conservative
            if pd.notna(data['rsi_14']):
                rsi = data['rsi_14']
                if 45 <= rsi <= 55:  # Very neutral zone - best
                    score += 18
                elif 40 <= rsi <= 60:  # Good zone
                    score += 15
                elif 35 <= rsi <= 65:  # Acceptable zone
                    score += 12
                elif 30 <= rsi <= 70:  # Wider acceptable
                    score += 8
                elif rsi < 25:  # Very oversold - opportunity
                    score += 10
                elif rsi > 75:  # Very overbought - risky
                    score += 3
                else:  # Moderate zones
                    score += 5
                factors += 1
                
            # MACD Analysis (0-12 points) - More conservative
            if pd.notna(data['macd_line']):
                macd = data['macd_line']
                if macd > 1.0:  # Strong bullish
                    score += 12
                elif macd > 0.5:  # Moderate bullish
                    score += 10
                elif macd > 0:  # Slight bullish
                    score += 8
                elif macd > -0.5:  # Slight bearish
                    score += 5
                else:  # Strong bearish
                    score += 2
                factors += 1
                
            # Moving Averages (0-15 points) - More conservative
            if pd.notna(data['ema_20']) and pd.notna(data['ema_50']):
                ema_20 = self.get_scaled_price(data['ema_20'])
                ema_50 = self.get_scaled_price(data['ema_50'])
                current_price = self.get_scaled_price(data['current_price'])
                
                if current_price > ema_20 > ema_50:
                    price_momentum = (current_price - ema_50) / ema_50
                    if price_momentum > 0.10:  # Strong uptrend (>10%)
                        score += 15
                    elif price_momentum > 0.05:  # Moderate uptrend
                        score += 12
                    else:  # Weak uptrend
                        score += 8
                elif current_price > ema_50:
                    score += 6  # Above long-term average
                elif current_price > ema_20:
                    score += 4   # Short-term strength only
                else:
                    score += 1   # Downtrend
                factors += 1
                
            # Price vs 200 SMA (0-15 points) - More conservative
            if pd.notna(data['sma_200']):
                sma_200 = self.get_scaled_price(data['sma_200'])
                current_price = self.get_scaled_price(data['current_price'])
                
                price_vs_sma = (current_price - sma_200) / sma_200
                if price_vs_sma > 0.25:  # 25% above 200 SMA
                    score += 15
                elif price_vs_sma > 0.15:  # 15% above
                    score += 12
                elif price_vs_sma > 0.05:  # 5% above 200 SMA
                    score += 8
                elif price_vs_sma > 0:  # Above 200 SMA
                    score += 5
                elif price_vs_sma > -0.05:  # Slightly below
                    score += 3
                else:  # Well below 200 SMA
                    score += 0
                factors += 1
            
            # Apply normalization with lower max
            if factors > 0:
                max_possible_score = base_score + 60  # Same max
                score = min(score, max_possible_score)
                
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating technical health: {e}")
            return 35  # More conservative neutral score
    
    def get_rating(self, composite_score, sector_weights):
        """Improved rating thresholds based on AI score analysis"""
        try:
            # OPTIMIZED thresholds based on AI score patterns:
            # AI Strong Buy avg: 68.5, AI Buy avg: 67.5, AI Hold avg: 65.6
            # AI Sell avg: 58.9, AI Strong Sell avg: 59.9
            
            if composite_score >= 70:    # Higher bar for Strong Buy
                return "Strong Buy"
            elif composite_score >= 64:  # Aligned with AI Buy average
                return "Buy"
            elif composite_score >= 60:  # More conservative Hold range
                return "Hold"
            elif composite_score >= 57:  # Aligned with AI Sell range
                return "Sell"
            else:                        # < 57 for Strong Sell
                return "Strong Sell"
                
        except Exception as e:
            logger.error(f"Error determining rating: {e}")
            return "Hold"
    
    def calculate_composite_score(self, fundamental_health, technical_health, vwap_sr_score, sector_weights):
        """Adjusted composite scoring with sector-specific optimizations"""
        try:
            # Get sector for specific adjustments
            sector = sector_weights.get('sector', 'Default')
            
            # Base weights
            fund_weight = sector_weights.get('fundamental_weight', 0.35)
            tech_weight = sector_weights.get('technical_weight', 0.25)
            vwap_weight = sector_weights.get('vwap_sr_weight', 0.25)
            sentiment_weight = sector_weights.get('market_sentiment_weight', 0.15)
            
            # Sector-specific adjustments for better alignment
            if sector == 'Technology':
                # Tech stocks: Reduce fundamental weight, increase technical
                fund_weight *= 0.9
                tech_weight *= 1.1
                vwap_weight *= 1.05
            elif sector == 'Healthcare':
                # Healthcare: Higher fundamental weight, conservative technical
                fund_weight *= 1.1
                tech_weight *= 0.9
            elif sector == 'Financial':
                # Financial: Balance fundamental and technical
                fund_weight *= 1.05
                tech_weight *= 0.95
            elif sector == 'Energy':
                # Energy: More conservative overall
                fund_weight *= 0.95
                tech_weight *= 0.95
                vwap_weight *= 0.9
            
            # Market Sentiment (adjusted calculation)
            market_sentiment = (fundamental_health * 0.4 + technical_health * 0.3 + vwap_sr_score * 0.3)
            
            # Apply sector-specific penalty for struggling sectors
            if sector == 'Energy':
                market_sentiment *= 0.95  # Energy sector discount
            elif sector == 'Communication Services':
                market_sentiment *= 0.93  # Communications sector discount
            
            # Calculate weighted composite score
            composite_score = (
                fundamental_health * fund_weight +
                technical_health * tech_weight +
                vwap_sr_score * vwap_weight +
                market_sentiment * sentiment_weight
            )
            
            return max(0, min(100, composite_score))
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 50

def main():
    """Test the improved alignment system"""
    test_system = ImprovedAlignmentScoring()
    
    if not test_system.connect_db():
        print("❌ Database connection failed")
        return
        
    if not test_system.load_sector_weights():
        print("❌ Failed to load sector weights")
        test_system.disconnect_db()
        return
    
    # Test on the same 40 tickers
    test_tickers = [
        # Technology
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
        'CRM', 'ORCL', 'ADBE', 'CSCO', 'QCOM',
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO', 'DHR',
        # Financial
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK',
        # Energy
        'XOM', 'CVX', 'COP', 'SLB',
        # Consumer
        'HD', 'MCD', 'KO', 'PEP',
        # Industrial
        'CAT', 'BA', 'GE',
        # Communication
        'DIS', 'CMCSA'
    ]
    
    print("🎯 TESTING IMPROVED ALIGNMENT ON 40 TICKERS...")
    
    results = []
    for i, ticker in enumerate(test_tickers, 1):
        print(f"   Processing {ticker} ({i}/{len(test_tickers)})...")
        result = test_system.score_stock(ticker)
        if result:
            results.append(result)
    
    # Export to CSV
    csv_file = test_system.export_to_csv(results, "improved_alignment_results.csv")
    
    # Analyze alignment
    df = pd.DataFrame([{
        'Ticker': r['ticker'],
        'Our_Rating': r['our_rating'],
        'AI_Rating': r['ai_rating'],
        'Combined_Score': r['composite_score'],
        'Sector': r['sector']
    } for r in results])
    
    # Calculate alignment
    exact_matches = sum(1 for r in results if r['our_rating'] == r['ai_rating'])
    close_matches = 0
    
    rating_values = {'Strong Sell': 1, 'Sell': 2, 'Hold': 3, 'Buy': 4, 'Strong Buy': 5}
    for r in results:
        our_val = rating_values.get(r['our_rating'], 3)
        ai_val = rating_values.get(r['ai_rating'], 3)
        if abs(our_val - ai_val) == 1:
            close_matches += 1
    
    total_alignment = (exact_matches + close_matches) / len(results) * 100
    
    print(f"\n🎯 IMPROVED ALIGNMENT RESULTS:")
    print(f"   Total Stocks: {len(results)}")
    print(f"   Exact Matches: {exact_matches}/{len(results)} ({exact_matches/len(results)*100:.1f}%)")
    print(f"   Close Matches: {close_matches}/{len(results)} ({close_matches/len(results)*100:.1f}%)")
    print(f"   Total Good Alignment: {total_alignment:.1f}%")
    
    # Rating distribution
    our_counts = {}
    ai_counts = {}
    for r in results:
        our_counts[r['our_rating']] = our_counts.get(r['our_rating'], 0) + 1
        ai_counts[r['ai_rating']] = ai_counts.get(r['ai_rating'], 0) + 1
    
    print(f"\n📊 RATING DISTRIBUTIONS:")
    rating_order = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
    
    print(f"   OUR SYSTEM:")
    for rating in rating_order:
        count = our_counts.get(rating, 0)
        pct = (count / len(results) * 100) if len(results) > 0 else 0
        print(f"     {rating}: {count} ({pct:.1f}%)")
    
    print(f"   AI SYSTEM:")
    for rating in rating_order:
        count = ai_counts.get(rating, 0)
        pct = (count / len(results) * 100) if len(results) > 0 else 0
        print(f"     {rating}: {count} ({pct:.1f}%)")
    
    test_system.disconnect_db()
    print(f"\n✅ COMPLETED! Improved results saved to: {csv_file}")

if __name__ == "__main__":
    main()
