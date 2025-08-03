# Fundamental Health Scoring System for Novice Investors

## Executive Summary

This document proposes a comprehensive scoring system to help novice investors quickly assess the fundamental health of companies and identify potential pitfalls like excessive debt, declining sales, or poor profitability. The system uses the 27 financial ratios calculated in our application to create multiple focused scores that provide actionable insights.

## Current Ratio Categories in Our Application

Our application calculates ratios across 8 categories:

1. **Valuation Ratios** (5 ratios): P/E, P/B, P/S, EV/EBITDA, PEG
2. **Profitability Ratios** (6 ratios): ROE, ROA, ROIC, Gross Margin, Operating Margin, Net Margin
3. **Financial Health Ratios** (5 ratios): Debt-to-Equity, Current Ratio, Quick Ratio, Interest Coverage, Altman Z-Score
4. **Efficiency Ratios** (3 ratios): Asset Turnover, Inventory Turnover, Receivables Turnover
5. **Growth Metrics** (3 ratios): Revenue Growth YoY, Earnings Growth YoY, FCF Growth YoY
6. **Quality Metrics** (2 ratios): FCF to Net Income, Cash Conversion Cycle
7. **Market Data** (2 ratios): Market Cap, Enterprise Value
8. **Intrinsic Value** (1 ratio): Graham Number

## Proposed Scoring System

### 1. Overall Financial Health Score (0-100)

**Purpose**: Primary indicator of company's overall financial strength and stability.

**Components**:
- **Financial Health** (40% weight)
- **Profitability** (30% weight)
- **Quality** (20% weight)
- **Growth** (10% weight)

**Scoring Logic**:
```
Financial Health Score = 
  (Financial Health Component × 0.4) +
  (Profitability Component × 0.3) +
  (Quality Component × 0.2) +
  (Growth Component × 0.1)
```

**Grade Scale**:
- **A+ (90-100)**: Exceptional financial health
- **A (80-89)**: Excellent financial health
- **B+ (70-79)**: Good financial health
- **B (60-69)**: Above average financial health
- **C+ (50-59)**: Average financial health
- **C (40-49)**: Below average financial health
- **D (30-39)**: Poor financial health
- **F (0-29)**: Very poor financial health

### 2. Risk Assessment Score (0-100)

**Purpose**: Identify potential red flags and financial risks.

**Components**:
- **Debt Risk** (35% weight)
- **Liquidity Risk** (25% weight)
- **Profitability Risk** (25% weight)
- **Growth Risk** (15% weight)

**Scoring Logic**:
```
Risk Score = 
  (Debt Risk Component × 0.35) +
  (Liquidity Risk Component × 0.25) +
  (Profitability Risk Component × 0.25) +
  (Growth Risk Component × 0.15)
```

**Risk Levels**:
- **Low Risk (0-20)**: Minimal financial risks
- **Moderate Risk (21-40)**: Some concerns, monitor closely
- **High Risk (41-60)**: Significant risks, proceed with caution
- **Very High Risk (61-80)**: Major red flags, avoid
- **Extreme Risk (81-100)**: Critical issues, avoid at all costs

### 3. Value Investment Score (0-100)

**Purpose**: Assess whether the company represents good value for value investors.

**Components**:
- **Valuation** (40% weight)
- **Quality** (30% weight)
- **Financial Health** (20% weight)
- **Growth** (10% weight)

**Scoring Logic**:
```
Value Score = 
  (Valuation Component × 0.4) +
  (Quality Component × 0.3) +
  (Financial Health Component × 0.2) +
  (Growth Component × 0.1)
```

**Value Ratings**:
- **Excellent Value (80-100)**: Strong value proposition
- **Good Value (60-79)**: Attractive value
- **Fair Value (40-59)**: Reasonable value
- **Poor Value (20-39)**: Overvalued
- **Very Poor Value (0-19)**: Significantly overvalued

## Detailed Component Scoring

### Financial Health Component (0-100)

**Debt-to-Equity Ratio** (30% weight):
- **0-0.5**: 100 points (Excellent)
- **0.5-1.0**: 80 points (Good)
- **1.0-1.5**: 60 points (Acceptable)
- **1.5-2.0**: 40 points (Concerning)
- **2.0+**: 20 points (High Risk)

**Current Ratio** (25% weight):
- **2.0+**: 100 points (Excellent)
- **1.5-2.0**: 80 points (Good)
- **1.0-1.5**: 60 points (Acceptable)
- **0.8-1.0**: 40 points (Concerning)
- **<0.8**: 20 points (High Risk)

**Quick Ratio** (25% weight):
- **1.5+**: 100 points (Excellent)
- **1.0-1.5**: 80 points (Good)
- **0.7-1.0**: 60 points (Acceptable)
- **0.5-0.7**: 40 points (Concerning)
- **<0.5**: 20 points (High Risk)

**Interest Coverage** (20% weight):
- **5.0+**: 100 points (Excellent)
- **3.0-5.0**: 80 points (Good)
- **2.0-3.0**: 60 points (Acceptable)
- **1.5-2.0**: 40 points (Concerning)
- **<1.5**: 20 points (High Risk)

