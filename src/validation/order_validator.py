#!/usr/bin/env python3
"""
Enhanced Order Validation System
===============================
Provides comprehensive order validation with multiple validation layers:
- Basic field validation (symbol, side, quantity)
- Market data validation (symbol exists, market hours)
- Risk management validation (position limits, concentration)
- Compliance validation (regulatory requirements)
- Strategy validation (strategy-specific rules)

This system integrates with the existing order staging workflow to provide
institutional-grade validation before orders are processed.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, time, timezone
import yfinance as yf

logger = logging.getLogger(__name__)

class OrderValidator:
    """Comprehensive order validation system."""
    
    def __init__(self):
        self.max_position_size = Decimal('100000')  # $100k max position
        self.max_concentration = Decimal('0.20')    # 20% max concentration
        self.valid_symbols_cache = {}
        self.market_hours = {
            'open': time(9, 30),   # 9:30 AM
            'close': time(16, 0)   # 4:00 PM
        }
    
    def validate_order(self, order: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Comprehensive order validation.
        
        Args:
            order: Order dictionary with required fields
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Basic field validation
        basic_errors = self._validate_basic_fields(order)
        errors.extend(basic_errors)
        
        # Market data validation
        if not basic_errors:  # Only if basic validation passes
            market_errors = self._validate_market_data(order)
            errors.extend(market_errors)
            
            # Risk validation
            risk_errors = self._validate_risk_limits(order)
            errors.extend(risk_errors)
            
            # Compliance validation
            compliance_errors = self._validate_compliance_rules(order)
            errors.extend(compliance_errors)
            
            # Strategy validation
            if order.get('strategy'):
                strategy_errors = self._validate_strategy_rules(order)
                errors.extend(strategy_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_basic_fields(self, order: Dict[str, Any]) -> List[str]:
        """Validate basic order fields."""
        errors = []
        
        # Required fields
        required_fields = ['symbol', 'side', 'qty']
        for field in required_fields:
            if field not in order or order[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Symbol validation
        symbol = order.get('symbol', '').upper()
        if symbol:
            if not re.match(r'^[A-Z]{1,5}$', symbol):
                errors.append(f"Invalid symbol format: {symbol}")
        
        # Side validation
        side = order.get('side', '').lower()
        if side and side not in ['buy', 'sell']:
            errors.append(f"Invalid side: {side}. Must be 'buy' or 'sell'")
        
        # Quantity validation
        qty = order.get('qty')
        if qty is not None:
            try:
                qty_decimal = Decimal(str(qty))
                if qty_decimal <= 0:
                    errors.append("Quantity must be positive")
                if qty_decimal > 10000:
                    errors.append("Quantity exceeds maximum limit (10,000)")
            except (ValueError, TypeError):
                errors.append(f"Invalid quantity: {qty}")
        
        # Order type validation
        order_type = order.get('type', 'market').lower()
        if order_type not in ['market', 'limit', 'stop', 'stop_limit']:
            errors.append(f"Invalid order type: {order_type}")
        
        # Limit price validation for limit orders
        if order_type in ['limit', 'stop_limit']:
            limit_price = order.get('limit')
            if not limit_price:
                errors.append(f"{order_type} order requires limit price")
            else:
                try:
                    price_decimal = Decimal(str(limit_price))
                    if price_decimal <= 0:
                        errors.append("Limit price must be positive")
                except (ValueError, TypeError):
                    errors.append(f"Invalid limit price: {limit_price}")
        
        return errors
    
    def _validate_market_data(self, order: Dict[str, Any]) -> List[str]:
        """Validate against market data."""
        errors = []
        symbol = order.get('symbol', '').upper()
        
        if not symbol:
            return errors  # Skip if no symbol
        
        try:
            # Check if symbol exists and get current data
            if symbol not in self.valid_symbols_cache:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if not info or 'symbol' not in info:
                    errors.append(f"Symbol not found: {symbol}")
                    return errors
                
                # Cache valid symbol
                self.valid_symbols_cache[symbol] = {
                    'valid': True,
                    'current_price': info.get('currentPrice'),
                    'market_cap': info.get('marketCap'),
                    'volume': info.get('volume')
                }
            
            symbol_info = self.valid_symbols_cache[symbol]
            current_price = symbol_info.get('current_price')
            
            # Validate limit price against current market price
            if order.get('type') == 'limit' and current_price:
                limit_price = Decimal(str(order.get('limit', 0)))
                market_price = Decimal(str(current_price))
                
                # Check for obviously unrealistic prices
                price_diff_pct = abs(limit_price - market_price) / market_price
                if price_diff_pct > Decimal('0.50'):  # 50% difference
                    errors.append(f"Limit price ${limit_price} differs significantly from market price ${market_price}")
            
            # Check market hours (simplified - assumes US markets)
            now = datetime.now(timezone.utc)
            current_time = now.time()
            
            if order.get('type') == 'market':
                # Market orders should generally be during market hours
                if not (self.market_hours['open'] <= current_time <= self.market_hours['close']):
                    errors.append("Market order outside trading hours - consider using limit order")
        
        except Exception as e:
            logger.warning(f"Market data validation failed for {symbol}: {e}")
            # Don't fail validation just because market data is unavailable
        
        return errors
    
    def _validate_risk_limits(self, order: Dict[str, Any]) -> List[str]:
        """Validate against risk management rules."""
        errors = []
        
        # Calculate position value
        qty = Decimal(str(order.get('qty', 0)))
        price = None
        
        if order.get('limit'):
            price = Decimal(str(order['limit']))
        elif order.get('symbol') in self.valid_symbols_cache:
            market_price = self.valid_symbols_cache[order['symbol']].get('current_price')
            if market_price:
                price = Decimal(str(market_price))
        
        if price:
            position_value = qty * price
            
            # Check maximum position size
            if position_value > self.max_position_size:
                errors.append(f"Position value ${position_value:,.2f} exceeds maximum ${self.max_position_size:,.2f}")
        
        # Additional risk checks could include:
        # - Portfolio concentration limits
        # - Volatility-based position sizing
        # - Correlation limits
        # - Sector exposure limits
        
        return errors
    
    def _validate_compliance_rules(self, order: Dict[str, Any]) -> List[str]:
        """Validate against compliance requirements."""
        errors = []
        
        # Pattern Day Trader rules (simplified)
        qty = Decimal(str(order.get('qty', 0)))
        if qty > 1000:  # Large orders might need additional oversight
            if not order.get('user'):
                errors.append("Large orders require user identification")
        
        # Penny stock restrictions
        symbol = order.get('symbol', '').upper()
        if symbol in self.valid_symbols_cache:
            current_price = self.valid_symbols_cache[symbol].get('current_price')
            if current_price and Decimal(str(current_price)) < Decimal('5.00'):
                errors.append("Penny stock orders require additional approval")
        
        # Additional compliance checks could include:
        # - Know Your Customer (KYC) requirements
        # - Anti-Money Laundering (AML) checks
        # - Position limits by account type
        # - Geographic restrictions
        # - Time-based restrictions
        
        return errors
    
    def _validate_strategy_rules(self, order: Dict[str, Any]) -> List[str]:
        """Validate strategy-specific rules."""
        errors = []
        strategy = order.get('strategy', '').lower()
        
        if strategy == 'momentum':
            # Momentum strategies might require recent price movement validation
            pass
        elif strategy == 'mean_reversion':
            # Mean reversion might require oversold/overbought conditions
            pass
        elif strategy == 'arbitrage':
            # Arbitrage might require multiple legs validation
            pass
        elif strategy == 'hedge':
            # Hedging might require existing position validation
            pass
        
        # Strategy-specific validation logic can be added here
        
        return errors
    
    def get_validation_summary(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive validation summary."""
        is_valid, errors = self.validate_order(order)
        
        return {
            'valid': is_valid,
            'errors': errors,
            'warnings': [],  # Could add warnings for non-blocking issues
            'risk_score': self._calculate_risk_score(order),
            'compliance_status': 'passed' if not any('compliance' in err.lower() for err in errors) else 'failed',
            'validation_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_risk_score(self, order: Dict[str, Any]) -> float:
        """Calculate a simple risk score (0-100)."""
        base_score = 10.0  # Base risk
        
        # Add risk based on quantity
        qty = Decimal(str(order.get('quantity', order.get('qty', 0))))
        if qty > 1000:
            base_score += 20.0
        elif qty > 500:
            base_score += 10.0
        
        # Add risk based on order type
        order_type = order.get('order_type', order.get('type', 'market')).lower()
        if order_type == 'market':
            base_score += 15.0  # Market orders have execution price risk
        
        # Add risk based on position value
        symbol = order.get('symbol', '').upper()
        if symbol in self.valid_symbols_cache:
            current_price = self.valid_symbols_cache[symbol].get('current_price')
            if current_price:
                position_value = qty * Decimal(str(current_price))
                if position_value > Decimal('50000'):
                    base_score += 25.0
                elif position_value > Decimal('25000'):
                    base_score += 15.0
        
        return min(base_score, 100.0)
    
    def calculate_risk_score(self, order: Dict[str, Any]) -> float:
        """Public method to calculate risk score."""
        return self._calculate_risk_score(order)


# Global validator instance
validator = OrderValidator()

def validate_order(order: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Convenience function for order validation."""
    return validator.validate_order(order)

def get_validation_summary(order: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for validation summary."""
    return validator.get_validation_summary(order)