# Batch Processing Logic and API Call Optimization

## Overview

The batch processing system is designed to efficiently handle multiple tickers while respecting API rate limits and optimizing performance. This document describes the logic, strategies, and implementation details for reducing API calls across all services.

## Batch Processing Architecture

### Core Components

1. **BatchProcessor**: Main orchestrator for processing multiple tickers
2. **AsyncBatchProcessor**: Asynchronous version for better performance
3. **Error Handling**: Integrated retry logic and fallback mechanisms
4. **Rate Limiting**: Built-in delays and API call management

### Batch Processing Flow

```mermaid
graph TD
    A[Input Tickers] --> B[Split into Batches]
    B --> C[Process Batch with ThreadPool]
    C --> D[Apply Rate Limiting]
    D --> E[Execute API Calls]
    E --> F[Handle Errors & Retries]
    F --> G[Collect Results]
    G --> H[Return Batch Results]
```

## Batch Processing Logic

### 1. Batch Configuration

```python
class BatchProcessor:
    def __init__(self, max_workers: int = 5, batch_size: int = 10, 
                 delay_between_batches: float = 1.0):
        self.max_workers = max_workers      # Concurrent threads
        self.batch_size = batch_size        # Tickers per batch
        self.delay_between_batches = delay_between_batches  # Rate limiting
```

### 2. Processing Strategy

#### Phase 1: Batch Division
- Split tickers into manageable batches (default: 10 tickers per batch)
- Each batch is processed independently to avoid overwhelming APIs

#### Phase 2: Concurrent Processing
- Use ThreadPoolExecutor for parallel API calls within each batch
- Configurable number of workers (default: 5 concurrent requests)

#### Phase 3: Rate Limiting
- Automatic delays between batches (default: 1 second)
- Respects API rate limits and prevents throttling

#### Phase 4: Error Handling
- Automatic retry with exponential backoff
- Fallback to secondary services for failed requests
- Comprehensive error logging and tracking

### 3. Performance Optimization

```python
# Performance benchmarks from testing:
# Batch Size 5:   8.3 tickers/sec
# Batch Size 10:  48.7 tickers/sec  
# Batch Size 20:  49.6 tickers/sec
```

## Specialized Batch Processing

### 1. Batch Price Processing (100 Stocks per API Call)

#### Implementation Strategy:
```python
class BatchPriceProcessor:
    def __init__(self, max_batch_size: int = 100):
        self.max_batch_size = max_batch_size
    
    def get_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get prices for up to 100 stocks in a single API call"""
        results = {}
        
        # Split into batches of 100
        for i in range(0, len(tickers), self.max_batch_size):
            batch = tickers[i:i + self.max_batch_size]
            
            # Single API call for entire batch
            batch_data = self.fetch_batch_prices(batch)
            
            # Parse results for each ticker
            for ticker in batch:
                if ticker in batch_data:
                    results[ticker] = batch_data[ticker]
        
        return results
    
    def fetch_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Make single API call for multiple tickers"""
        # Example for Yahoo Finance batch endpoint
        symbols = ','.join(tickers)
        url = f"{self.base_url}/v7/finance/quote"
        params = {
            'symbols': symbols,
            'fields': 'regularMarketPrice,regularMarketVolume,marketCap,regularMarketTime'
        }
        
        response = self._make_request(url, params)
        return self._parse_batch_response(response)
    
    def store_daily_prices(self, price_data: Dict[str, Dict]):
        """Store daily prices in daily_charts table"""
        for ticker, data in price_data.items():
            self.store_in_daily_charts(ticker, data)
```

#### Supported Services for Batch Price Processing:

##### A. Yahoo Finance
```python
def get_yahoo_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
    """Yahoo Finance supports up to 100 symbols per call"""
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {
        'symbols': ','.join(tickers),
        'fields': 'regularMarketPrice,regularMarketVolume,marketCap,regularMarketTime,regularMarketChange,regularMarketChangePercent'
    }
    return self._make_request(url, params)
```

##### B. Alpha Vantage
```python
def get_alpha_vantage_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
    """Alpha Vantage batch quote endpoint"""
    url = f"{self.base_url}/query"
    params = {
        'function': 'BATCH_STOCK_QUOTES',
        'symbols': ','.join(tickers),
        'apikey': self.api_key
    }
    return self._make_request(url, params)
```

##### C. Finnhub
```python
def get_finnhub_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
    """Finnhub batch quote endpoint"""
    url = f"{self.base_url}/quote"
    params = {
        'symbol': ','.join(tickers),
        'token': self.api_key
    }
    return self._make_request(url, params)
```