### Profitability Component (0-100)

**ROE** (25% weight):
- **15%+**: 100 points (Excellent)
- **10-15%**: 80 points (Good)
- **5-10%**: 60 points (Acceptable)
- **0-5%**: 40 points (Poor)
- **<0%**: 20 points (Very Poor)

**ROA** (20% weight):
- **8%+**: 100 points (Excellent)
- **5-8%**: 80 points (Good)
- **2-5%**: 60 points (Acceptable)
- **0-2%**: 40 points (Poor)
- **<0%**: 20 points (Very Poor)

**Net Margin** (25% weight):
- **15%+**: 100 points (Excellent)
- **10-15%**: 80 points (Good)
- **5-10%**: 60 points (Acceptable)
- **0-5%**: 40 points (Poor)
- **<0%**: 20 points (Very Poor)

**Operating Margin** (20% weight):
- **20%+**: 100 points (Excellent)
- **15-20%**: 80 points (Good)
- **10-15%**: 60 points (Acceptable)
- **5-10%**: 40 points (Poor)
- **<5%**: 20 points (Very Poor)

**ROIC** (10% weight):
- **12%+**: 100 points (Excellent)
- **8-12%**: 80 points (Good)
- **4-8%**: 60 points (Acceptable)
- **0-4%**: 40 points (Poor)
- **<0%**: 20 points (Very Poor)

### Quality Component (0-100)

**FCF to Net Income** (60% weight):
- **1.0+**: 100 points (Excellent)
- **0.8-1.0**: 80 points (Good)
- **0.6-0.8**: 60 points (Acceptable)
- **0.4-0.6**: 40 points (Poor)
- **<0.4**: 20 points (Very Poor)

**Asset Turnover** (40% weight):
- **1.5+**: 100 points (Excellent)
- **1.0-1.5**: 80 points (Good)
- **0.7-1.0**: 60 points (Acceptable)
- **0.5-0.7**: 40 points (Poor)
- **<0.5**: 20 points (Very Poor)

### Valuation Component (0-100)

**P/E Ratio** (30% weight):
- **<10**: 100 points (Excellent)
- **10-15**: 80 points (Good)
- **15-20**: 60 points (Acceptable)
- **20-25**: 40 points (Expensive)
- **25+**: 20 points (Very Expensive)

**P/B Ratio** (25% weight):
- **<1.0**: 100 points (Excellent)
- **1.0-1.5**: 80 points (Good)
- **1.5-2.5**: 60 points (Acceptable)
- **2.5-4.0**: 40 points (Expensive)
- **4.0+**: 20 points (Very Expensive)

**P/S Ratio** (25% weight):
- **<1.0**: 100 points (Excellent)
- **1.0-2.0**: 80 points (Good)
- **2.0-3.0**: 60 points (Acceptable)
- **3.0-5.0**: 40 points (Expensive)
- **5.0+**: 20 points (Very Expensive)

**EV/EBITDA** (20% weight):
- **<8**: 100 points (Excellent)
- **8-12**: 80 points (Good)
- **12-16**: 60 points (Acceptable)
- **16-20**: 40 points (Expensive)
- **20+**: 20 points (Very Expensive)

### Growth Component (0-100)

**Revenue Growth YoY** (40% weight):
- **15%+**: 100 points (Excellent)
- **10-15%**: 80 points (Good)
- **5-10%**: 60 points (Acceptable)
- **0-5%**: 40 points (Slow)
- **<0%**: 20 points (Declining)

**Earnings Growth YoY** (35% weight):
- **15%+**: 100 points (Excellent)
- **10-15%**: 80 points (Good)
- **5-10%**: 60 points (Acceptable)
- **0-5%**: 40 points (Slow)
- **<0%**: 20 points (Declining)

**FCF Growth YoY** (25% weight):
- **15%+**: 100 points (Excellent)
- **10-15%**: 80 points (Good)
- **5-10%**: 60 points (Acceptable)
- **0-5%**: 40 points (Slow)
- **<0%**: 20 points (Declining)

## Risk Assessment Scoring

### Debt Risk Component (0-100)

**Debt-to-Equity Ratio** (50% weight):
- **0-0.5**: 0 points (Low Risk)
- **0.5-1.0**: 25 points (Moderate Risk)
- **1.0-1.5**: 50 points (High Risk)
- **1.5-2.0**: 75 points (Very High Risk)
- **2.0+**: 100 points (Extreme Risk)

**Interest Coverage** (50% weight):
- **5.0+**: 0 points (Low Risk)
- **3.0-5.0**: 25 points (Moderate Risk)
- **2.0-3.0**: 50 points (High Risk)
- **1.5-2.0**: 75 points (Very High Risk)
- **<1.5**: 100 points (Extreme Risk)

### Liquidity Risk Component (0-100)

**Current Ratio** (50% weight):
- **2.0+**: 0 points (Low Risk)
- **1.5-2.0**: 25 points (Moderate Risk)
- **1.0-1.5**: 50 points (High Risk)
- **0.8-1.0**: 75 points (Very High Risk)
- **<0.8**: 100 points (Extreme Risk)

