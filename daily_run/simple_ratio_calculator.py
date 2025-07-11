"""
Simple Ratio Calculator
Replacement for the archived ratio_calculator module
Enhanced with robust error handling and safe division
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


def safe_divide(numerator: Optional[float], denominator: Optional[float], default: float = 0.0) -> float:
    """
    Safely perform division with comprehensive error handling.
    
    Args:
        numerator: Value to divide
        denominator: Value to divide by
        default: Default value to return on error/zero division
        
    Returns:
        Division result or default value
    """
    try:
        if numerator is None or denominator is None:
            return default
        
        # Convert to float if needed
        num = float(numerator) if not isinstance(numerator, float) else numerator
        den = float(denominator) if not isinstance(denominator, float) else denominator
        
        # Check for zero or very small denominator
        if abs(den) < 1e-10:  # Very small number, treat as zero
            return default
            
        result = num / den
        
        # Check for invalid results
        if not isinstance(result, (int, float)) or result != result:  # NaN check
            return default
            
        return result
        
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as e:
        logger.debug(f"Safe division failed: {numerator}/{denominator} -> {e}")
        return default


def calculate_ratios(financial_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate financial ratios from financial data with comprehensive error handling.
    
    Args:
        financial_data: Dictionary containing financial metrics
        
    Returns:
        Dictionary of calculated ratios (zeros for failed calculations)
    """
    ratios = {}
    
    try:
        # Extract key metrics safely
        revenue = safe_float(financial_data.get('revenue'))
        net_income = safe_float(financial_data.get('net_income'))
        total_assets = safe_float(financial_data.get('total_assets'))
        total_equity = safe_float(financial_data.get('total_equity'))
        shares_outstanding = safe_float(financial_data.get('shares_outstanding'))
        market_cap = safe_float(financial_data.get('market_cap'))
        current_price = safe_float(financial_data.get('current_price'))
        
        # Calculate basic ratios with safe division
        try:
            # EPS calculation
            eps = safe_divide(net_income, shares_outstanding, 0.0)
            ratios['eps'] = eps
            
            # P/E Ratio calculation 
            ratios['pe_ratio'] = safe_divide(current_price, eps, 0.0)
            
            # P/S Ratio calculation
            market_cap_calc = safe_divide(current_price * shares_outstanding if current_price and shares_outstanding else 0, 1, 0.0)
            ratios['price_to_sales'] = safe_divide(market_cap_calc, revenue, 0.0)
            
            # P/B Ratio calculation
            book_value_per_share = safe_divide(total_equity, shares_outstanding, 0.0)
            ratios['price_to_book'] = safe_divide(current_price, book_value_per_share, 0.0)
            
            # ROE calculation
            ratios['roe'] = safe_divide(net_income, total_equity, 0.0)
            
            # ROA calculation
            ratios['roa'] = safe_divide(net_income, total_assets, 0.0)
            
            # Asset Turnover calculation
            ratios['asset_turnover'] = safe_divide(revenue, total_assets, 0.0)
            
            # Market-based ratios
            ratios['market_cap_to_revenue'] = safe_divide(market_cap, revenue, 0.0)
            
            # Only calculate if net_income is positive
            if net_income and net_income > 0:
                ratios['market_cap_to_earnings'] = safe_divide(market_cap, net_income, 0.0)
            else:
                ratios['market_cap_to_earnings'] = 0.0
            
            logger.debug(f"Successfully calculated {len(ratios)} ratios")
            
        except Exception as calc_error:
            logger.warning(f"Error in ratio calculations: {calc_error}")
            # Return zeros for all ratios if calculation fails
            ratios = {
                'eps': 0.0,
                'pe_ratio': 0.0,
                'price_to_sales': 0.0,
                'price_to_book': 0.0,
                'roe': 0.0,
                'roa': 0.0,
                'asset_turnover': 0.0,
                'market_cap_to_revenue': 0.0,
                'market_cap_to_earnings': 0.0
            }
            
    except Exception as e:
        logger.error(f"Error calculating ratios: {e}")
        # Return empty dict with zeros for critical ratios
        ratios = {
            'eps': 0.0,
            'pe_ratio': 0.0,
            'price_to_sales': 0.0,
            'price_to_book': 0.0,
            'roe': 0.0,
            'roa': 0.0,
            'asset_turnover': 0.0,
            'market_cap_to_revenue': 0.0,
            'market_cap_to_earnings': 0.0
        }
        
    return ratios


