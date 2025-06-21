# VALUE INVESTING DASHBOARD - IMPLEMENTATION GUIDE (UPDATED)

## 1. DASHBOARD PHILOSOPHY

**Core Principle:**
This dashboard translates fundamental analysis into actionable insights, helping investors identify undervalued companies with strong business fundamentals. Unlike technical analysis which focuses on price patterns, we evaluate the intrinsic value and business quality.

**Educational Framework:**
- Progressive disclosure: Simple scores for beginners, detailed metrics for advanced users
- Context-sensitive explanations via CSV files
- Three investor profiles: Conservative Value, Growth-at-Reasonable-Price (GARP), Deep Value

## 2. LAYOUT STRUCTURE

**Grid System (Matching Technical Dashboard):**
- **Header**: Company info, price, fundamental score toggle (Conservative/GARP/Deep Value)
- **Primary Cards** (2 large): Valuation Matrix, Business Quality Score
- **Secondary Cards** (4 medium): Profitability Trends, Financial Health, Growth Momentum, Management Effectiveness
- **Advanced Section**: Collapsible area for detailed ratios and peer comparison

## 3. CARD SPECIFICATIONS

### Primary Card 1: VALUATION MATRIX
**Purpose:** Shows if stock is undervalued, fairly valued, or overvalued

**Metrics Displayed:**
- P/E vs Industry Average
- P/B vs Historical Average
- EV/EBITDA vs Sector Median
- PEG Ratio (for growth consideration)
- Graham Number comparison

**Signal Strength Logic:**
- 5 (Dark Green): Trading >30% below intrinsic value
- 4 (Light Green): Trading 15-30% below intrinsic value
- 3 (Yellow): Fairly valued (±15%)
- 2 (Orange): Trading 15-30% above intrinsic value
- 1 (Red): Trading >30% above intrinsic value

### Primary Card 2: BUSINESS QUALITY SCORE
**Purpose:** Evaluates the fundamental strength of the business

**Metrics Displayed:**
- Return on Equity (ROE) trend
- Return on Invested Capital (ROIC)
- Gross/Operating Margin stability
- Free Cash Flow consistency
- Competitive position score

**Quality Assessment:**
- Consistency over 5 years
- Comparison to industry leaders
- Trend direction
- Volatility measurement

### Secondary Card 1: PROFITABILITY TRENDS
**Metrics:**
- Net Profit Margin (5-year trend)
- Operating Margin evolution
- EBITDA Margin
- Cash Conversion Cycle

### Secondary Card 2: FINANCIAL HEALTH
**Metrics:**
- Debt/Equity Ratio
- Current Ratio
- Interest Coverage
- Altman Z-Score (bankruptcy risk)
- Cash/Total Assets

### Secondary Card 3: GROWTH MOMENTUM
**Metrics:**
- Revenue Growth (3-year CAGR)
- Earnings Growth Rate
- Free Cash Flow Growth
- Book Value Growth
- Dividend Growth (if applicable)

### Secondary Card 4: MANAGEMENT EFFECTIVENESS
**Metrics:**
- Return on Assets (ROA)
- Asset Turnover
- Capital Allocation Score
- Insider Ownership %
- Share Buyback History

## 4. INVESTOR PROFILE SCORING SYSTEM

### Conservative Value Investor
**Weights:**
- Financial Health: 30%
- Valuation: 25%
- Business Quality: 20%
- Profitability: 15%
- Growth: 5%
- Management: 5%

### GARP Investor
**Weights:**
- Valuation: 25%
- Growth: 25%
- Business Quality: 20%
- Profitability: 15%
- Financial Health: 10%
- Management: 5%

### Deep Value Investor
**Weights:**
- Valuation: 40%
- Financial Health: 25%
- Business Quality: 15%
- Profitability: 10%
- Management: 5%
- Growth: 5%

## 5. CALCULATION METHODOLOGIES

### Intrinsic Value Calculations
1. **Graham Number**: √(15 × Diluted EPS × Book Value per Share)
   - Use diluted EPS for conservative calculation
   - If negative earnings or book value, display "N/A" with explanation
   - For intangible-heavy businesses, provide adjusted calculation in tooltip

2. **DCF Simplified**: Use analyst consensus for cash flow projections
3. **Asset-Based**: Book Value with adjustments for intangibles
4. **Earnings Power**: Normalized earnings × appropriate multiple

### Business Quality Scoring
- **ROE Quality**: Adjust for leverage (ROE = ROA × Equity Multiplier)
- **ROIC**: (NOPAT / Invested Capital) compared to WACC
- **Moat Proxy**: Gross margin stability + ROIC persistence
- **FCF Quality**: FCF/Net Income ratio (quality of earnings)

### Risk Adjustments
- High debt (D/E > 2): Reduce score by 10%
- Negative FCF: Reduce score by 15%
- Declining margins: Reduce score by 5%
- High cyclicality: Adjust multiples downward

## 6. DATA HIERARCHY AND REQUIREMENTS

### Primary Data Points:
- Current Price (real-time during market hours)
- Market Cap (real-time)
- Enterprise Value (daily update)
- TTM Revenue, Earnings, FCF (quarterly update)
- Total Assets, Equity, Debt (quarterly update)
- Shares Outstanding (daily update)

### Data Handling Rules:
1. **Historical Data**: 
   - Minimum 3 years required, use available data if <5 years
   - Show "Limited History" warning for <3 years
   - Use TTM for all ratio calculations for consistency

2. **Missing Data**:
   - D/E Ratio with no debt: Display "No Debt" (positive indicator)
   - Missing metrics: Show "-" with tooltip explanation
   - Exclude from score calculation, adjust weights proportionally

3. **Update Frequency**:
   - Price & Market Cap: Every 5 minutes during market hours
   - Fundamental metrics: Daily after market close
   - Peer comparisons: Weekly on Sundays
   - Industry averages: Monthly

## 7. INDUSTRY COMPARISON LOGIC

### Classification Hierarchy:
1. Primary: Industry level (e.g., "Software")
2. Fallback: Sector level (e.g., "Technology")
3. Dynamic peer selection based on:
   - Market cap (±50% range)
   - Revenue (±50% range)
   - Minimum 5 peers required, maximum 20

### Special Entity Handling:
- **Financials**: Use P/B, ROE, NIM instead of D/E, margins
- **REITs**: Focus on FFO, dividend yield, P/FFO
- **Utilities**: Emphasize dividend stability, regulated ROE
- **Biotechs**: De-emphasize profitability, focus on cash runway

## 8. WARNING SYSTEM (ENHANCED)

### Threshold Types:
- **Absolute**: Apply regardless of industry (e.g., Altman Z < 1.8)
- **Relative**: Industry-adjusted (e.g., D/E > industry 75th percentile)
- **Dynamic**: Based on company history (e.g., margin decline >20%)

### Warning Aggregation:
- 2 yellow warnings = 1 orange warning
- 1 red warning overrides all others
- Cyclical adjustment: Reduce severity by one level for identified cyclicals

### Red Flags (🔴):
- Altman Z < 1.8 (absolute)
- Interest Coverage < 1.5x (absolute)
- Negative FCF for 2+ years (absolute)
- Debt/Equity > 90th percentile of industry (relative)

### Yellow Flags (🟡):
- Declining margins 3 years straight (dynamic)
- ROE declining while debt increasing (dynamic)
- Insider selling > 20% holdings (absolute)
- Revenue decline 2+ quarters (absolute)

## 9. CSV STRUCTURE REQUIREMENTS (ENHANCED)

### VALUATION_LOGIC.CSV
```
Investor_Type, Metric_Name, Weight_Percentage, Good_Threshold, Fair_Threshold, Poor_Threshold, Calculation_Formula, Industry_Adjustment, Explanation_Template
Conservative, P/E_Ratio, 25, "industry_avg*0.8", "industry_avg*1.0", "industry_avg*1.2", "price/diluted_eps_ttm", "true", "The P/E ratio of [VALUE] compared to industry average of [IND_AVG] suggests..."
```

### QUALITY_SCORING.CSV
```
Component_Name, Industry_Type, Excellent_Range, Good_Range, Average_Range, Poor_Range, Special_Calculation, Metric_Description
ROE, General, ">20", "15-20", "10-15", "<10", "standard", "Return on equity measures..."
ROE, Financial, ">15", "12-15", "8-12", "<8", "financial_adjusted", "For financial companies, ROE..."
```

### EDUCATIONAL_CONTENT.CSV
```
Metric_Name, Beginner_Explanation, Intermediate_Explanation, Advanced_Explanation, Why_It_Matters, Red_Flag_Levels, Learn_More_Link
P/E_Ratio, "Price divided by earnings - how much you pay for $1 of profit", "The P/E ratio contextualizes valuation against earnings power...", "P/E must be analyzed considering growth, quality, and cycle...", "Helps identify if paying too much", ">30 or <0", "/education/pe-ratio"
```

### CSV Configuration Features:
- Support for formulas using variables: industry_avg, historical_avg, peer_median
- Version control: Each CSV has version number, dashboard checks compatibility
- Refresh schedule: Educational content quarterly, thresholds monthly
- Fallback values for missing industry data

## 10. ERROR HANDLING AND DATA FRESHNESS

### Graceful Degradation Strategy:
1. Show all available data, mark missing with "-"
2. Adjust scores excluding missing components
3. Display data timestamp for each section
4. Color-code freshness: Green (<1hr), Yellow (<24hr), Red (>24hr)

### Market Holiday Handling:
- Show "Market Closed" badge
- Display last trading day's data
- Disable real-time updates
- Show next market open time

### API Failure Recovery:
- 3 retry attempts with exponential backoff
- Fallback cascade: Yahoo → Finnhub → Alpha Vantage
- Cache last successful data for 72 hours
- Admin alerts after 3 consecutive failures per source

## 11. PERFORMANCE OPTIMIZATION

### Loading Strategy:
1. Progressive loading: Score first, then cards, then details
2. Lazy load historical charts and peer comparisons
3. Virtualize long lists (peer companies)
4. Preload top 10 most viewed companies

### Caching Rules:
- Price data: 5 minutes during market, 1 hour after
- Fundamental data: 24 hours
- Industry averages: 7 days
- Calculated scores: 1 hour
- Educational content: 30 days

## 12. DASHBOARD INTEGRATION

### Cross-Dashboard Features:
1. Toggle button to switch between Technical/Fundamental views
2. Combined view shows simplified version of both (4 cards each)
3. Conflicting signals highlighted with explanation
4. Unified watchlist across both dashboards

### Export Capabilities:
- PDF: Full report with charts and explanations
- CSV: Raw data and calculated metrics
- PNG: Dashboard screenshot with watermark
- Shareable link: 30-day expiry, preserves all settings

### Mobile Adaptations:
- Swipe between investor profiles
- Tap-and-hold for detailed explanations  
- Landscape: Side-by-side card view
- Simplified mode: Only show scores and key metrics
- Native sharing integration