**Quick Ratio** (50% weight):
- **1.5+**: 0 points (Low Risk)
- **1.0-1.5**: 25 points (Moderate Risk)
- **0.7-1.0**: 50 points (High Risk)
- **0.5-0.7**: 75 points (Very High Risk)
- **<0.5**: 100 points (Extreme Risk)

### Profitability Risk Component (0-100)

**Net Margin** (40% weight):
- **15%+**: 0 points (Low Risk)
- **10-15%**: 25 points (Moderate Risk)
- **5-10%**: 50 points (High Risk)
- **0-5%**: 75 points (Very High Risk)
- **<0%**: 100 points (Extreme Risk)

**ROE** (30% weight):
- **15%+**: 0 points (Low Risk)
- **10-15%**: 25 points (Moderate Risk)
- **5-10%**: 50 points (High Risk)
- **0-5%**: 75 points (Very High Risk)
- **<0%**: 100 points (Extreme Risk)

**FCF to Net Income** (30% weight):
- **1.0+**: 0 points (Low Risk)
- **0.8-1.0**: 25 points (Moderate Risk)
- **0.6-0.8**: 50 points (High Risk)
- **0.4-0.6**: 75 points (Very High Risk)
- **<0.4**: 100 points (Extreme Risk)

### Growth Risk Component (0-100)

**Revenue Growth YoY** (50% weight):
- **10%+**: 0 points (Low Risk)
- **5-10%**: 25 points (Moderate Risk)
- **0-5%**: 50 points (High Risk)
- **-5-0%**: 75 points (Very High Risk)
- **<-5%**: 100 points (Extreme Risk)

**Earnings Growth YoY** (50% weight):
- **10%+**: 0 points (Low Risk)
- **5-10%**: 25 points (Moderate Risk)
- **0-5%**: 50 points (High Risk)
- **-5-0%**: 75 points (Very High Risk)
- **<-5%**: 100 points (Extreme Risk)

## Dashboard Implementation Recommendations

### 1. Visual Score Display

**Primary Score Cards**:
- **Overall Financial Health**: Large circular gauge (0-100)
- **Risk Assessment**: Color-coded bar (Green/Yellow/Red)
- **Value Investment**: Star rating (1-5 stars)

**Secondary Metrics**:
- **Key Ratios**: Top 5 most important ratios with current values
- **Trend Indicators**: Up/down arrows showing improvement/decline
- **Peer Comparison**: How scores compare to industry averages

### 2. Alert System

**Red Flags** (Immediate attention required):
- Debt-to-Equity > 2.0
- Current Ratio < 0.8
- Negative Net Margin
- Declining Revenue Growth
- Interest Coverage < 1.5

**Yellow Flags** (Monitor closely):
- Debt-to-Equity > 1.0
- Current Ratio < 1.0
- Net Margin < 5%
- Slow Revenue Growth (< 5%)
- Interest Coverage < 2.0

### 3. Educational Tooltips

For each ratio and score:
- **What it means**: Simple explanation
- **Why it matters**: Impact on investment decision
- **Industry context**: How it compares to peers
- **Historical trend**: How it's changed over time

### 4. Actionable Insights

**For High Scores (80-100)**:
- "Strong financial foundation"
- "Consider for long-term investment"
- "Low risk profile"

**For Medium Scores (40-79)**:
- "Monitor key metrics closely"
- "Consider position sizing"
- "Watch for improvements"

**For Low Scores (0-39)**:
- "High risk - proceed with caution"
- "Consider avoiding or small position"
- "Monitor for turnaround"

## Implementation Considerations

### 1. Data Quality

- **Missing Data Handling**: Use industry averages for missing ratios
- **Outlier Detection**: Flag unusually high/low values for manual review
- **Data Freshness**: Ensure ratios are calculated from recent financial data

### 2. Industry Adjustments

- **Sector-Specific Thresholds**: Different industries have different normal ranges
- **Size Adjustments**: Large vs. small companies may need different scoring
- **Growth vs. Value**: Different emphasis for different investment styles

### 3. Dynamic Weighting

- **Market Conditions**: Adjust weights based on economic environment
- **Company Lifecycle**: Different emphasis for growth vs. mature companies
- **Investment Horizon**: Short-term vs. long-term focus

### 4. Backtesting

- **Historical Performance**: Test scoring system against past market performance
- **Risk-Adjusted Returns**: Compare scores to actual investment outcomes
- **False Positives/Negatives**: Refine thresholds based on real-world results

## Implementation Specifications

### Core Calculation Functions

#### 1. Overall Financial Health Score Calculation

```python
def calculate_financial_health_score(ratios: dict) -> dict:
    """
    Calculate the overall financial health score (0-100)
    
    Args:
        ratios: Dictionary containing all calculated ratios
        
    Returns:
        Dictionary with score, grade, and component breakdown
    """
    # Calculate component scores
    financial_health_component = calculate_financial_health_component(ratios)
    profitability_component = calculate_profitability_component(ratios)
    quality_component = calculate_quality_component(ratios)
    growth_component = calculate_growth_component(ratios)
    
    # Weighted calculation
    total_score = (
        financial_health_component * 0.4 +
        profitability_component * 0.3 +
        quality_component * 0.2 +
        growth_component * 0.1
    )
    
    # Determine grade
    grade = get_grade_from_score(total_score)
    
    return {
        'score': round(total_score, 2),
        'grade': grade,
        'components': {
            'financial_health': round(financial_health_component, 2),
            'profitability': round(profitability_component, 2),
            'quality': round(quality_component, 2),
            'growth': round(growth_component, 2)
        }
    }
```

