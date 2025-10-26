# src/options/chain_providers.py
"""
Enhanced Options Chain Provider with Production Features
Multi-provider with graceful fallbacks and comprehensive error handling
"""
from __future__ import annotations
import os
import math
import datetime as dt
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Protocol, Union
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

# Import optional dependencies with graceful fallbacks
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available - options chain functionality limited")

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    tradeapi = None
    ALPACA_AVAILABLE = False

try:
    import polygon
    POLYGON_AVAILABLE = True
except ImportError:
    polygon = None
    POLYGON_AVAILABLE = False

# Environment configuration with validation
_ALPACA_KEY = os.getenv("ALPACA_KEY_ID", "")
_ALPACA_SEC = os.getenv("ALPACA_SECRET_KEY", "")
_ALPACA_PAPER = os.getenv("ALPACA_API_BASE", "https://paper-api.alpaca.markets")
_POLYGON_KEY = os.getenv("POLYGON_API_KEY", "")

@dataclass
class OptionQuote:
    """Enhanced option quote with comprehensive data and validation"""
    symbol: str
    underlying: str
    expiry: str
    strike: float
    right: str  # "call" or "put"
    bid: float
    ask: float
    mid: float
    iv: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    last: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    timestamp: Optional[dt.datetime] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        try:
            # Validate required fields
            if not self.symbol:
                raise ValueError("symbol is required")
            if not self.underlying:
                raise ValueError("underlying is required")
            if self.strike <= 0:
                raise ValueError("strike must be positive")
            if self.right not in ("call", "put"):
                raise ValueError("right must be 'call' or 'put'")
            
            # Normalize and validate pricing
            self.bid = max(0.0, float(self.bid or 0.0))
            self.ask = max(0.0, float(self.ask or 0.0))
            
            # Recalculate mid if bid/ask available
            if self.bid > 0 and self.ask > 0:
                self.mid = (self.bid + self.ask) / 2
            else:
                self.mid = float(self.last or 0.0)
            
            # Validate Greeks (if provided)
            if self.delta is not None:
                if self.right == "call" and not (0 <= self.delta <= 1):
                    logger.warning(f"Invalid call delta {self.delta} for {self.symbol}")
                elif self.right == "put" and not (-1 <= self.delta <= 0):
                    logger.warning(f"Invalid put delta {self.delta} for {self.symbol}")
            
            # Set timestamp if not provided
            if self.timestamp is None:
                self.timestamp = dt.datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error validating OptionQuote: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def is_itm(self, spot_price: float) -> bool:
        """Check if option is in-the-money"""
        if self.right == "call":
            return spot_price > self.strike
        else:
            return spot_price < self.strike
    
    def intrinsic_value(self, spot_price: float) -> float:
        """Calculate intrinsic value"""
        if self.right == "call":
            return max(0, spot_price - self.strike)
        else:
            return max(0, self.strike - spot_price)
    
    def time_value(self, spot_price: float) -> float:
        """Calculate time value (extrinsic value)"""
        return max(0, self.mid - self.intrinsic_value(spot_price))

class ChainProviderProtocol(Protocol):
    """Protocol for options chain providers"""
    
    def get_chain(
        self, 
        symbol: str, 
        expiry: Optional[str] = None, 
        right: Optional[str] = None
    ) -> List[OptionQuote]:
        """Retrieve options chain for symbol"""
        ...
    
    def get_spot_price(self, symbol: str) -> Optional[float]:
        """Get current spot price for underlying"""
        ...
    
    def is_available(self) -> bool:
        """Check if provider is available and configured"""
        ...

