import numpy as np
import pandas as pd

def detect_swing_points_advanced(high: pd.Series, low: pd.Series, close: pd.Series, 
                                window: int = 5, min_swing_strength: float = 0.02) -> tuple:
    """
    Advanced swing point detection with strength filtering
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        window: Window size for swing detection
        min_swing_strength: Minimum price movement to qualify as swing (2% default)
        
    Returns:
        Tuple of (swing_highs, swing_lows, swing_strengths) as series
    """
    swing_highs = pd.Series(False, index=high.index)
    swing_lows = pd.Series(False, index=low.index)
    swing_strengths = pd.Series(0.0, index=high.index)
    
    for i in range(window, len(high) - window):
        current_high = high.iloc[i]
        current_low = low.iloc[i]
        
        # Check if current high is a swing high
        left_highs = [high.iloc[i-j] for j in range(1, window+1)]
        right_highs = [high.iloc[i+j] for j in range(1, window+1)]
        
        if all(current_high >= h for h in left_highs) and all(current_high >= h for h in right_highs):
            # Calculate swing strength as percentage move from surrounding lows
            surrounding_lows = left_highs + right_highs
            avg_surrounding = np.mean(surrounding_lows)
            swing_strength = (current_high - avg_surrounding) / avg_surrounding
            
            if swing_strength >= min_swing_strength:
                swing_highs.iloc[i] = True
                swing_strengths.iloc[i] = swing_strength
        
        # Check if current low is a swing low
        left_lows = [low.iloc[i-j] for j in range(1, window+1)]
        right_lows = [low.iloc[i+j] for j in range(1, window+1)]
        
        if all(current_low <= l for l in left_lows) and all(current_low <= l for l in right_lows):
            # Calculate swing strength as percentage move from surrounding highs
            surrounding_highs = left_lows + right_lows
            avg_surrounding = np.mean(surrounding_highs)
            swing_strength = (avg_surrounding - current_low) / avg_surrounding
            
            if swing_strength >= min_swing_strength:
                swing_lows.iloc[i] = True
                swing_strengths.iloc[i] = swing_strength
    
    return swing_highs, swing_lows, swing_strengths

def calculate_fibonacci_levels(high: pd.Series, low: pd.Series, close: pd.Series, 
                              window: int = 20) -> dict:
    """
    Calculate Fibonacci retracement and extension levels with enhanced error handling
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        window: Window for swing detection
        
    Returns:
        Dictionary containing Fibonacci levels
    """
    try:
        # Validate input data
        if high.empty or low.empty or close.empty:
            return {f'fib_{level}': pd.Series(dtype=float) for level in ['236', '382', '500', '618', '786', '1272', '1618', '2618']}
        
        if window <= 0 or window > len(high):
            window = min(20, len(high))
        
        # Find recent swing high and low
        recent_high = high.rolling(window=window).max()
        recent_low = low.rolling(window=window).min()
        
        # Calculate price range with enhanced error handling
        price_range = recent_high - recent_low
        
        # Handle edge cases
        price_range = price_range.fillna(0)
        
        # Check for zero or negative price ranges
        zero_range_mask = price_range <= 0
        if zero_range_mask.any():
            # For zero ranges, use a small percentage of the price as range
            price_range = price_range.where(~zero_range_mask, recent_high * 0.01)
        
        # Fibonacci retracement levels (from high to low)
        fib_236 = recent_high - (0.236 * price_range)  # 23.6% retracement
        fib_382 = recent_high - (0.382 * price_range)  # 38.2% retracement
        fib_500 = recent_high - (0.500 * price_range)  # 50.0% retracement
        fib_618 = recent_high - (0.618 * price_range)  # 61.8% retracement
        fib_786 = recent_high - (0.786 * price_range)  # 78.6% retracement
        
        # Fibonacci extension levels (beyond the high)
        fib_1272 = recent_high + (1.272 * price_range)  # 127.2% extension
        fib_1618 = recent_high + (1.618 * price_range)  # 161.8% extension
        fib_2618 = recent_high + (2.618 * price_range)  # 261.8% extension
        
        # Ensure retracement levels are between high and low with bounds checking
        fib_236 = np.maximum(np.minimum(fib_236, recent_high), recent_low)
        fib_382 = np.maximum(np.minimum(fib_382, recent_high), recent_low)
        fib_500 = np.maximum(np.minimum(fib_500, recent_high), recent_low)
        fib_618 = np.maximum(np.minimum(fib_618, recent_high), recent_low)
        fib_786 = np.maximum(np.minimum(fib_786, recent_high), recent_low)
        
        # Handle NaN values in final results
        fib_236 = fib_236.fillna(0)
        fib_382 = fib_382.fillna(0)
        fib_500 = fib_500.fillna(0)
        fib_618 = fib_618.fillna(0)
        fib_786 = fib_786.fillna(0)
        fib_1272 = fib_1272.fillna(0)
        fib_1618 = fib_1618.fillna(0)
        fib_2618 = fib_2618.fillna(0)
        
        return {
            'fib_236': fib_236,
            'fib_382': fib_382,
            'fib_500': fib_500,
            'fib_618': fib_618,
            'fib_786': fib_786,
            'fib_1272': fib_1272,
            'fib_1618': fib_1618,
            'fib_2618': fib_2618
        }
        
    except Exception as e:
        # Return empty series on error
        return {f'fib_{level}': pd.Series(dtype=float) for level in ['236', '382', '500', '618', '786', '1272', '1618', '2618']}

