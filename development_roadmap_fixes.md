# Development Roadmap: Fixing Data Confidence & Risk Accuracy
## Specific Solutions to Achieve >80% Targets

**Current Status:**
- Data Confidence: 55.8% (Target: >80%) - Gap: -24.2%
- Risk Accuracy: 31.6% (Target: >80%) - Gap: -48.4%

---

## 🚨 PHASE 1: CRITICAL FIXES (2-4 weeks)

### 1.1 Fix Database Schema Constraints (URGENT)

**Problem:** Database constraint violations preventing score storage
```sql
-- Current error: "violates check constraint company_scores_current_technical_risk_level_check"
```

**Solution:**
```sql
-- Step 1: Drop dependent views
DROP MATERIALIZED VIEW IF EXISTS screener_summary_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS score_trends_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS screener_filters_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dashboard_metrics_view CASCADE;

-- Step 2: Recreate tables with correct constraints
DROP TABLE IF EXISTS company_scores_current CASCADE;
CREATE TABLE company_scores_current (
    ticker VARCHAR(10) PRIMARY KEY,
    calculation_date DATE NOT NULL,
    fundamental_health_score DECIMAL(5,2),
    fundamental_health_grade VARCHAR(20), -- Changed from VARCHAR(2)
    value_investment_score DECIMAL(5,2),
    value_rating VARCHAR(20), -- Changed from VARCHAR(2)
    fundamental_risk_score DECIMAL(5,2),
    fundamental_risk_level VARCHAR(20), -- Changed from VARCHAR(2)
    technical_health_score DECIMAL(5,2),
    technical_health_grade VARCHAR(20), -- Changed from VARCHAR(2)
    trading_signal_score DECIMAL(5,2),
    trading_signal_rating VARCHAR(20), -- Changed from VARCHAR(2)
    technical_risk_score DECIMAL(5,2),
    technical_risk_level VARCHAR(20), -- Changed from VARCHAR(2)
    data_confidence DECIMAL(5,2),
    missing_metrics TEXT[], -- Changed from VARCHAR
    data_warnings TEXT[], -- Changed from VARCHAR
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 3: Recreate views
-- (Add view recreation scripts here)
```

**Files to Modify:**
- `recreate_scoring_tables.py` - Complete table recreation
- `check_constraint.py` - Verify constraint status
- `fix_database_schema_final.py` - Apply schema fixes

### 1.2 Implement API Integration for Missing Fundamental Data

**Problem:** Missing PE, PB, ROE ratios causing low data confidence

**Solution:**
```python
# Enhanced API Integration Class
class EnhancedAPIDataFiller:
    def __init__(self):
        self.yahoo_api = YahooFinanceService()
        self.alpha_vantage_api = AlphaVantageService()
        self.fmp_api = FMPService()
        
    def fill_missing_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """Fill missing fundamental ratios using multiple APIs"""
        missing_data = {}
        
        # Get current fundamental data
        current_data = self.get_current_fundamental_data(ticker)
        
        # Identify missing metrics
        missing_metrics = self.identify_missing_metrics(current_data)
        
        # Fill missing data from APIs
        for metric in missing_metrics:
            api_data = self.fetch_metric_from_apis(ticker, metric)
            if api_data:
                missing_data[metric] = api_data
        
        return missing_data
    
    def fetch_metric_from_apis(self, ticker: str, metric: str) -> Optional[float]:
        """Fetch specific metric from multiple APIs with fallback"""
        apis = [
            (self.yahoo_api, 'yahoo'),
            (self.alpha_vantage_api, 'alpha_vantage'),
            (self.fmp_api, 'fmp')
        ]
        
        for api, source in apis:
            try:
                value = api.get_fundamental_ratio(ticker, metric)
                if value and self.validate_ratio_value(value, metric):
                    return value
            except Exception as e:
                continue
        
        return None
    
    def validate_ratio_value(self, value: float, metric: str) -> bool:
        """Validate ratio values are within reasonable ranges"""
        validation_rules = {
            'pe_ratio': (0, 1000),
            'pb_ratio': (0, 100),
            'roe': (-100, 100),
            'debt_to_equity': (0, 10),
            'current_ratio': (0, 10),
            'quick_ratio': (0, 10)
        }
        
        if metric in validation_rules:
            min_val, max_val = validation_rules[metric]
            return min_val <= value <= max_val
        
        return True
```