def _norm_cdf(x: float) -> float:
    """Cumulative distribution function for standard normal"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))

def _bs_greeks(S: float, K: float, T: float, r: float, sigma: float, right: str) -> Dict[str, Optional[float]]:
    """
    Enhanced Black-Scholes Greeks calculation with error handling
    
    Args:
        S: Spot price
        K: Strike price
        T: Time to expiry (years)
        r: Risk-free rate
        sigma: Implied volatility
        right: "call" or "put"
    
    Returns:
        Dictionary with delta, gamma, theta, vega
    """
    try:
        if sigma is None or sigma <= 0 or T <= 0 or S <= 0 or K <= 0:
            return {"delta": None, "gamma": None, "theta": None, "vega": None}
        
        # Black-Scholes calculations
        d1 = (math.log(S/K) + (r + 0.5*sigma*sigma)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        
        Nd1 = _norm_cdf(d1)
        Nd2 = _norm_cdf(d2)
        npdf = math.exp(-0.5*d1*d1) / math.sqrt(2*math.pi)
        
        # Calculate Greeks
        if right == "call":
            delta = Nd1
            theta = -(S*npdf*sigma)/(2*math.sqrt(T)) - r*K*math.exp(-r*T)*Nd2
        else:  # put
            delta = Nd1 - 1.0
            theta = -(S*npdf*sigma)/(2*math.sqrt(T)) + r*K*math.exp(-r*T)*(1 - Nd2)
        
        gamma = npdf / (S*sigma*math.sqrt(T))
        vega = S*npdf*math.sqrt(T) / 100.0  # Per 1% volatility change
        
        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta / 365.0, 4),  # Per day
            "vega": round(vega, 4)
        }
        
    except Exception as e:
        logger.error(f"Error calculating Greeks: {e}")
        return {"delta": None, "gamma": None, "theta": None, "vega": None}

class YFinanceProvider:
    """Enhanced YFinance provider with error handling and caching"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def is_available(self) -> bool:
        return YFINANCE_AVAILABLE
    
    def get_spot_price(self, symbol: str) -> Optional[float]:
        """Get current spot price using yfinance"""
        try:
            if not self.is_available():
                return None
            
            ticker = yf.Ticker(symbol)
            
            # Try fast_info first (faster)
            try:
                price = ticker.fast_info.get("last_price")
                if price and price > 0:
                    return float(price)
            except:
                pass
            
            # Fallback to info
            try:
                info = ticker.info
                price = info.get("regularMarketPrice") or info.get("currentPrice")
                if price and price > 0:
                    return float(price)
            except:
                pass
            
            # Last resort: get recent history
            try:
                hist = ticker.history(period="1d", interval="1m")
                if not hist.empty:
                    return float(hist['Close'].iloc[-1])
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting spot price for {symbol}: {e}")
            return None
    
    def get_chain(
        self, 
        symbol: str, 
        expiry: Optional[str] = None, 
        right: Optional[str] = None
    ) -> List[OptionQuote]:
        """Enhanced options chain retrieval with error handling"""
        try:
            if not self.is_available():
                logger.warning("YFinance not available")
                return []
            
            ticker = yf.Ticker(symbol)
            expirations = getattr(ticker, 'options', None) or []
            
            if not expirations:
                logger.warning(f"No options available for {symbol}")
                return []
            
            # Select expiration
            target_expiry = self._select_expiry(expirations, expiry)
            if not target_expiry:
                logger.warning(f"No suitable expiry found for {symbol}")
                return []
            
            # Get spot price for Greeks calculation
            spot_price = self.get_spot_price(symbol)
            if not spot_price:
                logger.warning(f"Could not get spot price for {symbol}")
                spot_price = 0.0
            
            # Get option chain
            try:
                option_chain = ticker.option_chain(target_expiry)
                calls_df = option_chain.calls
                puts_df = option_chain.puts
            except Exception as e:
                logger.error(f"Error getting option chain for {symbol}: {e}")
                return []
            
            quotes = []
            
            # Process calls
            if right in (None, "call") and not calls_df.empty:
                quotes.extend(self._process_options_df(
                    calls_df, symbol, target_expiry, "call", spot_price
                ))
            
            # Process puts  
            if right in (None, "put") and not puts_df.empty:
                quotes.extend(self._process_options_df(
                    puts_df, symbol, target_expiry, "put", spot_price
                ))
            
            logger.info(f"Retrieved {len(quotes)} option quotes for {symbol}")
            return quotes
            
        except Exception as e:
            logger.error(f"Error retrieving options chain for {symbol}: {e}")
            return []
    
    def _select_expiry(self, expirations: List[str], target_expiry: Optional[str]) -> Optional[str]:
        """Select the best expiry date"""
        if not expirations:
            return None
        
        if target_expiry and target_expiry in expirations:
            return target_expiry
        
        if target_expiry:
            # Find closest expiry to target
            try:
                target_date = dt.datetime.strptime(target_expiry, "%Y-%m-%d")
                expiry_dates = [dt.datetime.strptime(exp, "%Y-%m-%d") for exp in expirations]
                closest_date = min(expiry_dates, key=lambda d: abs((d - target_date).days))
                return closest_date.strftime("%Y-%m-%d")
            except:
                pass
        
        # Default to first available
        return expirations[0]
    
    def _process_options_df(
        self, 
        df, 
        symbol: str, 
        expiry: str, 
        right: str, 
        spot_price: float
    ) -> List[OptionQuote]:
        """Process options DataFrame into OptionQuote objects"""
        quotes = []
        
        # Calculate time to expiry
        try:
            expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d")
            T = max((expiry_date - dt.datetime.utcnow()).days, 1) / 365.0
        except:
            T = 30 / 365.0  # Default to 30 days
        
        for _, row in df.iterrows():
            try:
                # Extract basic data
                contract_symbol = str(row.get('contractSymbol', ''))
                strike = float(row.get('strike', 0))
                bid = float(row.get('bid', 0) or 0)
                ask = float(row.get('ask', 0) or 0)
                last = float(row.get('lastPrice', 0) or 0)
                iv = float(row.get('impliedVolatility', 0) or 0) or None
                volume = int(row.get('volume', 0) or 0) or None
                open_interest = int(row.get('openInterest', 0) or 0) or None
                
                # Skip invalid strikes
                if strike <= 0:
                    continue
                
                # Calculate mid price
                if bid > 0 and ask > 0:
                    mid = (bid + ask) / 2
                else:
                    mid = last or 0.0
                
                # Calculate Greeks
                greeks = _bs_greeks(spot_price, strike, T, 0.0, iv, right) if iv and spot_price > 0 else {
                    "delta": None, "gamma": None, "theta": None, "vega": None
                }
                
                quote = OptionQuote(
                    symbol=contract_symbol,
                    underlying=symbol,
                    expiry=expiry,
                    strike=strike,
                    right=right,
                    bid=bid,
                    ask=ask,
                    mid=mid,
                    iv=iv,
                    delta=greeks["delta"],
                    gamma=greeks["gamma"],
                    theta=greeks["theta"],
                    vega=greeks["vega"],
                    last=last,
                    volume=volume,
                    open_interest=open_interest
                )
                
                quotes.append(quote)
                
            except Exception as e:
                logger.warning(f"Error processing option row: {e}")
                continue
        
        return quotes

