# Stock Screener & Analysis API Design

## Overview
RESTful API for stock screening and analysis dashboards, inspired by SeekingAlpha, Finviz, and Yahoo Finance. Supports:
- Filterable screener (table) with technical/fundamental scores, price, company info, upside
- Technical analysis dashboard (per stock)
- Fundamental analysis dashboard (per stock)
- Sector dashboard (aggregated view)

**Versioned:** All endpoints prefixed with `/api/v1/`
**Authentication:** None required
**Batch Support:** Only for screener/table
**Ticker:** Always included in responses

---

## Data Model Mapping
- **Ticker**: Unique stock symbol (always included)
- **Company Name**: `stocks.company_name`
- **Price**: Latest price (from `stocks` or price table)
- **Technical Score**: `investor_scores.*` or technical scoring table
- **Fundamental Score**: `investor_scores.*` or calculated from ratios
- **Upside**: (Analyst avg target - current price) / current price
- **Market Cap**: `stocks.market_cap` or `financial_ratios.market_cap`
- **Sector**: `stocks.gics_sector`
- **Industry**: `stocks.gics_industry`
- **All Ratios**: `financial_ratios.*`
- **All Fundamentals**: `company_fundamentals.*`

---

## Endpoints

### 1. Stock Screener (Table)
**GET `/api/v1/screener`**

Returns a paginated, filterable list of stocks with key metrics.

#### Query Parameters
- `page` (int, default=1): Page number
- `page_size` (int, default=25, max=100): Results per page
- `sort_by` (string, default="upside"): Field to sort by (`upside`, `technical_score`, `fundamental_score`, `market_cap`, `price`)
- `sort_order` (string, default="desc"): `asc` or `desc`
- `market_cap_min` (float, optional): Minimum market cap
- `market_cap_max` (float, optional): Maximum market cap
- `sector` (string, optional): Filter by sector
- `industry` (string, optional): Filter by industry
- `technical_score_min` (int, optional): Minimum technical score
- `technical_score_max` (int, optional): Maximum technical score
- `fundamental_score_min` (int, optional): Minimum fundamental score
- `fundamental_score_max` (int, optional): Maximum fundamental score
- `upside_min` (float, optional): Minimum upside (e.g., 0.15 for 15%)
- `upside_max` (float, optional): Maximum upside

#### Example Request
```
GET /api/v1/screener?page=1&page_size=25&sector=Technology&market_cap_min=10000000000&sort_by=upside&sort_order=desc
```

#### Example Response
```json
{
  "page": 1,
  "page_size": 25,
  "total": 1200,
  "results": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "price": 195.12,
      "market_cap": 3000000000000,
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "technical_score": 87,
      "fundamental_score": 92,
      "upside": 0.18
    },
    // ...
  ]
}
```

---

### 2. Technical Analysis Dashboard
**GET `/api/v1/technical/{ticker}`**

Returns all technical indicators and scores for a single stock.

#### Path Parameters
- `ticker` (string, required): Stock symbol

#### Example Request
```
GET /api/v1/technical/AAPL
```

#### Example Response
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "price": 195.12,
  "technical_score": 87,
  "indicators": {
    "rsi": 54.2,
    "macd": 1.23,
    "adx": 28.1,
    "sma_50": 192.5,
    "sma_200": 180.3,
    // ...
  },
  "trend": "bullish",
  "last_updated": "2024-07-05T15:30:00Z"
}
```

---

### 3. Fundamental Analysis Dashboard
**GET `/api/v1/fundamental/{ticker}`**

Returns all fundamental metrics, scores, and explanations for a single stock.

#### Path Parameters
- `ticker` (string, required): Stock symbol

#### Example Request
```
GET /api/v1/fundamental/AAPL
```

#### Example Response
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "price": 195.12,
  "market_cap": 3000000000000,
  "fundamental_score": 92,
  "ratios": {
    "pe_ratio": 28.5,
    "pb_ratio": 32.1,
    "roe": 120.3,
    "debt_to_equity": 1.5,
    // ...
  },
  "fundamentals": {
    "revenue": 400000000000,
    "net_income": 95000000000,
    "eps_diluted": 6.12,
    // ...
  },
  "score_breakdown": {
    "valuation": 30,
    "quality": 25,
    "financial_health": 20,
    "profitability": 10,
    "growth": 7,
    "management": 5
  },
  "warnings": [
    {"type": "red", "message": "Altman Z < 1.8 (bankruptcy risk)"}
  ],
  "last_updated": "2024-07-05T15:30:00Z"
}
```

---

### 4. Sector Dashboard
**GET `/api/v1/sector/{sector}`**

Returns aggregated metrics, averages, and top stocks for a sector.

#### Path Parameters
- `sector` (string, required): Sector name (e.g., "Technology")

#### Query Parameters
- `top_n` (int, default=10): Number of top stocks to return
- `sort_by` (string, default="fundamental_score"): Field to sort top stocks

#### Example Request
```
GET /api/v1/sector/Technology?top_n=10&sort_by=fundamental_score
```

#### Example Response
```json
{
  "sector": "Technology",
  "company_count": 120,
  "averages": {
    "pe_ratio": 24.1,
    "pb_ratio": 8.2,
    "roe": 18.5,
    "debt_to_equity": 0.9,
    // ...
  },
  "top_stocks": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "fundamental_score": 92,
      "technical_score": 87,
      "price": 195.12,
      "market_cap": 3000000000000
    },
    // ...
  ],
  "last_updated": "2024-07-05T15:30:00Z"
}
```

---

## Filtering, Sorting, and Pagination
- All list endpoints support pagination (`page`, `page_size`)
- Filtering by sector, industry, market cap, scores, upside
- Sorting by any numeric field (default: upside for screener, fundamental_score for sector)

---

## Performance & Caching Notes
- Use materialized views for latest metrics
- Cache sector/industry aggregates for 5-15 minutes
- All endpoints should respond in <100ms for typical queries

---

## Error Handling
- 404 for unknown ticker/sector
- 400 for invalid parameters
- 500 for server/database errors

---

## Versioning
- All endpoints are under `/api/v1/` for future compatibility

---

## Example Error Response
```json
{
  "error": "Ticker not found"
}
``` 