**Files to Create/Modify:**
- `enhanced_api_data_filler.py` - New API integration class
- `calc_fundamental_scores_enhanced.py` - Integrate API filler
- `data_quality_improver.py` - Data validation and improvement

### 1.3 Add Growth Stock Risk Multipliers

**Problem:** High-risk growth stocks (NVDA, TSLA, UBER) classified as low-risk

**Solution:**
```python
class GrowthStockRiskAdjuster:
    def __init__(self):
        self.growth_stock_indicators = {
            'high_pe_threshold': 30,
            'high_volatility_threshold': 0.4,
            'growth_sector_multipliers': {
                'Technology': 1.5,
                'Communication Services': 1.3,
                'Consumer Discretionary': 1.2
            }
        }
    
    def adjust_risk_for_growth_stocks(self, ticker: str, base_risk_score: float, 
                                    fundamental_data: Dict[str, Any]) -> float:
        """Apply growth stock risk multipliers"""
        adjusted_risk = base_risk_score
        
        # Check for high PE ratio
        pe_ratio = fundamental_data.get('pe_ratio')
        if pe_ratio and pe_ratio > self.growth_stock_indicators['high_pe_threshold']:
            pe_multiplier = min(pe_ratio / self.growth_stock_indicators['high_pe_threshold'], 2.0)
            adjusted_risk *= pe_multiplier
        
        # Check for high volatility
        volatility = fundamental_data.get('beta', 1.0)
        if volatility > self.growth_stock_indicators['high_volatility_threshold']:
            vol_multiplier = min(volatility / self.growth_stock_indicators['high_volatility_threshold'], 1.5)
            adjusted_risk *= vol_multiplier
        
        # Apply sector-specific multipliers
        sector = self.get_stock_sector(ticker)
        if sector in self.growth_stock_indicators['growth_sector_multipliers']:
            sector_multiplier = self.growth_stock_indicators['growth_sector_multipliers'][sector]
            adjusted_risk *= sector_multiplier
        
        # Ensure risk score stays within bounds (0-100)
        return min(max(adjusted_risk, 0), 100)
    
    def get_stock_sector(self, ticker: str) -> str:
        """Get stock sector for risk adjustment"""
        sector_map = {
            'NVDA': 'Technology', 'TSLA': 'Consumer Discretionary', 
            'UBER': 'Technology', 'AMD': 'Technology',
            'NFLX': 'Communication Services', 'SNAP': 'Communication Services'
        }
        return sector_map.get(ticker, 'Unknown')
```

**Files to Create/Modify:**
- `growth_stock_risk_adjuster.py` - New risk adjustment class
- `calc_fundamental_scores_enhanced.py` - Integrate risk adjuster
- `risk_assessment_enhancer.py` - Enhanced risk calculations

---

## 🔧 PHASE 2: HIGH PRIORITY FIXES (4-6 weeks)

### 2.1 Enhanced Data Validation Algorithms

**Problem:** Limited cross-validation between data sources

**Solution:**
```python
class EnhancedDataValidator:
    def __init__(self):
        self.validation_thresholds = {
            'pe_ratio_variance': 0.3,  # 30% variance allowed between sources
            'pb_ratio_variance': 0.25,
            'roe_variance': 0.2
        }
    
    def cross_validate_fundamental_data(self, ticker: str, 
                                      data_sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Cross-validate data between multiple sources"""
        validated_data = {}
        confidence_scores = {}
        
        for metric in ['pe_ratio', 'pb_ratio', 'roe', 'debt_to_equity']:
            values = []
            sources = []
            
            # Collect values from all sources
            for source_name, source_data in data_sources.items():
                if metric in source_data and source_data[metric] is not None:
                    values.append(source_data[metric])
                    sources.append(source_name)
            
            if len(values) >= 2:
                # Calculate variance and confidence
                variance = self.calculate_variance(values)
                confidence = self.calculate_confidence(variance, len(values))
                
                # Use weighted average if variance is acceptable
                if variance <= self.validation_thresholds.get(f'{metric}_variance', 0.3):
                    validated_data[metric] = self.weighted_average(values, sources)
                    confidence_scores[metric] = confidence
                else:
                    # Use most reliable source
                    best_source = self.select_best_source(sources, values)
                    validated_data[metric] = values[best_source]
                    confidence_scores[metric] = 0.7  # Reduced confidence for variance
        
        return {
            'validated_data': validated_data,
            'confidence_scores': confidence_scores,
            'overall_confidence': sum(confidence_scores.values()) / len(confidence_scores)
        }
    
    def calculate_variance(self, values: List[float]) -> float:
        """Calculate coefficient of variation"""
        if not values:
            return float('inf')
        
        mean = sum(values) / len(values)
        if mean == 0:
            return float('inf')
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return (variance ** 0.5) / abs(mean)
    
    def calculate_confidence(self, variance: float, num_sources: int) -> float:
        """Calculate confidence score based on variance and number of sources"""
        base_confidence = 1.0 - min(variance, 1.0)
        source_bonus = min((num_sources - 1) * 0.1, 0.2)
        return min(base_confidence + source_bonus, 1.0)
```

