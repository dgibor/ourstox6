import numpy as np
import pandas as pd

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> tuple:
    """
    Calculate Stochastic Oscillator (%K and %D)
    
    Args:
        high: Series of high prices
        low: Series of low prices  
        close: Series of closing prices
        k_period: Period for %K calculation (default: 14)
        d_period: Period for %D SMA calculation (default: 3)
        
    Returns:
        Tuple containing (%K Series, %D Series)
    """
    # Calculate %K
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    # Prevent division by zero when highest_high == lowest_low
    range_diff = highest_high - lowest_low
    range_diff = range_diff.replace(0, np.nan)  # Replace zero range with NaN
    
    k_percent = 100 * ((close - lowest_low) / range_diff)
    
    # Calculate %D (SMA of %K)
    d_percent = k_percent.rolling(window=d_period).mean()
    
    return k_percent, d_percent 