#### 2. Risk Assessment Score Calculation

```python
def calculate_risk_assessment_score(ratios: dict) -> dict:
    """
    Calculate the risk assessment score (0-100, where higher = more risk)
    
    Args:
        ratios: Dictionary containing all calculated ratios
        
    Returns:
        Dictionary with risk score, level, and component breakdown
    """
    # Calculate risk components
    debt_risk = calculate_debt_risk_component(ratios)
    liquidity_risk = calculate_liquidity_risk_component(ratios)
    profitability_risk = calculate_profitability_risk_component(ratios)
    growth_risk = calculate_growth_risk_component(ratios)
    
    # Weighted calculation
    total_risk = (
        debt_risk * 0.35 +
        liquidity_risk * 0.25 +
        profitability_risk * 0.25 +
        growth_risk * 0.15
    )
    
    # Determine risk level
    risk_level = get_risk_level_from_score(total_risk)
    
    return {
        'score': round(total_risk, 2),
        'level': risk_level,
        'components': {
            'debt_risk': round(debt_risk, 2),
            'liquidity_risk': round(liquidity_risk, 2),
            'profitability_risk': round(profitability_risk, 2),
            'growth_risk': round(growth_risk, 2)
        }
    }
```

#### 3. Value Investment Score Calculation

```python
def calculate_value_investment_score(ratios: dict) -> dict:
    """
    Calculate the value investment score (0-100)
    
    Args:
        ratios: Dictionary containing all calculated ratios
        
    Returns:
        Dictionary with value score, rating, and component breakdown
    """
    # Calculate components
    valuation_component = calculate_valuation_component(ratios)
    quality_component = calculate_quality_component(ratios)
    financial_health_component = calculate_financial_health_component(ratios)
    growth_component = calculate_growth_component(ratios)
    
    # Weighted calculation
    total_score = (
        valuation_component * 0.4 +
        quality_component * 0.3 +
        financial_health_component * 0.2 +
        growth_component * 0.1
    )
    
    # Determine value rating
    value_rating = get_value_rating_from_score(total_score)
    
    return {
        'score': round(total_score, 2),
        'rating': value_rating,
        'components': {
            'valuation': round(valuation_component, 2),
            'quality': round(quality_component, 2),
            'financial_health': round(financial_health_component, 2),
            'growth': round(growth_component, 2)
        }
    }
```

### Component Calculation Functions

#### Financial Health Component (0-100)

```python
def calculate_financial_health_component(ratios: dict) -> float:
    """Calculate financial health component score"""
    
    # Debt-to-Equity scoring
    debt_equity = ratios.get('debt_to_equity')
    debt_equity_score = 0
    if debt_equity is not None:
        if debt_equity <= 0.5:
            debt_equity_score = 100
        elif debt_equity <= 1.0:
            debt_equity_score = 80
        elif debt_equity <= 1.5:
            debt_equity_score = 60
        elif debt_equity <= 2.0:
            debt_equity_score = 40
        else:
            debt_equity_score = 20
    
    # Current Ratio scoring
    current_ratio = ratios.get('current_ratio')
    current_ratio_score = 0
    if current_ratio is not None:
        if current_ratio >= 2.0:
            current_ratio_score = 100
        elif current_ratio >= 1.5:
            current_ratio_score = 80
        elif current_ratio >= 1.0:
            current_ratio_score = 60
        elif current_ratio >= 0.8:
            current_ratio_score = 40
        else:
            current_ratio_score = 20
    
    # Quick Ratio scoring
    quick_ratio = ratios.get('quick_ratio')
    quick_ratio_score = 0
    if quick_ratio is not None:
        if quick_ratio >= 1.5:
            quick_ratio_score = 100
        elif quick_ratio >= 1.0:
            quick_ratio_score = 80
        elif quick_ratio >= 0.7:
            quick_ratio_score = 60
        elif quick_ratio >= 0.5:
            quick_ratio_score = 40
        else:
            quick_ratio_score = 20
    
    # Interest Coverage scoring
    interest_coverage = ratios.get('interest_coverage')
    interest_coverage_score = 0
    if interest_coverage is not None:
        if interest_coverage >= 5.0:
            interest_coverage_score = 100
        elif interest_coverage >= 3.0:
            interest_coverage_score = 80
        elif interest_coverage >= 2.0:
            interest_coverage_score = 60
        elif interest_coverage >= 1.5:
            interest_coverage_score = 40
        else:
            interest_coverage_score = 20
    
    # Weighted calculation
    total_score = (
        debt_equity_score * 0.30 +
        current_ratio_score * 0.25 +
        quick_ratio_score * 0.25 +
        interest_coverage_score * 0.20
    )
    
    return total_score
```

#### Profitability Component (0-100)