**Files to Create/Modify:**
- `enhanced_data_validator.py` - New validation class
- `data_quality_improver.py` - Integrate validation
- `fundamental_data_processor.py` - Enhanced data processing

### 2.2 Implement Sector-Adjusted Scoring

**Problem:** Different sectors need different scoring weights

**Solution:**
```python
class SectorAdjustedScorer:
    def __init__(self):
        self.sector_weights = {
            'Technology': {
                'pe_ratio_weight': 0.15,
                'growth_rate_weight': 0.25,
                'profit_margin_weight': 0.20,
                'debt_ratio_weight': 0.10,
                'cash_flow_weight': 0.30
            },
            'Financial Services': {
                'pe_ratio_weight': 0.20,
                'book_value_weight': 0.30,
                'debt_ratio_weight': 0.25,
                'dividend_yield_weight': 0.15,
                'cash_flow_weight': 0.10
            },
            'Healthcare': {
                'pe_ratio_weight': 0.20,
                'pipeline_weight': 0.25,
                'patent_weight': 0.20,
                'debt_ratio_weight': 0.15,
                'cash_flow_weight': 0.20
            },
            'Consumer Staples': {
                'pe_ratio_weight': 0.25,
                'dividend_yield_weight': 0.25,
                'debt_ratio_weight': 0.20,
                'cash_flow_weight': 0.30
            },
            'Consumer Discretionary': {
                'pe_ratio_weight': 0.20,
                'growth_rate_weight': 0.25,
                'profit_margin_weight': 0.20,
                'debt_ratio_weight': 0.15,
                'cash_flow_weight': 0.20
            }
        }
    
    def calculate_sector_adjusted_score(self, ticker: str, 
                                      fundamental_data: Dict[str, Any]) -> float:
        """Calculate score using sector-specific weights"""
        sector = self.get_stock_sector(ticker)
        weights = self.sector_weights.get(sector, self.sector_weights['Technology'])
        
        score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in fundamental_data and fundamental_data[metric] is not None:
                normalized_value = self.normalize_metric(metric, fundamental_data[metric], sector)
                score += normalized_value * weight
                total_weight += weight
        
        if total_weight > 0:
            return score / total_weight
        return 50.0  # Default neutral score
    
    def normalize_metric(self, metric: str, value: float, sector: str) -> float:
        """Normalize metric values based on sector benchmarks"""
        sector_benchmarks = {
            'Technology': {
                'pe_ratio': {'good': 20, 'neutral': 30, 'poor': 50},
                'growth_rate': {'good': 0.15, 'neutral': 0.10, 'poor': 0.05},
                'profit_margin': {'good': 0.20, 'neutral': 0.15, 'poor': 0.10}
            },
            'Financial Services': {
                'pe_ratio': {'good': 12, 'neutral': 15, 'poor': 20},
                'book_value': {'good': 1.5, 'neutral': 1.0, 'poor': 0.8},
                'debt_ratio': {'good': 0.3, 'neutral': 0.5, 'poor': 0.8}
            }
            # Add more sector benchmarks
        }
        
        benchmarks = sector_benchmarks.get(sector, {})
        if metric in benchmarks:
            good, neutral, poor = benchmarks[metric].values()
            
            if value <= good:
                return 80 + (good - value) / good * 20
            elif value <= neutral:
                return 60 + (neutral - value) / (neutral - good) * 20
            elif value <= poor:
                return 40 + (poor - value) / (poor - neutral) * 20
            else:
                return max(20, 40 - (value - poor) / poor * 20)
        
        return 50.0  # Default neutral value
```

