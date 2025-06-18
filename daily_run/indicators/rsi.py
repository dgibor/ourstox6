import numpy as np
import pandas as pd

def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index
    
    Args:
        prices: Series of closing prices
        window: RSI window period (default: 14)
        
    Returns:
        Series containing RSI values
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    # Prevent division by zero when loss is zero
    loss = loss.replace(0, np.nan)
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi 