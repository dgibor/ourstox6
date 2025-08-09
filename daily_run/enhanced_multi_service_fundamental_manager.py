#!/usr/bin/env python3
"""
Enhanced Multi-Service Fundamental Manager

This module implements a fallback system for fundamental data:
1. Try FMP first (primary source)
2. For missing data, try Alpha Vantage
3. For still missing data, try Yahoo Finance
4. For still missing data, try Finnhub

This ensures maximum data coverage by leveraging multiple data sources.
"""

import logging
import time
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass
from datetime import datetime

# Import all services
try:
    from .enhanced_fmp_service import EnhancedFMPService
except ImportError:
    from enhanced_fmp_service import EnhancedFMPService
try:
    from .alpha_vantage_service import AlphaVantageService
except ImportError:
    from alpha_vantage_service import AlphaVantageService
try:
    from .yahoo_finance_service import YahooFinanceService
except ImportError:
    from yahoo_finance_service import YahooFinanceService
try:
    from .finnhub_service import FinnhubService
except ImportError:
    from finnhub_service import FinnhubService

logger = logging.getLogger(__name__)

@dataclass
class FundamentalDataItem:
    """Represents a single fundamental data item with source tracking"""
    value: Any
    source: str
    timestamp: datetime
    confidence: float = 1.0  # 0.0 to 1.0, higher is better

@dataclass
class FundamentalDataResult:
    """Complete fundamental data result with fallback information"""
    ticker: str
    data: Dict[str, FundamentalDataItem]
    primary_source: str
    fallback_sources_used: List[str]
    missing_fields: List[str]
    success_rate: float