**Files to Create/Modify:**
- `sector_adjusted_scorer.py` - New sector scoring class
- `calc_fundamental_scores_enhanced.py` - Integrate sector scoring
- `scoring_algorithm_enhancer.py` - Enhanced scoring logic

### 2.3 Add Market Cap Considerations

**Problem:** Small caps inherently riskier but not reflected in scoring

**Solution:**
```python
class MarketCapRiskAdjuster:
    def __init__(self):
        self.market_cap_thresholds = {
            'mega_cap': 200_000_000_000,  # $200B+
            'large_cap': 10_000_000_000,   # $10B-$200B
            'mid_cap': 2_000_000_000,      # $2B-$10B
            'small_cap': 300_000_000       # $300M-$2B
        }
        
        self.market_cap_risk_multipliers = {
            'mega_cap': 0.8,    # 20% risk reduction
            'large_cap': 1.0,   # No adjustment
            'mid_cap': 1.3,     # 30% risk increase
            'small_cap': 1.6    # 60% risk increase
        }
    
    def adjust_risk_for_market_cap(self, ticker: str, base_risk_score: float) -> float:
        """Adjust risk score based on market capitalization"""
        market_cap = self.get_market_cap(ticker)
        cap_category = self.categorize_market_cap(market_cap)
        
        multiplier = self.market_cap_risk_multipliers.get(cap_category, 1.0)
        adjusted_risk = base_risk_score * multiplier
        
        # Ensure risk stays within bounds
        return min(max(adjusted_risk, 0), 100)
    
    def categorize_market_cap(self, market_cap: float) -> str:
        """Categorize stock by market cap"""
        if market_cap >= self.market_cap_thresholds['mega_cap']:
            return 'mega_cap'
        elif market_cap >= self.market_cap_thresholds['large_cap']:
            return 'large_cap'
        elif market_cap >= self.market_cap_thresholds['mid_cap']:
            return 'mid_cap'
        elif market_cap >= self.market_cap_thresholds['small_cap']:
            return 'small_cap'
        else:
            return 'micro_cap'
    
    def get_market_cap(self, ticker: str) -> float:
        """Get current market cap for ticker"""
        # Implementation to fetch from database or API
        # This would integrate with existing market data services
        pass
```

**Files to Create/Modify:**
- `market_cap_risk_adjuster.py` - New market cap adjustment class
- `risk_assessment_enhancer.py` - Integrate market cap adjustments
- `fundamental_data_processor.py` - Include market cap data

---

## 📈 PHASE 3: MEDIUM PRIORITY FIXES (6-8 weeks)

### 3.1 Add Volatility-Based Risk Adjustments

**Problem:** Historical volatility not considered in risk assessment

**Solution:**
```python
class VolatilityRiskAdjuster:
    def __init__(self):
        self.volatility_periods = [30, 60, 90, 252]  # Days
        self.volatility_thresholds = {
            'low': 0.15,    # <15% annualized volatility
            'medium': 0.25, # 15-25% annualized volatility
            'high': 0.35    # >25% annualized volatility
        }
    
    def calculate_volatility_adjusted_risk(self, ticker: str, base_risk_score: float) -> float:
        """Adjust risk based on historical volatility"""
        volatility = self.calculate_historical_volatility(ticker)
        volatility_multiplier = self.get_volatility_multiplier(volatility)
        
        adjusted_risk = base_risk_score * volatility_multiplier
        return min(max(adjusted_risk, 0), 100)
    
    def calculate_historical_volatility(self, ticker: str) -> float:
        """Calculate annualized historical volatility"""
        # Implementation to calculate from price data
        # This would use existing technical analysis infrastructure
        pass
    
    def get_volatility_multiplier(self, volatility: float) -> float:
        """Get risk multiplier based on volatility level"""
        if volatility <= self.volatility_thresholds['low']:
            return 0.8  # 20% risk reduction for low volatility
        elif volatility <= self.volatility_thresholds['medium']:
            return 1.0  # No adjustment for medium volatility
        elif volatility <= self.volatility_thresholds['high']:
            return 1.4  # 40% risk increase for high volatility
        else:
            return 1.8  # 80% risk increase for very high volatility
```