```python
def calculate_profitability_component(ratios: dict) -> float:
    """Calculate profitability component score"""
    
    # ROE scoring
    roe = ratios.get('roe')
    roe_score = 0
    if roe is not None:
        if roe >= 15:
            roe_score = 100
        elif roe >= 10:
            roe_score = 80
        elif roe >= 5:
            roe_score = 60
        elif roe >= 0:
            roe_score = 40
        else:
            roe_score = 20
    
    # ROA scoring
    roa = ratios.get('roa')
    roa_score = 0
    if roa is not None:
        if roa >= 8:
            roa_score = 100
        elif roa >= 5:
            roa_score = 80
        elif roa >= 2:
            roa_score = 60
        elif roa >= 0:
            roa_score = 40
        else:
            roa_score = 20
    
    # Net Margin scoring
    net_margin = ratios.get('net_margin')
    net_margin_score = 0
    if net_margin is not None:
        if net_margin >= 15:
            net_margin_score = 100
        elif net_margin >= 10:
            net_margin_score = 80
        elif net_margin >= 5:
            net_margin_score = 60
        elif net_margin >= 0:
            net_margin_score = 40
        else:
            net_margin_score = 20
    
    # Operating Margin scoring
    operating_margin = ratios.get('operating_margin')
    operating_margin_score = 0
    if operating_margin is not None:
        if operating_margin >= 20:
            operating_margin_score = 100
        elif operating_margin >= 15:
            operating_margin_score = 80
        elif operating_margin >= 10:
            operating_margin_score = 60
        elif operating_margin >= 5:
            operating_margin_score = 40
        else:
            operating_margin_score = 20
    
    # ROIC scoring
    roic = ratios.get('roic')
    roic_score = 0
    if roic is not None:
        if roic >= 12:
            roic_score = 100
        elif roic >= 8:
            roic_score = 80
        elif roic >= 4:
            roic_score = 60
        elif roic >= 0:
            roic_score = 40
        else:
            roic_score = 20
    
    # Weighted calculation
    total_score = (
        roe_score * 0.25 +
        roa_score * 0.20 +
        net_margin_score * 0.25 +
        operating_margin_score * 0.20 +
        roic_score * 0.10
    )
    
    return total_score
```

#### Quality Component (0-100)

```python
def calculate_quality_component(ratios: dict) -> float:
    """Calculate quality component score"""
    
    # FCF to Net Income scoring
    fcf_to_net_income = ratios.get('fcf_to_net_income')
    fcf_score = 0
    if fcf_to_net_income is not None:
        if fcf_to_net_income >= 1.0:
            fcf_score = 100
        elif fcf_to_net_income >= 0.8:
            fcf_score = 80
        elif fcf_to_net_income >= 0.6:
            fcf_score = 60
        elif fcf_to_net_income >= 0.4:
            fcf_score = 40
        else:
            fcf_score = 20
    
    # Asset Turnover scoring
    asset_turnover = ratios.get('asset_turnover')
    asset_turnover_score = 0
    if asset_turnover is not None:
        if asset_turnover >= 1.5:
            asset_turnover_score = 100
        elif asset_turnover >= 1.0:
            asset_turnover_score = 80
        elif asset_turnover >= 0.7:
            asset_turnover_score = 60
        elif asset_turnover >= 0.5:
            asset_turnover_score = 40
        else:
            asset_turnover_score = 20
    
    # Weighted calculation
    total_score = (
        fcf_score * 0.60 +
        asset_turnover_score * 0.40
    )
    
    return total_score
```

#### Valuation Component (0-100)

```python
def calculate_valuation_component(ratios: dict) -> float:
    """Calculate valuation component score"""
    
    # P/E Ratio scoring (lower is better)
    pe_ratio = ratios.get('pe_ratio')
    pe_score = 0
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio < 10:
            pe_score = 100
        elif pe_ratio < 15:
            pe_score = 80
        elif pe_ratio < 20:
            pe_score = 60
        elif pe_ratio < 25:
            pe_score = 40
        else:
            pe_score = 20
    
    # P/B Ratio scoring (lower is better)
    pb_ratio = ratios.get('pb_ratio')
    pb_score = 0
    if pb_ratio is not None and pb_ratio > 0:
        if pb_ratio < 1.0:
            pb_score = 100
        elif pb_ratio < 1.5:
            pb_score = 80
        elif pb_ratio < 2.5:
            pb_score = 60
        elif pb_ratio < 4.0:
            pb_score = 40
        else:
            pb_score = 20
    
    # P/S Ratio scoring (lower is better)
    ps_ratio = ratios.get('ps_ratio')
    ps_score = 0
    if ps_ratio is not None and ps_ratio > 0:
        if ps_ratio < 1.0:
            ps_score = 100
        elif ps_ratio < 2.0:
            ps_score = 80
        elif ps_ratio < 3.0:
            ps_score = 60
        elif ps_ratio < 5.0:
            ps_score = 40
        else:
            ps_score = 20
    
    # EV/EBITDA scoring (lower is better)
    ev_ebitda = ratios.get('ev_ebitda')
    ev_ebitda_score = 0
    if ev_ebitda is not None and ev_ebitda > 0:
        if ev_ebitda < 8:
            ev_ebitda_score = 100
        elif ev_ebitda < 12:
            ev_ebitda_score = 80
        elif ev_ebitda < 16:
            ev_ebitda_score = 60
        elif ev_ebitda < 20:
            ev_ebitda_score = 40
        else:
            ev_ebitda_score = 20
    
    # Weighted calculation
    total_score = (
        pe_score * 0.30 +
        pb_score * 0.25 +
        ps_score * 0.25 +
        ev_ebitda_score * 0.20
    )
    
    return total_score
```