class EnhancedMultiServiceFundamentalManager:
    """Enhanced fundamental data manager with intelligent fallback system"""
    
    def __init__(self):
        """Initialize all service connections"""
        self.services = {
            'fmp': EnhancedFMPService(),
            'alpha_vantage': AlphaVantageService(),
            'yahoo_finance': YahooFinanceService(),
            'finnhub': FinnhubService()
        }
        
        # Define the priority order for data sources
        self.service_priority = ['fmp', 'alpha_vantage', 'yahoo_finance', 'finnhub']
        
        # Define which fields each service can provide (updated for enhanced FMP)
        self.service_capabilities = {
            'fmp': [
                'revenue', 'net_income', 'total_assets', 'total_debt', 'total_equity',
                'current_assets', 'current_liabilities', 'cost_of_goods_sold',
                'operating_income', 'ebitda', 'free_cash_flow', 'shares_outstanding',
                'market_cap', 'enterprise_value', 'eps_diluted', 'book_value_per_share',
                'gross_profit', 'cash_and_equivalents', 'operating_cash_flow', 'capex',
                'inventory', 'accounts_receivable', 'accounts_payable', 'retained_earnings',
                'shares_float'
            ],
            'alpha_vantage': [
                'revenue', 'net_income', 'total_assets', 'total_debt', 'total_equity',
                'current_assets', 'current_liabilities', 'operating_income',
                'shares_outstanding', 'market_cap', 'eps_diluted', 'book_value_per_share'
            ],
            'yahoo_finance': [
                'revenue', 'net_income', 'total_assets', 'total_debt', 'total_equity',
                'current_assets', 'current_liabilities', 'operating_income',
                'shares_outstanding', 'market_cap', 'eps_diluted', 'book_value_per_share'
            ],
            'finnhub': [
                'revenue', 'net_income', 'total_assets', 'total_debt', 'total_equity',
                'current_assets', 'current_liabilities', 'operating_income',
                'shares_outstanding', 'market_cap', 'eps_diluted', 'book_value_per_share'
            ]
        }
        
        # Define field mappings between services
        self.field_mappings = {
            'fmp': {
                'revenue': 'revenue',
                'net_income': 'net_income',
                'total_assets': 'total_assets',
                'total_debt': 'total_debt',
                'total_equity': 'total_equity',
                'current_assets': 'current_assets',
                'current_liabilities': 'current_liabilities',
                'cost_of_goods_sold': 'cost_of_goods_sold',
                'operating_income': 'operating_income',
                'ebitda': 'ebitda',
                'free_cash_flow': 'free_cash_flow',
                'shares_outstanding': 'shares_outstanding',
                'market_cap': 'market_cap',
                'enterprise_value': 'enterprise_value',
                'eps_diluted': 'eps_diluted',
                'book_value_per_share': 'book_value_per_share'
            },
            'alpha_vantage': {
                'revenue': 'revenue_ttm',
                'net_income': 'net_income_ttm',
                'total_assets': 'total_assets',
                'total_debt': 'total_debt',
                'total_equity': 'total_equity',
                'current_assets': 'current_assets',
                'current_liabilities': 'current_liabilities',
                'operating_income': 'operating_income',
                'shares_outstanding': 'shares_outstanding',
                'market_cap': 'market_cap',
                'eps_diluted': 'eps_ttm',
                'book_value_per_share': 'book_value'
            },
            'yahoo_finance': {
                'revenue': 'revenue_ttm',
                'net_income': 'net_income_ttm',
                'total_assets': 'total_assets',
                'total_debt': 'total_debt',
                'total_equity': 'total_equity',
                'current_assets': 'current_assets',
                'current_liabilities': 'current_liabilities',
                'operating_income': 'operating_income',
                'shares_outstanding': 'shares_outstanding',
                'market_cap': 'market_cap',
                'eps_diluted': 'eps_ttm',
                'book_value_per_share': 'book_value'
            },
            'finnhub': {
                'revenue': 'revenue',
                'net_income': 'net_income',
                'total_assets': 'total_assets',
                'total_debt': 'total_debt',
                'total_equity': 'total_equity',
                'current_assets': 'current_assets',
                'current_liabilities': 'current_liabilities',
                'operating_income': 'operating_income',
                'shares_outstanding': 'shares_outstanding',
                'market_cap': 'market_cap',
                'eps_diluted': 'eps',
                'book_value_per_share': 'book_value'
            }
        }
    
    def get_fundamental_data_with_fallback(self, ticker: str) -> FundamentalDataResult:
        """
        Get fundamental data with intelligent fallback system
        
        Args:
            ticker: Stock symbol (1-5 characters, alphanumeric)
            
        Returns:
            FundamentalDataResult with complete data and fallback information
        """
        # Input validation
        if not ticker or not isinstance(ticker, str):
            logger.error(f"Invalid ticker: {ticker}")
            return self._create_empty_result(ticker, "Invalid ticker format")
        
        ticker = ticker.strip().upper()
        if not ticker.isalnum() or len(ticker) > 5:
            logger.error(f"Invalid ticker format: {ticker}")
            return self._create_empty_result(ticker, "Invalid ticker format")
        
        logger.info(f"Getting fundamental data for {ticker} with fallback system")
        
        # Initialize result tracking
        result_data = {}
        fallback_sources_used = []
        missing_fields = []
        
        # Define all fields we want to collect
        target_fields = [
            'revenue', 'net_income', 'total_assets', 'total_debt', 'total_equity',
            'current_assets', 'current_liabilities', 'cost_of_goods_sold',
            'operating_income', 'ebitda', 'free_cash_flow', 'shares_outstanding',
            'market_cap', 'enterprise_value', 'eps_diluted', 'book_value_per_share'
        ]
        
        # Try each service in priority order
        for service_name in self.service_priority:
            if not self._has_missing_fields(target_fields, result_data):
                break  # All fields found, no need to continue
                
            logger.info(f"Trying {service_name.upper()} for {ticker}")
            
            try:
                # Add timeout handling for API calls (Windows compatible)
                import threading
                import queue
                
                def api_call_with_timeout():
                    try:
                        service_data = self._get_data_from_service(ticker, service_name, target_fields, result_data)
                        result_queue.put(('success', service_data))
                    except Exception as e:
                        result_queue.put(('error', e))
                
                result_queue = queue.Queue()
                api_thread = threading.Thread(target=api_call_with_timeout)
                api_thread.daemon = True
                api_thread.start()
                
                # Wait for 60 seconds maximum
                api_thread.join(timeout=60)
                
                if api_thread.is_alive():
                    logger.warning(f"TIMEOUT: {service_name.upper()} timed out for {ticker}")
                    continue
                
                try:
                    result_type, result_data_or_error = result_queue.get_nowait()
                    
                    if result_type == 'error':
                        raise result_data_or_error
                    
                    service_data = result_data_or_error
                    
                    if service_data:
                        # Add new data to result with type validation
                        for field, value in service_data.items():
                            if field not in result_data and value is not None:
                                # Validate and convert data type
                                validated_value = self._validate_and_convert_value(field, value)
                                if validated_value is not None:
                                    result_data[field] = FundamentalDataItem(
                                        value=validated_value,
                                        source=service_name,
                                        timestamp=datetime.now(),
                                        confidence=self._get_confidence_score(service_name, field)
                                    )
                                    logger.info(f"SUCCESS: {service_name.upper()}: Found {field} = {validated_value}")
                    
                    if service_name != 'fmp':  # FMP is primary, others are fallbacks
                        fallback_sources_used.append(service_name)
                    
                except queue.Empty:
                    logger.warning(f"TIMEOUT: {service_name.upper()} timed out for {ticker}")
                    continue
                
                # Rate limiting between services
                if service_name != self.service_priority[-1]:  # Don't sleep after last service
                    time.sleep(1)
                    
            except TimeoutError as e:
                logger.warning(f"TIMEOUT: {service_name.upper()} timed out for {ticker}: {e}")
                continue
            except Exception as e:
                logger.warning(f"ERROR: {service_name.upper()} failed for {ticker}: {e}")
                continue
        
        # Determine missing fields
        missing_fields = [field for field in target_fields if field not in result_data]
        
        # Calculate success rate
        success_rate = len(result_data) / len(target_fields) if target_fields else 0.0
        
        # Determine primary source (first service that provided data)
        primary_source = 'unknown'
        if result_data:
            primary_source = next(iter(result_data.values())).source
        
        logger.info(f"{ticker} data collection complete:")
        logger.info(f"   Fields found: {len(result_data)}/{len(target_fields)}")
        logger.info(f"   Success rate: {success_rate:.1%}")
        logger.info(f"   Primary source: {primary_source}")
        logger.info(f"   Fallback sources: {fallback_sources_used}")
        logger.info(f"   Missing fields: {missing_fields}")
        
        return FundamentalDataResult(
            ticker=ticker,
            data=result_data,
            primary_source=primary_source,
            fallback_sources_used=fallback_sources_used,
            missing_fields=missing_fields,
            success_rate=success_rate
        )
    
    def _create_empty_result(self, ticker: str, reason: str) -> FundamentalDataResult:
        """Create an empty result for failed requests"""
        logger.warning(f"Creating empty result for {ticker}: {reason}")
        return FundamentalDataResult(
            ticker=ticker,
            data={},
            primary_source='none',
            fallback_sources_used=[],
            missing_fields=self._get_all_target_fields(),
            success_rate=0.0
        )
    
    def _get_all_target_fields(self) -> List[str]:
        """Get all target fields for data collection"""
        return [
            'revenue', 'net_income', 'total_assets', 'total_debt', 'total_equity',
            'current_assets', 'current_liabilities', 'cost_of_goods_sold',
            'operating_income', 'ebitda', 'free_cash_flow', 'shares_outstanding',
            'market_cap', 'enterprise_value', 'eps_diluted', 'book_value_per_share'
        ]
    
    def _validate_and_convert_value(self, field: str, value: Any) -> Optional[Union[int, float]]:
        """
        Validate and convert data values to appropriate types
        
        Args:
            field: Field name for context
            value: Raw value from API
            
        Returns:
            Converted value or None if invalid
        """
        try:
            if value is None:
                return None
            
            # Convert to string first to handle various input types
            str_value = str(value).strip()
            if not str_value or str_value.lower() in ['null', 'none', 'nan', '']:
                return None
            
            # Handle numeric fields
            if field in ['revenue', 'net_income', 'total_assets', 'total_debt', 'total_equity',
                        'current_assets', 'current_liabilities', 'cost_of_goods_sold',
                        'operating_income', 'ebitda', 'free_cash_flow', 'market_cap', 
                        'enterprise_value', 'book_value_per_share']:
                # Remove common formatting
                str_value = str_value.replace(',', '').replace('$', '').replace('%', '')
                return float(str_value)
            
            # Handle integer fields
            elif field in ['shares_outstanding']:
                str_value = str_value.replace(',', '')
                return int(float(str_value))
            
            # Handle ratio fields
            elif field in ['eps_diluted']:
                str_value = str_value.replace(',', '').replace('$', '')
                return float(str_value)
            
            else:
                # Default to float for unknown fields
                str_value = str_value.replace(',', '').replace('$', '').replace('%', '')
                return float(str_value)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {field} value '{value}': {e}")
            return None
    
    def _has_missing_fields(self, target_fields: List[str], current_data: Dict[str, FundamentalDataItem]) -> bool:
        """Check if there are still missing fields"""
        return len(current_data) < len(target_fields)
    
    def _get_data_from_service(self, ticker: str, service_name: str, target_fields: List[str], 
                              existing_data: Dict[str, FundamentalDataItem]) -> Optional[Dict[str, Any]]:
        """Get data from a specific service for missing fields only"""
        
        # Determine which fields this service can provide and are still missing
        service_capabilities = self.service_capabilities.get(service_name, [])
        missing_fields = [field for field in target_fields 
                         if field not in existing_data and field in service_capabilities]
        
        if not missing_fields:
            logger.debug(f"{service_name.upper()}: No missing fields to fetch")
            return None
        
        logger.info(f"{service_name.upper()}: Fetching {missing_fields}")
        
        try:
            service = self.services[service_name]
            
            if service_name == 'fmp':
                return self._get_fmp_data(ticker, missing_fields)
            elif service_name == 'alpha_vantage':
                return self._get_alpha_vantage_data(ticker, missing_fields)
            elif service_name == 'yahoo_finance':
                return self._get_yahoo_finance_data(ticker, missing_fields)
            elif service_name == 'finnhub':
                return self._get_finnhub_data(ticker, missing_fields)
            else:
                logger.warning(f"Unknown service: {service_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting data from {service_name}: {e}")
            return None
    
    def _get_fmp_data(self, ticker: str, missing_fields: List[str]) -> Optional[Dict[str, Any]]:
        """Get data from Enhanced FMP service"""
        try:
            # Use the enhanced FMP service
            result = self.services['fmp'].get_comprehensive_fundamental_data(ticker)
            if not result:
                return None
            
            extracted_data = {}
            
            # Map fields from enhanced FMP response
            field_mappings = {
                'revenue': 'revenue',
                'net_income': 'net_income',
                'total_assets': 'total_assets',
                'total_debt': 'total_debt',
                'total_equity': 'total_equity',
                'current_assets': 'current_assets',
                'current_liabilities': 'current_liabilities',
                'cost_of_goods_sold': 'cost_of_goods_sold',
                'operating_income': 'operating_income',
                'ebitda': 'ebitda',
                'free_cash_flow': 'free_cash_flow',
                'shares_outstanding': 'shares_outstanding',
                'market_cap': 'market_cap',
                'enterprise_value': 'enterprise_value',
                'eps_diluted': 'eps_diluted',
                'book_value_per_share': 'book_value_per_share',
                'gross_profit': 'gross_profit',
                'cash_and_equivalents': 'cash_and_equivalents',
                'operating_cash_flow': 'operating_cash_flow',
                'capex': 'capex',
                'inventory': 'inventory',
                'accounts_receivable': 'accounts_receivable',
                'accounts_payable': 'accounts_payable',
                'retained_earnings': 'retained_earnings',
                'shares_float': 'shares_float'
            }
            
            # Extract only the missing fields
            for field in missing_fields:
                if field in field_mappings:
                    mapped_field = field_mappings[field]
                    value = result.get(mapped_field)
                    if value is not None:
                        extracted_data[field] = value
            
            return extracted_data if extracted_data else None
            
        except Exception as e:
            logger.error(f"Error getting data from FMP: {e}")
            return None
    
    def _get_alpha_vantage_data(self, ticker: str, missing_fields: List[str]) -> Optional[Dict[str, Any]]:
        """Get data from Alpha Vantage service"""
        try:
            result = self.services['alpha_vantage'].get_fundamental_data(ticker)
            if not result:
                return None
            
            extracted_data = {}
            
            # Map fields from Alpha Vantage response
            if 'revenue' in missing_fields:
                revenue = result.get('revenue_ttm')
                if revenue:
                    extracted_data['revenue'] = revenue
            
            if 'net_income' in missing_fields:
                net_income = result.get('net_income_ttm')
                if net_income:
                    extracted_data['net_income'] = net_income
            
            if 'total_assets' in missing_fields:
                total_assets = result.get('total_assets')
                if total_assets:
                    extracted_data['total_assets'] = total_assets
            
            if 'total_debt' in missing_fields:
                total_debt = result.get('total_debt')
                if total_debt:
                    extracted_data['total_debt'] = total_debt
            
            if 'total_equity' in missing_fields:
                total_equity = result.get('total_equity')
                if total_equity:
                    extracted_data['total_equity'] = total_equity
            
            if 'current_assets' in missing_fields:
                current_assets = result.get('current_assets')
                if current_assets:
                    extracted_data['current_assets'] = current_assets
            
            if 'current_liabilities' in missing_fields:
                current_liabilities = result.get('current_liabilities')
                if current_liabilities:
                    extracted_data['current_liabilities'] = current_liabilities
            
            if 'operating_income' in missing_fields:
                operating_income = result.get('operating_income')
                if operating_income:
                    extracted_data['operating_income'] = operating_income
            
            if 'shares_outstanding' in missing_fields:
                shares_outstanding = result.get('shares_outstanding')
                if shares_outstanding:
                    extracted_data['shares_outstanding'] = shares_outstanding
            
            if 'market_cap' in missing_fields:
                market_cap = result.get('market_cap')
                if market_cap:
                    extracted_data['market_cap'] = market_cap
            
            if 'eps_diluted' in missing_fields:
                eps_diluted = result.get('eps_ttm')
                if eps_diluted:
                    extracted_data['eps_diluted'] = eps_diluted
            
            if 'book_value_per_share' in missing_fields:
                book_value = result.get('book_value')
                if book_value:
                    extracted_data['book_value_per_share'] = book_value
            
            return extracted_data if extracted_data else None
            
        except Exception as e:
            logger.error(f"Error getting Alpha Vantage data: {e}")
            return None
    
    def _get_yahoo_finance_data(self, ticker: str, missing_fields: List[str]) -> Optional[Dict[str, Any]]:
        """Get data from Yahoo Finance service"""
        try:
            result = self.services['yahoo_finance'].get_fundamental_data(ticker)
            if not result:
                return None
            
            extracted_data = {}
            
            # Map fields from Yahoo Finance response
            if 'revenue' in missing_fields:
                revenue = result.get('revenue_ttm')
                if revenue:
                    extracted_data['revenue'] = revenue
            
            if 'net_income' in missing_fields:
                net_income = result.get('net_income_ttm')
                if net_income:
                    extracted_data['net_income'] = net_income
            
            if 'total_assets' in missing_fields:
                total_assets = result.get('total_assets')
                if total_assets:
                    extracted_data['total_assets'] = total_assets
            
            if 'total_debt' in missing_fields:
                total_debt = result.get('total_debt')
                if total_debt:
                    extracted_data['total_debt'] = total_debt
            
            if 'total_equity' in missing_fields:
                total_equity = result.get('total_equity')
                if total_equity:
                    extracted_data['total_equity'] = total_equity
            
            if 'current_assets' in missing_fields:
                current_assets = result.get('current_assets')
                if current_assets:
                    extracted_data['current_assets'] = current_assets
            
            if 'current_liabilities' in missing_fields:
                current_liabilities = result.get('current_liabilities')
                if current_liabilities:
                    extracted_data['current_liabilities'] = current_liabilities
            
            if 'operating_income' in missing_fields:
                operating_income = result.get('operating_income')
                if operating_income:
                    extracted_data['operating_income'] = operating_income
            
            if 'shares_outstanding' in missing_fields:
                shares_outstanding = result.get('shares_outstanding')
                if shares_outstanding:
                    extracted_data['shares_outstanding'] = shares_outstanding
            
            if 'market_cap' in missing_fields:
                market_cap = result.get('market_cap')
                if market_cap:
                    extracted_data['market_cap'] = market_cap
            
            if 'eps_diluted' in missing_fields:
                eps_diluted = result.get('eps_ttm')
                if eps_diluted:
                    extracted_data['eps_diluted'] = eps_diluted
            
            if 'book_value_per_share' in missing_fields:
                book_value = result.get('book_value')
                if book_value:
                    extracted_data['book_value_per_share'] = book_value
            
            return extracted_data if extracted_data else None
            
        except Exception as e:
            logger.error(f"Error getting Yahoo Finance data: {e}")
            return None
    
    def _get_finnhub_data(self, ticker: str, missing_fields: List[str]) -> Optional[Dict[str, Any]]:
        """Get data from Finnhub service"""
        try:
            result = self.services['finnhub'].get_fundamental_data(ticker)
            if not result:
                return None
            
            extracted_data = {}
            
            # Map fields from Finnhub response
            if 'revenue' in missing_fields:
                revenue = result.get('revenue')
                if revenue:
                    extracted_data['revenue'] = revenue
            
            if 'net_income' in missing_fields:
                net_income = result.get('net_income')
                if net_income:
                    extracted_data['net_income'] = net_income
            
            if 'total_assets' in missing_fields:
                total_assets = result.get('total_assets')
                if total_assets:
                    extracted_data['total_assets'] = total_assets
            
            if 'total_debt' in missing_fields:
                total_debt = result.get('total_debt')
                if total_debt:
                    extracted_data['total_debt'] = total_debt
            
            if 'total_equity' in missing_fields:
                total_equity = result.get('total_equity')
                if total_equity:
                    extracted_data['total_equity'] = total_equity
            
            if 'current_assets' in missing_fields:
                current_assets = result.get('current_assets')
                if current_assets:
                    extracted_data['current_assets'] = current_assets
            
            if 'current_liabilities' in missing_fields:
                current_liabilities = result.get('current_liabilities')
                if current_liabilities:
                    extracted_data['current_liabilities'] = current_liabilities
            
            if 'operating_income' in missing_fields:
                operating_income = result.get('operating_income')
                if operating_income:
                    extracted_data['operating_income'] = operating_income
            
            if 'shares_outstanding' in missing_fields:
                shares_outstanding = result.get('shares_outstanding')
                if shares_outstanding:
                    extracted_data['shares_outstanding'] = shares_outstanding
            
            if 'market_cap' in missing_fields:
                market_cap = result.get('market_cap')
                if market_cap:
                    extracted_data['market_cap'] = market_cap
            
            if 'eps_diluted' in missing_fields:
                eps_diluted = result.get('eps')
                if eps_diluted:
                    extracted_data['eps_diluted'] = eps_diluted
            
            if 'book_value_per_share' in missing_fields:
                book_value = result.get('book_value')
                if book_value:
                    extracted_data['book_value_per_share'] = book_value
            
            return extracted_data if extracted_data else None
            
        except Exception as e:
            logger.error(f"Error getting Finnhub data: {e}")
            return None
    
    def _get_confidence_score(self, service_name: str, field: str) -> float:
        """Get confidence score for data from a specific service and field"""
        # Base confidence scores (0.0 to 1.0)
        base_scores = {
            'fmp': 0.95,  # FMP is most reliable
            'alpha_vantage': 0.85,
            'yahoo_finance': 0.80,
            'finnhub': 0.75
        }
        
        # Field-specific adjustments
        field_adjustments = {
            'shares_outstanding': 0.9,  # Usually reliable
            'market_cap': 0.95,         # Very reliable
            'revenue': 0.9,             # Usually reliable
            'net_income': 0.85,         # Good reliability
            'eps_diluted': 0.8,         # Can vary between sources
            'book_value_per_share': 0.75  # Can vary significantly
        }
        
        base_score = base_scores.get(service_name, 0.5)
        field_adjustment = field_adjustments.get(field, 1.0)
        
        return min(base_score * field_adjustment, 1.0)
    
    def store_fundamental_data(self, result: FundamentalDataResult) -> bool:
        """Store the collected fundamental data in the database"""
        try:
            # Convert to standard format for storage
            storage_data = {}
            for field, item in result.data.items():
                storage_data[field] = item.value
            
            # Add required metadata fields
            storage_data.update({
                'ticker': result.ticker,
                'last_updated': datetime.now(),
                'period_type': 'ttm',
                'fiscal_year': datetime.now().year,
                'fiscal_quarter': 1,
                'data_source': result.primary_source
            })
            
            # Use FMP service to store (it has the best storage logic)
            fmp_service = self.services['fmp']
            
            # Store using FMP service
            success = fmp_service.store_comprehensive_data(result.ticker, storage_data)
            
            if success:
                logger.info(f"Successfully stored fundamental data for {result.ticker}")
                logger.info(f"   Data sources: {[item.source for item in result.data.values()]}")
                logger.info(f"   Success rate: {result.success_rate:.1%}")
            else:
                logger.error(f"Failed to store fundamental data for {result.ticker}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing fundamental data for {result.ticker}: {e}")
            return False
    
    def close(self):
        """Close all service connections"""
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'close'):
                    service.close()
                logger.info(f"Closed {service_name} connection")
            except Exception as e:
                logger.warning(f"Error closing {service_name}: {e}")

# Example usage
if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'daily_run')
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the enhanced manager
    manager = EnhancedMultiServiceFundamentalManager()
    
    try:
        # Test with a ticker
        ticker = "AAPL"
        result = manager.get_fundamental_data_with_fallback(ticker)
        
        print(f"\nRESULTS FOR {ticker}:")
        print(f"Primary source: {result.primary_source}")
        print(f"Fallback sources: {result.fallback_sources_used}")
        print(f"Success rate: {result.success_rate:.1%}")
        print(f"Missing fields: {result.missing_fields}")
        
        print(f"\nDATA COLLECTED:")
        for field, item in result.data.items():
            print(f"  {field}: {item.value} (from {item.source}, confidence: {item.confidence:.2f})")
        
        # Store the data
        if result.data:
            success = manager.store_fundamental_data(result)
            print(f"\nStorage result: {'Success' if success else 'Failed'}")
        
    finally:
        manager.close() 