### 3.2 Implement Advanced Technical Indicators

**Problem:** Limited technical analysis integration

**Solution:**
```python
class AdvancedTechnicalAnalyzer:
    def __init__(self):
        self.indicators = {
            'rsi': RSIIndicator(),
            'macd': MACDIndicator(),
            'bollinger': BollingerBandsIndicator(),
            'atr': ATRIndicator(),
            'adx': ADXIndicator()
        }
    
    def calculate_technical_risk_score(self, ticker: str) -> float:
        """Calculate technical risk score using multiple indicators"""
        technical_signals = self.get_technical_signals(ticker)
        
        risk_score = 50.0  # Base neutral score
        
        # Adjust based on trend strength
        if technical_signals['trend_strength'] == 'strong_uptrend':
            risk_score -= 10
        elif technical_signals['trend_strength'] == 'strong_downtrend':
            risk_score += 15
        
        # Adjust based on volatility
        if technical_signals['volatility'] == 'high':
            risk_score += 20
        elif technical_signals['volatility'] == 'low':
            risk_score -= 10
        
        # Adjust based on momentum
        if technical_signals['momentum'] == 'overbought':
            risk_score += 10
        elif technical_signals['momentum'] == 'oversold':
            risk_score -= 5
        
        return min(max(risk_score, 0), 100)
```

### 3.3 Create Backtesting Framework

**Problem:** No validation against historical performance

**Solution:**
```python
class ScoringBacktester:
    def __init__(self):
        self.test_period = 365  # 1 year
        self.rebalance_frequency = 30  # Monthly rebalancing
    
    def backtest_scoring_system(self, tickers: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
        """Backtest scoring system performance"""
        results = {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'accuracy_by_grade': {},
            'risk_adjustment_accuracy': 0.0
        }
        
        # Implementation for historical backtesting
        # This would validate scoring accuracy against actual returns
        
        return results
```

---

## 🎯 IMPLEMENTATION CHECKLIST

### Week 1-2: Database & API Integration
- [ ] Fix database schema constraints
- [ ] Implement API integration for missing data
- [ ] Test data retrieval from multiple sources

### Week 3-4: Risk Assessment Fixes
- [ ] Implement growth stock risk multipliers
- [ ] Add market cap risk adjustments
- [ ] Integrate volatility-based adjustments

### Week 5-6: Data Quality Improvements
- [ ] Implement cross-validation algorithms
- [ ] Add sector-adjusted scoring
- [ ] Enhance data validation

### Week 7-8: Testing & Validation
- [ ] Create backtesting framework
- [ ] Validate improvements against historical data
- [ ] Performance testing and optimization

---

## 📊 EXPECTED IMPROVEMENTS

### Data Confidence Target: >80%
**Current:** 55.8% → **Target:** >80%
**Expected Improvements:**
- API Integration: +15-20%
- Cross-validation: +10%
- Enhanced validation: +5%
**Total Expected:** 85.8-90.8%

### Risk Accuracy Target: >80%
**Current:** 31.6% → **Target:** >80%
**Expected Improvements:**
- Growth stock multipliers: +20%
- Market cap adjustments: +15%
- Volatility adjustments: +10%
- Sector-specific scoring: +5%
**Total Expected:** 81.6%

---

## 🔍 SUCCESS METRICS

### Phase 1 Success Criteria:
- Database storage working for all stocks
- API integration filling >90% of missing data
- Risk multipliers correctly identifying high-risk growth stocks

### Phase 2 Success Criteria:
- Data confidence >75%
- Risk accuracy >60%
- Cross-validation reducing data inconsistencies

### Phase 3 Success Criteria:
- Data confidence >80% ✅
- Risk accuracy >80% ✅
- Backtesting showing improved performance

---

**Implementation Priority:** Start with Phase 1 critical fixes immediately, as these address the most fundamental issues preventing the system from achieving target accuracy levels. 