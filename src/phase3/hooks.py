# src/phase3/hooks.py
"""
Enhanced Phase 3 Integration Hooks
Production-ready orchestration with comprehensive error handling and fallbacks
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Import our enhanced modules
try:
    from src.options.chain_providers import OptionsChainProvider, OptionQuote
    from src.risk.math import Leg, iron_condor_risk, vertical_spread_risk, calculate_position_risk
    from src.ai.json_orchestrator import analyze_request_to_json, AnalysisPlan, TradeIdea
    from src.staging.writer import stage_trade, validate_trade_plan
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

class OptionsChainIntegrator:
    """Enhanced options chain integration with intelligent selection"""
    
    def __init__(self, chain_provider: Optional[OptionsChainProvider] = None):
        self.chain_provider = chain_provider or OptionsChainProvider()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_chain_with_cache(
        self, 
        symbol: str, 
        expiry: Optional[str] = None
    ) -> List[OptionQuote]:
        """Get options chain with caching"""
        cache_key = f"{symbol}_{expiry or 'auto'}"
        now = datetime.utcnow()
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (now - timestamp).total_seconds() < self.cache_ttl:
                logger.debug(f"Using cached chain for {symbol}")
                return cached_data
        
        # Fetch fresh data
        try:
            chain = self.chain_provider.get_chain(symbol, expiry)
            self.cache[cache_key] = (chain, now)
            logger.info(f"Fetched fresh chain for {symbol}: {len(chain)} quotes")
            return chain
        except Exception as e:
            logger.error(f"Error fetching options chain for {symbol}: {e}")
            return []
    
    def get_spot_price(self, symbol: str) -> Optional[float]:
        """Get current spot price with caching"""
        cache_key = f"spot_{symbol}"
        now = datetime.utcnow()
        
        # Check cache (shorter TTL for spot prices)
        if cache_key in self.cache:
            cached_price, timestamp = self.cache[cache_key]
            if (now - timestamp).total_seconds() < 60:  # 1 minute TTL
                return cached_price
        
        try:
            price = self.chain_provider.get_spot_price(symbol)
            if price:
                self.cache[cache_key] = (price, now)
            return price
        except Exception as e:
            logger.error(f"Error getting spot price for {symbol}: {e}")
            return None
    
    def select_strikes_by_delta(
        self, 
        chain: List[OptionQuote], 
        target_delta: float, 
        right: str
    ) -> List[OptionQuote]:
        """Select strikes by target delta"""
        try:
            # Filter by option type and ensure delta is available
            candidates = [
                quote for quote in chain 
                if quote.right == right and quote.delta is not None
            ]
            
            if not candidates:
                logger.warning(f"No {right} options with delta found")
                return []
            
            # Sort by delta proximity to target
            candidates.sort(key=lambda q: abs(abs(q.delta) - target_delta))
            
            # Return top candidates
            return candidates[:5]  # Top 5 closest
            
        except Exception as e:
            logger.error(f"Error selecting strikes by delta: {e}")
            return []
    
    def select_strikes_by_moneyness(
        self, 
        chain: List[OptionQuote], 
        spot_price: float, 
        moneyness_range: Tuple[float, float] = (0.95, 1.05)
    ) -> List[OptionQuote]:
        """Select strikes by moneyness (proximity to spot)"""
        try:
            min_moneyness, max_moneyness = moneyness_range
            
            candidates = []
            for quote in chain:
                moneyness = spot_price / quote.strike
                if min_moneyness <= moneyness <= max_moneyness:
                    candidates.append(quote)
            
            # Sort by proximity to ATM
            candidates.sort(key=lambda q: abs(spot_price - q.strike))
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error selecting strikes by moneyness: {e}")
            return []

def build_iron_condor_legs(
    chain: List[OptionQuote], 
    trade_idea: TradeIdea, 
    spot_price: float
) -> List[Leg]:
    """
    Build iron condor legs with intelligent strike selection
    
    Args:
        chain: Available option quotes
        trade_idea: Trade parameters from AI analysis
        spot_price: Current underlying price
    
    Returns:
        List of Leg objects for the iron condor
    """
    try:
        integrator = OptionsChainIntegrator()
        
        # Separate calls and puts
        calls = [q for q in chain if q.right == "call"]
        puts = [q for q in chain if q.right == "put"]
        
        if not calls or not puts:
            raise ValueError("Insufficient options data for iron condor")
        
        # Target delta for short strikes
        target_delta = abs(trade_idea.target_delta or 0.15)
        
        # Select short strikes by delta
        short_call_candidates = integrator.select_strikes_by_delta(calls, target_delta, "call")
        short_put_candidates = integrator.select_strikes_by_delta(puts, target_delta, "put")
        
        if not short_call_candidates or not short_put_candidates:
            # Fallback: select by moneyness
            logger.warning("Delta selection failed, using moneyness")
            short_call_candidates = integrator.select_strikes_by_moneyness(
                calls, spot_price, (1.02, 1.10)
            )
            short_put_candidates = integrator.select_strikes_by_moneyness(
                puts, spot_price, (0.90, 0.98)
            )
        
        if not short_call_candidates or not short_put_candidates:
            raise ValueError("Could not select appropriate short strikes")
        
        # Select best short strikes
        short_call = short_call_candidates[0]
        short_put = short_put_candidates[0]
        
        # Calculate wing positions
        wings_width = trade_idea.wings_width or 5.0
        long_call_strike = short_call.strike + wings_width
        long_put_strike = short_put.strike - wings_width
        
        # Find long strikes (closest available)
        long_call = min(
            calls, 
            key=lambda q: abs(q.strike - long_call_strike)
        )
        long_put = min(
            puts,
            key=lambda q: abs(q.strike - long_put_strike)
        )
        
        # Build legs
        legs = [
            # Short put (receive premium)
            Leg(
                right="put",
                strike=short_put.strike,
                qty=-1,  # Short position
                price=short_put.mid,
                delta=short_put.delta,
                gamma=short_put.gamma,
                theta=short_put.theta,
                vega=short_put.vega,
                symbol=short_put.symbol,
                expiry=short_put.expiry
            ),
            # Long put (pay premium)
            Leg(
                right="put",
                strike=long_put.strike,
                qty=1,  # Long position
                price=long_put.mid,
                delta=long_put.delta,
                gamma=long_put.gamma,
                theta=long_put.theta,
                vega=long_put.vega,
                symbol=long_put.symbol,
                expiry=long_put.expiry
            ),
            # Short call (receive premium)
            Leg(
                right="call",
                strike=short_call.strike,
                qty=-1,  # Short position
                price=short_call.mid,
                delta=short_call.delta,
                gamma=short_call.gamma,
                theta=short_call.theta,
                vega=short_call.vega,
                symbol=short_call.symbol,
                expiry=short_call.expiry
            ),
            # Long call (pay premium)
            Leg(
                right="call",
                strike=long_call.strike,
                qty=1,  # Long position
                price=long_call.mid,
                delta=long_call.delta,
                gamma=long_call.gamma,
                theta=long_call.theta,
                vega=long_call.vega,
                symbol=long_call.symbol,
                expiry=long_call.expiry
            )
        ]
        
        logger.info(f"Built iron condor: Put spread {long_put.strike}-{short_put.strike}, Call spread {short_call.strike}-{long_call.strike}")
        return legs
        
    except Exception as e:
        logger.error(f"Error building iron condor legs: {e}")
        raise

def build_vertical_spread_legs(
    chain: List[OptionQuote],
    trade_idea: TradeIdea,
    spot_price: float,
    analysis_plan: AnalysisPlan
) -> List[Leg]:
    """Build vertical spread legs based on outlook"""
    try:
        outlook = analysis_plan.outlook
        strategy = trade_idea.strategy
        
        # Determine spread type
        if "put" in strategy.lower():
            option_type = "put"
            options = [q for q in chain if q.right == "put"]
        else:
            option_type = "call" 
            options = [q for q in chain if q.right == "call"]
        
        if not options:
            raise ValueError(f"No {option_type} options available")
        
        # Select strikes based on outlook and credit/debit preference
        target_delta = abs(trade_idea.target_delta or 0.20)
        
        if "credit" in strategy.lower():
            # Credit spread: sell higher delta, buy lower delta
            if option_type == "call":
                # Call credit spread (bearish): sell lower strike, buy higher strike
                short_strike_candidates = [q for q in options if q.delta and abs(q.delta) >= target_delta]
                short_strike = min(short_strike_candidates, key=lambda q: q.strike) if short_strike_candidates else options[0]
                
                wings_width = trade_idea.wings_width or 5.0
                long_strike_target = short_strike.strike + wings_width
                long_strike = min(options, key=lambda q: abs(q.strike - long_strike_target))
            else:
                # Put credit spread (bullish): sell higher strike, buy lower strike  
                short_strike_candidates = [q for q in options if q.delta and abs(q.delta) >= target_delta]
                short_strike = max(short_strike_candidates, key=lambda q: q.strike) if short_strike_candidates else options[0]
                
                wings_width = trade_idea.wings_width or 5.0
                long_strike_target = short_strike.strike - wings_width
                long_strike = min(options, key=lambda q: abs(q.strike - long_strike_target))
            
            # Build credit spread legs
            legs = [
                Leg(
                    right=option_type,
                    strike=short_strike.strike,
                    qty=-1,  # Short
                    price=short_strike.mid,
                    delta=short_strike.delta,
                    gamma=short_strike.gamma,
                    theta=short_strike.theta,
                    vega=short_strike.vega,
                    symbol=short_strike.symbol,
                    expiry=short_strike.expiry
                ),
                Leg(
                    right=option_type,
                    strike=long_strike.strike,
                    qty=1,  # Long
                    price=long_strike.mid,
                    delta=long_strike.delta,
                    gamma=long_strike.gamma,
                    theta=long_strike.theta,
                    vega=long_strike.vega,
                    symbol=long_strike.symbol,
                    expiry=long_strike.expiry
                )
            ]
        else:
            # Debit spread: buy higher delta, sell lower delta
            # Implementation for debit spreads
            primary_candidates = [q for q in options if q.delta and abs(q.delta) >= target_delta]
            if not primary_candidates:
                primary_candidates = options
            
            primary_strike = primary_candidates[0]
            
            wings_width = trade_idea.wings_width or 5.0
            if option_type == "call":
                secondary_target = primary_strike.strike + wings_width
            else:
                secondary_target = primary_strike.strike - wings_width
            
            secondary_strike = min(options, key=lambda q: abs(q.strike - secondary_target))
            
            legs = [
                Leg(
                    right=option_type,
                    strike=primary_strike.strike,
                    qty=1,  # Long
                    price=primary_strike.mid,
                    delta=primary_strike.delta,
                    gamma=primary_strike.gamma,
                    theta=primary_strike.theta,
                    vega=primary_strike.vega,
                    symbol=primary_strike.symbol,
                    expiry=primary_strike.expiry
                ),
                Leg(
                    right=option_type,
                    strike=secondary_strike.strike,
                    qty=-1,  # Short
                    price=secondary_strike.mid,
                    delta=secondary_strike.delta,
                    gamma=secondary_strike.gamma,
                    theta=secondary_strike.theta,
                    vega=secondary_strike.vega,
                    symbol=secondary_strike.symbol,
                    expiry=secondary_strike.expiry
                )
            ]
        
        logger.info(f"Built {strategy}: {legs[0].strike}-{legs[1].strike} {option_type} spread")
        return legs
        
    except Exception as e:
        logger.error(f"Error building vertical spread legs: {e}")
        raise

def enhanced_synthesis_pipeline(
    user_text: str, 
    options_override: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Enhanced synthesis pipeline with comprehensive error handling
    
    Args:
        user_text: User's trading request
        options_override: Override options for testing/customization
    
    Returns:
        Complete synthesis result with trade plan and metadata
    """
    try:
        logger.info(f"Starting enhanced synthesis for: {user_text[:100]}...")
        
        # Step 1: AI Analysis
        logger.debug("Step 1: Analyzing user intent")
        analysis_plan, trade_idea = analyze_request_to_json(user_text)
        
        logger.info(f"Analysis: {analysis_plan.symbol} {analysis_plan.outlook} -> {trade_idea.strategy}")
        
        # Step 2: Options Chain Retrieval
        logger.debug("Step 2: Retrieving options chain")
        integrator = OptionsChainIntegrator()
        
        # Override for testing
        symbol = options_override.get("symbol", analysis_plan.symbol) if options_override else analysis_plan.symbol
        expiry = options_override.get("expiry", trade_idea.expiry) if options_override else trade_idea.expiry
        
        chain = integrator.get_chain_with_cache(symbol, expiry)
        if not chain:
            raise RuntimeError(f"No options chain available for {symbol}")
        
        spot_price = integrator.get_spot_price(symbol)
        if not spot_price:
            raise RuntimeError(f"Could not get spot price for {symbol}")
        
        logger.info(f"Retrieved chain: {len(chain)} quotes, spot: ${spot_price:.2f}")
        
        # Step 3: Strategy Implementation
        logger.debug("Step 3: Building option legs")
        
        if trade_idea.strategy == "iron_condor":
            legs = build_iron_condor_legs(chain, trade_idea, spot_price)
            risk_profile = iron_condor_risk(legs)
        elif "spread" in trade_idea.strategy:
            legs = build_vertical_spread_legs(chain, trade_idea, spot_price, analysis_plan)
            risk_profile = vertical_spread_risk(legs)
        else:
            # Fallback for other strategies
            logger.warning(f"Strategy {trade_idea.strategy} not fully implemented, using simple approach")
            # Create a simple long call/put based on outlook
            option_type = "call" if analysis_plan.outlook == "bullish" else "put"
            options = [q for q in chain if q.right == option_type]
            
            if not options:
                raise ValueError(f"No {option_type} options available")
            
            # Select ATM or nearest
            best_option = min(options, key=lambda q: abs(q.strike - spot_price))
            
            legs = [Leg(
                right=option_type,
                strike=best_option.strike,
                qty=1,
                price=best_option.mid,
                delta=best_option.delta,
                gamma=best_option.gamma,
                theta=best_option.theta,
                vega=best_option.vega,
                symbol=best_option.symbol,
                expiry=best_option.expiry
            )]
            
            risk_profile = calculate_position_risk(legs, trade_idea.strategy)
        
        # Step 4: Create Trade Plan
        logger.debug("Step 4: Creating trade plan")
        trade_plan = {
            "symbol": symbol,
            "strategy": trade_idea.strategy,
            "legs": [leg.to_dict() for leg in legs],
            "risk": risk_profile.to_dict(),
            "analysis": analysis_plan.to_dict(),
            "trade_idea": trade_idea.to_dict(),
            "market_data": {
                "spot_price": spot_price,
                "chain_size": len(chain),
                "expiry": legs[0].expiry if legs else None
            },
            "notes": analysis_plan.notes + (trade_idea.comments or [])
        }
        
        # Step 5: Validation
        logger.debug("Step 5: Validating trade plan")
        validation_errors = validate_trade_plan(trade_plan)
        if validation_errors:
            logger.warning(f"Trade plan validation issues: {', '.join(validation_errors)}")
        
        # Step 6: Return complete result
        result = {
            "trade_plan": trade_plan,
            "analysis_plan": analysis_plan.to_dict(),
            "trade_idea": trade_idea.to_dict(),
            "risk_profile": risk_profile.to_dict(),
            "market_data": {
                "symbol": symbol,
                "spot_price": spot_price,
                "chain_quotes": len(chain),
                "expiry_used": legs[0].expiry if legs else None
            },
            "validation": {
                "passed": len(validation_errors) == 0,
                "errors": validation_errors
            },
            "synthesis_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "provider_used": analysis_plan.source,
                "confidence": analysis_plan.confidence,
                "complexity": trade_idea.complexity_score(),
                "risk_grade": risk_profile.risk_grade()
            }
        }
        
        logger.info(f"Synthesis complete: {trade_idea.strategy} with {len(legs)} legs, max risk ${risk_profile.max_loss:.0f}")
        return result
        
    except Exception as e:
        logger.error(f"Enhanced synthesis pipeline failed: {e}")
        
        # Return error result with safe fallback
        return {
            "error": str(e),
            "fallback_used": True,
            "trade_plan": None,
            "synthesis_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "user_input": user_text[:200]
            }
        }

def synthesize_and_stage(
    user_text: str, 
    spot: Optional[float] = None,
    auto_stage: bool = True
) -> str:
    """
    Legacy compatibility function with enhanced features
    
    Args:
        user_text: User's trading request
        spot: Override spot price (for compatibility)
        auto_stage: Whether to automatically stage successful trades
    
    Returns:
        Path to staged trade file or error message
    """
    try:
        # Use enhanced pipeline
        result = enhanced_synthesis_pipeline(user_text)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        if not auto_stage:
            return "Trade synthesis complete (not staged)"
        
        # Stage the trade
        trade_plan = result["trade_plan"]
        metadata = {
            "source": "phase3/hooks.py",
            "synthesis_result": result["synthesis_metadata"],
            "confidence_score": result["analysis_plan"].get("confidence", 0.7)
        }
        
        staged_path = stage_trade(trade_plan, metadata)
        
        logger.info(f"Trade synthesized and staged: {staged_path}")
        return str(staged_path)
        
    except Exception as e:
        error_msg = f"Synthesis and staging failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Export main functions
__all__ = [
    "synthesize_and_stage",
    "enhanced_synthesis_pipeline",
    "OptionsChainIntegrator",
    "build_iron_condor_legs",
    "build_vertical_spread_legs"
]