def identify_psychological_levels(close: pd.Series) -> dict:
    """
    Identify psychological support and resistance levels
    
    Args:
        close: Series of close prices
        
    Returns:
        Dictionary containing psychological levels
    """
    current_price = close.iloc[-1]
    
    # Round to nearest psychological levels
    if current_price >= 100:
        # For stocks above $100, round to nearest $10
        base_level = round(current_price / 10) * 10
    elif current_price >= 10:
        # For stocks $10-$100, round to nearest $5
        base_level = round(current_price / 5) * 5
    else:
        # For stocks under $10, round to nearest $1
        base_level = round(current_price)
    
    # Generate psychological levels around current price
    levels = {}
    for i in range(-5, 6):  # 5 levels above and below
        if current_price >= 100:
            level = base_level + (i * 10)
        elif current_price >= 10:
            level = base_level + (i * 5)
        else:
            level = base_level + i
        
        if level > 0:
            levels[f'psych_level_{i}'] = pd.Series(level, index=close.index)
    
    return levels

def calculate_volume_weighted_levels(high: pd.Series, low: pd.Series, close: pd.Series, 
                                   volume: pd.Series, window: int = 20) -> dict:
    """
    Calculate volume-weighted support and resistance levels with enhanced error handling
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        volume: Series of volume values
        window: Window for calculation
        
    Returns:
        Dictionary containing volume-weighted levels
    """
    try:
        # Validate input data
        if high.empty or low.empty or close.empty or volume.empty:
            return {
                'vwap': pd.Series(dtype=float),
                'volume_weighted_high': pd.Series(dtype=float),
                'volume_weighted_low': pd.Series(dtype=float),
                'high_volume_levels': pd.Series(dtype=float)
            }
        
        if window <= 0 or window > len(high):
            window = min(20, len(high))
        
        # Volume-weighted average price
        typical_price = (high + low + close) / 3
        
        # Handle NaN values with forward fill
        typical_price = typical_price.fillna(method='ffill').fillna(method='bfill')
        volume = volume.fillna(0)
        
        # Calculate VWAP with enhanced zero volume handling
        volume_sum = volume.rolling(window=window).sum()
        
        # Handle zero volume scenarios
        zero_volume_mask = volume_sum == 0
        if zero_volume_mask.any():
            # For zero volume periods, use simple average
            volume_sum = volume_sum.where(~zero_volume_mask, window)
        
        # Calculate VWAP
        vwap = ((typical_price * volume).rolling(window=window).sum() / volume_sum).fillna(typical_price)
        
        # Volume-weighted high and low with error handling
        volume_weighted_high = ((high * volume).rolling(window=window).sum() / volume_sum).fillna(high)
        volume_weighted_low = ((low * volume).rolling(window=window).sum() / volume_sum).fillna(low)
        
        # Volume profile levels (price levels with highest volume)
        try:
            # Create price bins for volume profile analysis
            price_volume = pd.DataFrame({'close': close, 'volume': volume})
            
            # Handle edge cases for binning
            if len(price_volume) > 1 and price_volume['close'].nunique() > 1:
                # Create bins only if we have sufficient price variation
                bins = min(20, price_volume['close'].nunique())
                price_volume['price_bin'] = pd.cut(price_volume['close'], bins=bins, labels=False, duplicates='drop')
                
                # Group by price bins and sum volumes
                volume_profile = price_volume.groupby('price_bin')['volume'].sum()
                
                # Find price levels with highest volume
                if not volume_profile.empty:
                    high_volume_levels = volume_profile.nlargest(3)
                else:
                    high_volume_levels = pd.Series([volume.mean()], index=[0])
            else:
                # Fallback for insufficient data
                high_volume_levels = pd.Series([volume.mean()], index=[0])
                
        except Exception as e:
            # Fallback if volume profile analysis fails
            high_volume_levels = pd.Series([volume.mean()], index=[0])
        
        # Final NaN handling
        vwap = vwap.fillna(typical_price)
        volume_weighted_high = volume_weighted_high.fillna(high)
        volume_weighted_low = volume_weighted_low.fillna(low)
        
        return {
            'vwap': vwap,
            'volume_weighted_high': volume_weighted_high,
            'volume_weighted_low': volume_weighted_low,
            'high_volume_levels': high_volume_levels
        }
        
    except Exception as e:
        # Return empty series on error
        return {
            'vwap': pd.Series(dtype=float),
            'volume_weighted_high': pd.Series(dtype=float),
            'volume_weighted_low': pd.Series(dtype=float),
            'high_volume_levels': pd.Series(dtype=float)
        }