#### Growth Component (0-100)

```python
def calculate_growth_component(ratios: dict) -> float:
    """Calculate growth component score"""
    
    # Revenue Growth scoring
    revenue_growth = ratios.get('revenue_growth_yoy')
    revenue_growth_score = 0
    if revenue_growth is not None:
        if revenue_growth >= 15:
            revenue_growth_score = 100
        elif revenue_growth >= 10:
            revenue_growth_score = 80
        elif revenue_growth >= 5:
            revenue_growth_score = 60
        elif revenue_growth >= 0:
            revenue_growth_score = 40
        else:
            revenue_growth_score = 20
    
    # Earnings Growth scoring
    earnings_growth = ratios.get('earnings_growth_yoy')
    earnings_growth_score = 0
    if earnings_growth is not None:
        if earnings_growth >= 15:
            earnings_growth_score = 100
        elif earnings_growth >= 10:
            earnings_growth_score = 80
        elif earnings_growth >= 5:
            earnings_growth_score = 60
        elif earnings_growth >= 0:
            earnings_growth_score = 40
        else:
            earnings_growth_score = 20
    
    # FCF Growth scoring
    fcf_growth = ratios.get('fcf_growth_yoy')
    fcf_growth_score = 0
    if fcf_growth is not None:
        if fcf_growth >= 15:
            fcf_growth_score = 100
        elif fcf_growth >= 10:
            fcf_growth_score = 80
        elif fcf_growth >= 5:
            fcf_growth_score = 60
        elif fcf_growth >= 0:
            fcf_growth_score = 40
        else:
            fcf_growth_score = 20
    
    # Weighted calculation
    total_score = (
        revenue_growth_score * 0.40 +
        earnings_growth_score * 0.35 +
        fcf_growth_score * 0.25
    )
    
    return total_score
```

### Risk Component Calculations

#### Debt Risk Component (0-100, higher = more risk)

```python
def calculate_debt_risk_component(ratios: dict) -> float:
    """Calculate debt risk component (higher score = higher risk)"""
    
    # Debt-to-Equity risk scoring
    debt_equity = ratios.get('debt_to_equity')
    debt_equity_risk = 0
    if debt_equity is not None:
        if debt_equity <= 0.5:
            debt_equity_risk = 0
        elif debt_equity <= 1.0:
            debt_equity_risk = 25
        elif debt_equity <= 1.5:
            debt_equity_risk = 50
        elif debt_equity <= 2.0:
            debt_equity_risk = 75
        else:
            debt_equity_risk = 100
    
    # Interest Coverage risk scoring
    interest_coverage = ratios.get('interest_coverage')
    interest_coverage_risk = 0
    if interest_coverage is not None:
        if interest_coverage >= 5.0:
            interest_coverage_risk = 0
        elif interest_coverage >= 3.0:
            interest_coverage_risk = 25
        elif interest_coverage >= 2.0:
            interest_coverage_risk = 50
        elif interest_coverage >= 1.5:
            interest_coverage_risk = 75
        else:
            interest_coverage_risk = 100
    
    # Weighted calculation
    total_risk = (
        debt_equity_risk * 0.50 +
        interest_coverage_risk * 0.50
    )
    
    return total_risk
```

#### Liquidity Risk Component (0-100, higher = more risk)

```python
def calculate_liquidity_risk_component(ratios: dict) -> float:
    """Calculate liquidity risk component (higher score = higher risk)"""
    
    # Current Ratio risk scoring
    current_ratio = ratios.get('current_ratio')
    current_ratio_risk = 0
    if current_ratio is not None:
        if current_ratio >= 2.0:
            current_ratio_risk = 0
        elif current_ratio >= 1.5:
            current_ratio_risk = 25
        elif current_ratio >= 1.0:
            current_ratio_risk = 50
        elif current_ratio >= 0.8:
            current_ratio_risk = 75
        else:
            current_ratio_risk = 100
    
    # Quick Ratio risk scoring
    quick_ratio = ratios.get('quick_ratio')
    quick_ratio_risk = 0
    if quick_ratio is not None:
        if quick_ratio >= 1.5:
            quick_ratio_risk = 0
        elif quick_ratio >= 1.0:
            quick_ratio_risk = 25
        elif quick_ratio >= 0.7:
            quick_ratio_risk = 50
        elif quick_ratio >= 0.5:
            quick_ratio_risk = 75
        else:
            quick_ratio_risk = 100
    
    # Weighted calculation
    total_risk = (
        current_ratio_risk * 0.50 +
        quick_ratio_risk * 0.50
    )
    
    return total_risk
```

