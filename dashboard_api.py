#!/usr/bin/env python3
"""
Dashboard API for Value Investing Dashboard
Serves financial data from the new database schema
"""

import os
import psycopg2
import logging
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Pydantic models
class StockSummary(BaseModel):
    ticker: str
    company_name: Optional[str]
    current_price: Optional[float]
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    ps_ratio: Optional[float]
    roe: Optional[float]
    debt_to_equity: Optional[float]
    data_quality_score: Optional[int]
    last_updated: Optional[datetime]

class ValueStock(BaseModel):
    ticker: str
    company_name: Optional[str]
    current_price: Optional[float]
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    ps_ratio: Optional[float]
    graham_number: Optional[float]
    value_score: Optional[float]
    data_quality_score: Optional[int]

class FundamentalData(BaseModel):
    ticker: str
    market_cap: Optional[float]
    shares_outstanding: Optional[int]
    revenue_ttm: Optional[float]
    net_income_ttm: Optional[float]
    ebitda_ttm: Optional[float]
    total_debt: Optional[float]
    shareholders_equity: Optional[float]
    cash_and_equivalents: Optional[float]
    diluted_eps_ttm: Optional[float]
    book_value_per_share: Optional[float]
    next_earnings_date: Optional[date]
    data_source: Optional[str]
    last_updated: Optional[datetime]

class RatioData(BaseModel):
    ticker: str
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    ps_ratio: Optional[float]
    ev_ebitda: Optional[float]
    roe: Optional[float]
    roa: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    gross_margin: Optional[float]
    operating_margin: Optional[float]
    net_margin: Optional[float]
    graham_number: Optional[float]
    enterprise_value: Optional[float]
    calculation_date: Optional[date]
    data_quality_score: Optional[int]

class DashboardStats(BaseModel):
    total_stocks: int
    stocks_with_ratios: int
    avg_data_quality: float
    last_pipeline_run: Optional[datetime]
    market_status: str

# Initialize FastAPI app
app = FastAPI(
    title="Value Investing Dashboard API",
    description="API for accessing financial data and ratios",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        self.config = DB_CONFIG
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.config)
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a query and return results"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            results = cur.fetchall()
            cur.close()
            return results
        finally:
            conn.close()