def calculate_dynamic_support_resistance(high: pd.Series, low: pd.Series, close: pd.Series,
                                       window: int = 20, std_multiplier: float = 2.0) -> dict:
    """
    Calculate dynamic support and resistance using statistical methods with enhanced error handling
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        window: Window for calculation
        std_multiplier: Standard deviation multiplier
        
    Returns:
        Dictionary containing dynamic levels
    """
    try:
        # Validate input data
        if high.empty or low.empty or close.empty:
            return {
                'dynamic_resistance': pd.Series(dtype=float),
                'dynamic_support': pd.Series(dtype=float),
                'keltner_upper': pd.Series(dtype=float),
                'keltner_lower': pd.Series(dtype=float)
            }
        
        if window <= 0 or window > len(close):
            window = min(20, len(close))
        
        if std_multiplier <= 0:
            std_multiplier = 2.0
        
        # Dynamic levels based on price volatility
        price_mean = close.rolling(window=window).mean()
        price_std = close.rolling(window=window).std()
        
        # Handle NaN values with forward fill and backward fill
        price_mean = price_mean.fillna(method='ffill').fillna(method='bfill')
        price_std = price_std.fillna(0)
        
        # Ensure price_std is not zero to avoid division issues
        price_std = price_std.where(price_std > 0, close.std() * 0.01)
        
        dynamic_resistance = price_mean + (std_multiplier * price_std)
        dynamic_support = price_mean - (std_multiplier * price_std)
        
        # Ensure resistance is above support with bounds checking
        dynamic_resistance = np.maximum(dynamic_resistance, dynamic_support + (price_std * 0.1))
        dynamic_support = np.minimum(dynamic_support, dynamic_resistance - (price_std * 0.1))
        
        # Keltner Channel style levels
        atr = calculate_atr(high, low, close, window)
        atr = atr.fillna(0)
        
        # Ensure ATR is not zero
        atr = atr.where(atr > 0, price_std * 0.5)
        
        keltner_upper = price_mean + (std_multiplier * atr)
        keltner_lower = price_mean - (std_multiplier * atr)
        
        # Ensure Keltner levels are properly ordered
        keltner_upper = np.maximum(keltner_upper, keltner_lower + (atr * 0.1))
        keltner_lower = np.minimum(keltner_lower, keltner_upper - (atr * 0.1))
        
        # Final NaN handling
        dynamic_resistance = dynamic_resistance.fillna(close)
        dynamic_support = dynamic_support.fillna(close)
        keltner_upper = keltner_upper.fillna(close)
        keltner_lower = keltner_lower.fillna(close)
        
        return {
            'dynamic_resistance': dynamic_resistance,
            'dynamic_support': dynamic_support,
            'keltner_upper': keltner_upper,
            'keltner_lower': keltner_lower
        }
        
    except Exception as e:
        # Return empty series on error
        return {
            'dynamic_resistance': pd.Series(dtype=float),
            'dynamic_support': pd.Series(dtype=float),
            'keltner_upper': pd.Series(dtype=float),
            'keltner_lower': pd.Series(dtype=float)
        }

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Average True Range for Keltner Channels"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    return atr

