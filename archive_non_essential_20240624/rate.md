# API Rate Limiting Research & Optimization Guide

## Executive Summary
This document provides comprehensive research on rate limits for all API services used in the financial data collection system, along with optimization recommendations for the FMP Starter membership and other services.

## Current API Services & Rate Limits

### 1. Financial Modeling Prep (FMP) - **STARTER MEMBERSHIP**
**Current Plan:** Starter ($19.99/month)
**Rate Limits:**
- **Daily Limit:** 1,000 API calls per day
- **Concurrent Requests:** 5 requests per second
- **Reset Time:** Midnight UTC
- **Premium Features:** 
  - Real-time data
  - Advanced financial ratios
  - Earnings calendar
  - Company profiles
  - Financial statements (Income, Balance Sheet, Cash Flow)

**Optimization Strategy:**
- Batch requests where possible (up to 100 symbols per call)
- Prioritize high-value endpoints
- Implement intelligent retry logic with exponential backoff
- Cache frequently accessed data

### 2. Alpha Vantage
**Current Plan:** Free Tier
**Rate Limits:**
- **Daily Limit:** 500 API calls per day
- **Per Minute:** 5 calls per minute
- **Reset Time:** Midnight UTC
- **Premium Plans:** 
  - Basic: $49.99/month (1,200 calls/day)
  - Premium: $99.99/month (5,000 calls/day)

**Optimization Strategy:**
- Use as fallback only due to low limits
- Implement strict rate limiting (12-second delays between calls)
- Prioritize essential endpoints only

### 3. Yahoo Finance (yfinance)
**Current Plan:** Free (No API key required)
**Rate Limits:**
- **Estimated Daily Limit:** 2,000+ calls per day
- **Per Minute:** ~100 calls per minute
- **No Official Documentation:** Limits are not publicly documented
- **Advantages:** No API key required, good data quality

**Optimization Strategy:**
- Use as primary price data source
- Implement conservative rate limiting (1 call per second)
- Monitor for 429 responses and adjust accordingly

### 4. Finnhub
**Current Plan:** Free Tier
**Rate Limits:**
- **Daily Limit:** 60,000 API calls per day
- **Per Minute:** 60 calls per minute
- **Reset Time:** Midnight UTC
- **Premium Plans:**
  - Basic: $9.99/month (100,000 calls/day)
  - Professional: $99.99/month (1,000,000 calls/day)

**Optimization Strategy:**
- Excellent for high-volume data collection
- Use for real-time quotes and market data
- Implement 1-second delays between calls

### 5. Polygon.io
**Current Plan:** Basic (Free)
**Rate Limits:**
- **Daily Limit:** 5 calls per minute
- **Per Second:** 1 call per second
- **Paid Plans:**
  - Starter: $29/month (5 calls/second)
  - Developer: $99/month (5 calls/second)
  - Advanced: $199/month (10 calls/second)
  - Enterprise: Custom pricing (50+ calls/second)

**Optimization Strategy:**
- Limited free tier, consider paid upgrade for production use
- Use for high-quality market data when available
- Implement strict rate limiting

## Current System Analysis

### Existing Rate Limiting Implementation
```python
# Current configuration in config.py
RATE_LIMITS = {
    'finnhub': 60,        # calls per minute
    'alpha_vantage': 5,   # calls per minute  
    'fmp': 300,           # calls per minute (INACCURATE)
    'yahoo': 100          # calls per minute (estimated)
}
```

### Issues Identified
1. **FMP Rate Limit Inaccuracy:** Configured for 300 calls/minute but Starter plan is 1,000 calls/day
2. **Missing Polygon.io Configuration:** Not included in rate limits
3. **Inconsistent Implementation:** Different services use different rate limiting approaches
4. **No Daily Limit Tracking:** Only per-minute limits are tracked
5. **Inefficient Batch Processing:** Not optimized for FMP's batch capabilities

## Optimization Recommendations

### 1. FMP Starter Membership Optimization

**Priority 1: Batch Processing**
```python
# FMP Batch Endpoints (1 call = multiple tickers)
- /v3/quote/{symbols} (up to 100 symbols)
- /v3/profile/{symbols} (up to 100 symbols)
- /v3/income-statement/{symbols} (up to 100 symbols)
```

**Priority 2: Endpoint Optimization**
```python
# High-Value Endpoints (use daily quota efficiently)
1. Company Profile (1 call) - contains key metrics
2. Financial Ratios (1 call) - pre-calculated ratios
3. Income Statement (1 call) - raw financial data
4. Balance Sheet (1 call) - raw financial data
5. Cash Flow (1 call) - raw financial data
```

**Priority 3: Caching Strategy**
```python
# Cache durations for different data types
- Company Profile: 7 days (rarely changes)
- Financial Statements: 1 day (quarterly updates)
- Real-time Quotes: 5 minutes (market hours)
- Historical Data: 1 day (daily updates)
```

### 2. Rate Limiting Architecture Improvements

**New Rate Limiting Class:**
```python
class AdvancedRateLimiter:
    def __init__(self):
        self.daily_limits = {
            'fmp': 1000,
            'alpha_vantage': 500,
            'finnhub': 60000,
            'yahoo': 2000,
            'polygon': 300  # 5 calls/min * 60 min * 24 hours
        }
        self.minute_limits = {
            'fmp': 5,  # 5 calls per second = 300 per minute
            'alpha_vantage': 5,
            'finnhub': 60,
            'yahoo': 100,
            'polygon': 5
        }
```

