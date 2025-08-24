# Stock Existence Checker

## Overview

The Stock Existence Checker is a comprehensive solution for identifying and removing delisted stocks from the database. It checks if stocks exist across multiple APIs and automatically removes those that can't be found in any available service.

## Features

- **Multi-API Validation**: Checks stock existence across Yahoo Finance, FMP, Finnhub, and Alpha Vantage
- **Batch Processing**: Processes large numbers of tickers efficiently with configurable batch sizes
- **Rate Limit Respect**: Includes delays between API calls and batches to respect rate limits
- **Automatic Cleanup**: Removes delisted stocks from all related database tables
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Error Handling**: Robust error handling with fallback strategies

## Architecture

### Core Components

1. **StockExistenceChecker**: Main class that orchestrates the checking and removal process
2. **ExistenceCheckResult**: Data class that stores the results of existence checks
3. **Integration Points**: Updated daily trading system and analyst scoring manager

### API Priority Order

1. **Yahoo Finance** (Primary) - Free, reliable, no rate limits
2. **FMP** (Secondary) - Paid, reliable, moderate rate limits
3. **Finnhub** (Secondary) - Paid, reliable, moderate rate limits
4. **Alpha Vantage** (Fallback) - Paid, less reliable, strict rate limits

## Usage

### Basic Usage

```python
from stock_existence_checker import StockExistenceChecker
from database import DatabaseManager

# Initialize
db = DatabaseManager()
checker = StockExistenceChecker(db)

# Check a single stock
result = checker.check_stock_exists('AAPL')
if result.should_remove:
    print(f"{result.ticker} should be removed")

# Process multiple tickers
tickers = ['AAPL', 'MSFT', 'GOOGL']
results = checker.process_tickers_in_batches(tickers)

# Remove delisted stocks
removal_results = checker.remove_delisted_stocks(results)
```

### Integration with Daily Trading System

The checker is automatically integrated into the daily trading system's `_remove_delisted_stocks()` function. It runs as part of the daily cleanup process.

### Integration with Analyst Scoring

The analyst scoring manager now includes a `filter_existing_tickers()` method that samples tickers to identify potential delisted stocks before processing.

## Configuration

### Batch Processing

- **Batch Size**: 50 tickers per batch (configurable)
- **Delay Between Batches**: 2 seconds (configurable)
- **Delay Between API Calls**: 0.1 seconds (configurable)

### API Configuration

APIs can be enabled/disabled by modifying the `apis_to_check` list in the checker initialization.

## Database Tables Cleaned

When removing a delisted stock, the following tables are cleaned (in order):

1. `daily_charts` - Price data
2. `technical_indicators` - Technical analysis data
3. `company_fundamentals` - Financial data
4. `stocks` - Main stock information

## Error Handling

- **API Failures**: Individual API failures don't stop the process
- **Database Errors**: Database errors are logged and the process continues
- **Import Errors**: Graceful fallback if the checker can't be imported
- **Rate Limiting**: Automatic delays and retry logic

## Monitoring

### Logging Levels

- **INFO**: General process information and results
- **WARNING**: Stocks marked for removal
- **ERROR**: Failed operations and exceptions
- **DEBUG**: Detailed API call information

### Key Metrics

- Total tickers checked
- Stocks found in each API
- Stocks marked for removal
- Removal success/failure counts
- Processing time

## Testing

Run the test script to verify functionality:

```bash
cd daily_run
python test_stock_existence_checker.py
```

## Performance Considerations

- **API Calls**: Each ticker requires up to 4 API calls (one per service)
- **Batch Processing**: Reduces overall processing time for large datasets
- **Rate Limiting**: Built-in delays prevent API quota exhaustion
- **Database Operations**: Bulk operations minimize database overhead

## Future Enhancements

- **Caching**: Cache API responses to reduce redundant calls
- **Parallel Processing**: Process multiple tickers simultaneously
- **Machine Learning**: Use historical data to predict delisted stocks
- **Webhook Integration**: Notify external systems of removals
- **Scheduled Cleanup**: Automatic periodic cleanup without manual intervention

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **API Failures**: Check API keys and rate limits
3. **Database Errors**: Verify database connectivity and permissions
4. **Memory Issues**: Reduce batch size for large datasets

### Debug Mode

Enable debug logging to see detailed API call information:

```python
import logging
logging.getLogger('stock_existence_checker').setLevel(logging.DEBUG)
```

## Security Considerations

- **API Keys**: Stored securely in environment variables
- **Database Access**: Uses existing database connection with proper permissions
- **Error Logging**: Sensitive information is not logged
- **Rate Limiting**: Prevents API abuse and quota exhaustion