#### Profitability Risk Component (0-100, higher = more risk)

```python
def calculate_profitability_risk_component(ratios: dict) -> float:
    """Calculate profitability risk component (higher score = higher risk)"""
    
    # Net Margin risk scoring
    net_margin = ratios.get('net_margin')
    net_margin_risk = 0
    if net_margin is not None:
        if net_margin >= 15:
            net_margin_risk = 0
        elif net_margin >= 10:
            net_margin_risk = 25
        elif net_margin >= 5:
            net_margin_risk = 50
        elif net_margin >= 0:
            net_margin_risk = 75
        else:
            net_margin_risk = 100
    
    # ROE risk scoring
    roe = ratios.get('roe')
    roe_risk = 0
    if roe is not None:
        if roe >= 15:
            roe_risk = 0
        elif roe >= 10:
            roe_risk = 25
        elif roe >= 5:
            roe_risk = 50
        elif roe >= 0:
            roe_risk = 75
        else:
            roe_risk = 100
    
    # FCF to Net Income risk scoring
    fcf_to_net_income = ratios.get('fcf_to_net_income')
    fcf_risk = 0
    if fcf_to_net_income is not None:
        if fcf_to_net_income >= 1.0:
            fcf_risk = 0
        elif fcf_to_net_income >= 0.8:
            fcf_risk = 25
        elif fcf_to_net_income >= 0.6:
            fcf_risk = 50
        elif fcf_to_net_income >= 0.4:
            fcf_risk = 75
        else:
            fcf_risk = 100
    
    # Weighted calculation
    total_risk = (
        net_margin_risk * 0.40 +
        roe_risk * 0.30 +
        fcf_risk * 0.30
    )
    
    return total_risk
```

#### Growth Risk Component (0-100, higher = more risk)

```python
def calculate_growth_risk_component(ratios: dict) -> float:
    """Calculate growth risk component (higher score = higher risk)"""
    
    # Revenue Growth risk scoring
    revenue_growth = ratios.get('revenue_growth_yoy')
    revenue_growth_risk = 0
    if revenue_growth is not None:
        if revenue_growth >= 10:
            revenue_growth_risk = 0
        elif revenue_growth >= 5:
            revenue_growth_risk = 25
        elif revenue_growth >= 0:
            revenue_growth_risk = 50
        elif revenue_growth >= -5:
            revenue_growth_risk = 75
        else:
            revenue_growth_risk = 100
    
    # Earnings Growth risk scoring
    earnings_growth = ratios.get('earnings_growth_yoy')
    earnings_growth_risk = 0
    if earnings_growth is not None:
        if earnings_growth >= 10:
            earnings_growth_risk = 0
        elif earnings_growth >= 5:
            earnings_growth_risk = 25
        elif earnings_growth >= 0:
            earnings_growth_risk = 50
        elif earnings_growth >= -5:
            earnings_growth_risk = 75
        else:
            earnings_growth_risk = 100
    
    # Weighted calculation
    total_risk = (
        revenue_growth_risk * 0.50 +
        earnings_growth_risk * 0.50
    )
    
    return total_risk
```

### Helper Functions

#### Grade and Rating Functions

```python
def get_grade_from_score(score: float) -> str:
    """Convert score to letter grade"""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C+"
    elif score >= 40:
        return "C"
    elif score >= 30:
        return "D"
    else:
        return "F"

def get_risk_level_from_score(score: float) -> str:
    """Convert risk score to risk level"""
    if score <= 20:
        return "Low Risk"
    elif score <= 40:
        return "Moderate Risk"
    elif score <= 60:
        return "High Risk"
    elif score <= 80:
        return "Very High Risk"
    else:
        return "Extreme Risk"

def get_value_rating_from_score(score: float) -> str:
    """Convert value score to value rating"""
    if score >= 80:
        return "Excellent Value"
    elif score >= 60:
        return "Good Value"
    elif score >= 40:
        return "Fair Value"
    elif score >= 20:
        return "Poor Value"
    else:
        return "Very Poor Value"
```

#### Alert Detection Functions

```python
def detect_red_flags(ratios: dict) -> list:
    """Detect red flags that require immediate attention"""
    red_flags = []
    
    # Debt-to-Equity > 2.0
    if ratios.get('debt_to_equity', 0) > 2.0:
        red_flags.append("High debt-to-equity ratio (>2.0)")
    
    # Current Ratio < 0.8
    if ratios.get('current_ratio', 0) < 0.8:
        red_flags.append("Low current ratio (<0.8)")
    
    # Negative Net Margin
    if ratios.get('net_margin', 0) < 0:
        red_flags.append("Negative net margin")
    
    # Declining Revenue Growth
    if ratios.get('revenue_growth_yoy', 0) < 0:
        red_flags.append("Declining revenue growth")
    
    # Interest Coverage < 1.5
    if ratios.get('interest_coverage', 0) < 1.5:
        red_flags.append("Low interest coverage (<1.5)")
    
    return red_flags

def detect_yellow_flags(ratios: dict) -> list:
    """Detect yellow flags that require monitoring"""
    yellow_flags = []
    
    # Debt-to-Equity > 1.0
    if ratios.get('debt_to_equity', 0) > 1.0:
        yellow_flags.append("Elevated debt-to-equity ratio (>1.0)")
    
    # Current Ratio < 1.0
    if ratios.get('current_ratio', 0) < 1.0:
        yellow_flags.append("Current ratio below 1.0")
    
    # Net Margin < 5%
    if ratios.get('net_margin', 0) < 5:
        yellow_flags.append("Low net margin (<5%)")
    
    # Slow Revenue Growth (< 5%)
    if ratios.get('revenue_growth_yoy', 0) < 5:
        yellow_flags.append("Slow revenue growth (<5%)")
    
    # Interest Coverage < 2.0
    if ratios.get('interest_coverage', 0) < 2.0:
        yellow_flags.append("Interest coverage below 2.0")
    
    return yellow_flags
```