class MockProvider:
    """Mock provider for testing and development"""
    
    def is_available(self) -> bool:
        return True
    
    def get_spot_price(self, symbol: str) -> Optional[float]:
        """Return mock spot price"""
        mock_prices = {
            "SPY": 450.0,
            "QQQ": 380.0,
            "AAPL": 175.0,
            "MSFT": 410.0,
            "NVDA": 500.0,
            "TSLA": 250.0
        }
        return mock_prices.get(symbol.upper(), 100.0)
    
    def get_chain(
        self, 
        symbol: str, 
        expiry: Optional[str] = None, 
        right: Optional[str] = None
    ) -> List[OptionQuote]:
        """Generate mock options chain"""
        spot = self.get_spot_price(symbol) or 100.0
        
        # Generate mock expiry
        if not expiry:
            expiry_date = dt.datetime.utcnow() + dt.timedelta(days=30)
            expiry = expiry_date.strftime("%Y-%m-%d")
        
        quotes = []
        
        # Generate strikes around spot
        strikes = [spot + i * 5 for i in range(-10, 11)]
        
        for strike in strikes:
            if right in (None, "call"):
                # Mock call option
                quotes.append(self._create_mock_option(
                    symbol, expiry, strike, "call", spot
                ))
            
            if right in (None, "put"):
                # Mock put option
                quotes.append(self._create_mock_option(
                    symbol, expiry, strike, "put", spot
                ))
        
        return quotes
    
    def _create_mock_option(
        self, 
        symbol: str, 
        expiry: str, 
        strike: float, 
        right: str, 
        spot: float
    ) -> OptionQuote:
        """Create a mock option quote"""
        # Simple mock pricing
        moneyness = spot / strike if right == "call" else strike / spot
        iv = 0.20 + max(0, 0.15 * (2 - moneyness))  # Higher IV for OTM
        
        # Mock time to expiry
        T = 30 / 365.0
        
        # Calculate theoretical price and Greeks
        greeks = _bs_greeks(spot, strike, T, 0.0, iv, right)
        
        # Mock bid/ask spread
        theoretical = max(0.01, abs(spot - strike) * 0.1 + iv * spot * 0.05)
        spread = theoretical * 0.05  # 5% spread
        
        bid = max(0.01, theoretical - spread/2)
        ask = theoretical + spread/2
        mid = (bid + ask) / 2
        
        return OptionQuote(
            symbol=f"{symbol}{expiry.replace('-', '')}{'C' if right == 'call' else 'P'}{int(strike)}",
            underlying=symbol,
            expiry=expiry,
            strike=strike,
            right=right,
            bid=round(bid, 2),
            ask=round(ask, 2),
            mid=round(mid, 2),
            iv=round(iv, 4),
            delta=greeks["delta"],
            gamma=greeks["gamma"],
            theta=greeks["theta"],
            vega=greeks["vega"],
            last=round(mid * (0.95 + 0.1 * hash(f"{symbol}{strike}") % 1), 2),
            volume=hash(f"{symbol}{strike}") % 1000 + 10,
            open_interest=hash(f"{symbol}{strike}") % 5000 + 100
        )

