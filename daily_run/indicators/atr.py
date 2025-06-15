import numpy as np
import pandas as pd

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Average True Range
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        window: ATR window period (default: 14)
        
    Returns:
        Series containing ATR values
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    
    return atr 