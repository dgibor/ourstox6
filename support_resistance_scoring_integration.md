# Support & Resistance Integration with Stock Scoring System

## Overview

This document explains how support and resistance levels are calculated in our system and provides recommendations for integrating them into the stock scoring algorithm to enhance trading decisions.

## Current Support & Resistance Calculation Methods

### 1. Multi-Timeframe Approach

Our system calculates support and resistance using three different time windows to ensure varied levels:

#### Support Levels
- **Support 1 (S1)**: Recent swing low - Last 20 days minimum
- **Support 2 (S2)**: Medium-term support - Last 50 days minimum  
- **Support 3 (S3)**: Long-term support - Last 100 days minimum

#### Resistance Levels
- **Resistance 1 (R1)**: Recent swing high - Last 20 days maximum
- **Resistance 2 (R2)**: Medium-term resistance - Last 50 days maximum
- **Resistance 3 (R3)**: Long-term resistance - Last 100 days maximum

### 2. Offset Algorithm

To ensure levels are always different (addressing the previous issue where S1=S2=S3), we apply small offsets:

```python
# Support offsets
if medium_low == support_1:
    medium_low = medium_low * 0.995  # 0.5% below
if long_low == support_1 or long_low == support_2:
    long_low = long_low * 0.99      # 1% below

# Resistance offsets  
if medium_high == resistance_1:
    medium_high = medium_high * 1.005  # 0.5% above
if long_high == resistance_1 or long_high == resistance_2:
    long_high = long_high * 1.01      # 1% above
```

### 3. Additional Technical Levels

Beyond basic support/resistance, we calculate:

- **Pivot Point**: (High + Low + Close) / 3
- **Fibonacci Retracements**: 23.6%, 38.2%, 61.8% levels
- **Moving Averages**: 20-day and 50-day MA
- **VWAP**: Volume-weighted average price

## Integration with Scoring System

### Current Scoring Components

Our existing scoring system includes:
- **Fundamental Scores**: Financial ratios, earnings quality
- **Technical Scores**: RSI, MACD, moving averages
- **Market Scores**: Sector performance, market cap

### Proposed Support/Resistance Scoring Integration

#### 1. Price Position Score (25% weight)

Calculate how the current price relates to support/resistance levels:

```python
def calculate_price_position_score(current_price, support_levels, resistance_levels):
    """
    Score based on price position relative to support/resistance
    Higher score = better risk/reward ratio
    """
    # Distance to nearest support
    nearest_support = min(support_levels)
    support_distance = (current_price - nearest_support) / current_price
    
    # Distance to nearest resistance  
    nearest_resistance = min(resistance_levels)
    resistance_distance = (nearest_resistance - current_price) / current_price
    
    # Risk/reward ratio
    risk_reward_ratio = resistance_distance / support_distance if support_distance > 0 else 0
    
    # Score calculation
    if risk_reward_ratio >= 2.0:  # 2:1 or better
        return 100
    elif risk_reward_ratio >= 1.5:
        return 80
    elif risk_reward_ratio >= 1.0:
        return 60
    else:
        return max(20, int(risk_reward_ratio * 40))
```

#### 2. Support Strength Score (20% weight)

Evaluate the strength of support levels:

```python
def calculate_support_strength_score(price_data, support_levels):
    """
    Score based on how well support levels have held historically
    """
    scores = []
    
    for support_level in support_levels:
        # Count how many times price bounced off this level
        bounces = 0
        touches = 0
        
        for i in range(1, len(price_data)):
            if (price_data[i-1]['low'] > support_level and 
                price_data[i]['low'] <= support_level):
                touches += 1
                # Check if price bounced back up
                if price_data[i+1]['close'] > support_level:
                    bounces += 1
        
        # Calculate bounce rate
        bounce_rate = bounces / touches if touches > 0 else 0
        scores.append(bounce_rate * 100)
    
    return sum(scores) / len(scores)
```

#### 3. Resistance Breakout Potential Score (20% weight)

Assess likelihood of breaking through resistance:

```python
def calculate_breakout_potential_score(current_price, resistance_levels, volume_data):
    """
    Score based on proximity to resistance and volume confirmation
    """
    nearest_resistance = min(resistance_levels)
    distance_to_resistance = (nearest_resistance - current_price) / current_price
    
    # Volume analysis for breakout confirmation
    recent_volume_avg = sum(volume_data[-5:]) / 5
    historical_volume_avg = sum(volume_data[-20:]) / 20
    volume_ratio = recent_volume_avg / historical_volume_avg
    
    # Score calculation
    if distance_to_resistance <= 0.02:  # Within 2% of resistance
        if volume_ratio >= 1.5:  # High volume
            return 90
        elif volume_ratio >= 1.2:
            return 70
        else:
            return 50
    elif distance_to_resistance <= 0.05:  # Within 5% of resistance
        return 40
    else:
        return 20
```

#### 4. Trend Alignment Score (15% weight)

Check if support/resistance aligns with overall trend:

```python
def calculate_trend_alignment_score(price_data, support_levels, resistance_levels):
    """
    Score based on whether S/R levels align with price trend
    """
    # Calculate trend direction
    short_ma = sum([p['close'] for p in price_data[-10:]]) / 10
    long_ma = sum([p['close'] for p in price_data[-30:]]) / 30
    trend = 1 if short_ma > long_ma else -1
    
    # Check if support/resistance levels align with trend
    current_price = price_data[-1]['close']
    
    if trend == 1:  # Uptrend
        # Higher support levels are better
        support_trend_score = sum([1 for s in support_levels if s > current_price * 0.9])
        resistance_trend_score = sum([1 for r in resistance_levels if r > current_price * 1.1])
    else:  # Downtrend
        # Lower resistance levels are better
        support_trend_score = sum([1 for s in support_levels if s < current_price * 1.1])
        resistance_trend_score = sum([1 for r in resistance_levels if r < current_price * 0.9])
    
    total_score = (support_trend_score + resistance_trend_score) / 6 * 100
    return total_score
```

