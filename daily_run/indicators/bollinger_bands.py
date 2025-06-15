import pandas as pd
import numpy as np

def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0):
    """
    Calculate Bollinger Bands for a given price series.

    Args:
        prices (pd.Series): Series of closing prices.
        window (int): The window period for the moving average.
        num_std (float): Number of standard deviations for the bands.

    Returns:
        tuple: (upper_band, middle_band, lower_band) as pd.Series
    """
    middle_band = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = middle_band + (num_std * std)
    lower_band = middle_band - (num_std * std)
    return upper_band, middle_band, lower_band 