def calculate_support_resistance_strength_enhanced(high: pd.Series, low: pd.Series, close: pd.Series, 
                                                 volume: pd.Series, support_levels: pd.Series, 
                                                 resistance_levels: pd.Series, window: int = 20) -> tuple:
    """
    Enhanced support and resistance strength calculation with volume analysis
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        volume: Series of volume values
        support_levels: Series of support levels
        resistance_levels: Series of resistance levels
        window: Lookback window for strength calculation
        
    Returns:
        Tuple of (support_strength, resistance_strength, volume_confirmation)
    """
    support_strength = pd.Series(1, index=close.index, dtype=int)
    resistance_strength = pd.Series(1, index=close.index, dtype=int)
    volume_confirmation = pd.Series(0, index=close.index, dtype=int)
    
    for i in range(window, len(close)):
        # Calculate support strength with volume confirmation
        support_touches = 0
        support_bounces = 0
        support_volume = 0
        
        for j in range(i-window, i):
            if not pd.isna(support_levels.iloc[j]):
                # Count touches (price comes close to support)
                if abs(low.iloc[j] - support_levels.iloc[j]) / support_levels.iloc[j] < 0.01:  # 1% tolerance
                    support_touches += 1
                    support_volume += volume.iloc[j]
                    
                    # Count bounces (price bounces off support)
                    if j < len(close) - 1 and close.iloc[j+1] > close.iloc[j]:
                        support_bounces += 1
        
        # Enhanced strength calculation
        if support_touches > 0:
            # Base strength from touches and bounces
            base_strength = 1 + support_touches + support_bounces
            
            # Volume confirmation bonus
            avg_volume = support_volume / support_touches if support_touches > 0 else 0
            current_avg_volume = volume.iloc[i-window:i].mean()
            volume_bonus = min(2, avg_volume / current_avg_volume) if current_avg_volume > 0 else 0
            
            support_strength.iloc[i] = min(10, base_strength + volume_bonus)
            volume_confirmation.iloc[i] = 1 if volume_bonus > 1.5 else 0
        
        # Calculate resistance strength with volume confirmation
        resistance_touches = 0
        resistance_bounces = 0
        resistance_volume = 0
        
        for j in range(i-window, i):
            if not pd.isna(resistance_levels.iloc[j]):
                # Count touches (price comes close to resistance)
                if abs(high.iloc[j] - resistance_levels.iloc[j]) / resistance_levels.iloc[j] < 0.01:  # 1% tolerance
                    resistance_touches += 1
                    resistance_volume += volume.iloc[j]
                    
                    # Count bounces (price bounces off resistance)
                    if j < len(close) - 1 and close.iloc[j+1] < close.iloc[j]:
                        resistance_bounces += 1
        
        # Enhanced strength calculation
        if resistance_touches > 0:
            # Base strength from touches and bounces
            base_strength = 1 + resistance_touches + resistance_bounces
            
            # Volume confirmation bonus
            avg_volume = resistance_volume / resistance_touches if resistance_touches > 0 else 0
            current_avg_volume = volume.iloc[i-window:i].mean()
            volume_bonus = min(2, avg_volume / current_avg_volume) if current_avg_volume > 0 else 0
            
            resistance_strength.iloc[i] = min(10, base_strength + volume_bonus)
            volume_confirmation.iloc[i] = 1 if volume_bonus > 1.5 else 0
    
    return support_strength, resistance_strength, volume_confirmation