#### 5. Volatility Context Score (20% weight)

Adjust scoring based on market volatility:

```python
def calculate_volatility_context_score(price_data, support_levels, resistance_levels):
    """
    Score based on how S/R levels relate to current volatility
    """
    # Calculate current volatility
    returns = [(price_data[i]['close'] - price_data[i-1]['close']) / price_data[i-1]['close'] 
               for i in range(1, len(price_data))]
    volatility = (sum([r**2 for r in returns]) / len(returns))**0.5
    
    # Calculate average distance between S/R levels
    all_levels = sorted(support_levels + resistance_levels)
    level_distances = [(all_levels[i] - all_levels[i-1]) / all_levels[i-1] 
                       for i in range(1, len(all_levels))]
    avg_level_distance = sum(level_distances) / len(level_distances)
    
    # Score based on volatility vs level spacing
    if avg_level_distance >= volatility * 2:
        return 100  # Good spacing for current volatility
    elif avg_level_distance >= volatility * 1.5:
        return 80
    elif avg_level_distance >= volatility:
        return 60
    else:
        return 30  # Levels too close together for current volatility
```

## Final Composite Score

Combine all components into a final support/resistance score:

```python
def calculate_support_resistance_score(stock_data):
    """
    Calculate final S/R score for a stock
    """
    price_position = calculate_price_position_score(...) * 0.25
    support_strength = calculate_support_strength_score(...) * 0.20
    breakout_potential = calculate_breakout_potential_score(...) * 0.20
    trend_alignment = calculate_trend_alignment_score(...) * 0.15
    volatility_context = calculate_volatility_context_score(...) * 0.20
    
    final_score = (price_position + support_strength + breakout_potential + 
                   trend_alignment + volatility_context)
    
    return min(100, max(0, final_score))
```

## Integration with Existing System

### 1. Database Schema Updates

Add new fields to store S/R scores:

```sql
ALTER TABLE daily_charts ADD COLUMN support_resistance_score DECIMAL(5,2);
ALTER TABLE daily_charts ADD COLUMN price_position_score DECIMAL(5,2);
ALTER TABLE daily_charts ADD COLUMN support_strength_score DECIMAL(5,2);
ALTER TABLE daily_charts ADD COLUMN breakout_potential_score DECIMAL(5,2);
ALTER TABLE daily_charts ADD COLUMN trend_alignment_score DECIMAL(5,2);
ALTER TABLE daily_charts ADD COLUMN volatility_context_score DECIMAL(5,2);
```

### 2. Scoring Weight Distribution

Update the main scoring algorithm:

```python
# Current weights
FUNDAMENTAL_WEIGHT = 0.40
TECHNICAL_WEIGHT = 0.35
MARKET_WEIGHT = 0.25

# New weights with S/R integration
FUNDAMENTAL_WEIGHT = 0.35
TECHNICAL_WEIGHT = 0.30
SUPPORT_RESISTANCE_WEIGHT = 0.20
MARKET_WEIGHT = 0.15

final_score = (fundamental_score * FUNDAMENTAL_WEIGHT +
               technical_score * TECHNICAL_WEIGHT +
               support_resistance_score * SUPPORT_RESISTANCE_WEIGHT +
               market_score * MARKET_WEIGHT)
```

### 3. Daily Update Process

Integrate S/R scoring into the daily calculation workflow:

```python
def update_daily_scores():
    """
    Daily update process including S/R scoring
    """
    # 1. Update price data and calculate S/R levels
    update_support_resistance_levels()
    
    # 2. Calculate S/R component scores
    calculate_support_resistance_scores()
    
    # 3. Update main scoring system
    update_fundamental_scores()
    update_technical_scores()
    update_market_scores()
    
    # 4. Calculate final composite scores
    calculate_composite_scores()
```

## Implementation Priority

### Phase 1: Core S/R Calculation (Week 1-2)
- Implement multi-timeframe S/R calculation
- Add offset algorithm to ensure level variation
- Create database schema updates

### Phase 2: Scoring Components (Week 3-4)
- Implement price position scoring
- Add support strength calculation
- Create breakout potential assessment

### Phase 3: Advanced Features (Week 5-6)
- Implement trend alignment scoring
- Add volatility context analysis
- Create composite score calculation

### Phase 4: Integration & Testing (Week 7-8)
- Integrate with existing scoring system
- Performance testing and optimization
- Backtesting with historical data

## Benefits of Integration

1. **Risk Management**: Better identification of entry/exit points
2. **Trend Confirmation**: S/R levels validate technical analysis
3. **Volatility Adaptation**: Dynamic scoring based on market conditions
4. **Performance Improvement**: Enhanced scoring accuracy for trading decisions

## Monitoring & Maintenance

- **Daily Validation**: Check S/R level calculations for accuracy
- **Weekly Review**: Analyze scoring performance and adjust weights
- **Monthly Optimization**: Fine-tune algorithms based on market conditions
- **Quarterly Backtesting**: Validate scoring effectiveness with historical data

## Conclusion

Integrating support and resistance analysis into the scoring system will significantly enhance our ability to identify high-probability trading opportunities. The multi-component approach ensures robust scoring that adapts to different market conditions while maintaining consistency with our existing fundamental and technical analysis framework.

The phased implementation approach allows for gradual integration and testing, minimizing disruption to the current system while building a more comprehensive and effective stock scoring algorithm.
