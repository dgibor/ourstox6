"""
Data Validation Module

Provides comprehensive data validation for API responses,
database inputs, and data quality checks.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np
from daily_run.error_handler import ErrorHandler, ErrorSeverity

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Comprehensive data validation for financial data.
    """
    
    def __init__(self):
        self.error_handler = ErrorHandler("data_validator")
        
        # Reasonable ranges for financial data
        self.price_range = (0.01, 100000.0)  # $0.01 to $100,000
        self.volume_range = (0, 10_000_000_000)  # 0 to 10B shares
        self.market_cap_range = (1_000_000, 10_000_000_000_000)  # $1M to $10T
        self.pe_ratio_range = (-1000, 1000)  # Allow negative P/E ratios
        self.ratio_range = (-100, 100)  # Most financial ratios
        self.percentage_range = (-100, 100)  # Percentage changes
    
    def validate_price_data(self, ticker: str, price_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate price data from API responses with enhanced edge case handling.
        
        Args:
            ticker: Stock ticker symbol
            price_data: Price data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check required fields
            required_fields = ['close_price']
            for field in required_fields:
                if field not in price_data or price_data[field] is None:
                    errors.append(f"Missing required field: {field}")
            
            # Enhanced price validation
            if 'close_price' in price_data and price_data['close_price'] is not None:
                try:
                    price = float(price_data['close_price'])
                    
                    # Check for NaN, infinity, and extremely large values
                    if not isinstance(price, (int, float)) or price != price:  # NaN check
                        errors.append(f"Close price is NaN or invalid: {price}")
                    elif abs(price) == float('inf'):
                        errors.append(f"Close price is infinite: {price}")
                    elif abs(price) > 1e12:  # Extremely large number (> 1 trillion)
                        errors.append(f"Close price suspiciously large: {price}")
                    elif not self._is_in_range(price, self.price_range):
                        errors.append(f"Close price {price} outside valid range {self.price_range}")
                    elif price <= 0:
                        errors.append(f"Close price must be positive, got {price}")
                        
                except (ValueError, TypeError, OverflowError) as e:
                    errors.append(f"Invalid close_price value: {price_data['close_price']} - {e}")
            
            # Enhanced volume validation
            if 'volume' in price_data and price_data['volume'] is not None:
                try:
                    volume = float(price_data['volume'])
                    
                    # Check for NaN, infinity, and extremely large values
                    if volume != volume:  # NaN check
                        errors.append(f"Volume is NaN: {volume}")
                    elif abs(volume) == float('inf'):
                        errors.append(f"Volume is infinite: {volume}")
                    elif volume < 0:
                        errors.append(f"Volume cannot be negative, got {volume}")
                    elif volume > 1e15:  # Extremely large volume (> 1 quadrillion)
                        errors.append(f"Volume suspiciously large: {volume}")
                    elif not self._is_in_range(volume, self.volume_range):
                        errors.append(f"Volume {volume} outside valid range {self.volume_range}")
                        
                except (ValueError, TypeError, OverflowError) as e:
                    errors.append(f"Invalid volume value: {price_data['volume']} - {e}")
            
            # Enhanced market cap validation
            if 'market_cap' in price_data and price_data['market_cap'] is not None:
                try:
                    market_cap = float(price_data['market_cap'])
                    
                    # Check for NaN, infinity, and extremely large values
                    if market_cap != market_cap:  # NaN check
                        errors.append(f"Market cap is NaN: {market_cap}")
                    elif abs(market_cap) == float('inf'):
                        errors.append(f"Market cap is infinite: {market_cap}")
                    elif market_cap <= 0:
                        errors.append(f"Market cap must be positive, got {market_cap}")
                    elif market_cap > 1e16:  # Extremely large market cap (> 10 quadrillion)
                        errors.append(f"Market cap suspiciously large: {market_cap}")
                    elif not self._is_in_range(market_cap, self.market_cap_range):
                        errors.append(f"Market cap {market_cap} outside valid range {self.market_cap_range}")
                        
                except (ValueError, TypeError, OverflowError) as e:
                    errors.append(f"Invalid market_cap value: {price_data['market_cap']} - {e}")
            
            # Enhanced percentage change validation
            for field in ['change_percent']:
                if field in price_data and price_data[field] is not None:
                    try:
                        # Handle percentage strings like "5.2%" or just numbers
                        value_str = str(price_data[field]).replace('%', '').replace(',', '')
                        pct_change = float(value_str)
                        
                        # Check for NaN, infinity, and extremely large values
                        if pct_change != pct_change:  # NaN check
                            errors.append(f"{field} is NaN: {pct_change}")
                        elif abs(pct_change) == float('inf'):
                            errors.append(f"{field} is infinite: {pct_change}")
                        elif abs(pct_change) > 1000:  # More than 1000% change
                            errors.append(f"{field} suspiciously large: {pct_change}%")
                        elif not self._is_in_range(pct_change, self.percentage_range):
                            errors.append(f"{field} {pct_change}% outside valid range {self.percentage_range}%")
                            
                    except (ValueError, TypeError, OverflowError) as e:
                        errors.append(f"Invalid {field} format: {price_data[field]} - {e}")
            
            # Check for data staleness with enhanced validation
            if 'timestamp' in price_data:
                try:
                    timestamp = price_data['timestamp']
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif not isinstance(timestamp, datetime):
                        errors.append(f"Invalid timestamp type: {type(timestamp)}")
                        timestamp = None
                    
                    if timestamp:
                        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                        if age_hours > 48:  # Data older than 48 hours
                            errors.append(f"Price data is {age_hours:.1f} hours old")
                        elif age_hours < 0:  # Future timestamp
                            errors.append(f"Price data has future timestamp: {age_hours:.1f} hours ahead")
                            
                except Exception as e:
                    errors.append(f"Invalid timestamp format: {e}")
            
            # Additional data consistency checks
            if 'price' in price_data and 'close_price' in price_data:
                try:
                    price1 = float(price_data['price'])
                    price2 = float(price_data['close_price'])
                    if abs(price1 - price2) / max(price1, price2) > 0.1:  # More than 10% difference
                        errors.append(f"Inconsistent price fields: price={price1}, close_price={price2}")
                except:
                    pass  # Already validated individually
            
            is_valid = len(errors) == 0
            
            if not is_valid:
                logger.warning(f"Price data validation failed for {ticker}: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating price data for {ticker}: {e}")
            return False, [f"Validation error: {e}"]
    
    def validate_fundamental_data(self, ticker: str, fund_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate fundamental data from API responses.
        
        Args:
            ticker: Stock ticker symbol
            fund_data: Fundamental data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check for basic required fields
            required_fields = ['symbol']
            for field in required_fields:
                if field not in fund_data or fund_data[field] is None:
                    errors.append(f"Missing required field: {field}")
            
            # Validate symbol matches ticker
            if 'symbol' in fund_data and fund_data['symbol'] != ticker:
                errors.append(f"Symbol mismatch: expected {ticker}, got {fund_data['symbol']}")
            
            # Validate financial metrics
            financial_fields = {
                'revenue': 'revenue',
                'totalRevenue': 'revenue',
                'netIncome': 'net_income',
                'totalAssets': 'total_assets',
                'totalEquity': 'total_equity',
                'sharesOutstanding': 'shares_outstanding'
            }
            
            for api_field, db_field in financial_fields.items():
                if api_field in fund_data and fund_data[api_field] is not None:
                    try:
                        value = float(fund_data[api_field])
                        
                        # Revenue and total assets should be positive
                        if db_field in ['revenue', 'total_assets'] and value <= 0:
                            errors.append(f"{db_field} must be positive, got {value}")
                        
                        # Shares outstanding should be positive
                        if db_field == 'shares_outstanding' and value <= 0:
                            errors.append(f"Shares outstanding must be positive, got {value}")
                        
                        # Check for unreasonably large values (likely in wrong units)
                        if db_field in ['revenue', 'total_assets'] and value > 1e15:  # > $1 quadrillion
                            errors.append(f"{db_field} value {value} seems unreasonably large")
                            
                    except ValueError:
                        errors.append(f"Invalid numeric value for {api_field}: {fund_data[api_field]}")
            
            # Validate ratios if present
            ratio_fields = {
                'peRatio': 'pe_ratio',
                'priceToBook': 'pb_ratio',
                'debtToEquity': 'debt_to_equity',
                'returnOnEquity': 'roe',
                'returnOnAssets': 'roa'
            }
            
            for api_field, db_field in ratio_fields.items():
                if api_field in fund_data and fund_data[api_field] is not None:
                    try:
                        value = float(fund_data[api_field])
                        if not self._is_in_range(value, self.ratio_range):
                            errors.append(f"{db_field} {value} outside reasonable range {self.ratio_range}")
                    except ValueError:
                        errors.append(f"Invalid ratio value for {api_field}: {fund_data[api_field]}")
            
            # Check data completeness score
            total_fields = len(financial_fields) + len(ratio_fields)
            present_fields = sum(1 for field in list(financial_fields.keys()) + list(ratio_fields.keys()) 
                               if field in fund_data and fund_data[field] is not None)
            
            completeness = present_fields / total_fields
            if completeness < 0.3:  # Less than 30% data present
                errors.append(f"Low data completeness: {completeness:.1%} of expected fields present")
            
            is_valid = len(errors) == 0
            
            if not is_valid:
                logger.warning(f"Fundamental data validation failed for {ticker}: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating fundamental data for {ticker}: {e}")
            return False, [f"Validation error: {e}"]
    
    def validate_technical_indicators(self, ticker: str, indicators: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate technical indicator values with enhanced checks.
        
        Args:
            ticker: Stock ticker symbol
            indicators: Technical indicators dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validate RSI (0-100 range)
            if 'rsi_14' in indicators:
                rsi = indicators['rsi_14']
                if pd.isna(rsi) or np.isinf(rsi):
                    errors.append(f"RSI has invalid value: {rsi}")
                elif not (0 <= rsi <= 100):
                    errors.append(f"RSI {rsi} outside valid range [0, 100]")
            
            # Validate EMA values (should be positive for stock prices)
            for field in ['ema_20', 'ema_50']:
                if field in indicators:
                    ema = indicators[field]
                    if pd.isna(ema) or np.isinf(ema):
                        errors.append(f"{field} has invalid value: {ema}")
                    elif ema <= 0:
                        errors.append(f"{field} must be positive, got {ema}")
                    elif not self._is_in_range(ema, self.price_range):
                        errors.append(f"{field} {ema} outside reasonable price range {self.price_range}")
            
            # Validate MACD values (reasonable ranges)
            macd_fields = ['macd_line', 'macd_signal', 'macd_histogram']
            for field in macd_fields:
                if field in indicators:
                    value = indicators[field]
                    if pd.isna(value) or np.isinf(value):
                        errors.append(f"{field} has invalid value: {value}")
                    elif abs(value) > 100:  # MACD shouldn't be extremely large
                        errors.append(f"{field} {value} seems unreasonably large")
            
            # Validate Bollinger Bands (upper > middle > lower)
            if all(field in indicators for field in ['bb_upper', 'bb_middle', 'bb_lower']):
                bb_upper = indicators['bb_upper']
                bb_middle = indicators['bb_middle']
                bb_lower = indicators['bb_lower']
                
                if not (pd.isna(bb_upper) or pd.isna(bb_middle) or pd.isna(bb_lower)):
                    if not (bb_upper >= bb_middle >= bb_lower):
                        errors.append(f"Bollinger Bands order invalid: upper={bb_upper}, middle={bb_middle}, lower={bb_lower}")
            
            # Validate Stochastic (0-100 range)
            for field in ['stoch_k', 'stoch_d']:
                if field in indicators:
                    stoch = indicators[field]
                    if pd.isna(stoch) or np.isinf(stoch):
                        errors.append(f"{field} has invalid value: {stoch}")
                    elif not (0 <= stoch <= 100):
                        errors.append(f"{field} {stoch} outside valid range [0, 100]")
            
            # Validate CCI (reasonable range)
            if 'cci_20' in indicators:
                cci = indicators['cci_20']
                if pd.isna(cci) or np.isinf(cci):
                    errors.append(f"CCI has invalid value: {cci}")
                elif abs(cci) > 300:  # CCI shouldn't be extremely large
                    errors.append(f"CCI {cci} seems unreasonably large")
            
            # Validate ATR (should be positive)
            if 'atr_14' in indicators:
                atr = indicators['atr_14']
                if pd.isna(atr) or np.isinf(atr):
                    errors.append(f"ATR has invalid value: {atr}")
                elif atr < 0:
                    errors.append(f"ATR must be non-negative, got {atr}")
            
            # Check for zero values that might indicate calculation failures
            zero_count = sum(1 for value in indicators.values() if value == 0)
            if zero_count > len(indicators) * 0.7:  # More than 70% are zero
                errors.append(f"Too many zero values ({zero_count}/{len(indicators)}) - possible calculation failure")
            
            is_valid = len(errors) == 0
            
            if not is_valid:
                logger.warning(f"Technical indicators validation failed for {ticker}: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating technical indicators for {ticker}: {e}")
            return False, [f"Validation error: {e}"]
    
    def validate_api_response(self, service_name: str, response: Any) -> Tuple[bool, List[str]]:
        """
        Validate API response structure and content.
        
        Args:
            service_name: Name of the API service
            response: API response to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check if response exists
            if response is None:
                errors.append("API response is None")
                return False, errors
            
            # Check for error indicators in response
            if isinstance(response, dict):
                # Check for common error indicators
                error_fields = ['error', 'Error', 'errorMessage', 'message']
                for field in error_fields:
                    if field in response:
                        errors.append(f"API returned error: {response[field]}")
                
                # Check for rate limit indicators
                rate_limit_indicators = ['rate limit', 'too many requests', 'quota exceeded']
                for field, value in response.items():
                    if isinstance(value, str):
                        for indicator in rate_limit_indicators:
                            if indicator.lower() in value.lower():
                                errors.append(f"Rate limit detected: {value}")
                
                # Service-specific validations
                if service_name.lower() == 'yahoo':
                    if 'quoteResponse' in response:
                        quote_response = response['quoteResponse']
                        if 'error' in quote_response and quote_response['error']:
                            errors.append(f"Yahoo Finance error: {quote_response['error']}")
                        if 'result' not in quote_response:
                            errors.append("Yahoo Finance response missing 'result' field")
                
                elif service_name.lower() == 'fmp':
                    if isinstance(response, list) and len(response) == 0:
                        errors.append("FMP returned empty result list")
                
                elif service_name.lower() == 'alpha_vantage':
                    if 'Error Message' in response:
                        errors.append(f"Alpha Vantage error: {response['Error Message']}")
                    if 'Note' in response and 'call frequency' in response['Note']:
                        errors.append(f"Alpha Vantage rate limit: {response['Note']}")
            
            # Check response size (too small might indicate error)
            if isinstance(response, (dict, list)) and len(response) == 0:
                errors.append("API response is empty")
            
            is_valid = len(errors) == 0
            
            if not is_valid:
                logger.warning(f"{service_name} API response validation failed: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating {service_name} API response: {e}")
            return False, [f"Validation error: {e}"]
    
    def _is_in_range(self, value: float, valid_range: Tuple[float, float]) -> bool:
        """Check if value is within the specified range."""
        return valid_range[0] <= value <= valid_range[1]
    
    def get_data_quality_score(self, ticker: str, data: Dict[str, Any]) -> float:
        """
        Calculate a data quality score (0-1) based on completeness and validity.
        
        Args:
            ticker: Stock ticker symbol
            data: Data dictionary to score
            
        Returns:
            Quality score between 0 and 1
        """
        try:
            total_score = 0
            max_score = 0
            
            # Score based on field presence
            expected_fields = ['close_price', 'volume', 'revenue', 'net_income', 'total_assets']
            for field in expected_fields:
                max_score += 1
                if field in data and data[field] is not None:
                    total_score += 1
            
            # Score based on data validity
            if 'close_price' in data:
                max_score += 1
                if self._is_in_range(float(data['close_price']), self.price_range):
                    total_score += 1
            
            return total_score / max_score if max_score > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating data quality score for {ticker}: {e}")
            return 0


# Global validator instance
data_validator = DataValidator()


def validate_price_data(ticker: str, price_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Convenience function for price data validation."""
    return data_validator.validate_price_data(ticker, price_data)


def validate_fundamental_data(ticker: str, fund_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Convenience function for fundamental data validation."""
    return data_validator.validate_fundamental_data(ticker, fund_data)


def validate_api_response(service_name: str, response: Any) -> Tuple[bool, List[str]]:
    """Convenience function for API response validation."""
    return data_validator.validate_api_response(service_name, response) 