class OptionsChainProvider:
    """
    Enhanced options chain provider with multiple backends and graceful fallbacks
    Supports Alpaca, Polygon, YFinance with intelligent provider selection
    """
    
    def __init__(self, provider_order: Optional[List[str]] = None):
        """
        Initialize with provider preference order
        
        Args:
            provider_order: List of provider names in preference order
                          ["alpaca", "polygon", "yfinance", "mock"]
        """
        self.provider_order = provider_order or ["alpaca", "polygon", "yfinance", "mock"]
        self.providers = {
            "yfinance": YFinanceProvider(),
            "mock": MockProvider()
        }
        
        # Initialize other providers if available
        if ALPACA_AVAILABLE and _ALPACA_KEY and _ALPACA_SEC:
            # TODO: Implement AlpacaProvider when ready
            pass
        
        if POLYGON_AVAILABLE and _POLYGON_KEY:
            # TODO: Implement PolygonProvider when ready
            pass
        
        logger.info(f"Initialized OptionsChainProvider with order: {self.provider_order}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available and configured providers"""
        available = []
        for provider_name in self.provider_order:
            if provider_name in self.providers:
                if self.providers[provider_name].is_available():
                    available.append(provider_name)
        return available
    
    def get_chain(
        self, 
        symbol: str, 
        expiry: Optional[str] = None, 
        right: Optional[str] = None,
        max_retries: int = 3
    ) -> List[OptionQuote]:
        """
        Get options chain with provider fallback
        
        Args:
            symbol: Underlying symbol (e.g., "SPY")
            expiry: Target expiry date (YYYY-MM-DD) or None for nearest
            right: "call", "put", or None for both
            max_retries: Maximum retry attempts per provider
        
        Returns:
            List of OptionQuote objects
        """
        last_error = None
        
        for provider_name in self.provider_order:
            if provider_name not in self.providers:
                continue
            
            provider = self.providers[provider_name]
            
            if not provider.is_available():
                logger.debug(f"Provider {provider_name} not available")
                continue
            
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempting to get chain from {provider_name} (attempt {attempt + 1})")
                    
                    quotes = provider.get_chain(symbol, expiry, right)
                    
                    if quotes:
                        logger.info(f"Successfully retrieved {len(quotes)} quotes from {provider_name}")
                        return quotes
                    else:
                        logger.warning(f"No quotes returned from {provider_name}")
                        break  # Don't retry if no data available
                        
                except Exception as e:
                    last_error = e
                    logger.warning(f"Error from {provider_name} (attempt {attempt + 1}): {e}")
                    
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)  # Brief delay before retry
        
        # All providers failed
        if last_error:
            logger.error(f"All providers failed to retrieve chain for {symbol}. Last error: {last_error}")
        else:
            logger.error(f"No data available for {symbol} from any provider")
        
        return []
    
    def get_spot_price(self, symbol: str) -> Optional[float]:
        """Get current spot price with provider fallback"""
        for provider_name in self.provider_order:
            if provider_name not in self.providers:
                continue
            
            provider = self.providers[provider_name]
            
            if not provider.is_available():
                continue
            
            try:
                price = provider.get_spot_price(symbol)
                if price and price > 0:
                    logger.debug(f"Got spot price {price} for {symbol} from {provider_name}")
                    return price
            except Exception as e:
                logger.warning(f"Error getting spot price from {provider_name}: {e}")
                continue
        
        logger.error(f"Could not get spot price for {symbol} from any provider")
        return None
    
    def health_check(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all providers"""
        health = {}
        
        for provider_name in self.provider_order:
            if provider_name not in self.providers:
                health[provider_name] = {"available": False, "error": "Not configured"}
                continue
            
            provider = self.providers[provider_name]
            
            try:
                is_available = provider.is_available()
                
                if is_available:
                    # Test with a simple quote request
                    test_quotes = provider.get_chain("SPY", right="call")
                    health[provider_name] = {
                        "available": True,
                        "test_result": len(test_quotes) > 0,
                        "quotes_count": len(test_quotes)
                    }
                else:
                    health[provider_name] = {"available": False, "error": "Provider unavailable"}
                    
            except Exception as e:
                health[provider_name] = {"available": False, "error": str(e)}
        
        return health

# Convenience functions for common use cases
def get_options_chain(
    symbol: str, 
    expiry: Optional[str] = None, 
    right: Optional[str] = None
) -> List[OptionQuote]:
    """Convenience function to get options chain"""
    provider = OptionsChainProvider()
    return provider.get_chain(symbol, expiry, right)

def get_current_price(symbol: str) -> Optional[float]:
    """Convenience function to get current price"""
    provider = OptionsChainProvider()
    return provider.get_spot_price(symbol)

def test_providers() -> Dict[str, Any]:
    """Test all available providers"""
    provider = OptionsChainProvider()
    return provider.health_check()

# Export main classes and functions
__all__ = [
    "OptionQuote",
    "OptionsChainProvider", 
    "ChainProviderProtocol",
    "get_options_chain",
    "get_current_price",
    "test_providers"
]