# Initialize database manager
db = DatabaseManager()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Value Investing Dashboard API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        results = db.execute_query("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get total stocks
        total_stocks = db.execute_query("SELECT COUNT(*) FROM stocks WHERE is_active = true")[0][0]
        
        # Get stocks with ratios
        stocks_with_ratios = db.execute_query("SELECT COUNT(*) FROM current_ratios")[0][0]
        
        # Get average data quality
        avg_quality = db.execute_query("""
            SELECT AVG(data_quality_score) FROM current_ratios 
            WHERE data_quality_score IS NOT NULL
        """)[0][0]
        
        # Get last pipeline run
        last_run = db.execute_query("""
            SELECT completed_at FROM update_log 
            WHERE update_type = 'daily_pipeline' 
              AND status = 'success'
            ORDER BY completed_at DESC 
            LIMIT 1
        """)
        last_pipeline_run = last_run[0][0] if last_run else None
        
        # Check market status (simplified)
        market_status = "open"  # You can implement actual market hours check
        
        return DashboardStats(
            total_stocks=total_stocks,
            stocks_with_ratios=stocks_with_ratios,
            avg_data_quality=round(avg_quality, 1) if avg_quality else 0,
            last_pipeline_run=last_pipeline_run,
            market_status=market_status
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

@app.get("/stocks", response_model=List[StockSummary])
async def get_stocks(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("ticker", regex="^(ticker|market_cap|pe_ratio|pb_ratio|ps_ratio|roe)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$")
):
    """Get list of stocks with summary data"""
    try:
        query = f"""
            SELECT 
                s.ticker,
                s.company_name,
                f.current_price,
                f.market_cap,
                cr.pe_ratio,
                cr.pb_ratio,
                cr.ps_ratio,
                cr.roe,
                cr.debt_to_equity,
                cr.data_quality_score,
                cr.last_updated
            FROM stocks s
            LEFT JOIN financials f ON s.ticker = f.ticker
            LEFT JOIN current_ratios cr ON s.ticker = cr.ticker
            WHERE s.is_active = true
            ORDER BY {sort_by} {sort_order.upper()}
            LIMIT %s OFFSET %s
        """
        
        results = db.execute_query(query, (limit, offset))
        
        stocks = []
        for row in results:
            stocks.append(StockSummary(
                ticker=row[0],
                company_name=row[1],
                current_price=float(row[2]) if row[2] else None,
                market_cap=float(row[3]) if row[3] else None,
                pe_ratio=float(row[4]) if row[4] else None,
                pb_ratio=float(row[5]) if row[5] else None,
                ps_ratio=float(row[6]) if row[6] else None,
                roe=float(row[7]) if row[7] else None,
                debt_to_equity=float(row[8]) if row[8] else None,
                data_quality_score=row[9],
                last_updated=row[10]
            ))
        
        return stocks
        
    except Exception as e:
        logger.error(f"Error getting stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stocks")

@app.get("/value-stocks", response_model=List[ValueStock])
async def get_value_stocks(
    limit: int = Query(20, ge=1, le=100),
    min_market_cap: Optional[float] = Query(None, description="Minimum market cap in billions"),
    max_pe: Optional[float] = Query(None, description="Maximum P/E ratio"),
    max_pb: Optional[float] = Query(None, description="Maximum P/B ratio"),
    max_ps: Optional[float] = Query(None, description="Maximum P/S ratio")
):
    """Get value stocks based on criteria"""
    try:
        # Build WHERE clause
        where_conditions = ["s.is_active = true"]
        params = []
        
        if min_market_cap:
            where_conditions.append("f.market_cap >= %s")
            params.append(min_market_cap * 1e9)  # Convert billions to actual value
        
        if max_pe:
            where_conditions.append("cr.pe_ratio <= %s")
            params.append(max_pe)
        
        if max_pb:
            where_conditions.append("cr.pb_ratio <= %s")
            params.append(max_pb)
        
        if max_ps:
            where_conditions.append("cr.ps_ratio <= %s")
            params.append(max_ps)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                s.ticker,
                s.company_name,
                f.current_price,
                cr.pe_ratio,
                cr.pb_ratio,
                cr.ps_ratio,
                cr.graham_number,
                cr.data_quality_score
            FROM stocks s
            LEFT JOIN financials f ON s.ticker = f.ticker
            LEFT JOIN current_ratios cr ON s.ticker = cr.ticker
            WHERE {where_clause}
              AND cr.pe_ratio IS NOT NULL 
              AND cr.pb_ratio IS NOT NULL 
              AND cr.ps_ratio IS NOT NULL
              AND cr.pe_ratio > 0 
              AND cr.pb_ratio > 0 
              AND cr.ps_ratio > 0
            ORDER BY (cr.pe_ratio + cr.pb_ratio + cr.ps_ratio) ASC
            LIMIT %s
        """
        
        params.append(limit)
        results = db.execute_query(query, tuple(params))
        
        value_stocks = []
        for row in results:
            # Calculate value score (lower is better)
            pe = float(row[3]) if row[3] else 999
            pb = float(row[4]) if row[4] else 999
            ps = float(row[5]) if row[5] else 999
            value_score = (pe + pb + ps) / 3
            
            value_stocks.append(ValueStock(
                ticker=row[0],
                company_name=row[1],
                current_price=float(row[2]) if row[2] else None,
                pe_ratio=float(row[3]) if row[3] else None,
                pb_ratio=float(row[4]) if row[4] else None,
                ps_ratio=float(row[5]) if row[5] else None,
                graham_number=float(row[6]) if row[6] else None,
                value_score=round(value_score, 2),
                data_quality_score=row[7]
            ))
        
        return value_stocks
        
    except Exception as e:
        logger.error(f"Error getting value stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get value stocks")

@app.get("/stocks/{ticker}/fundamentals", response_model=FundamentalData)
async def get_stock_fundamentals(ticker: str):
    """Get fundamental data for a specific stock"""
    try:
        query = """
            SELECT 
                ticker, market_cap, shares_outstanding, revenue_ttm, net_income_ttm,
                ebitda_ttm, total_debt, shareholders_equity, cash_and_equivalents,
                diluted_eps_ttm, book_value_per_share, next_earnings_date,
                data_source, last_updated
            FROM financials 
            WHERE ticker = %s
        """
        
        results = db.execute_query(query, (ticker.upper(),))
        
        if not results:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        row = results[0]
        return FundamentalData(
            ticker=row[0],
            market_cap=float(row[1]) if row[1] else None,
            shares_outstanding=row[2],
            revenue_ttm=float(row[3]) if row[3] else None,
            net_income_ttm=float(row[4]) if row[4] else None,
            ebitda_ttm=float(row[5]) if row[5] else None,
            total_debt=float(row[6]) if row[6] else None,
            shareholders_equity=float(row[7]) if row[7] else None,
            cash_and_equivalents=float(row[8]) if row[8] else None,
            diluted_eps_ttm=float(row[9]) if row[9] else None,
            book_value_per_share=float(row[10]) if row[10] else None,
            next_earnings_date=row[11],
            data_source=row[12],
            last_updated=row[13]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fundamentals for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fundamentals")

@app.get("/stocks/{ticker}/ratios", response_model=RatioData)
async def get_stock_ratios(ticker: str):
    """Get ratio data for a specific stock"""
    try:
        query = """
            SELECT 
                ticker, pe_ratio, pb_ratio, ps_ratio, ev_ebitda, roe, roa,
                debt_to_equity, current_ratio, gross_margin, operating_margin,
                net_margin, graham_number, enterprise_value, calculation_date,
                data_quality_score
            FROM current_ratios 
            WHERE ticker = %s
        """
        
        results = db.execute_query(query, (ticker.upper(),))
        
        if not results:
            raise HTTPException(status_code=404, detail="Stock ratios not found")
        
        row = results[0]
        return RatioData(
            ticker=row[0],
            pe_ratio=float(row[1]) if row[1] else None,
            pb_ratio=float(row[2]) if row[2] else None,
            ps_ratio=float(row[3]) if row[3] else None,
            ev_ebitda=float(row[4]) if row[4] else None,
            roe=float(row[5]) if row[5] else None,
            roa=float(row[6]) if row[6] else None,
            debt_to_equity=float(row[7]) if row[7] else None,
            current_ratio=float(row[8]) if row[8] else None,
            gross_margin=float(row[9]) if row[9] else None,
            operating_margin=float(row[10]) if row[10] else None,
            net_margin=float(row[11]) if row[11] else None,
            graham_number=float(row[12]) if row[12] else None,
            enterprise_value=float(row[13]) if row[13] else None,
            calculation_date=row[14],
            data_quality_score=row[15]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ratios for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ratios")

@app.get("/search")
async def search_stocks(q: str = Query(..., min_length=1, max_length=10)):
    """Search stocks by ticker or company name"""
    try:
        query = """
            SELECT 
                s.ticker,
                s.company_name,
                f.current_price,
                f.market_cap,
                cr.pe_ratio,
                cr.pb_ratio,
                cr.ps_ratio
            FROM stocks s
            LEFT JOIN financials f ON s.ticker = f.ticker
            LEFT JOIN current_ratios cr ON s.ticker = cr.ticker
            WHERE s.is_active = true
              AND (UPPER(s.ticker) LIKE UPPER(%s) OR UPPER(s.company_name) LIKE UPPER(%s))
            ORDER BY s.ticker
            LIMIT 20
        """
        
        search_term = f"%{q}%"
        results = db.execute_query(query, (search_term, search_term))
        
        stocks = []
        for row in results:
            stocks.append({
                "ticker": row[0],
                "company_name": row[1],
                "current_price": float(row[2]) if row[2] else None,
                "market_cap": float(row[3]) if row[3] else None,
                "pe_ratio": float(row[4]) if row[4] else None,
                "pb_ratio": float(row[5]) if row[5] else None,
                "ps_ratio": float(row[6]) if row[6] else None
            })
        
        return {"results": stocks}
        
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to search stocks")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 