#### Main Scoring Function

```python
def calculate_all_scores(ratios: dict) -> dict:
    """
    Calculate all three scores for a company
    
    Args:
        ratios: Dictionary containing all calculated ratios
        
    Returns:
        Dictionary with all scores, grades, and alerts
    """
    # Calculate main scores
    financial_health = calculate_financial_health_score(ratios)
    risk_assessment = calculate_risk_assessment_score(ratios)
    value_investment = calculate_value_investment_score(ratios)
    
    # Detect flags
    red_flags = detect_red_flags(ratios)
    yellow_flags = detect_yellow_flags(ratios)
    
    return {
        'financial_health': financial_health,
        'risk_assessment': risk_assessment,
        'value_investment': value_investment,
        'alerts': {
            'red_flags': red_flags,
            'yellow_flags': yellow_flags
        },
        'summary': {
            'overall_grade': financial_health['grade'],
            'risk_level': risk_assessment['level'],
            'value_rating': value_investment['rating'],
            'has_red_flags': len(red_flags) > 0,
            'has_yellow_flags': len(yellow_flags) > 0
        }
    }
```

### Database Schema for Storing Scores

```sql
-- Table to store calculated scores
CREATE TABLE company_scores (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date_calculated DATE NOT NULL,
    
    -- Financial Health Score
    financial_health_score DECIMAL(5,2),
    financial_health_grade VARCHAR(2),
    financial_health_components JSONB,
    
    -- Risk Assessment Score
    risk_assessment_score DECIMAL(5,2),
    risk_level VARCHAR(20),
    risk_components JSONB,
    
    -- Value Investment Score
    value_investment_score DECIMAL(5,2),
    value_rating VARCHAR(20),
    value_components JSONB,
    
    -- Alerts
    red_flags JSONB,
    yellow_flags JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker, date_calculated)
);

-- Index for efficient queries
CREATE INDEX idx_company_scores_ticker_date ON company_scores(ticker, date_calculated);
CREATE INDEX idx_company_scores_financial_health ON company_scores(financial_health_score DESC);
CREATE INDEX idx_company_scores_risk_assessment ON company_scores(risk_assessment_score ASC);
CREATE INDEX idx_company_scores_value_investment ON company_scores(value_investment_score DESC);
```

### API Endpoint Specifications

```python
# Example API endpoints for the scoring system

@app.route('/api/v1/scores/<ticker>', methods=['GET'])
def get_company_scores(ticker):
    """
    Get all scores for a specific company
    
    Response format:
    {
        "ticker": "AAPL",
        "date_calculated": "2024-01-15",
        "financial_health": {
            "score": 85.5,
            "grade": "A",
            "components": {...}
        },
        "risk_assessment": {
            "score": 15.2,
            "level": "Low Risk",
            "components": {...}
        },
        "value_investment": {
            "score": 72.8,
            "rating": "Good Value",
            "components": {...}
        },
        "alerts": {
            "red_flags": [],
            "yellow_flags": ["Slow revenue growth (<5%)"]
        },
        "summary": {
            "overall_grade": "A",
            "risk_level": "Low Risk",
            "value_rating": "Good Value",
            "has_red_flags": false,
            "has_yellow_flags": true
        }
    }
    """
    pass

@app.route('/api/v1/scores/screener', methods=['POST'])
def screener_scores():
    """
    Get scores for multiple companies with filtering
    
    Request body:
    {
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "filters": {
            "min_financial_health": 70,
            "max_risk_score": 30,
            "min_value_score": 60
        }
    }
    """
    pass
```

## Conclusion

This comprehensive scoring system provides novice investors with:

1. **Quick Assessment**: Three focused scores for different investment perspectives
2. **Risk Identification**: Clear red flags and warning signs
3. **Educational Value**: Understanding of what each ratio means
4. **Actionable Insights**: Specific recommendations based on scores
5. **Context**: Industry comparisons and historical trends

The system balances simplicity for novice investors with comprehensive coverage of key financial metrics, helping them make more informed investment decisions while learning about fundamental analysis.

**Implementation Notes:**
- All calculations handle missing data gracefully by defaulting to 0
- Scores are rounded to 2 decimal places for consistency
- The system is designed to be easily extensible for additional ratios
- Database schema supports historical tracking of scores
- API endpoints provide both individual company and screener functionality 