def find_nearest_levels_enhanced(close: pd.Series, support_levels: pd.Series, 
                                resistance_levels: pd.Series, fibonacci_levels: dict,
                                psychological_levels: dict) -> tuple:
    """
    Enhanced nearest level detection including Fibonacci and psychological levels
    
    Args:
        close: Series of close prices
        support_levels: Series of support levels
        resistance_levels: Series of resistance levels
        fibonacci_levels: Dictionary of Fibonacci levels
        psychological_levels: Dictionary of psychological levels
        
    Returns:
        Tuple of (nearest_support, nearest_resistance, level_type)
    """
    nearest_support = pd.Series(dtype=float, index=close.index)
    nearest_resistance = pd.Series(dtype=float, index=close.index)
    level_type = pd.Series(dtype=str, index=close.index)
    
    for i in range(len(close)):
        current_price = close.iloc[i]
        
        # Collect all potential levels
        all_levels = []
        
        # Add traditional support/resistance
        if not pd.isna(support_levels.iloc[i]):
            all_levels.append(('support', support_levels.iloc[i]))
        if not pd.isna(resistance_levels.iloc[i]):
            all_levels.append(('resistance', resistance_levels.iloc[i]))
        
        # Add Fibonacci levels
        for fib_name, fib_series in fibonacci_levels.items():
            if not pd.isna(fib_series.iloc[i]):
                level_type_fib = 'fib_support' if fib_series.iloc[i] < current_price else 'fib_resistance'
                all_levels.append((level_type_fib, fib_series.iloc[i]))
        
        # Add psychological levels
        for psych_name, psych_series in psychological_levels.items():
            if not pd.isna(psych_series.iloc[i]):
                level_type_psych = 'psych_support' if psych_series.iloc[i] < current_price else 'psych_resistance'
                all_levels.append((level_type_psych, psych_series.iloc[i]))
        
        # Find nearest support and resistance
        supports = [(level_type, level) for level_type, level in all_levels if level < current_price]
        resistances = [(level_type, level) for level_type, level in all_levels if level > current_price]
        
        if supports:
            nearest_support_info = min(supports, key=lambda x: current_price - x[1])
            nearest_support.iloc[i] = nearest_support_info[1]
            level_type.iloc[i] = f"nearest_{nearest_support_info[0]}"
        
        if resistances:
            nearest_resistance_info = min(resistances, key=lambda x: x[1] - current_price)
            nearest_resistance.iloc[i] = nearest_resistance_info[1]
            if pd.isna(level_type.iloc[i]):
                level_type.iloc[i] = f"nearest_{nearest_resistance_info[0]}"
    
    return nearest_support, nearest_resistance, level_type

