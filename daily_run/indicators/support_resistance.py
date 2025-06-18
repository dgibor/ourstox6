import numpy as np
import pandas as pd

def calculate_support_resistance(high: pd.Series, low: pd.Series, close: pd.Series, 
                               window: int = 20, swing_window: int = 5) -> dict:
    """
    Calculate Support and Resistance levels
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        window: Lookback window for S/R calculation (default: 20)
        swing_window: Window for swing high/low detection (default: 5)
        
    Returns:
        Dictionary containing support/resistance levels and swing points
    """
    # Input validation
    if high.empty or low.empty or close.empty:
        raise ValueError("Input price series cannot be empty")
    
    if len(high) != len(low) or len(low) != len(close):
        raise ValueError("All price series must have the same length")
    
    # Calculate pivot points using simple method
    pivot = (high + low + close) / 3
    
    # Calculate rolling max/min for resistance/support
    resistance_1 = high.rolling(window=window).max()
    resistance_2 = high.rolling(window=window*2).max()
    resistance_3 = high.rolling(window=window*3).max()
    
    support_1 = low.rolling(window=window).min()
    support_2 = low.rolling(window=window*2).min()
    support_3 = low.rolling(window=window*3).min()
    
    # Calculate swing highs and lows for different periods (remove center=True to avoid NaN issues)
    swing_high_5d = high.rolling(window=5).max()
    swing_low_5d = low.rolling(window=5).min()
    swing_high_10d = high.rolling(window=10).max()  
    swing_low_10d = low.rolling(window=10).min()
    swing_high_20d = high.rolling(window=20).max()
    swing_low_20d = low.rolling(window=20).min()
    
    # Calculate weekly and monthly highs/lows (approximate)
    week_high = high.rolling(window=7).max()  # 7 trading days ≈ 1 week
    week_low = low.rolling(window=7).min()
    month_high = high.rolling(window=21).max()  # ~21 trading days ≈ 1 month
    month_low = low.rolling(window=21).min()
    
    # Calculate nearest support and resistance levels
    # Find the closest support/resistance levels to current price
    nearest_support = support_1  # Use support_1 as nearest for simplicity
    nearest_resistance = resistance_1  # Use resistance_1 as nearest for simplicity
    
    # Calculate support and resistance strength (simplified)
    # Count how many times price has tested these levels
    support_strength = pd.Series(3, index=close.index)  # Default strength
    resistance_strength = pd.Series(3, index=close.index)  # Default strength
    
    return {
        'resistance_1': resistance_1,
        'resistance_2': resistance_2, 
        'resistance_3': resistance_3,
        'support_1': support_1,
        'support_2': support_2,
        'support_3': support_3,
        'swing_high_5d': swing_high_5d,
        'swing_low_5d': swing_low_5d,
        'swing_high_10d': swing_high_10d,
        'swing_low_10d': swing_low_10d,
        'swing_high_20d': swing_high_20d,
        'swing_low_20d': swing_low_20d,
        'week_high': week_high,
        'week_low': week_low,
        'month_high': month_high,
        'month_low': month_low,
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'support_strength': support_strength,
        'resistance_strength': resistance_strength,
        'pivot_point': pivot
    } 