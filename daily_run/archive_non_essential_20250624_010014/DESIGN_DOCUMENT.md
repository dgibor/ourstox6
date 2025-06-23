# Daily Financial Data Pipeline - Design Document

## Overview

This document describes the new modular architecture for the daily financial data pipeline that processes stock prices, fundamental data, and calculates financial ratios for value investing analysis.

## Architecture Overview

The system follows a **modular, service-oriented architecture** with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Production    │    │   Service       │    │   Database      │
│   Daily Runner  │───▶│   Factory       │───▶│   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Daily         │    │   Price         │    │   Ratios        │
│   Pipeline      │    │   Service       │    │   Calculator    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Fundamental   │    │   Base          │    │   Configuration │
│   Service       │    │   Service       │    │   Management    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Configuration Management (`config.py`)
- **Purpose**: Centralized configuration for all components
- **Features**:
  - Database connection settings
  - API keys management
  - Rate limits configuration
  - Batch processing settings
- **Usage**: All components import from this single source

### 2. Database Manager (`database.py`)
- **Purpose**: Centralized database operations
- **Features**:
  - Connection pooling and management
  - Context manager for transactions
  - Standardized query execution
  - Price data updates
  - Ticker retrieval methods
- **Key Methods**:
  - `connect()` / `disconnect()`
  - `execute_query()` / `execute_update()`
  - `get_tickers()`
  - `update_price_data()`

### 3. Service Factory (`service_factory.py`)
- **Purpose**: Factory pattern for creating and managing API services
- **Features**:
  - Service registry for different providers
  - Automatic service creation and caching
  - Rate limit management
  - Service testing capabilities
- **Supported Services**:
  - Price services: Yahoo, Finnhub, FMP
  - Fundamental services: Consolidated (Yahoo + FMP)

### 4. Base Service (`base_service.py`)
- **Purpose**: Abstract base class for all API services
- **Features**:
  - Common service functionality
  - Rate limiting support
  - Error handling
  - Logging and monitoring
- **Key Methods**:
  - `validate_ticker()`
  - `log_request()`
  - `get_data()` (abstract)

### 5. Price Service (`price_service.py`)
- **Purpose**: Multi-provider price data collection
- **Providers**:
  - **YahooPriceService**: Uses yfinance (no API key required)
  - **FinnhubPriceService**: Uses Finnhub API
  - **FMPPriceService**: Uses Financial Modeling Prep API
- **Features**:
  - Automatic fallback between providers
  - Rate limiting per provider
  - Batch processing
  - Price data standardization

### 6. Fundamental Service (`fundamental_service.py`)
- **Purpose**: Multi-provider fundamental data collection
- **Providers**:
  - Yahoo Finance Service
  - Financial Modeling Prep Service
- **Features**:
  - Fallback logic between providers
  - Data merging and standardization
  - Batch processing capabilities

### 7. Ratios Calculator (`ratios_calculator.py`)
- **Purpose**: Financial ratio calculations with exact formulas
- **Supported Ratios**:
  - P/E Ratio (Price to Earnings)
  - P/B Ratio (Price to Book)
  - P/S Ratio (Price to Sales)
  - EV/EBITDA (Enterprise Value to EBITDA)
  - ROE (Return on Equity)
  - ROA (Return on Assets)
  - Debt to Equity Ratio
  - Current Ratio
  - Graham Number
- **Features**:
  - Edge case handling
  - Data quality scoring
  - Rounding to 2 decimal places
  - Comprehensive error handling

### 8. Daily Pipeline (`new_daily_pipeline.py`)
- **Purpose**: Orchestrates the complete daily data processing workflow
- **Steps**:
  1. **Price Updates**: Collect current market prices
  2. **Fundamental Updates**: Fetch latest financial data
  3. **Ratio Calculations**: Compute financial ratios
- **Features**:
  - Step-by-step execution
  - Comprehensive logging
  - Error handling and recovery
  - Progress tracking
  - Summary generation

