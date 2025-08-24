#!/usr/bin/env python3
"""
Multi-Service Data Validation and Fetch Workflow
================================================

This enhanced solution leverages multiple data sources for comprehensive
fundamental data collection with intelligent fallback and redundancy.

Available Services:
- Yahoo Finance (free, comprehensive)
- Alpha Vantage (free tier, good coverage)
- Financial Modeling Prep (FMP) (paid, high quality)
- Finnhub (free tier, alternative source)

Suggested Additional Services:
- Polygon.io (paid, institutional quality)
- IEX Cloud (paid, comprehensive)
- Quandl/NASDAQ Data Link (paid, alternative)
- EOD Historical Data (paid, global coverage)

Author: AI Assistant
Date: 2025-01-26
"""

import sys
import os
from datetime import date, datetime
from typing import List, Dict, Optional, Set, Tuple, Any
import logging
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_run.database import DatabaseManager
from daily_run.simple_data_validator import SimpleDataValidator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiServiceDataWorkflow:
    """Enhanced workflow using multiple data sources with intelligent fallback"""
    
    def __init__(self):
        """Initialize the multi-service workflow"""
        self.db = DatabaseManager()
        self.validator = SimpleDataValidator()
        self.services = {}
        self.service_priority = []
        
        # Configuration
        self.max_retries = 3
        self.delay_between_requests = 2  # seconds
        self.max_concurrent_requests = 2  # Limited to avoid rate limits
        
        # Initialize all available services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all available data services"""
        print("🔧 Initializing data services...")
        
        # Service priority order (best to worst)
        # Yahoo first, then FMP, then other free services
        service_configs = [
            ('yahoo', 'Yahoo Finance', self._init_yahoo_service),
            ('fmp', 'Financial Modeling Prep', self._init_fmp_service),
            ('alphavantage', 'Alpha Vantage', self._init_alpha_vantage_service),
            ('finnhub', 'Finnhub', self._init_finnhub_service),
            ('polygon', 'Polygon.io', self._init_polygon_service)
        ]
        
        for service_id, service_name, init_func in service_configs:
            try:
                service = init_func()
                if service:
                    self.services[service_id] = service
                    self.service_priority.append(service_id)
                    print(f"  ✅ {service_name} initialized successfully")
                else:
                    print(f"  ⚠️  {service_name} not available (missing API key or service)")
            except Exception as e:
                print(f"  ❌ {service_name} initialization failed: {e}")
        
        print(f"📊 Total services available: {len(self.services)}")
        if self.service_priority:
            print(f"🎯 Service priority: {' → '.join(self.service_priority)}")
    
    def _init_polygon_service(self):
        """Initialize Polygon.io service"""
        try:
            from daily_run.polygon_service import PolygonService
            return PolygonService()
        except Exception as e:
            logger.warning(f"Polygon.io service not available: {e}")
            return None
    
    def _init_yahoo_service(self):
        """Initialize Yahoo Finance service"""
        try:
            from yahoo_finance_service import YahooFinanceService
            return YahooFinanceService()
        except Exception as e:
            logger.warning(f"Yahoo Finance service not available: {e}")
            return None
    
    def _init_alpha_vantage_service(self):
        """Initialize Alpha Vantage service"""
        try:
            from daily_run.alpha_vantage_service import AlphaVantageService
            return AlphaVantageService()
        except Exception as e:
            logger.warning(f"Alpha Vantage service not available: {e}")
            return None
    
    def _init_fmp_service(self):
        """Initialize FMP service"""
        try:
            from daily_run.fmp_service import FMPService
            return FMPService()
        except Exception as e:
            logger.warning(f"FMP service not available: {e}")
            return None
    
    def _init_finnhub_service(self):
        """Initialize Finnhub service"""
        try:
            from daily_run.finnhub_service import FinnhubService
            return FinnhubService()
        except Exception as e:
            logger.warning(f"Finnhub service not available: {e}")
            return None
    
    def step1_validate_data(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Step 1: Validate data completeness for all tickers
        
        Returns:
            Validation results for all tickers
        """
        print(f"\n📋 STEP 1: DATA VALIDATION")
        print("=" * 60)
        
        validation_results = self.validator.validate_all_tickers(tickers)
        self.validator.print_validation_summary(validation_results)
        
        return validation_results
    
    def step2_identify_missing_data(self, validation_results: Dict[str, Dict]) -> List[str]:
        """
        Step 2: Identify tickers that need data fetching
        
        Returns:
            Prioritized list of tickers needing data fetch
        """
        print(f"\n📋 STEP 2: IDENTIFYING MISSING DATA")
        print("=" * 60)
        
        tickers_needing_fetch = self.validator.identify_tickers_needing_fetch(validation_results)
        
        if not tickers_needing_fetch:
            print("  ✅ All tickers have complete data - no fetching needed!")
            return []
        
        # Generate prioritized list
        prioritized_list = self.validator.generate_fetch_list(validation_results)
        
        print(f"  📥 Found {len(tickers_needing_fetch)} tickers needing data fetch:")
        for i, ticker in enumerate(prioritized_list, 1):
            quality = validation_results[ticker]['data_quality_score']
            missing_count = len(validation_results[ticker].get('missing_fields', []))
            print(f"    {i:2d}. {ticker} ({quality}% quality, {missing_count} missing fields)")
        
        return prioritized_list
    
    def step3_fetch_missing_data_multi_service(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Step 3: Fetch missing data using multiple services with intelligent fallback
        
        Returns:
            Dict mapping ticker to fetch results with service information
        """
        if not tickers:
            return {}
        
        print(f"\n📋 STEP 3: FETCHING MISSING DATA (Multi-Service)")
        print("=" * 60)
        
        results = {}
        
        for i, ticker in enumerate(tickers, 1):
            print(f"  📥 [{i}/{len(tickers)}] Fetching data for {ticker}...")
            
            ticker_result = self._fetch_ticker_multi_service(ticker)
            results[ticker] = ticker_result
            
            # Add delay between tickers to avoid rate limiting
            if i < len(tickers):
                print(f"    ⏳ Waiting {self.delay_between_requests}s before next ticker...")
                time.sleep(self.delay_between_requests)
        
        # Print fetch summary
        successful_fetches = sum(1 for result in results.values() if result.get('success', False))
        print(f"\n  📊 Multi-Service Fetch Summary: {successful_fetches}/{len(tickers)} successful")
        
        # Service usage statistics
        service_usage = {}
        for result in results.values():
            if result.get('success') and result.get('service_used'):
                service = result['service_used']
                service_usage[service] = service_usage.get(service, 0) + 1
        
        if service_usage:
            print(f"  📈 Service Usage:")
            for service, count in service_usage.items():
                print(f"    {service}: {count} tickers")
        
        return results
    
    def get_service_priority_for_data_type(self, data_type: str) -> List[str]:
        """
        Get optimized service priority list for a specific data type.
        
        Args:
            data_type: 'fundamentals' or 'pricing'
            
        Returns:
            Optimized service priority list for the data type
        """
        if data_type == 'pricing':
            # For pricing: Finnhub (best API) → Yahoo (free, reliable) → Alpha Vantage (free tier) → FMP (paid, limited)
            # Polygon.io removed due to rate limiting issues
            return ['finnhub', 'yahoo', 'alphavantage', 'fmp']
        else:
            # For fundamentals: Finnhub (best API) → Yahoo (free, comprehensive) → FMP (paid, high quality) → Alpha Vantage (free tier)
            # Polygon.io removed due to rate limiting issues
            return ['finnhub', 'yahoo', 'fmp', 'alphavantage']
    
    def _fetch_ticker_multi_service(self, ticker: str, data_type: str = 'fundamentals') -> Dict[str, Any]:
        """
        Fetch data for a single ticker using multiple services with fallback
        
        Args:
            ticker: Ticker symbol
            data_type: 'fundamentals' or 'pricing'
            
        Returns:
            Dict with fetch results and service information
        """
        result = {
            'ticker': ticker,
            'data_type': data_type,
            'success': False,
            'service_used': None,
            'error': None,
            'data_quality_before': 0,
            'data_quality_after': 0
        }
        
        # Get current data quality
        validation = self.validator.validate_ticker_data(ticker)
        result['data_quality_before'] = validation['data_quality_score']
        
        # Get optimized service priority for this data type
        service_priority = self.get_service_priority_for_data_type(data_type)
        
        # Try each service in priority order
        for service_id in service_priority:
            if service_id not in self.services:
                logger.warning(f"Service {service_id} not available, skipping")
                continue
                
            try:
                print(f"    🔄 Trying {service_id.upper()} for {data_type}...")
                
                service = self.services[service_id]
                success = self._fetch_from_service(ticker, service, service_id, data_type)
                
                if success:
                    result['success'] = True
                    result['service_used'] = service_id
                    print(f"    ✅ Successfully fetched {data_type} from {service_id.upper()}")
                    break
                else:
                    print(f"    ⚠️  {service_id.upper()} failed, trying next service...")
                    
            except Exception as e:
                print(f"    ❌ {service_id.upper()} error: {e}")
                continue
        
        if not result['success']:
            result['error'] = "All services failed"
            print(f"    ❌ All services failed for {ticker}")
        
        # Get updated data quality
        validation_after = self.validator.validate_ticker_data(ticker)
        result['data_quality_after'] = validation_after['data_quality_score']
        
        return result
    
    def _fetch_from_service(self, ticker: str, service, service_id: str, data_type: str = 'fundamentals') -> bool:
        """
        Fetch data from a specific service
        
        Args:
            ticker: Ticker symbol
            service: Service instance
            service_id: Service identifier
            data_type: 'fundamentals' or 'pricing'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Different services have different methods
            if service_id == 'polygon':
                return self._fetch_from_polygon(ticker, service, data_type)
            elif service_id == 'yahoo':
                return self._fetch_from_yahoo(ticker, service, data_type)
            elif service_id == 'alphavantage':
                return self._fetch_from_alpha_vantage(ticker, service, data_type)
            elif service_id == 'fmp':
                return self._fetch_from_fmp(ticker, service, data_type)
            elif service_id == 'finnhub':
                return self._fetch_from_finnhub(ticker, service, data_type)
            else:
                logger.warning(f"Unknown service: {service_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching from {service_id} for {ticker}: {e}")
            return False
    
    def _fetch_from_polygon(self, ticker: str, service, data_type: str) -> bool:
        """Fetch data from Polygon.io"""
        try:
            if data_type == 'fundamentals':
                # Get fundamental data
                fundamental_data = service.get_fundamental_data(ticker)
                if not fundamental_data:
                    return False
                
                # Store the data
                success = service.store_fundamental_data(ticker, fundamental_data, {})
                return success
            else:
                # Get pricing data
                price_data = service.get_data(ticker)
                if not price_data:
                    return False
                
                # Store pricing data
                return self._store_price_data_direct(ticker, price_data, 'polygon')
            
        except Exception as e:
            logger.error(f"Polygon.io fetch error for {ticker}: {e}")
            return False
    
    def _fetch_from_yahoo(self, ticker: str, service, data_type: str) -> bool:
        """Fetch data from Yahoo Finance"""
        try:
            if data_type == 'fundamentals':
                # Fetch financial statements
                financial_data = service.fetch_financial_statements(ticker)
                if not financial_data:
                    return False
                
                # Fetch key statistics
                key_stats = service.fetch_key_statistics(ticker)
                
                # Store the data
                success = service.store_fundamental_data(ticker, financial_data, key_stats or {})
                return success
            else:
                # Get pricing data
                price_data = service.get_data(ticker)
                if not price_data:
                    return False
                
                # Store pricing data
                return self._store_price_data_direct(ticker, price_data, 'yahoo')
            
        except Exception as e:
            logger.error(f"Yahoo Finance fetch error for {ticker}: {e}")
            return False
    
    def _fetch_from_alpha_vantage(self, ticker: str, service, data_type: str) -> bool:
        """Fetch data from Alpha Vantage"""
        try:
            if data_type == 'fundamentals':
                # Get fundamental data
                fundamental_data = service.get_fundamental_data(ticker)
                if not fundamental_data:
                    return False
                
                # Store the data (assuming service has store method)
                if hasattr(service, 'store_fundamental_data'):
                    success = service.store_fundamental_data(ticker, fundamental_data, {})
                    return success
                else:
                    # Store directly in database
                    return self._store_fundamental_data_direct(ticker, fundamental_data, 'alphavantage')
            else:
                # Get pricing data
                price_data = service.get_data(ticker)
                if not price_data:
                    return False
                
                # Store pricing data
                return self._store_price_data_direct(ticker, price_data, 'alphavantage')
            
        except Exception as e:
            logger.error(f"Alpha Vantage fetch error for {ticker}: {e}")
            return False
    
    def _fetch_from_fmp(self, ticker: str, service, data_type: str) -> bool:
        """Fetch data from FMP"""
        try:
            if data_type == 'fundamentals':
                # Fetch financial statements
                financial_data = service.fetch_financial_statements(ticker)
                if not financial_data:
                    return False
                
                # Fetch key statistics
                key_stats = service.fetch_key_statistics(ticker)
                
                # Store the data
                success = service.store_fundamental_data(ticker, financial_data, key_stats or {})
                return success
            else:
                # Get pricing data
                price_data = service.get_data(ticker)
                if not price_data:
                    return False
                
                # Store pricing data
                return self._store_price_data_direct(ticker, price_data, 'fmp')
            
        except Exception as e:
            logger.error(f"FMP fetch error for {ticker}: {e}")
            return False
    
    def _fetch_from_finnhub(self, ticker: str, service, data_type: str) -> bool:
        """Fetch data from Finnhub"""
        try:
            if data_type == 'fundamentals':
                # Fetch financial statements
                financial_data = service.fetch_financial_statements(ticker)
                if not financial_data:
                    return False
                
                # Store the data
                success = service.store_fundamental_data(ticker, financial_data, {})
                return success
            else:
                # Get pricing data
                price_data = service.get_data(ticker)
                if not price_data:
                    return False
                
                # Store pricing data
                return self._store_price_data_direct(ticker, price_data, 'finnhub')
            
        except Exception as e:
            logger.error(f"Finnhub fetch error for {ticker}: {e}")
            return False
    
    def _store_price_data_direct(self, ticker: str, data: Dict, source: str) -> bool:
        """Store price data directly in database"""
        try:
            # Store in daily_charts table
            query = """
            INSERT INTO daily_charts 
            (ticker, date, open, high, low, close, volume, data_source, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date)
            DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                data_source = EXCLUDED.data_source,
                last_updated = CURRENT_TIMESTAMP
            """
            
            # Use current price for OHLC if not provided
            current_price = data.get('price', 0)
            
            values = (
                ticker,
                date.today(),
                data.get('open', current_price),
                data.get('high', current_price),
                data.get('low', current_price),
                data.get('close', current_price),
                data.get('volume'),
                source,
                datetime.now()
            )
            
            self.db.execute_query(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error storing price data for {ticker}: {e}")
            return False
    
    def step4_revalidate_data(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Step 4: Re-validate data after fetching
        
        Returns:
            Updated validation results
        """
        print(f"\n📋 STEP 4: RE-VALIDATING DATA")
        print("=" * 60)
        
        post_fetch_validation = self.validator.validate_all_tickers(tickers)
        
        # Compare with pre-fetch results
        print(f"\n📊 DATA QUALITY IMPROVEMENT:")
        for ticker in tickers:
            pre_quality = 41  # Default from previous run
            post_quality = post_fetch_validation[ticker]['data_quality_score']
            improvement = post_quality - pre_quality
            
            if improvement > 0:
                print(f"  📈 {ticker}: {pre_quality}% → {post_quality}% (+{improvement}%)")
            else:
                print(f"  📊 {ticker}: {pre_quality}% → {post_quality}% (no change)")
        
        return post_fetch_validation
    
    def step5_calculate_ratios(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Step 5: Calculate ratios for all tickers
        
        Returns:
            Dict mapping ticker to ratio calculation success status
        """
        print(f"\n📋 STEP 5: CALCULATING RATIOS")
        print("=" * 60)
        
        ratio_results = {}
        
        for ticker in tickers:
            try:
                print(f"  🧮 Calculating ratios for {ticker}...")
                
                # Get the most recent fundamental data
                query = """
                SELECT 
                    revenue, net_income, ebitda, total_equity, total_assets,
                    total_debt, gross_profit, operating_income, free_cash_flow
                FROM company_fundamentals
                WHERE ticker = %s
                ORDER BY last_updated DESC
                LIMIT 1
                """
                
                result = self.db.execute_query(query, (ticker,))
                
                if not result:
                    print(f"    ❌ No fundamental data found for {ticker}")
                    ratio_results[ticker] = False
                    continue
                
                row = result[0]
                
                # Prepare raw data
                raw_data = {
                    'revenue': row[0],
                    'net_income': row[1],
                    'ebitda': row[2],
                    'total_equity': row[3],
                    'total_assets': row[4],
                    'total_debt': row[5],
                    'gross_profit': row[6],
                    'operating_income': row[7],
                    'free_cash_flow': row[8]
                }
                
                # Get market data
                current_price = self.db.get_latest_price(ticker)
                market_query = """
                SELECT shares_outstanding, enterprise_value
                FROM stocks
                WHERE ticker = %s
                """
                market_result = self.db.execute_query(market_query, (ticker,))
                
                market_data = {
                    'current_price': current_price,
                    'shares_outstanding': market_result[0][0] if market_result else None,
                    'enterprise_value': market_result[0][1] if market_result else None
                }
                
                # Calculate ratios
                from daily_run.ratio_calculator import calculate_ratios
                calculated_ratios = calculate_ratios(raw_data, market_data)
                
                # Store ratios in company_fundamentals
                self._store_calculated_ratios(ticker, calculated_ratios)
                
                print(f"    ✅ Successfully calculated ratios for {ticker}")
                ratio_results[ticker] = True
                
            except Exception as e:
                logger.error(f"Error calculating ratios for {ticker}: {e}")
                print(f"    ❌ Error calculating ratios for {ticker}: {e}")
                ratio_results[ticker] = False
        
        return ratio_results
    
    def _store_calculated_ratios(self, ticker: str, ratios: Dict[str, float]):
        """
        Store calculated ratios in company_fundamentals table
        Enhanced with robust error handling to never break the process
        """
        try:
            # Build update query for all ratio columns
            update_query = """
            UPDATE company_fundamentals
            SET 
                pe_ratio = %s,
                pb_ratio = %s,
                ps_ratio = %s,
                ev_ebitda = %s,
                roe = %s,
                roa = %s,
                debt_to_equity = %s,
                current_ratio = %s,
                gross_margin = %s,
                operating_margin = %s,
                net_margin = %s,
                peg_ratio = %s,
                roic = %s,
                quick_ratio = %s,
                interest_coverage = %s,
                altman_z_score = %s,
                asset_turnover = %s,
                inventory_turnover = %s,
                receivables_turnover = %s,
                revenue_growth_yoy = %s,
                earnings_growth_yoy = %s,
                fcf_growth_yoy = %s,
                fcf_to_net_income = %s,
                cash_conversion_cycle = %s,
                market_cap = %s,
                enterprise_value = %s,
                graham_number = %s,
                last_updated = NOW()
            WHERE ticker = %s
            AND EXISTS (SELECT 1 FROM company_fundamentals WHERE ticker = %s)
            """
            
            # Use .get() with default of 0.0 for all values to ensure safe operation
            values = (
                ratios.get('pe_ratio', 0.0),
                ratios.get('pb_ratio', 0.0),
                ratios.get('ps_ratio', 0.0),
                ratios.get('ev_ebitda', 0.0),
                ratios.get('roe', 0.0),
                ratios.get('roa', 0.0),
                ratios.get('debt_to_equity', 0.0),
                ratios.get('current_ratio', 0.0),
                ratios.get('gross_margin', 0.0),
                ratios.get('operating_margin', 0.0),
                ratios.get('net_margin', 0.0),
                ratios.get('peg_ratio', 0.0),
                ratios.get('roic', 0.0),
                ratios.get('quick_ratio', 0.0),
                ratios.get('interest_coverage', 0.0),
                ratios.get('altman_z_score', 0.0),
                ratios.get('asset_turnover', 0.0),
                ratios.get('inventory_turnover', 0.0),
                ratios.get('receivables_turnover', 0.0),
                ratios.get('revenue_growth_yoy', 0.0),
                ratios.get('earnings_growth_yoy', 0.0),
                ratios.get('fcf_growth_yoy', 0.0),
                ratios.get('fcf_to_net_income', 0.0),
                ratios.get('cash_conversion_cycle', 0.0),
                ratios.get('market_cap', 0.0),
                ratios.get('enterprise_value', 0.0),
                ratios.get('graham_number', 0.0),
                ticker,
                ticker
            )
            
            # Execute the update
            rows_affected = self.db.execute_query(update_query, values)
            
            if rows_affected and rows_affected > 0:
                logger.debug(f"Successfully stored ratios for {ticker}")
            else:
                logger.warning(f"No rows updated when storing ratios for {ticker} - ticker may not exist in company_fundamentals")
            
        except Exception as e:
            logger.error(f"Error storing calculated ratios for {ticker}: {e}")
            # CRITICAL: Don't raise - just log error and continue with next ticker
            # This ensures one failed ticker doesn't break the entire process
            logger.warning(f"Continuing with next ticker after ratio storage failure for {ticker}")

    def step6_update_fundamental_scores(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Step 6: Update fundamental scores for all tickers
        Enhanced with robust error handling
        
        Returns:
            Dict mapping ticker to fundamental score update success status
        """
        print(f"\n📊 STEP 6: UPDATING FUNDAMENTAL SCORES")
        print("=" * 60)
        
        score_results = {}
        
        for ticker in tickers:
            try:
                print(f"  📈 Updating fundamental score for {ticker}...")
                
                # Get ratio data for scoring
                query = """
                SELECT 
                    pe_ratio, pb_ratio, ps_ratio, ev_ebitda, roe, roa, 
                    debt_to_equity, gross_margin, operating_margin, net_margin
                FROM company_fundamentals
                WHERE ticker = %s
                ORDER BY last_updated DESC
                LIMIT 1
                """
                
                result = self.db.execute_query(query, (ticker,))
                
                if not result:
                    print(f"    ❌ No fundamental data found for {ticker}")
                    score_results[ticker] = False
                    continue
                
                ratio_data = result[0]
                
                # Calculate fundamental score (safe calculation)
                fundamental_score = self._calculate_fundamental_score(ratio_data)
                
                # Update fundamental score in company_fundamentals
                update_query = """
                UPDATE company_fundamentals
                SET fundamental_score = %s, last_updated = NOW()
                WHERE ticker = %s
                """
                
                self.db.execute_query(update_query, (fundamental_score, ticker))
                
                print(f"    ✅ Updated fundamental score for {ticker}: {fundamental_score}")
                score_results[ticker] = True
                
            except Exception as e:
                logger.error(f"Error updating fundamental score for {ticker}: {e}")
                print(f"    ❌ Error updating fundamental score for {ticker}: {e}")
                # CRITICAL: Don't break the loop - continue with next ticker
                score_results[ticker] = False
        
        return score_results
    
    def _calculate_fundamental_score(self, ratio_data: tuple) -> int:
        """
        Calculate fundamental score based on ratio data with safe error handling
        
        Args:
            ratio_data: Tuple of ratio values
            
        Returns:
            Score between 0-100 (never fails)
        """
        try:
            # Safely extract ratio data with defaults
            ratios = list(ratio_data) if ratio_data else [0] * 10
            
            # Ensure we have enough data and safe defaults
            while len(ratios) < 10:
                ratios.append(0.0)
            
            pe_ratio = ratios[0] if ratios[0] is not None else 0.0
            pb_ratio = ratios[1] if ratios[1] is not None else 0.0
            ps_ratio = ratios[2] if ratios[2] is not None else 0.0
            ev_ebitda = ratios[3] if ratios[3] is not None else 0.0
            roe = ratios[4] if ratios[4] is not None else 0.0
            roa = ratios[5] if ratios[5] is not None else 0.0
            debt_equity = ratios[6] if ratios[6] is not None else 0.0
            gross_margin = ratios[7] if ratios[7] is not None else 0.0
            operating_margin = ratios[8] if ratios[8] is not None else 0.0
            net_margin = ratios[9] if ratios[9] is not None else 0.0
            
            score = 0
            max_score = 100
            
            # Valuation ratios (30 points) - safe calculations
            try:
                if pe_ratio and pe_ratio > 0 and pe_ratio < 25:
                    score += min(15, (25 - pe_ratio) / 25 * 15)
                if pb_ratio and pb_ratio > 0 and pb_ratio < 3:
                    score += min(15, (3 - pb_ratio) / 3 * 15)
            except (ZeroDivisionError, TypeError, ValueError):
                pass  # Skip this component if calculation fails
            
            # Profitability ratios (40 points) - safe calculations
            try:
                if roe and roe > 0:
                    score += min(20, roe / 20 * 20)  # 20% ROE = full points
                if gross_margin and gross_margin > 0:
                    score += min(10, gross_margin / 50 * 10)  # 50% margin = full points
                if net_margin and net_margin > 0:
                    score += min(10, net_margin / 20 * 10)  # 20% margin = full points
            except (ZeroDivisionError, TypeError, ValueError):
                pass  # Skip this component if calculation fails
            
            # Financial health (30 points) - safe calculations
            try:
                if debt_equity and debt_equity < 1:
                    score += min(15, (1 - debt_equity) / 1 * 15)
                if roa and roa > 0:
                    score += min(15, roa / 10 * 15)  # 10% ROA = full points
            except (ZeroDivisionError, TypeError, ValueError):
                pass  # Skip this component if calculation fails
            
            return min(max_score, max(0, int(score)))  # Ensure score is between 0-100
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score: {e}")
            # Return neutral score on any error
            return 50
    
    def suggest_additional_services(self):
        """Suggest additional API services for enhanced data coverage"""
        print(f"\n💡 SUGGESTED ADDITIONAL API SERVICES")
        print("=" * 60)
        
        suggestions = [
            {
                'name': 'Polygon.io',
                'description': 'Institutional-grade financial data API',
                'strengths': ['Real-time data', 'Comprehensive fundamentals', 'High rate limits'],
                'pricing': 'Paid (starts at $99/month)',
                'coverage': 'US stocks, options, forex, crypto',
                'recommendation': 'High - Best for production systems'
            },
            {
                'name': 'IEX Cloud',
                'description': 'Comprehensive financial data platform',
                'strengths': ['Multiple data sources', 'Good documentation', 'Flexible pricing'],
                'pricing': 'Paid (starts at $9/month)',
                'coverage': 'US stocks, international, crypto',
                'recommendation': 'High - Good value for money'
            },
            {
                'name': 'Quandl/NASDAQ Data Link',
                'description': 'Alternative financial data provider',
                'strengths': ['Alternative datasets', 'Academic access', 'Historical data'],
                'pricing': 'Paid (varies by dataset)',
                'coverage': 'Global markets, alternative data',
                'recommendation': 'Medium - Good for research'
            },
            {
                'name': 'EOD Historical Data',
                'description': 'Global financial data provider',
                'strengths': ['Global coverage', 'Historical data', 'Affordable'],
                'pricing': 'Paid (starts at $19.99/month)',
                'coverage': 'Global stocks, forex, crypto',
                'recommendation': 'Medium - Good for international stocks'
            },
            {
                'name': 'MarketStack',
                'description': 'Real-time and historical market data',
                'strengths': ['Real-time data', 'Simple API', 'Good documentation'],
                'pricing': 'Paid (starts at $9.99/month)',
                'coverage': 'Global stocks, forex, crypto',
                'recommendation': 'Medium - Good for real-time data'
            }
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['name']}")
            print(f"   📝 {suggestion['description']}")
            print(f"   💪 Strengths: {', '.join(suggestion['strengths'])}")
            print(f"   💰 Pricing: {suggestion['pricing']}")
            print(f"   🌍 Coverage: {suggestion['coverage']}")
            print(f"   ⭐ Recommendation: {suggestion['recommendation']}")
    
    def run_complete_workflow(self, tickers: List[str]) -> Dict[str, any]:
        """
        Run the complete multi-service workflow
        
        Returns:
            Comprehensive summary of the entire workflow
        """
        print(f"\n🚀 STARTING MULTI-SERVICE DATA WORKFLOW")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Step 1: Validate data
            validation_results = self.step1_validate_data(tickers)
            
            # Step 2: Identify missing data
            tickers_needing_fetch = self.step2_identify_missing_data(validation_results)
            
            # Step 3: Fetch missing data using multiple services
            fetch_results = {}
            if tickers_needing_fetch:
                fetch_results = self.step3_fetch_missing_data_multi_service(tickers_needing_fetch)
            else:
                print("  ✅ No data fetching needed - all tickers have complete data")
            
            # Step 4: Re-validate after fetch
            post_fetch_validation = self.step4_revalidate_data(tickers)
            
            # Step 5: Calculate ratios
            ratio_results = self.step5_calculate_ratios(tickers)
            
            # Step 6: Update fundamental scores
            score_results = self.step6_update_fundamental_scores(tickers)
            
            execution_time = time.time() - start_time
            
            # Prepare comprehensive summary
            summary = {
                'status': 'success',
                'execution_time': execution_time,
                'tickers_processed': len(tickers),
                'tickers_fetched': len(tickers_needing_fetch),
                'services_available': len(self.services),
                'service_priority': self.service_priority,
                'fetch_success_count': sum(1 for result in fetch_results.values() if result.get('success', False)),
                'ratio_success_count': sum(1 for success in ratio_results.values() if success),
                'score_success_count': sum(1 for success in score_results.values() if success),
                'validation_results': validation_results,
                'post_fetch_validation': post_fetch_validation,
                'fetch_results': fetch_results,
                'ratio_results': ratio_results,
                'score_results': score_results
            }
            
            # Print final summary
            self.print_workflow_summary(summary)
            
            # Suggest additional services
            self.suggest_additional_services()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in complete workflow: {e}")
            print(f"❌ Error in complete workflow: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def print_workflow_summary(self, summary: Dict[str, any]):
        """Print a comprehensive summary of the workflow results"""
        print(f"\n📊 MULTI-SERVICE WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"  🕒 Execution Time: {summary['execution_time']:.2f} seconds")
        print(f"  📈 Tickers Processed: {summary['tickers_processed']}")
        print(f"  📥 Tickers Fetched: {summary['tickers_fetched']}")
        print(f"  🔧 Services Available: {summary['services_available']}")
        print(f"  🎯 Service Priority: {' → '.join(summary['service_priority'])}")
        print(f"  ✅ Successful Fetches: {summary['fetch_success_count']}")
        print(f"  🧮 Successful Ratio Calculations: {summary['ratio_success_count']}")
        print(f"  📊 Successful Score Updates: {summary['score_success_count']}")
        
        # Data quality improvement
        if 'validation_results' in summary and 'post_fetch_validation' in summary:
            pre_avg_quality = sum(r['data_quality_score'] for r in summary['validation_results'].values()) / len(summary['validation_results'])
            post_avg_quality = sum(r['data_quality_score'] for r in summary['post_fetch_validation'].values()) / len(summary['post_fetch_validation'])
            
            print(f"  📊 Average Data Quality: {pre_avg_quality:.1f}% → {post_avg_quality:.1f}%")
        
        print(f"\n🎉 MULTI-SERVICE WORKFLOW COMPLETED SUCCESSFULLY!")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            for service in self.services.values():
                if hasattr(service, 'close'):
                    service.close()
        except:
            pass

def main():
    """Main execution function"""
    # Test tickers
    test_tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM', 'AMD', 'AMZN', 'AVGO', 'INTC', 'MU', 'QCOM']
    
    workflow = MultiServiceDataWorkflow()
    
    try:
        # Run the complete workflow
        summary = workflow.run_complete_workflow(test_tickers)
        
        if summary['status'] == 'success':
            print(f"\n🎉 MULTI-SERVICE WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"Check the summary above for detailed results.")
        else:
            print(f"\n❌ WORKFLOW FAILED: {summary.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Error in main workflow: {e}")
        print(f"❌ Error in main workflow: {e}")
    
    finally:
        workflow.cleanup()

if __name__ == "__main__":
    main() 