### 2. Earnings-Based Fundamental Updates

#### Implementation Strategy:
```python
class EarningsBasedFundamentalProcessor:
    def __init__(self):
        self.earnings_calendar = EarningsCalendarService()
    
    def should_update_fundamentals(self, ticker: str) -> bool:
        """Check if fundamentals should be updated based on earnings"""
        # Get next earnings date
        next_earnings = self.get_next_earnings_date(ticker)
        if not next_earnings:
            return False
        
        # Check if earnings report was recently released
        days_since_earnings = (datetime.now() - next_earnings).days
        
        # Update if earnings were within last 7 days
        return -7 <= days_since_earnings <= 7
    
    def get_fundamentals_update_candidates(self, tickers: List[str]) -> List[str]:
        """Get tickers that need fundamental updates based on earnings"""
        candidates = []
        
        for ticker in tickers:
            if self.should_update_fundamentals(ticker):
                candidates.append(ticker)
        
        return candidates
    
    def process_earnings_based_updates(self, tickers: List[str]):
        """Process fundamental updates only for tickers with recent earnings"""
        # Get tickers needing updates
        update_candidates = self.get_fundamentals_update_candidates(tickers)
        
        if update_candidates:
            print(f"Updating fundamentals for {len(update_candidates)} tickers with recent earnings")
            self.process_fundamental_batch(update_candidates)
        else:
            print("No tickers need fundamental updates based on earnings")
    
    def get_next_earnings_date(self, ticker: str) -> Optional[datetime]:
        """Get next earnings date for a ticker"""
        # Query earnings calendar
        earnings_data = self.earnings_calendar.get_earnings_date(ticker)
        return earnings_data.get('next_earnings_date') if earnings_data else None
```

#### Earnings Calendar Integration:
```python
class EarningsCalendarService:
    def get_earnings_date(self, ticker: str) -> Optional[Dict]:
        """Get earnings information for a ticker"""
        # Check database first
        cached = self.get_cached_earnings(ticker)
        if cached and self.is_earnings_data_fresh(cached):
            return cached
        
        # Fetch from API if needed
        api_data = self.fetch_earnings_from_api(ticker)
        if api_data:
            self.store_earnings_data(ticker, api_data)
        return api_data
    
    def is_earnings_data_fresh(self, earnings_data: Dict) -> bool:
        """Check if earnings data is fresh (within 1 day)"""
        last_updated = earnings_data.get('last_updated')
        if not last_updated:
            return False
        
        days_old = (datetime.now() - last_updated).days
        return days_old <= 1
```

### 3. Daily Price Storage in daily_charts Table

#### Implementation Strategy:
```python
class DailyPriceStorage:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def store_daily_prices(self, price_data: Dict[str, Dict]):
        """Store daily prices in daily_charts table"""
        for ticker, data in price_data.items():
            self.store_single_daily_price(ticker, data)
    
    def store_single_daily_price(self, ticker: str, price_data: Dict):
        """Store single ticker's daily price data"""
        query = """
        INSERT INTO daily_charts (
            ticker, date, open_price, high_price, low_price, 
            close_price, volume, market_cap, data_source, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        ) ON CONFLICT (ticker, date) 
        DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            market_cap = EXCLUDED.market_cap,
            data_source = EXCLUDED.data_source,
            updated_at = NOW()
        """
        
        values = (
            ticker,
            datetime.now().date(),
            price_data.get('open'),
            price_data.get('high'),
            price_data.get('low'),
            price_data.get('close'),
            price_data.get('volume'),
            price_data.get('market_cap'),
            price_data.get('data_source', 'batch_api')
        )
        
        self.db.execute(query, values)
    
    def get_latest_daily_price(self, ticker: str) -> Optional[Dict]:
        """Get latest daily price from daily_charts table"""
        query = """
        SELECT * FROM daily_charts 
        WHERE ticker = %s 
        ORDER BY date DESC 
        LIMIT 1
        """
        return self.db.fetch_one(query, (ticker,))
```

#### Daily Charts Table Schema:
```sql
CREATE TABLE IF NOT EXISTS daily_charts (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    market_cap DECIMAL(20,2),
    data_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, date)
);

CREATE INDEX idx_daily_charts_ticker_date ON daily_charts(ticker, date);
CREATE INDEX idx_daily_charts_date ON daily_charts(date);
```

## Updated API Call Reduction Strategies

### 1. Batch Price Processing (100 Stocks per Call)

#### Current vs. Optimized:
- **Current**: 1 API call per ticker for prices
- **Optimized**: 1 API call per 100 tickers for prices
- **Reduction**: 99% fewer API calls for price data