### 3. Service Priority Matrix

| Service | Primary Use | Daily Limit | Priority | Optimization |
|---------|-------------|-------------|----------|--------------|
| FMP | Fundamentals | 1,000 | HIGH | Batch processing, caching |
| Yahoo | Price Data | 2,000+ | HIGH | Conservative rate limiting |
| Finnhub | Market Data | 60,000 | MEDIUM | High-volume operations |
| Alpha Vantage | Fallback | 500 | LOW | Essential endpoints only |
| Polygon | Premium Data | 300 | LOW | Paid upgrade recommended |

### 4. Implementation Plan

**Phase 1: FMP Optimization (Week 1)**
- [ ] Update rate limiting configuration for FMP Starter plan
- [ ] Implement batch processing for company profiles
- [ ] Add intelligent caching for financial data
- [ ] Create daily quota monitoring

**Phase 2: Service Integration (Week 2)**
- [ ] Standardize rate limiting across all services
- [ ] Implement service fallback logic
- [ ] Add real-time quota monitoring
- [ ] Create alert system for quota usage

**Phase 3: Advanced Features (Week 3)**
- [ ] Implement adaptive rate limiting
- [ ] Add predictive quota management
- [ ] Create cost optimization recommendations
- [ ] Add performance analytics

## Cost Analysis & Recommendations

### Current Monthly Costs
- FMP Starter: $19.99/month
- Alpha Vantage: Free
- Finnhub: Free
- Yahoo Finance: Free
- Polygon.io: Free

### Recommended Upgrades
1. **FMP Premium ($39.99/month):** 10,000 calls/day for high-volume operations
2. **Polygon.io Starter ($29/month):** Better market data quality
3. **Finnhub Basic ($9.99/month):** Higher limits for real-time data

### ROI Analysis
- **Current Setup:** $19.99/month for 1,000 FMP calls/day
- **Optimized Setup:** $19.99/month with 10x efficiency through batching
- **Recommended Setup:** $58.97/month for comprehensive coverage

## Technical Implementation

### 1. Updated Configuration
```python
# New rate limiting configuration
API_LIMITS = {
    'fmp': {
        'daily_limit': 1000,
        'minute_limit': 300,  # 5 calls/second
        'batch_size': 100,
        'plan': 'starter',
        'cost_per_call': 0.02  # $19.99 / 1000 calls
    },
    'yahoo': {
        'daily_limit': 2000,
        'minute_limit': 100,
        'batch_size': 1,
        'plan': 'free',
        'cost_per_call': 0.0
    },
    # ... other services
}
```

### 2. Batch Processing Implementation
```python
def process_fmp_batch(tickers: List[str]) -> Dict:
    """Process up to 100 tickers in a single FMP API call"""
    batches = [tickers[i:i+100] for i in range(0, len(tickers), 100)]
    results = {}
    
    for batch in batches:
        symbols = ','.join(batch)
        url = f"{FMP_BASE_URL}/profile/{symbols}"
        # Single API call for 100 tickers
        response = make_fmp_request(url)
        results.update(parse_batch_response(response))
        
        # Rate limiting delay
        time.sleep(0.2)  # 5 calls per second
    
    return results
```

### 3. Quota Management
```python
class QuotaManager:
    def __init__(self):
        self.daily_usage = {}
        self.reset_times = {}
    
    def can_make_request(self, service: str) -> bool:
        """Check if we can make a request without exceeding daily limit"""
        today = datetime.utcnow().date()
        current_usage = self.daily_usage.get(f"{service}_{today}", 0)
        daily_limit = API_LIMITS[service]['daily_limit']
        return current_usage < daily_limit
    
    def record_request(self, service: str):
        """Record an API request"""
        today = datetime.utcnow().date()
        key = f"{service}_{today}"
        self.daily_usage[key] = self.daily_usage.get(key, 0) + 1
```

## Monitoring & Alerts

### 1. Quota Monitoring
- Real-time daily usage tracking
- 80% quota usage alerts
- Service-specific performance metrics
- Cost tracking and optimization recommendations

### 2. Performance Metrics
- API response times
- Success/failure rates
- Rate limit hit frequency
- Data quality metrics

### 3. Alert System
```python
ALERT_THRESHOLDS = {
    'fmp': {
        'daily_usage_warning': 800,  # 80% of 1000
        'daily_usage_critical': 950, # 95% of 1000
        'error_rate_warning': 0.05,  # 5% error rate
        'response_time_warning': 5.0  # 5 seconds
    }
}
```

## Conclusion

The current system has significant optimization opportunities, particularly for the FMP Starter membership. By implementing batch processing, intelligent caching, and proper rate limiting, we can achieve 10x efficiency improvements while maintaining data quality.

**Key Recommendations:**
1. **Immediate:** Update FMP rate limiting to reflect Starter plan limits
2. **Short-term:** Implement batch processing for all FMP endpoints
3. **Medium-term:** Add comprehensive quota management and monitoring
4. **Long-term:** Consider service upgrades based on usage patterns

**Expected Outcomes:**
- 90% reduction in API calls through batching
- 50% improvement in data collection speed
- 100% quota utilization efficiency
- Proactive cost management and optimization 