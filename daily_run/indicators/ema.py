import numpy as np
import pandas as pd

def calculate_ema(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate Exponential Moving Average
    
    Args:
        prices: Series of closing prices
        window: EMA window period
        
    Returns:
        Series containing EMA values
    """
    multiplier = 2 / (window + 1)
    ema = prices.ewm(span=window, adjust=False).mean()
    return ema 