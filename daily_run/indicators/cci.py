import numpy as np
import pandas as pd

def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
    """
    Calculate Commodity Channel Index
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        window: CCI window period (default: 20)
        
    Returns:
        Series containing CCI values
    """
    tp = (high + low + close) / 3
    tp_sma = tp.rolling(window=window).mean()
    tp_md = tp.rolling(window=window).apply(lambda x: np.abs(x - x.mean()).mean())
    
    cci = (tp - tp_sma) / (0.015 * tp_md)
    return cci 