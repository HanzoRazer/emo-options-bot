"""Market data provider interface."""

from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime
import yfinance as yf


class MarketDataProvider:
    """
    Provide market data for options and underlying securities.
    
    Currently uses Yahoo Finance as the data source.
    """
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize market data provider."""
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, dict] = {}
    
    def get_option_price(
        self,
        symbol: str,
        strike: Decimal,
        expiration: str,
        option_type: str
    ) -> Optional[Decimal]:
        """
        Get current option price.
        
        Args:
            symbol: Underlying symbol
            strike: Strike price
            expiration: Expiration date
            option_type: 'CALL' or 'PUT'
            
        Returns:
            Current option price or None if not available
        """
        cache_key = f"{symbol}_{strike}_{expiration}_{option_type}"
        
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < 60:
                return cached["price"]
        
        try:
            ticker = yf.Ticker(symbol)
            # Note: This is simplified - real implementation would query option chain
            # For now, return None to indicate data would need to be fetched
            return None
        except Exception:
            return None
    
    def get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current stock price.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current stock price or None if not available
        """
        cache_key = f"stock_{symbol}"
        
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < 60:
                return cached["price"]
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            
            if price:
                price_decimal = Decimal(str(price))
                
                if self.cache_enabled:
                    self._cache[cache_key] = {
                        "price": price_decimal,
                        "timestamp": datetime.now()
                    }
                
                return price_decimal
        except Exception:
            pass
        
        return None
    
    def get_option_chain(self, symbol: str, expiration: Optional[str] = None) -> Optional[dict]:
        """
        Get option chain for a symbol.
        
        Args:
            symbol: Underlying symbol
            expiration: Specific expiration date (optional)
            
        Returns:
            Option chain data or None if not available
        """
        try:
            ticker = yf.Ticker(symbol)
            
            if expiration:
                options = ticker.option_chain(expiration)
            else:
                # Get nearest expiration
                expirations = ticker.options
                if not expirations:
                    return None
                options = ticker.option_chain(expirations[0])
            
            return {
                "calls": options.calls.to_dict('records'),
                "puts": options.puts.to_dict('records'),
            }
        except Exception:
            return None
    
    def get_implied_volatility(
        self,
        symbol: str,
        strike: Decimal,
        expiration: str,
        option_type: str
    ) -> Optional[float]:
        """
        Get implied volatility for an option.
        
        Args:
            symbol: Underlying symbol
            strike: Strike price
            expiration: Expiration date
            option_type: 'CALL' or 'PUT'
            
        Returns:
            Implied volatility or None if not available
        """
        # Simplified implementation
        return None
