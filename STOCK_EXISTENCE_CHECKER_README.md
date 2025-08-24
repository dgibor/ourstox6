# Stock Existence Checker

## Overview

The `StockExistenceChecker` is a robust system for identifying and removing delisted stocks from the database. It implements a **refined deletion strategy** that only removes stocks when multiple APIs explicitly confirm they don't exist, protecting against false positives from rate limits or temporary API failures.

## Key Features

### 🔍 Multi-API Validation
- Checks stock existence across **4 major APIs**: Yahoo Finance, FMP, Finnhub, and Alpha Vantage
- **Intelligent error handling** that distinguishes between different types of API failures
- **Configurable threshold** for deletion (default: requires 2 APIs to explicitly report "not found")

### 🛡️ Rate Limit Protection
- **Rate limit awareness**: Distinguishes between rate limit errors and actual "stock not found" responses
- **Batch processing** with configurable delays to respect API quotas
- **Graceful degradation** when APIs are temporarily unavailable

### 🗄️ Database Integrity
- **Foreign key constraint compliance** during deletion
- **Ordered cleanup** across all related tables
- **Transaction safety** with proper error handling

## Architecture

### Core Components

```python
@dataclass
class ExistenceCheckResult:
    ticker: str
    exists_in_apis: List[str]        # APIs that found the stock
    not_found_in_apis: List[str]     # APIs that explicitly reported "not found"
    rate_limited_apis: List[str]     # APIs that hit rate limits
    error_apis: List[str]            # APIs with other errors
    total_apis_checked: int
    should_remove: bool
    check_time: datetime
```

### Deletion Logic

The system implements a **sophisticated decision matrix**:

| Scenario | APIs Found | APIs Not Found | APIs Rate Limited | APIs with Errors | Result |
|----------|------------|----------------|-------------------|-------------------|---------|
| **Stock exists** | 2+ | 0-1 | 0-2 | 0-2 | ✅ **KEEP** |
| **Below threshold** | 1+ | 1 | 0-3 | 0-3 | ✅ **KEEP** |
| **At threshold** | 0-1 | 2 | 0-2 | 0-2 | 🚨 **REMOVE** |
| **Above threshold** | 0 | 3+ | 0-1 | 0-1 | 🚨 **REMOVE** |
| **Rate limited** | 1+ | 0-1 | 2+ | 0-1 | ✅ **KEEP** |

**Key Principle**: Only APIs that explicitly report "stock not found" count toward the deletion threshold. Rate limits, timeouts, and other errors are **ignored** for deletion decisions.

## API Priority & Reliability

### 1. **Yahoo Finance** (Most Reliable)
- Free tier with generous limits
- Comprehensive stock coverage
- Stable API responses

### 2. **FMP (Financial Modeling Prep)**
- Premium data quality
- Good coverage of US stocks
- Reliable error responses

### 3. **Finnhub**
- Real-time data
- Good international coverage
- Clear "not found" responses

### 4. **Alpha Vantage**
- Extensive historical data
- Good for validation
- Clear error messaging

## Usage

### Basic Usage

```python
from daily_run.stock_existence_checker import StockExistenceChecker
from daily_run.database import DatabaseManager
from daily_run.enhanced_multi_service_manager import EnhancedMultiServiceManager

# Initialize
db = DatabaseManager()
service_manager = EnhancedMultiServiceManager()
checker = StockExistenceChecker(db, service_manager)

# Check single stock
result = checker.check_stock_exists('AAPL')
print(f"Should remove: {result.should_remove}")

# Process multiple stocks
tickers = ['AAPL', 'MSFT', 'INVALID', 'DELISTED']
results = checker.process_tickers_in_batches(tickers)

# Remove delisted stocks
removal_stats = checker.remove_delisted_stocks(results)
```

### Integration with Daily Trading System

The checker is automatically integrated into the daily trading workflow:

```python
# In daily_trading_system.py
def _remove_delisted_stocks(self):
    """Remove delisted stocks using enhanced multi-API validation"""
    tickers = self._get_all_tickers()
    
    # Initialize existence checker
    existence_checker = StockExistenceChecker(self.db, self.service_manager)
    
    # Check existence across all APIs
    check_results = existence_checker.process_tickers_in_batches(tickers)
    
    # Remove stocks that meet deletion criteria
    removal_results = existence_checker.remove_delisted_stocks(check_results)
    
    return {
        'total_tickers_checked': len(tickers),
        'delisted_removed': removal_results['removed'],
        'removal_errors': removal_results['errors'],
        'apis_checked': ['yahoo', 'fmp', 'finnhub', 'alpha_vantage']
    }
```

## Configuration

### Batch Processing