def calculate_pivot_points_enhanced(high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
    """
    Enhanced pivot point calculation with multiple methods
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        
    Returns:
        Dictionary containing different pivot point calculations
    """
    # Standard pivot point
    pivot_standard = (high + low + close) / 3
    
    # Fibonacci pivot point
    pivot_fib = (high + low + close) / 3  # Same as standard for daily
    
    # Camarilla pivot point
    pivot_camarilla = (high + low + close) / 3
    
    # Woodie pivot point
    pivot_woodie = (high + low + (close * 2)) / 4
    
    # DeMark pivot point - fix the Series comparison issue
    close_shift = close.shift(1)
    low_shift = low.shift(1)
    high_shift = high.shift(1)
    
    # Use numpy.where for vectorized conditional logic
    x = np.where(close_shift < low_shift, 
                 high + (low * 2) + close,
                 np.where(close_shift > high_shift,
                         (high * 2) + low + close,
                         high + low + (close * 2)))
    
    pivot_demark = pd.Series(x / 4, index=close.index)
    
    return {
        'pivot_point': pivot_standard,
        'pivot_fibonacci': pivot_fib,
        'pivot_camarilla': pivot_camarilla,
        'pivot_woodie': pivot_woodie,
        'pivot_demark': pivot_demark
    }

def calculate_support_resistance(high: pd.Series, low: pd.Series, close: pd.Series, 
                               volume: pd.Series = None, window: int = 20, swing_window: int = 5) -> dict:
    """
    Enhanced Support and Resistance calculation with multiple methods
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        volume: Series of volume values (optional)
        window: Lookback window for S/R calculation (default: 20)
        swing_window: Window for swing high/low detection (default: 5)
        
    Returns:
        Dictionary containing comprehensive support/resistance levels
    """
    # Input validation
    if high.empty or low.empty or close.empty:
        raise ValueError("Input price series cannot be empty")
    
    if len(high) != len(low) or len(low) != len(close):
        raise ValueError("All price series must have the same length")
    
    # Basic support and resistance levels
    support_1 = low.rolling(window=window).min()
    support_2 = low.rolling(window=window*2).min()
    support_3 = low.rolling(window=window*3).min()
    
    resistance_1 = high.rolling(window=window).max()
    resistance_2 = high.rolling(window=window*2).max()
    resistance_3 = high.rolling(window=window*3).max()
    
    # Enhanced pivot points
    pivot_points = calculate_pivot_points_enhanced(high, low, close)
    
    # Advanced swing point detection
    swing_highs, swing_lows, swing_strengths = detect_swing_points_advanced(high, low, close, swing_window)
    
    # Swing highs and lows for different periods
    swing_high_5d = high.rolling(window=5).max()
    swing_low_5d = low.rolling(window=5).min()
    swing_high_10d = high.rolling(window=10).max()
    swing_low_10d = low.rolling(window=10).min()
    swing_high_20d = high.rolling(window=20).max()
    swing_low_20d = low.rolling(window=20).min()
    
    # Weekly and monthly highs/lows
    week_high = high.rolling(window=7).max()
    week_low = low.rolling(window=7).min()
    month_high = high.rolling(window=21).max()
    month_low = low.rolling(window=21).min()
    
    # Fibonacci levels
    fibonacci_levels = calculate_fibonacci_levels(high, low, close, window)
    
    # Psychological levels
    psychological_levels = identify_psychological_levels(close)
    
    # Dynamic levels
    dynamic_levels = calculate_dynamic_support_resistance(high, low, close, window)
    
    # Volume-weighted levels (if volume data available)
    volume_levels = {}
    if volume is not None:
        volume_levels = calculate_volume_weighted_levels(high, low, close, volume, window)
    
    # Enhanced strength calculation
    if volume is not None:
        support_strength, resistance_strength, volume_confirmation = calculate_support_resistance_strength_enhanced(
            high, low, close, volume, support_1, resistance_1, window
        )
    else:
        support_strength, resistance_strength = calculate_support_resistance_strength(
            high, low, close, support_1, resistance_1, window
        )
        volume_confirmation = pd.Series(0, index=close.index, dtype=int)
    
    # Enhanced nearest level detection
    nearest_support, nearest_resistance, level_type = find_nearest_levels_enhanced(
        close, support_1, resistance_1, fibonacci_levels, psychological_levels
    )
    
    # Compile comprehensive results
    result = {
        # Basic levels
        'resistance_1': resistance_1,
        'resistance_2': resistance_2,
        'resistance_3': resistance_3,
        'support_1': support_1,
        'support_2': support_2,
        'support_3': support_3,
        
        # Swing points
        'swing_high_5d': swing_high_5d,
        'swing_low_5d': swing_low_5d,
        'swing_high_10d': swing_high_10d,
        'swing_low_10d': swing_low_10d,
        'swing_high_20d': swing_high_20d,
        'swing_low_20d': swing_low_20d,
        
        # Time-based levels
        'week_high': week_high,
        'week_low': week_low,
        'month_high': month_high,
        'month_low': month_low,
        
        # Enhanced features
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'support_strength': support_strength,
        'resistance_strength': resistance_strength,
        'volume_confirmation': volume_confirmation,
        'level_type': level_type,
        'swing_strengths': swing_strengths,
        
        # Pivot points
        **pivot_points,
        
        # Fibonacci levels
        **fibonacci_levels,
        
        # Dynamic levels
        **dynamic_levels,
    }
    
    # Add volume levels if available
    if volume_levels:
        result.update(volume_levels)
    
    # Add psychological levels
    result.update(psychological_levels)
    
    return result

# Legacy functions for backward compatibility
def detect_swing_points(high: pd.Series, low: pd.Series, window: int = 5) -> tuple:
    """Legacy swing point detection for backward compatibility"""
    swing_highs, swing_lows, _ = detect_swing_points_advanced(high, low, pd.Series(), window)
    return swing_highs, swing_lows

def calculate_pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Legacy pivot point calculation for backward compatibility"""
    return (high + low + close) / 3

def calculate_support_resistance_strength(high: pd.Series, low: pd.Series, close: pd.Series, 
                                        support_levels: pd.Series, resistance_levels: pd.Series,
                                        window: int = 20) -> tuple:
    """Legacy strength calculation for backward compatibility"""
    support_strength, resistance_strength, _ = calculate_support_resistance_strength_enhanced(
        high, low, close, pd.Series(1, index=close.index), support_levels, resistance_levels, window
    )
    return support_strength, resistance_strength

def find_nearest_levels(close: pd.Series, support_levels: pd.Series, resistance_levels: pd.Series) -> tuple:
    """Legacy nearest level detection for backward compatibility"""
    nearest_support, nearest_resistance, _ = find_nearest_levels_enhanced(
        close, support_levels, resistance_levels, {}, {}
    )
    return nearest_support, nearest_resistance 