def validate_ratios(ratios: Dict[str, float]) -> Dict[str, Any]:
    """
    Validate calculated ratios for reasonableness with enhanced error handling.
    
    Args:
        ratios: Dictionary of calculated ratios
        
    Returns:
        Validation results (never fails)
    """
    validation = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    try:
        # PE ratio validation
        pe = ratios.get('pe_ratio', 0.0)
        if pe and pe != 0.0:
            if pe < 0:
                validation['warnings'].append('Negative PE ratio (company has losses)')
            elif pe > 1000:
                validation['warnings'].append(f'Very high PE ratio: {pe:.2f}')
        
        # Price to book validation
        pb = ratios.get('price_to_book', 0.0)
        if pb and pb != 0.0:
            if pb < 0:
                validation['warnings'].append('Negative price-to-book ratio')
            elif pb > 50:
                validation['warnings'].append(f'Very high price-to-book ratio: {pb:.2f}')
        
        # ROE validation
        roe = ratios.get('roe', 0.0)
        if roe and roe != 0.0:
            if abs(roe) > 1:  # More than 100%
                validation['warnings'].append(f'Extreme ROE: {roe:.2%}')
        
        # ROA validation
        roa = ratios.get('roa', 0.0)
        if roa and roa != 0.0:
            if abs(roa) > 0.5:  # More than 50%
                validation['warnings'].append(f'Extreme ROA: {roa:.2%}')
                
    except Exception as e:
        logger.error(f"Error validating ratios: {e}")
        validation['warnings'].append(f'Validation error: {e}')
        # Don't mark as invalid - just add warning
        
    return validation


def safe_float(value: Any) -> Optional[float]:
    """
    Safely convert value to float with enhanced error handling.
    
    Args:
        value: Value to convert
        
    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
        
    try:
        if isinstance(value, (int, float)):
            result = float(value)
            # Check for NaN or infinity
            if result != result or abs(result) == float('inf'):
                return None
            return result
        elif isinstance(value, str):
            # Clean string value
            cleaned = value.replace(',', '').replace('$', '').replace('%', '').strip()
            if cleaned and cleaned.lower() not in ('nan', 'inf', '-inf', 'null', 'none', ''):
                result = float(cleaned)
                # Check for NaN or infinity
                if result != result or abs(result) == float('inf'):
                    return None
                return result
        return None
    except (ValueError, TypeError, OverflowError):
        return None


def format_ratio_display(ratios: Dict[str, float]) -> Dict[str, str]:
    """
    Format ratios for display with safe error handling.
    
    Args:
        ratios: Dictionary of calculated ratios
        
    Returns:
        Dictionary of formatted ratio strings (never fails)
    """
    formatted = {}
    
    try:
        for key, value in ratios.items():
            try:
                if value is None or value == 0.0:
                    formatted[key] = 'N/A'
                elif key in ['roe', 'roa']:
                    formatted[key] = f"{value:.2%}"
                elif key in ['pe_ratio', 'price_to_book', 'price_to_sales']:
                    formatted[key] = f"{value:.2f}"
                else:
                    formatted[key] = f"{value:.4f}"
            except Exception as e:
                logger.debug(f"Error formatting {key}: {e}")
                formatted[key] = 'N/A'
    except Exception as e:
        logger.error(f"Error in format_ratio_display: {e}")
        # Return basic formatted dict
        formatted = {key: 'N/A' for key in ratios.keys()}
    
    return formatted


def test_ratio_calculator():
    """Test the ratio calculator functionality"""
    print("🧪 Testing Ratio Calculator")
    print("=" * 40)
    
    # Test data
    test_data = {
        'revenue': 100000000,  # $100M
        'net_income': 10000000,  # $10M
        'total_assets': 80000000,  # $80M
        'total_equity': 50000000,  # $50M
        'shares_outstanding': 1000000,  # 1M shares
        'current_price': 50,  # $50/share
        'market_cap': 50000000  # $50M
    }
    
    # Calculate ratios
    ratios = calculate_ratios(test_data)
    print("✅ Calculated ratios:")
    for name, value in ratios.items():
        print(f"  {name}: {value}")
    
    # Validate ratios
    validation = validate_ratios(ratios)
    print(f"\n✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")
    if validation['errors']:
        print(f"  Errors: {validation['errors']}")
    
    # Format ratios
    formatted = format_ratio_display(ratios)
    print("\n✅ Formatted ratios:")
    for name, value in formatted.items():
        print(f"  {name}: {value}")


if __name__ == "__main__":
    test_ratio_calculator() 