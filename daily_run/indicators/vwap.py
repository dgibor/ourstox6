import numpy as np
import pandas as pd

def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calculate Volume Weighted Average Price
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        volume: Series of volume values
        
    Returns:
        Series containing VWAP values
    """
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap 