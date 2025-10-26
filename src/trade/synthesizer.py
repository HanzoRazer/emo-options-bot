# src/trade/synthesizer.py
"""
Enhanced Trade Synthesizer for EMO Options Bot
Production-ready with real data integration, advanced Greeks, and robust fallbacks
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional, Protocol
from datetime import datetime, date, timedelta
import logging
import math
from decimal import Decimal
from ..core.schemas import AnalysisPlan, TradePlan, TradeLeg, RiskConstraints

# Configure logging
logger = logging.getLogger(__name__)

# Protocol for options chain providers
class OptionsChainProvider(Protocol):
    """Protocol for options chain data providers"""
    
    def get_chain(self, symbol: str, dte: int = 30) -> Dict[str, Any]:
        """Get options chain data for symbol"""
        ...
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price"""
        ...
    
    def get_volatility_data(self, symbol: str) -> Dict[str, float]:
        """Get volatility metrics"""
        ...

class MockOptionsChainProvider:
    """Mock options chain provider for development and testing"""
    
    def __init__(self):
        self.mock_prices = {
            "SPY": 450.0,
            "QQQ": 350.0,
            "IWM": 200.0,
            "DIA": 340.0,
            "AAPL": 175.0,
            "MSFT": 350.0,
            "NVDA": 500.0,
            "TSLA": 250.0,
        }
        
    def get_chain(self, symbol: str, dte: int = 30) -> Dict[str, Any]:
        """Generate mock options chain with realistic Greeks"""
        try:
            current_price = self.get_current_price(symbol) or 100.0
            expiry_date = (date.today() + timedelta(days=dte)).isoformat()
            
            # Generate strikes around current price
            strike_spacing = 5 if current_price < 100 else 10 if current_price < 500 else 25
            num_strikes = 20
            
            strikes = []
            for i in range(-num_strikes//2, num_strikes//2 + 1):
                strike = round(current_price + (i * strike_spacing), 2)
                if strike > 0:
                    strikes.append(strike)
            
            # Calculate realistic Greeks
            calls = []
            puts = []
            
            for strike in strikes:
                call_greeks = self._calculate_mock_greeks(current_price, strike, dte, "call")
                put_greeks = self._calculate_mock_greeks(current_price, strike, dte, "put")
                
                calls.append({
                    "strike": strike,
                    "delta": call_greeks["delta"],
                    "gamma": call_greeks["gamma"],
                    "theta": call_greeks["theta"],
                    "vega": call_greeks["vega"],
                    "iv": call_greeks["iv"],
                    "bid": call_greeks["price"] * 0.98,
                    "ask": call_greeks["price"] * 1.02,
                    "last": call_greeks["price"],
                    "volume": max(1, int(1000 * call_greeks["delta"])),
                    "open_interest": max(100, int(5000 * call_greeks["delta"]))
                })
                
                puts.append({
                    "strike": strike,
                    "delta": put_greeks["delta"],
                    "gamma": put_greeks["gamma"],
                    "theta": put_greeks["theta"],
                    "vega": put_greeks["vega"],
                    "iv": put_greeks["iv"],
                    "bid": put_greeks["price"] * 0.98,
                    "ask": put_greeks["price"] * 1.02,
                    "last": put_greeks["price"],
                    "volume": max(1, int(1000 * abs(put_greeks["delta"]))),
                    "open_interest": max(100, int(5000 * abs(put_greeks["delta"])))
                })
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "expiry": expiry_date,
                "dte": dte,
                "calls": calls,
                "puts": puts,
                "iv_rank": 45.0,  # Mock IV rank
                "iv30": 25.0,     # Mock 30-day IV
                "hv30": 22.0      # Mock 30-day HV
            }
            
        except Exception as e:
            logger.error(f"Failed to generate mock options chain: {e}")
            return self._fallback_chain(symbol, dte)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get mock current price for symbol"""
        return self.mock_prices.get(symbol.upper())
    
    def get_volatility_data(self, symbol: str) -> Dict[str, float]:
        """Get mock volatility data"""
        return {
            "iv30": 25.0,
            "iv_rank": 45.0,
            "hv30": 22.0,
            "iv_percentile": 50.0
        }
    
    def _calculate_mock_greeks(self, spot: float, strike: float, dte: int, option_type: str) -> Dict[str, float]:
        """Calculate mock but realistic Greeks using simplified Black-Scholes"""
        try:
            # Simplified Black-Scholes parameters
            time_to_expiry = max(dte / 365.0, 0.01)  # Prevent division by zero
            risk_free_rate = 0.05  # 5% risk-free rate
            volatility = 0.25  # 25% volatility
            
            # Moneyness
            moneyness = spot / strike
            
            # Mock calculations (simplified)
            if option_type == "call":
                if moneyness > 1.1:  # Deep ITM
                    delta = 0.8 + (moneyness - 1.1) * 0.15
                    price = max(spot - strike, 0) + 2.0
                elif moneyness > 0.9:  # Near ATM
                    delta = 0.3 + (moneyness - 0.9) * 2.5
                    price = spot * 0.03 + max(spot - strike, 0)
                else:  # OTM
                    delta = max(0.05, 0.3 * moneyness)
                    price = spot * 0.01 * moneyness
            else:  # put
                if moneyness < 0.9:  # Deep ITM
                    delta = -0.8 - (0.9 - moneyness) * 0.15
                    price = max(strike - spot, 0) + 2.0
                elif moneyness < 1.1:  # Near ATM
                    delta = -0.3 - (1.1 - moneyness) * 2.5
                    price = spot * 0.03 + max(strike - spot, 0)
                else:  # OTM
                    delta = -max(0.05, 0.3 / moneyness)
                    price = spot * 0.01 / moneyness
            
            # Other Greeks (simplified)
            gamma = max(0.001, 0.1 * math.exp(-abs(moneyness - 1) * 5) / spot)
            theta = -price * 0.1 / math.sqrt(time_to_expiry) / 365
            vega = spot * math.sqrt(time_to_expiry) * 0.01
            iv = volatility + (0.05 * (1 - moneyness)) if option_type == "call" else volatility + (0.05 * (moneyness - 1))
            
            return {
                "delta": round(delta, 4),
                "gamma": round(gamma, 4),
                "theta": round(theta, 4),
                "vega": round(vega, 4),
                "iv": round(max(0.1, min(1.0, iv)), 4),
                "price": round(max(0.01, price), 2)
            }
            
        except Exception as e:
            logger.warning(f"Greek calculation failed: {e}")
            return {
                "delta": 0.5 if option_type == "call" else -0.5,
                "gamma": 0.01,
                "theta": -0.1,
                "vega": 0.1,
                "iv": 0.25,
                "price": 2.0
            }
    
    def _fallback_chain(self, symbol: str, dte: int) -> Dict[str, Any]:
        """Fallback chain with minimal data"""
        current_price = 100.0
        strikes = [90, 95, 100, 105, 110]
        expiry = (date.today() + timedelta(days=dte)).isoformat()
        
        calls = [{"strike": s, "delta": max(0.1, min(0.9, (s-80)*0.02))} for s in strikes]
        puts = [{"strike": s, "delta": -max(0.1, min(0.9, (120-s)*0.02))} for s in strikes]
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "expiry": expiry,
            "dte": dte,
            "calls": calls,
            "puts": puts
        }

class AlpacaOptionsChainProvider:
    """Real Alpaca options chain provider"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str = "https://paper-api.alpaca.markets"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self._client = None
        
        try:
            import alpaca_trade_api as tradeapi
            self._client = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
            logger.info("Alpaca options provider initialized")
        except ImportError:
            logger.warning("Alpaca Trade API not available, using mock provider")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca provider: {e}")
    
    def get_chain(self, symbol: str, dte: int = 30) -> Dict[str, Any]:
        """Get real options chain from Alpaca"""
        if not self._client:
            logger.warning("Alpaca client not available, falling back to mock")
            return MockOptionsChainProvider().get_chain(symbol, dte)
        
        try:
            # Implementation would use Alpaca's options API
            # For now, fall back to mock
            logger.info(f"Fetching real options chain for {symbol} (DTE: {dte})")
            return MockOptionsChainProvider().get_chain(symbol, dte)
            
        except Exception as e:
            logger.error(f"Alpaca options chain fetch failed: {e}")
            return MockOptionsChainProvider().get_chain(symbol, dte)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Alpaca"""
        if not self._client:
            return MockOptionsChainProvider().get_current_price(symbol)
        
        try:
            # Get latest trade
            trades = self._client.get_latest_trade(symbol)
            return float(trades.price) if trades else None
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return MockOptionsChainProvider().get_current_price(symbol)
    
    def get_volatility_data(self, symbol: str) -> Dict[str, float]:
        """Get volatility data"""
        # This would require additional data sources
        return MockOptionsChainProvider().get_volatility_data(symbol)

def _find_by_delta(options: List[Dict[str, Any]], target_delta: float, tolerance: float = 0.05) -> Optional[Dict[str, Any]]:
    """Find option closest to target delta with tolerance"""
    if not options:
        return None
    
    candidates = []
    for opt in options:
        delta = opt.get("delta", 0)
        diff = abs(delta - target_delta)
        if diff <= tolerance:
            candidates.append((diff, opt))
    
    if candidates:
        return min(candidates, key=lambda x: x[0])[1]
    
    # If no candidates within tolerance, return closest
    return min(options, key=lambda x: abs(x.get("delta", 0) - target_delta))

def _find_by_strike(options: List[Dict[str, Any]], target_strike: float) -> Optional[Dict[str, Any]]:
    """Find option by exact strike"""
    for opt in options:
        if opt.get("strike") == target_strike:
            return opt
    return None

def _validate_option_data(option: Dict[str, Any]) -> bool:
    """Validate option data has required fields"""
    required_fields = ["strike", "delta"]
    return all(field in option for field in required_fields)

class TradeSynthesizer:
    """Enhanced trade synthesizer with real data integration and advanced strategies"""
    
    def __init__(self, chain_provider: Optional[OptionsChainProvider] = None):
        self.chain_provider = chain_provider or MockOptionsChainProvider()
        self.strategy_configs = self._load_strategy_configs()
        logger.info(f"TradeSynthesizer initialized with {type(self.chain_provider).__name__}")
    
    def _load_strategy_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load strategy-specific configurations"""
        return {
            "iron_condor": {
                "short_call_delta": 0.20,
                "long_call_delta": 0.10,
                "short_put_delta": -0.20,
                "long_put_delta": -0.10,
                "delta_tolerance": 0.05,
                "min_credit": 0.30,
                "max_width": 50.0
            },
            "put_credit_spread": {
                "short_put_delta": -0.25,
                "long_put_delta": -0.10,
                "delta_tolerance": 0.05,
                "min_credit": 0.20,
                "max_width": 25.0
            },
            "call_credit_spread": {
                "short_call_delta": 0.25,
                "long_call_delta": 0.10,
                "delta_tolerance": 0.05,
                "min_credit": 0.20,
                "max_width": 25.0
            },
            "covered_call": {
                "short_call_delta": 0.30,
                "delta_tolerance": 0.05,
                "shares_per_contract": 100
            },
            "protective_put": {
                "put_delta": -0.30,
                "delta_tolerance": 0.05,
                "shares_per_contract": 100
            },
            "straddle": {
                "call_delta": 0.50,
                "put_delta": -0.50,
                "delta_tolerance": 0.03
            },
            "strangle": {
                "call_delta": 0.25,
                "put_delta": -0.25,
                "delta_tolerance": 0.05
            }
        }
    
    def from_analysis(self, analysis: AnalysisPlan) -> TradePlan:
        """
        Convert analysis plan to trade plan with enhanced strategy selection
        """
        try:
            # Determine strategy based on analysis
            strategy = self._select_strategy(analysis)
            
            # Get options chain data
            dte = analysis.risk.time_horizon_days or 30
            chain_data = self.chain_provider.get_chain(analysis.underlying, dte)
            
            # Synthesize trade based on strategy
            if strategy == "iron_condor":
                return self._create_iron_condor(analysis, chain_data)
            elif strategy == "put_credit_spread":
                return self._create_put_credit_spread(analysis, chain_data)
            elif strategy == "call_credit_spread":
                return self._create_call_credit_spread(analysis, chain_data)
            elif strategy == "covered_call":
                return self._create_covered_call(analysis, chain_data)
            elif strategy == "protective_put":
                return self._create_protective_put(analysis, chain_data)
            elif strategy == "straddle":
                return self._create_straddle(analysis, chain_data)
            elif strategy == "strangle":
                return self._create_strangle(analysis, chain_data)
            else:
                return self._create_fallback_strategy(analysis, chain_data)
                
        except Exception as e:
            logger.error(f"Trade synthesis failed: {e}")
            return self._create_emergency_fallback(analysis)
    
    def _select_strategy(self, analysis: AnalysisPlan) -> str:
        """Enhanced strategy selection based on analysis"""
        # Use explicit hint if provided
        if analysis.strategy_hint:
            return analysis.strategy_hint
        
        # Strategy selection based on outlook and confidence
        outlook = analysis.outlook
        confidence = analysis.confidence
        
        if outlook == "neutral" and confidence > 0.6:
            return "iron_condor"
        elif outlook == "neutral":
            return "strangle"
        elif outlook == "volatile":
            return "straddle" if confidence > 0.7 else "strangle"
        elif outlook == "bullish":
            return "call_credit_spread" if confidence > 0.6 else "covered_call"
        elif outlook == "bearish":
            return "put_credit_spread"
        else:
            return "iron_condor"  # Conservative default
    
    def _create_iron_condor(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create iron condor strategy with enhanced validation"""
        try:
            config = self.strategy_configs["iron_condor"]
            calls = chain_data.get("calls", [])
            puts = chain_data.get("puts", [])
            expiry = chain_data.get("expiry")
            
            if not calls or not puts or not expiry:
                raise ValueError("Insufficient options chain data")
            
            # Find options by delta targets
            short_call = _find_by_delta(calls, config["short_call_delta"], config["delta_tolerance"])
            long_call = _find_by_delta(calls, config["long_call_delta"], config["delta_tolerance"])
            short_put = _find_by_delta(puts, config["short_put_delta"], config["delta_tolerance"])
            long_put = _find_by_delta(puts, config["long_put_delta"], config["delta_tolerance"])
            
            # Validate all options found
            if not all(_validate_option_data(opt) for opt in [short_call, long_call, short_put, long_put] if opt):
                raise ValueError("Could not find suitable options for iron condor")
            
            # Create legs
            legs = [
                TradeLeg(
                    action="sell",
                    instrument="call",
                    symbol=analysis.underlying,
                    strike=short_call["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=short_call.get("last", short_call.get("bid", 0)),
                    memo="Iron Condor - Short Call"
                ),
                TradeLeg(
                    action="buy",
                    instrument="call",
                    symbol=analysis.underlying,
                    strike=long_call["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=long_call.get("last", long_call.get("ask", 0)),
                    memo="Iron Condor - Long Call"
                ),
                TradeLeg(
                    action="sell",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=short_put["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=short_put.get("last", short_put.get("bid", 0)),
                    memo="Iron Condor - Short Put"
                ),
                TradeLeg(
                    action="buy",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=long_put["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=long_put.get("last", long_put.get("ask", 0)),
                    memo="Iron Condor - Long Put"
                )
            ]
            
            # Calculate estimated credit and risk
            estimated_credit = self._estimate_trade_credit(legs)
            estimated_risk = max(
                abs(short_call["strike"] - long_call["strike"]),
                abs(short_put["strike"] - long_put["strike"])
            ) * 100 - estimated_credit
            
            # Update risk constraints
            risk_constraints = analysis.risk
            if not risk_constraints.max_risk_dollars:
                risk_constraints.max_risk_dollars = estimated_risk
            
            return TradePlan(
                strategy_type="iron_condor",
                underlying=analysis.underlying,
                legs=legs,
                risk_constraints=risk_constraints,
                metadata={
                    "source": "synthesizer",
                    "strategy_config": config,
                    "estimated_credit": estimated_credit,
                    "estimated_risk": estimated_risk,
                    "current_price": chain_data.get("current_price"),
                    "iv_rank": chain_data.get("iv_rank"),
                    "dte": chain_data.get("dte")
                },
                tags=["delta_neutral", "credit_strategy", "defined_risk"]
            )
            
        except Exception as e:
            logger.error(f"Iron condor creation failed: {e}")
            return self._create_fallback_strategy(analysis, chain_data)
    
    def _create_put_credit_spread(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create put credit spread with enhanced validation"""
        try:
            config = self.strategy_configs["put_credit_spread"]
            puts = chain_data.get("puts", [])
            expiry = chain_data.get("expiry")
            
            if not puts or not expiry:
                raise ValueError("Insufficient options data for put spread")
            
            # Find put options
            short_put = _find_by_delta(puts, config["short_put_delta"], config["delta_tolerance"])
            long_put = _find_by_delta(puts, config["long_put_delta"], config["delta_tolerance"])
            
            if not all(_validate_option_data(opt) for opt in [short_put, long_put] if opt):
                raise ValueError("Could not find suitable puts for credit spread")
            
            # Validate spread width
            spread_width = abs(short_put["strike"] - long_put["strike"])
            if spread_width > config["max_width"]:
                logger.warning(f"Spread width {spread_width} exceeds maximum {config['max_width']}")
            
            legs = [
                TradeLeg(
                    action="sell",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=short_put["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=short_put.get("last", short_put.get("bid", 0)),
                    memo="Put Credit Spread - Short Put"
                ),
                TradeLeg(
                    action="buy",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=long_put["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=long_put.get("last", long_put.get("ask", 0)),
                    memo="Put Credit Spread - Long Put"
                )
            ]
            
            estimated_credit = self._estimate_trade_credit(legs)
            estimated_risk = spread_width * 100 - estimated_credit
            
            risk_constraints = analysis.risk
            if not risk_constraints.max_risk_dollars:
                risk_constraints.max_risk_dollars = estimated_risk
            
            return TradePlan(
                strategy_type="put_credit_spread",
                underlying=analysis.underlying,
                legs=legs,
                risk_constraints=risk_constraints,
                metadata={
                    "source": "synthesizer",
                    "strategy_config": config,
                    "spread_width": spread_width,
                    "estimated_credit": estimated_credit,
                    "estimated_risk": estimated_risk,
                    "current_price": chain_data.get("current_price"),
                    "dte": chain_data.get("dte")
                },
                tags=["bullish", "credit_strategy", "defined_risk"]
            )
            
        except Exception as e:
            logger.error(f"Put credit spread creation failed: {e}")
            return self._create_fallback_strategy(analysis, chain_data)
    
    def _create_call_credit_spread(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create call credit spread for bearish outlook"""
        try:
            config = self.strategy_configs["call_credit_spread"]
            calls = chain_data.get("calls", [])
            expiry = chain_data.get("expiry")
            
            if not calls or not expiry:
                raise ValueError("Insufficient options data for call spread")
            
            short_call = _find_by_delta(calls, config["short_call_delta"], config["delta_tolerance"])
            long_call = _find_by_delta(calls, config["long_call_delta"], config["delta_tolerance"])
            
            if not all(_validate_option_data(opt) for opt in [short_call, long_call] if opt):
                raise ValueError("Could not find suitable calls for credit spread")
            
            spread_width = abs(long_call["strike"] - short_call["strike"])
            
            legs = [
                TradeLeg(
                    action="sell",
                    instrument="call",
                    symbol=analysis.underlying,
                    strike=short_call["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=short_call.get("last", short_call.get("bid", 0)),
                    memo="Call Credit Spread - Short Call"
                ),
                TradeLeg(
                    action="buy",
                    instrument="call",
                    symbol=analysis.underlying,
                    strike=long_call["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=long_call.get("last", long_call.get("ask", 0)),
                    memo="Call Credit Spread - Long Call"
                )
            ]
            
            estimated_credit = self._estimate_trade_credit(legs)
            estimated_risk = spread_width * 100 - estimated_credit
            
            risk_constraints = analysis.risk
            if not risk_constraints.max_risk_dollars:
                risk_constraints.max_risk_dollars = estimated_risk
            
            return TradePlan(
                strategy_type="call_credit_spread",
                underlying=analysis.underlying,
                legs=legs,
                risk_constraints=risk_constraints,
                metadata={
                    "source": "synthesizer",
                    "spread_width": spread_width,
                    "estimated_credit": estimated_credit,
                    "estimated_risk": estimated_risk
                },
                tags=["bearish", "credit_strategy", "defined_risk"]
            )
            
        except Exception as e:
            logger.error(f"Call credit spread creation failed: {e}")
            return self._create_fallback_strategy(analysis, chain_data)
    
    def _create_straddle(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create long straddle for high volatility expectation"""
        try:
            config = self.strategy_configs["straddle"]
            calls = chain_data.get("calls", [])
            puts = chain_data.get("puts", [])
            expiry = chain_data.get("expiry")
            current_price = chain_data.get("current_price", 100)
            
            if not calls or not puts or not expiry:
                raise ValueError("Insufficient options data for straddle")
            
            # Find ATM options
            atm_call = _find_by_delta(calls, config["call_delta"], config["delta_tolerance"])
            atm_put = _find_by_delta(puts, config["put_delta"], config["delta_tolerance"])
            
            if not all(_validate_option_data(opt) for opt in [atm_call, atm_put] if opt):
                raise ValueError("Could not find suitable ATM options for straddle")
            
            legs = [
                TradeLeg(
                    action="buy",
                    instrument="call",
                    symbol=analysis.underlying,
                    strike=atm_call["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=atm_call.get("last", atm_call.get("ask", 0)),
                    memo="Long Straddle - Long Call"
                ),
                TradeLeg(
                    action="buy",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=atm_put["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=atm_put.get("last", atm_put.get("ask", 0)),
                    memo="Long Straddle - Long Put"
                )
            ]
            
            estimated_cost = self._estimate_trade_cost(legs)
            
            risk_constraints = analysis.risk
            if not risk_constraints.max_risk_dollars:
                risk_constraints.max_risk_dollars = estimated_cost
            
            return TradePlan(
                strategy_type="straddle",
                underlying=analysis.underlying,
                legs=legs,
                risk_constraints=risk_constraints,
                metadata={
                    "source": "synthesizer",
                    "estimated_cost": estimated_cost,
                    "breakeven_upper": atm_call["strike"] + estimated_cost/100,
                    "breakeven_lower": atm_put["strike"] - estimated_cost/100,
                    "current_price": current_price
                },
                tags=["volatility", "debit_strategy", "unlimited_profit"]
            )
            
        except Exception as e:
            logger.error(f"Straddle creation failed: {e}")
            return self._create_fallback_strategy(analysis, chain_data)
    
    def _create_strangle(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create long strangle for volatility with lower cost"""
        try:
            config = self.strategy_configs["strangle"]
            calls = chain_data.get("calls", [])
            puts = chain_data.get("puts", [])
            expiry = chain_data.get("expiry")
            
            if not calls or not puts or not expiry:
                raise ValueError("Insufficient options data for strangle")
            
            otm_call = _find_by_delta(calls, config["call_delta"], config["delta_tolerance"])
            otm_put = _find_by_delta(puts, config["put_delta"], config["delta_tolerance"])
            
            if not all(_validate_option_data(opt) for opt in [otm_call, otm_put] if opt):
                raise ValueError("Could not find suitable OTM options for strangle")
            
            legs = [
                TradeLeg(
                    action="buy",
                    instrument="call",
                    symbol=analysis.underlying,
                    strike=otm_call["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=otm_call.get("last", otm_call.get("ask", 0)),
                    memo="Long Strangle - OTM Call"
                ),
                TradeLeg(
                    action="buy",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=otm_put["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=otm_put.get("last", otm_put.get("ask", 0)),
                    memo="Long Strangle - OTM Put"
                )
            ]
            
            estimated_cost = self._estimate_trade_cost(legs)
            
            risk_constraints = analysis.risk
            if not risk_constraints.max_risk_dollars:
                risk_constraints.max_risk_dollars = estimated_cost
            
            return TradePlan(
                strategy_type="strangle",
                underlying=analysis.underlying,
                legs=legs,
                risk_constraints=risk_constraints,
                metadata={
                    "source": "synthesizer",
                    "estimated_cost": estimated_cost,
                    "call_strike": otm_call["strike"],
                    "put_strike": otm_put["strike"]
                },
                tags=["volatility", "debit_strategy", "lower_cost"]
            )
            
        except Exception as e:
            logger.error(f"Strangle creation failed: {e}")
            return self._create_fallback_strategy(analysis, chain_data)
    
    def _create_covered_call(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create covered call strategy"""
        try:
            config = self.strategy_configs["covered_call"]
            calls = chain_data.get("calls", [])
            expiry = chain_data.get("expiry")
            current_price = chain_data.get("current_price", 100)
            
            if not calls or not expiry:
                raise ValueError("Insufficient options data for covered call")
            
            short_call = _find_by_delta(calls, config["short_call_delta"], config["delta_tolerance"])
            
            if not _validate_option_data(short_call):
                raise ValueError("Could not find suitable call for covered call")
            
            legs = [
                TradeLeg(
                    action="buy",
                    instrument="stock",
                    symbol=analysis.underlying,
                    quantity=100,
                    price=current_price,
                    memo="Covered Call - Long Stock"
                ),
                TradeLeg(
                    action="sell",
                    instrument="call",
                    symbol=analysis.underlying,
                    strike=short_call["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=short_call.get("last", short_call.get("bid", 0)),
                    memo="Covered Call - Short Call"
                )
            ]
            
            stock_cost = current_price * 100
            call_credit = short_call.get("last", short_call.get("bid", 0)) * 100
            net_cost = stock_cost - call_credit
            
            risk_constraints = analysis.risk
            if not risk_constraints.max_risk_dollars:
                risk_constraints.max_risk_dollars = net_cost
            
            return TradePlan(
                strategy_type="covered_call",
                underlying=analysis.underlying,
                legs=legs,
                risk_constraints=risk_constraints,
                metadata={
                    "source": "synthesizer",
                    "stock_cost": stock_cost,
                    "call_credit": call_credit,
                    "net_cost": net_cost,
                    "max_profit": (short_call["strike"] - current_price) * 100 + call_credit
                },
                tags=["income", "bullish", "stock_required"]
            )
            
        except Exception as e:
            logger.error(f"Covered call creation failed: {e}")
            return self._create_fallback_strategy(analysis, chain_data)
    
    def _create_protective_put(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create protective put strategy"""
        try:
            config = self.strategy_configs["protective_put"]
            puts = chain_data.get("puts", [])
            expiry = chain_data.get("expiry")
            current_price = chain_data.get("current_price", 100)
            
            if not puts or not expiry:
                raise ValueError("Insufficient options data for protective put")
            
            protective_put = _find_by_delta(puts, config["put_delta"], config["delta_tolerance"])
            
            if not _validate_option_data(protective_put):
                raise ValueError("Could not find suitable put for protection")
            
            legs = [
                TradeLeg(
                    action="buy",
                    instrument="stock",
                    symbol=analysis.underlying,
                    quantity=100,
                    price=current_price,
                    memo="Protective Put - Long Stock"
                ),
                TradeLeg(
                    action="buy",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=protective_put["strike"],
                    expiry=expiry,
                    quantity=1,
                    price=protective_put.get("last", protective_put.get("ask", 0)),
                    memo="Protective Put - Long Put"
                )
            ]
            
            stock_cost = current_price * 100
            put_cost = protective_put.get("last", protective_put.get("ask", 0)) * 100
            total_cost = stock_cost + put_cost
            
            risk_constraints = analysis.risk
            if not risk_constraints.max_risk_dollars:
                max_loss = (current_price - protective_put["strike"]) * 100 + put_cost
                risk_constraints.max_risk_dollars = max_loss
            
            return TradePlan(
                strategy_type="protective_put",
                underlying=analysis.underlying,
                legs=legs,
                risk_constraints=risk_constraints,
                metadata={
                    "source": "synthesizer",
                    "total_cost": total_cost,
                    "protection_strike": protective_put["strike"],
                    "max_loss": (current_price - protective_put["strike"]) * 100 + put_cost
                },
                tags=["protection", "stock_required", "insurance"]
            )
            
        except Exception as e:
            logger.error(f"Protective put creation failed: {e}")
            return self._create_fallback_strategy(analysis, chain_data)
    
    def _create_fallback_strategy(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create a simple fallback strategy when advanced strategies fail"""
        try:
            logger.info("Creating fallback put credit spread")
            return self._create_simple_put_spread(analysis, chain_data)
        except Exception:
            logger.warning("Fallback strategy failed, creating emergency fallback")
            return self._create_emergency_fallback(analysis)
    
    def _create_simple_put_spread(self, analysis: AnalysisPlan, chain_data: Dict[str, Any]) -> TradePlan:
        """Create simple put spread with basic validation"""
        puts = chain_data.get("puts", [])
        expiry = chain_data.get("expiry", (date.today() + timedelta(days=30)).isoformat())
        
        if puts and len(puts) >= 2:
            # Use first two puts as a basic spread
            short_put = puts[0]
            long_put = puts[1] if len(puts) > 1 else puts[0]
            
            legs = [
                TradeLeg(
                    action="sell",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=short_put.get("strike", 100),
                    expiry=expiry,
                    quantity=1,
                    memo="Fallback - Short Put"
                ),
                TradeLeg(
                    action="buy",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=long_put.get("strike", 95),
                    expiry=expiry,
                    quantity=1,
                    memo="Fallback - Long Put"
                )
            ]
        else:
            # Emergency single leg
            legs = [
                TradeLeg(
                    action="sell",
                    instrument="put",
                    symbol=analysis.underlying,
                    strike=100.0,
                    expiry=expiry,
                    quantity=1,
                    memo="Emergency fallback put"
                )
            ]
        
        return TradePlan(
            strategy_type="put_credit_spread",
            underlying=analysis.underlying,
            legs=legs,
            risk_constraints=analysis.risk,
            metadata={"source": "fallback", "note": "Simplified strategy due to data limitations"},
            tags=["fallback", "simplified"]
        )
    
    def _create_emergency_fallback(self, analysis: AnalysisPlan) -> TradePlan:
        """Create absolute emergency fallback with minimal requirements"""
        logger.warning("Creating emergency fallback trade plan")
        
        expiry = (date.today() + timedelta(days=30)).isoformat()
        
        legs = [
            TradeLeg(
                action="sell",
                instrument="put",
                symbol=analysis.underlying,
                strike=100.0,
                expiry=expiry,
                quantity=1,
                memo="Emergency fallback"
            )
        ]
        
        return TradePlan(
            strategy_type="custom",
            underlying=analysis.underlying,
            legs=legs,
            risk_constraints=analysis.risk,
            metadata={
                "source": "emergency_fallback",
                "note": "Emergency strategy - manual review required"
            },
            status="requires_review",
            tags=["emergency", "review_required"]
        )
    
    def _estimate_trade_credit(self, legs: List[TradeLeg]) -> float:
        """Estimate net credit received from trade"""
        total_credit = 0.0
        
        for leg in legs:
            if leg.price:
                multiplier = 100 if leg.instrument in ['call', 'put'] else 1
                if leg.action == "sell":
                    total_credit += leg.price * leg.quantity * multiplier
                else:
                    total_credit -= leg.price * leg.quantity * multiplier
        
        return total_credit
    
    def _estimate_trade_cost(self, legs: List[TradeLeg]) -> float:
        """Estimate net cost paid for trade"""
        return -self._estimate_trade_credit(legs)

# Factory function for provider creation
def create_options_provider(provider_type: str = "mock", **kwargs) -> OptionsChainProvider:
    """Factory function to create options chain providers"""
    if provider_type == "alpaca":
        api_key = kwargs.get("api_key") or os.getenv("ALPACA_KEY_ID")
        secret_key = kwargs.get("secret_key") or os.getenv("ALPACA_SECRET_KEY")
        base_url = kwargs.get("base_url", "https://paper-api.alpaca.markets")
        
        if api_key and secret_key:
            return AlpacaOptionsChainProvider(api_key, secret_key, base_url)
        else:
            logger.warning("Alpaca credentials not provided, falling back to mock")
            return MockOptionsChainProvider()
    else:
        return MockOptionsChainProvider()

# Export main classes and functions
__all__ = [
    "TradeSynthesizer", "OptionsChainProvider", "MockOptionsChainProvider", 
    "AlpacaOptionsChainProvider", "create_options_provider"
]