```python
# Configurable batch settings
self.batch_size = 50                    # Tickers per batch
self.delay_between_batches = 2          # Seconds between batches
self.min_not_found_apis = 2             # Minimum APIs reporting "not found"
```

### API Selection

```python
# APIs to check (in order of reliability)
self.apis_to_check = [
    'yahoo',           # Most reliable
    'fmp',            # Premium data
    'finnhub',        # Real-time
    'alpha_vantage'   # Historical data
]
```

## Database Tables Cleaned

The system removes delisted stocks from all related tables in the correct order:

1. **`daily_charts`** - Price history data
2. **`technical_indicators`** - Calculated indicators
3. **`company_fundamentals`** - Financial ratios and metrics
4. **`stocks`** - Main stock information

## Error Handling

### Exception Types

- **`DataNotFoundError`**: Stock explicitly doesn't exist in API
- **`RateLimitError`**: API rate limit exceeded
- **`ServiceError`**: General API service error
- **`DatabaseError`**: Database operation failure

### Error Recovery

- **Rate limit errors**: Logged but don't affect deletion decisions
- **Service errors**: Logged and marked as "error" status
- **Database errors**: Logged with rollback protection
- **Network timeouts**: Retried with exponential backoff

## Monitoring & Logging

### Log Levels

- **DEBUG**: Detailed API call information
- **INFO**: Batch processing progress and results
- **WARNING**: Stocks marked for removal
- **ERROR**: Failed operations and exceptions

### Key Metrics

- Total tickers processed
- APIs checked per ticker
- Rate limit occurrences
- Deletion success/failure rates
- Processing time per batch

## Testing

### Test Coverage

```bash
# Run comprehensive tests
python daily_run/test_stock_existence_checker.py
```

### Test Scenarios

1. **Single Stock Check**: Verify individual stock validation
2. **Batch Processing**: Test multiple ticker processing
3. **Deletion Logic**: Validate threshold-based decisions
4. **Database Removal**: Test cleanup operations (dry run)

### Edge Cases Tested

- All APIs rate limited
- Mixed API responses
- Network failures
- Invalid ticker symbols
- Database connection issues

## Performance

### Optimization Features

- **Batch processing** to minimize API calls
- **Configurable delays** to respect rate limits
- **Parallel API checking** within batches
- **Efficient database queries** with proper indexing

### Expected Performance

- **Small batches (50 tickers)**: ~2-3 minutes
- **Medium batches (500 tickers)**: ~15-20 minutes
- **Large batches (1000+ tickers)**: ~30-45 minutes

*Performance varies based on API response times and rate limits*

## Future Enhancements

### Planned Features

- **Machine learning** for better false positive detection
- **API health monitoring** and automatic failover
- **Real-time notifications** for delisted stock detection
- **Historical tracking** of stock status changes
- **Integration with** external delisting databases

### Configuration Improvements

- **Dynamic API selection** based on availability
- **Adaptive rate limiting** based on API performance
- **Customizable thresholds** per stock category
- **Scheduled cleanup** during low-traffic periods

## Troubleshooting

### Common Issues

#### Rate Limit Errors
```
WARNING: Rate limit exceeded for yahoo
```
**Solution**: Increase delays between batches or reduce batch size

#### API Service Errors
```
ERROR: Service error with fmp: HTTP 500
```
**Solution**: Check API status and consider temporary exclusion

#### Database Connection Issues
```
ERROR: Database connection failed
```
**Solution**: Verify database connectivity and credentials

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger('stock_existence_checker').setLevel(logging.DEBUG)
```

## Security Considerations

### API Key Management

- **Environment variables** for sensitive credentials
- **Rate limit enforcement** to prevent abuse
- **Request validation** to prevent injection attacks
- **Error message sanitization** to avoid information leakage

### Database Security

- **Parameterized queries** to prevent SQL injection
- **Transaction isolation** for data consistency
- **Access control** through database user permissions
- **Audit logging** for all deletion operations

## Contributing

### Development Guidelines

1. **Follow PEP 8** coding standards
2. **Add comprehensive tests** for new features
3. **Update documentation** for API changes
4. **Use type hints** for all function parameters
5. **Handle exceptions** gracefully with proper logging

### Testing Requirements

- **Unit tests** for all new functions
- **Integration tests** for API interactions
- **Performance tests** for batch operations
- **Edge case coverage** for error scenarios

---

## Summary

The `StockExistenceChecker` provides a **robust, intelligent solution** for managing delisted stocks. By requiring multiple APIs to explicitly confirm a stock's non-existence, it eliminates false positives from temporary API failures while maintaining efficient database cleanup.

The system's **sophisticated error handling** and **configurable thresholds** make it suitable for production environments where data accuracy and system reliability are critical.

