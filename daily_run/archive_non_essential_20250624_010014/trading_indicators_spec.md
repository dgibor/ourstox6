# Technical Trading Indicators Specification

## 1. List of Indicators

### Core Indicators

**Relative Strength Index (RSI)**
- **Measures:** Momentum, identifying overbought and oversold conditions.
- **Usefulness:** Identifies potential trend reversals.
- **Parameters:** Typical window: 14 periods.

**Commodity Channel Index (CCI)**
- **Measures:** Difference between current price and historical average price.
- **Usefulness:** Indicates cyclical trends, signaling overbought/oversold conditions.
- **Parameters:** Typical window: 20 periods.

**Exponential Moving Averages (EMA)**
- **Measures:** Average price with emphasis on recent data.
- **Usefulness:** Identifies trends, signals crossovers (buy/sell).
- **Parameters:** Typical periods: 20 (short-term), 100 (medium-term), 200 (long-term).

**Bollinger Bands (BB)**
- **Measures:** Volatility bands around a moving average.
- **Usefulness:** Signals volatility and potential price breakouts.
- **Parameters:** Typical period: 20; Standard deviation: 2.

### Additional Recommended Indicators

**Moving Average Convergence Divergence (MACD)**
- **Measures:** Momentum and trend strength.
- **Usefulness:** Identifies potential buy/sell signals through crossovers.
- **Parameters:** Fast EMA: 12, Slow EMA: 26, Signal EMA: 9.

**Average True Range (ATR)**
- **Measures:** Market volatility.
- **Usefulness:** Adjusting stop-loss and take-profit levels.
- **Parameters:** Typical window: 14 periods.

**Volume Weighted Average Price (VWAP)**
- **Measures:** Average price weighted by volume.
- **Usefulness:** Indicates price level institutions are trading.
- **Parameters:** Daily calculation.

## 2. Calculation Details

### RSI
- **Formula:** RSI = 100 - (100 / (1 + Average Gain / Average Loss))
- **Inputs:** Closing prices.
- **Output:** New column (`ticker_RSI_14`).

### CCI
- **Formula:** CCI = (Typical Price - SMA of Typical Price) / (0.015 × Mean Deviation)
- **Typical Price:** (High + Low + Close) / 3
- **Inputs:** High, Low, Close prices.
- **Output:** New column (`ticker_CCI_20`).

### EMA
- **Formula:** EMA_today = (Close_today × multiplier) + (EMA_yesterday × (1 - multiplier))
- **Multiplier:** (2 / (window + 1))
- **Inputs:** Closing prices.
- **Outputs:** New columns (`ticker_EMA_20`, `ticker_EMA_100`, `ticker_EMA_200`).

### Bollinger Bands
- **Formula:**
  - Middle Band = EMA (20)
  - Upper Band = Middle Band + 2 × standard deviation
  - Lower Band = Middle Band - 2 × standard deviation
- **Inputs:** Closing prices.
- **Outputs:** New columns (`ticker_BB_upper`, `ticker_BB_middle`, `ticker_BB_lower`).

### MACD
- **Formula:** MACD Line = EMA (12) – EMA (26), Signal Line = EMA (9 of MACD Line)
- **Inputs:** Closing prices.
- **Outputs:** New columns (`ticker_MACD`, `ticker_MACD_signal`).

### ATR
- **Formula:** ATR = EMA of True Range (max[high-low, abs(high-previous close), abs(low-previous close)])
- **Inputs:** High, Low, Close prices.
- **Output:** New column (`ticker_ATR_14`).

### VWAP
- **Formula:** VWAP = (Sum of (Price × Volume)) / Total Volume
- **Inputs:** Typical Price, Volume.
- **Output:** New column (`ticker_VWAP`).

## 3. Usage Guidelines

- **RSI:**
  - Overbought: RSI > 70
  - Oversold: RSI < 30

- **CCI:**
  - Overbought: CCI > 100
  - Oversold: CCI < -100

- **EMA:**
  - Bullish: Short-term EMA crosses above long-term EMA.
  - Bearish: Short-term EMA crosses below long-term EMA.

- **Bollinger Bands:**
  - Breakout: Close price crossing above upper or below lower bands.

- **MACD:**
  - Bullish: MACD line crosses above signal line.
  - Bearish: MACD line crosses below signal line.

- **ATR:**
  - Used to set dynamic stop-loss based on volatility.

- **VWAP:**
  - Price above VWAP: Bullish intraday sentiment.
  - Price below VWAP: Bearish intraday sentiment.

## 4. Support & Resistance Levels

### Method 1: Pivot Points
- **Calculation:**
  - Pivot Point = (High + Low + Close) / 3
  - Resistance (R1, R2), Support (S1, S2): Calculated using pivot point formula.
- **Usefulness:** Intraday traders for short-term levels.

### Method 2: Local Extrema
- **Calculation:** Identify recent highs and lows over lookback window (e.g., 30 days).
- **Usefulness:** Swing traders, medium-term strategies.

## 5. Output Format

| Date | Ticker | Close | ticker_RSI_14 | ticker_CCI_20 | ticker_EMA_20 | ticker_EMA_100 | ticker_EMA_200 | ticker_BB_upper | ticker_BB_middle | ticker_BB_lower | ticker_MACD | ticker_MACD_signal | ticker_ATR_14 | ticker_VWAP |
|------|--------|-------|---------------|---------------|---------------|----------------|----------------|-----------------|------------------|-----------------|-------------|--------------------|---------------|-------------|
| YYYY-MM-DD | XYZ | 100.5 | 45.2 | 89.1 | 98.5 | 102.3 | 104.7 | 107.5 | 102.3 | 97.1 | 1.2 | 1.0 | 2.5 | 101.3 |

## 6. Extensibility Notes
- Integrate fundamental analysis (PE ratio, EPS).
- Expand to multi-timeframe analysis (weekly, monthly).
- Connect with trading APIs for automated trading systems.
- Include sentiment analysis from news sources.