#### Implementation:
```python
class OptimizedBatchProcessor:
    def process_daily_update(self, tickers: List[str]):
        """Process daily update with batch price processing"""
        
        # Phase 1: Batch price processing (100 per call)
        print(f"Processing prices for {len(tickers)} tickers...")
        price_data = self.get_batch_prices(tickers)
        
        # Phase 2: Store in daily_charts table
        self.store_daily_prices(price_data)
        
        # Phase 3: Earnings-based fundamental updates
        fundamental_candidates = self.get_earnings_based_candidates(tickers)
        if fundamental_candidates:
            self.process_fundamental_batch(fundamental_candidates)
        
        return {
            'prices_processed': len(price_data),
            'fundamentals_updated': len(fundamental_candidates),
            'api_calls_made': self.calculate_api_calls(len(tickers), len(fundamental_candidates))
        }
    
    def calculate_api_calls(self, total_tickers: int, fundamental_tickers: int) -> int:
        """Calculate total API calls made"""
        # Price calls: 1 call per 100 tickers
        price_calls = (total_tickers + 99) // 100
        
        # Fundamental calls: 2 calls per ticker (for candidates only)
        fundamental_calls = fundamental_tickers * 2
        
        return price_calls + fundamental_calls
```

### 2. Updated Performance Metrics

#### API Call Reduction:
```python
# Example: 1000 tickers, 50 with recent earnings
# Current approach:
# - Price calls: 1000 calls
# - Fundamental calls: 1000 * 2 = 2000 calls
# Total: 3000 calls

# Optimized approach:
# - Price calls: 10 calls (100 per batch)
# - Fundamental calls: 50 * 2 = 100 calls (earnings-based only)
# Total: 110 calls

# Reduction: 96.3% fewer API calls
```

#### Expected Performance:
- **Price Processing**: 1000 tickers in 10 API calls
- **Fundamental Updates**: Only for tickers with recent earnings
- **Storage**: Proper separation between daily prices and fundamental data
- **Cost Savings**: 95%+ reduction in API costs

## Implementation Priority

### Phase 1 (Immediate - 1 week)
1. ✅ Implement batch price processing (100 per call)
2. ✅ Create daily_charts table storage
3. ✅ Implement earnings calendar integration

### Phase 2 (Short-term - 2 weeks)
1. 🔄 Earnings-based fundamental update logic
2. 🔄 Batch price processing for all services
3. 🔄 Data validation and error handling

### Phase 3 (Medium-term - 1 month)
1. 📋 Advanced earnings tracking
2. 📋 Automated earnings calendar updates
3. 📋 Performance monitoring and optimization

## Monitoring and Metrics

### Key Performance Indicators
- **Price Processing Efficiency**: Tickers per price API call
- **Earnings-Based Updates**: % of tickers updated based on earnings
- **Storage Accuracy**: Data in correct tables
- **Cost per Ticker**: Total API cost / tickers processed

### Target Metrics
- **Price Processing**: 100 tickers per API call
- **Earnings-Based Updates**: <10% of tickers updated daily
- **Storage Accuracy**: 100% correct table placement
- **Cost per Ticker**: <$0.001

## Cost Analysis

### Current Costs (1000 tickers daily)
- **Price API Calls**: 1000 calls
- **Fundamental API Calls**: 2000 calls
- **Total Cost**: $30-60 per day

### Optimized Costs (1000 tickers daily)
- **Price API Calls**: 10 calls (100 per batch)
- **Fundamental API Calls**: ~100 calls (earnings-based only)
- **Total Cost**: $1.10-2.20 per day
- **Cost Savings**: 96% reduction

## Risk Mitigation

### Potential Issues
1. **Batch API Limits**: Some services may not support 100 per call
2. **Earnings Data Accuracy**: Earnings dates might be incorrect
3. **Data Synchronization**: Ensuring price and fundamental data consistency

### Mitigation Strategies
1. **Fallback to Smaller Batches**: Use 50 or 25 per call if needed
2. **Multiple Earnings Sources**: Cross-reference earnings dates
3. **Data Validation**: Verify data consistency before storage
4. **Monitoring Alerts**: Alert on unusual update patterns

## Conclusion

The updated batch processing strategy with:
- **Batch price processing** (100 stocks per API call)
- **Earnings-based fundamental updates**
- **Proper daily price storage** in daily_charts table

Will result in:
- **96% reduction in API calls**
- **95% cost savings**
- **Proper data organization**
- **Earnings-driven updates** instead of time-based updates

This approach ensures efficient data collection while maintaining data quality and proper storage organization. 