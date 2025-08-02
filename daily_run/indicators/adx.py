import numpy as np
import pandas as pd

def wilder_smoothing(series: pd.Series, period: int) -> pd.Series:
    """
    Implement Wilder's smoothing formula for ADX calculation
    
    Args:
        series: Input series to smooth
        period: Smoothing period
        
    Returns:
        Smoothed series using Wilder's method
    """
    smoothed = pd.Series(index=series.index, dtype=float)
    
    # Initialize first smoothed value as sum of first 'period' values
    smoothed.iloc[period-1] = series.iloc[:period].sum()
    
    # Apply Wilder's smoothing formula
    for i in range(period, len(series)):
        smoothed.iloc[i] = smoothed.iloc[i-1] - (smoothed.iloc[i-1]/period) + series.iloc[i]
    
    return smoothed

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (ADX) using Wilder's smoothing
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        window: ADX window period (default: 14)
        
    Returns:
        Series containing ADX values (0-100 range)
    """
    try:
        # Validate inputs
        if len(high) < window * 2:
            return pd.Series(dtype=float)
        
        # Calculate True Range (TR)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement (DM)
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        # Positive Directional Movement (+DM)
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        plus_dm = pd.Series(plus_dm, index=high.index)
        
        # Negative Directional Movement (-DM)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        minus_dm = pd.Series(minus_dm, index=high.index)
        
        # Apply Wilder's smoothing to TR and DM values
        tr_smooth = wilder_smoothing(tr, window)
        plus_dm_smooth = wilder_smoothing(plus_dm, window)
        minus_dm_smooth = wilder_smoothing(minus_dm, window)
        
        # Calculate Directional Indicators (+DI and -DI) with division by zero protection
        plus_di = 100 * (plus_dm_smooth / tr_smooth.replace(0, np.nan))
        minus_di = 100 * (minus_dm_smooth / tr_smooth.replace(0, np.nan))
        
        # Calculate Directional Index (DX) with division by zero protection
        di_sum = plus_di + minus_di
        di_sum = di_sum.replace(0, np.nan)  # Prevent division by zero
        dx = 100 * abs(plus_di - minus_di) / di_sum
        
        # Calculate Average Directional Index (ADX) using Wilder's smoothing
        adx = wilder_smoothing(dx, window)
        
        # Ensure ADX is in valid range (0-100) and handle NaN values
        adx = adx.clip(0, 100)  # Clip to valid range
        adx = adx.fillna(0)     # Replace NaN with 0
        
        return adx
        
    except Exception as e:
        # Return empty series on any calculation error
        return pd.Series(dtype=float) 