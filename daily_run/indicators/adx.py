import numpy as np
import pandas as pd

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (ADX)
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        window: ADX window period (default: 14)
        
    Returns:
        Series containing ADX values
    """
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
    
    # Smooth the TR and DM values using Wilder's smoothing
    tr_smooth = tr.rolling(window=window).mean()
    plus_dm_smooth = plus_dm.rolling(window=window).mean()
    minus_dm_smooth = minus_dm.rolling(window=window).mean()
    
    # Calculate Directional Indicators (+DI and -DI)
    plus_di = 100 * (plus_dm_smooth / tr_smooth)
    minus_di = 100 * (minus_dm_smooth / tr_smooth)
    
    # Calculate Directional Index (DX)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # Calculate Average Directional Index (ADX)
    adx = dx.rolling(window=window).mean()
    
    return adx 