### 9. Production Daily Runner (`production_daily_runner.py`)
- **Purpose**: Production-ready script for running the complete pipeline
- **Features**:
  - Command-line interface
  - Test mode support
  - Comprehensive statistics
  - Detailed logging
  - Error handling and reporting
  - Progress tracking

## Data Flow

### 1. Price Data Flow
```
Ticker List → Price Service → Database (daily_charts table)
     ↓              ↓                    ↓
   Stocks      Multi-provider      Price History
   Table       Fallback Logic      Storage
```

### 2. Fundamental Data Flow
```
Ticker List → Fundamental Service → Database (financials table)
     ↓              ↓                      ↓
   Stocks      Multi-provider        Financial Data
   Table       Fallback Logic        Storage
```

### 3. Ratio Calculation Flow
```
Financial Data → Ratios Calculator → Database (ratios table)
     ↓              ↓                    ↓
   Database     Formula-based        Calculated Ratios
   Query        Calculations         Storage
```

## Database Schema

### Key Tables
1. **stocks**: Company information and fundamental data
2. **daily_charts**: Historical price data
3. **financials**: Financial statement data
4. **ratios**: Calculated financial ratios

## Error Handling Strategy

### 1. Service Level
- Rate limit detection and handling
- Automatic fallback between providers
- Retry logic with exponential backoff
- Comprehensive error logging

### 2. Pipeline Level
- Step-by-step error isolation
- Graceful degradation
- Detailed error reporting
- Recovery mechanisms

### 3. Production Level
- Comprehensive statistics tracking
- Error categorization
- Success rate monitoring
- Alert mechanisms

## Rate Limiting Strategy

### Provider Limits
- **Yahoo Finance**: 100 calls/minute (conservative)
- **Finnhub**: 60 calls/minute
- **FMP**: 300 calls/minute
- **Alpha Vantage**: 5 calls/minute

### Implementation
- Decorator-based rate limiting
- Automatic retry with delays
- Provider fallback on rate limits

## Configuration Management

### Environment Variables
- Database connection details
- API keys for paid services
- Logging configuration
- Batch processing settings

### Validation
- Required environment variable checking
- Configuration validation on startup
- Graceful error handling for missing config

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock external dependencies
- Error condition testing

### Integration Tests
- End-to-end workflow testing
- Database integration testing
- Service interaction testing

### Production Testing
- Test mode with limited tickers
- Performance monitoring
- Error rate tracking

## Deployment Considerations

### Requirements
- Python 3.8+
- PostgreSQL database
- Required Python packages (see requirements.txt)
- Environment variables configuration

### Monitoring
- Comprehensive logging
- Performance metrics
- Error tracking
- Success rate monitoring

### Scalability
- Batch processing capabilities
- Rate limit management
- Database connection pooling
- Modular architecture for easy extension

## Future Enhancements

### Planned Features
1. **Scheduler Integration**: Automated daily runs
2. **Additional Data Sources**: More fundamental data providers
3. **Advanced Ratios**: More sophisticated financial metrics
4. **Real-time Updates**: WebSocket-based price updates
5. **Dashboard Integration**: Real-time monitoring interface

### Architecture Extensions
1. **Microservice Architecture**: Service decomposition
2. **Message Queues**: Asynchronous processing
3. **Caching Layer**: Redis integration
4. **API Gateway**: RESTful API interface

## Code Quality Standards

### Code Organization
- Single responsibility principle
- Clear separation of concerns
- Consistent naming conventions
- Comprehensive documentation

### Error Handling
- Graceful degradation
- Comprehensive logging
- User-friendly error messages
- Recovery mechanisms

### Performance
- Efficient database queries
- Rate limit compliance
- Batch processing optimization
- Memory management

## Conclusion

This modular architecture provides a robust, scalable, and maintainable foundation for daily financial data processing. The clear separation of concerns, comprehensive error handling, and multi-provider support ensure reliable operation in production environments.

The system is designed to be easily extensible, with new data sources and calculation methods can be added without affecting existing functionality. The production-ready components provide the foundation for a comprehensive value investing data platform. 