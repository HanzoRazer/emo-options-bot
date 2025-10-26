"""
Trade Planner & Synthesizer - Phase 3 Implementation
Converts LLM trading analysis into executable trade plans with precise strike selection.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import math
from dataclasses import dataclass

from ..schemas import TradePlan, StrategySpec, StrategyType, OutlookType, RiskMetrics
from ..orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Current market data for trade planning"""
    symbol: str
    current_price: float
    iv_rank: float
    iv_percentile: float
    bid_ask_spread: float
    volume: int
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0

@dataclass
class OptionChain:
    """Option chain data for strike selection"""
    expiration: datetime
    calls: Dict[float, Dict]  # strike -> option data
    puts: Dict[float, Dict]   # strike -> option data
    dte: int  # days to expiration

class TradeSynthesizer:
    """
    Synthesizes executable trades from LLM analysis.
    Handles precise strike selection, position sizing, and risk constraints.
    """
    
    def __init__(self, orchestrator: LLMOrchestrator):
        self.orchestrator = orchestrator
        self.strategy_templates = self._load_strategy_templates()
        
    def _load_strategy_templates(self) -> Dict[StrategyType, Dict]:
        """Load strategy-specific templates and rules"""
        return {
            StrategyType.IRON_CONDOR: {
                "legs": 4,
                "structure": "sell_put_spread + sell_call_spread",
                "ideal_dte": 30,
                "target_delta": 0.16,  # ~16 delta short strikes
                "wing_width": 10,  # $10 wide spreads
                "min_premium": 1.50,  # Minimum credit received
                "max_width": 50,  # Maximum wing width
            },
            StrategyType.PUT_CREDIT_SPREAD: {
                "legs": 2,
                "structure": "sell_put + buy_put",
                "ideal_dte": 30,
                "target_delta": 0.20,  # ~20 delta short strike
                "default_width": 5,  # $5 wide spread
                "min_premium": 0.75,  # Minimum credit
                "max_width": 25,
            },
            StrategyType.COVERED_CALL: {
                "legs": 2,
                "structure": "long_stock + sell_call",
                "ideal_dte": 30,
                "target_delta": 0.30,  # ~30 delta call
                "min_premium": 0.50,
                "assignment_ok": True,
            },
            StrategyType.PROTECTIVE_PUT: {
                "legs": 2,
                "structure": "long_stock + long_put",
                "ideal_dte": 60,
                "target_delta": 0.20,  # ~20 delta put
                "protection_level": 0.90,  # Protect 90% of position
            },
            StrategyType.COLLAR: {
                "legs": 3,
                "structure": "long_stock + sell_call + long_put",
                "ideal_dte": 45,
                "call_delta": 0.25,
                "put_delta": 0.20,
                "net_credit": 0.0,  # Aim for net zero cost
            }
        }
    
    def synthesize_trade(self, 
                        trade_plan: TradePlan, 
                        market_data: MarketData,
                        option_chains: List[OptionChain],
                        account_equity: float = 100000) -> Dict:
        """
        Convert TradePlan into executable trade with precise strikes and sizing.
        
        Args:
            trade_plan: LLM-generated trade plan
            market_data: Current market data
            option_chains: Available option chains
            account_equity: Account size for position sizing
            
        Returns:
            Executable trade dictionary with legs, quantities, risk metrics
        """
        try:
            # 1. Validate strategy compatibility with market conditions
            strategy_template = self.strategy_templates.get(trade_plan.strategy.strategy_type)
            if not strategy_template:
                raise ValueError(f"No template for strategy: {trade_plan.strategy.strategy_type}")
            
            # 2. Select optimal expiration
            optimal_chain = self._select_expiration(
                option_chains, 
                strategy_template["ideal_dte"],
                trade_plan.strategy.time_horizon_days
            )
            
            # 3. Calculate strikes based on strategy and outlook
            strikes = self._calculate_strikes(
                trade_plan.strategy.strategy_type,
                trade_plan.strategy.outlook,
                market_data,
                optimal_chain,
                strategy_template
            )
            
            # 4. Build trade legs
            legs = self._build_trade_legs(
                trade_plan.strategy.strategy_type,
                strikes,
                optimal_chain,
                strategy_template
            )
            
            # 5. Calculate position sizing
            position_size = self._calculate_position_size(
                legs,
                trade_plan.risk_assessment.max_loss_pct,
                account_equity,
                market_data
            )
            
            # 6. Apply position sizing to legs
            sized_legs = self._apply_position_sizing(legs, position_size)
            
            # 7. Calculate trade metrics
            trade_metrics = self._calculate_trade_metrics(sized_legs, market_data)
            
            # 8. Generate executable trade
            executable_trade = {
                "symbol": market_data.symbol,
                "strategy_type": trade_plan.strategy.strategy_type.value,
                "legs": sized_legs,
                "position_size": position_size,
                "metrics": trade_metrics,
                "expiration": optimal_chain.expiration,
                "rationale": trade_plan.rationale.summary,
                "risk_constraints": {
                    "max_loss": trade_metrics["max_loss"],
                    "max_loss_pct": trade_plan.risk_assessment.max_loss_pct,
                    "pop": trade_metrics.get("probability_of_profit", 0.5),
                    "margin_requirement": trade_metrics.get("margin_requirement", 0)
                },
                "kill_switches": self._generate_kill_switches(trade_plan, trade_metrics),
                "created_at": datetime.now(),
                "plan_id": f"plan_{int(datetime.now().timestamp())}"
            }
            
            logger.info(f"Synthesized executable trade: {executable_trade['strategy_type']} "
                       f"for {executable_trade['symbol']} with {len(sized_legs)} legs")
            
            return executable_trade
            
        except Exception as e:
            logger.error(f"Failed to synthesize trade: {e}")
            raise
    
    def _select_expiration(self, 
                          chains: List[OptionChain], 
                          ideal_dte: int,
                          max_dte: Optional[int] = None) -> OptionChain:
        """Select optimal expiration based on strategy requirements"""
        if not chains:
            raise ValueError("No option chains available")
        
        # Filter chains within acceptable DTE range
        min_dte = max(7, ideal_dte - 15)  # Don't go below 7 days
        max_dte_limit = max_dte or (ideal_dte + 30)
        
        valid_chains = [
            chain for chain in chains
            if min_dte <= chain.dte <= max_dte_limit
        ]
        
        if not valid_chains:
            # Fallback to closest available
            return min(chains, key=lambda x: abs(x.dte - ideal_dte))
        
        # Select chain closest to ideal DTE
        return min(valid_chains, key=lambda x: abs(x.dte - ideal_dte))
    
    def _calculate_strikes(self,
                          strategy_type: StrategyType,
                          outlook: OutlookType,
                          market_data: MarketData,
                          option_chain: OptionChain,
                          template: Dict) -> Dict[str, float]:
        """Calculate optimal strikes for the strategy"""
        current_price = market_data.current_price
        strikes = {}
        
        if strategy_type == StrategyType.IRON_CONDOR:
            # Iron Condor: Sell puts/calls at ~16 delta, buy wings
            target_delta = template["target_delta"]
            wing_width = min(template["wing_width"], template["max_width"])
            
            # Find strikes closest to target delta
            put_strike = self._find_strike_by_delta(
                option_chain.puts, target_delta, "put"
            )
            call_strike = self._find_strike_by_delta(
                option_chain.calls, target_delta, "call"
            )
            
            strikes = {
                "short_put": put_strike,
                "long_put": put_strike - wing_width,
                "short_call": call_strike,
                "long_call": call_strike + wing_width
            }
            
        elif strategy_type == StrategyType.PUT_CREDIT_SPREAD:
            target_delta = template["target_delta"]
            width = template["default_width"]
            
            # Adjust for outlook
            if outlook == OutlookType.BULLISH:
                target_delta *= 0.8  # More aggressive (lower strike)
            elif outlook == OutlookType.BEARISH:
                target_delta *= 1.2  # More conservative (higher strike)
            
            short_put = self._find_strike_by_delta(
                option_chain.puts, target_delta, "put"
            )
            
            strikes = {
                "short_put": short_put,
                "long_put": short_put - width
            }
            
        elif strategy_type == StrategyType.COVERED_CALL:
            target_delta = template["target_delta"]
            
            # Adjust call strike based on outlook
            if outlook == OutlookType.BULLISH:
                target_delta *= 0.7  # Higher strike (less likely assignment)
            elif outlook == OutlookType.NEUTRAL:
                target_delta *= 1.0  # Target strike
            
            call_strike = self._find_strike_by_delta(
                option_chain.calls, target_delta, "call"
            )
            
            strikes = {
                "stock": current_price,
                "short_call": call_strike
            }
            
        elif strategy_type == StrategyType.PROTECTIVE_PUT:
            protection_level = template["protection_level"]
            put_strike = current_price * protection_level
            
            # Find closest available strike
            available_strikes = list(option_chain.puts.keys())
            put_strike = min(available_strikes, key=lambda x: abs(x - put_strike))
            
            strikes = {
                "stock": current_price,
                "long_put": put_strike
            }
            
        elif strategy_type == StrategyType.COLLAR:
            call_delta = template["call_delta"]
            put_delta = template["put_delta"]
            
            call_strike = self._find_strike_by_delta(
                option_chain.calls, call_delta, "call"
            )
            put_strike = self._find_strike_by_delta(
                option_chain.puts, put_delta, "put"
            )
            
            strikes = {
                "stock": current_price,
                "short_call": call_strike,
                "long_put": put_strike
            }
        
        logger.debug(f"Calculated strikes for {strategy_type}: {strikes}")
        return strikes
    
    def _find_strike_by_delta(self, 
                             options: Dict[float, Dict], 
                             target_delta: float, 
                             option_type: str) -> float:
        """Find strike closest to target delta"""
        if not options:
            raise ValueError(f"No {option_type} options available")
        
        best_strike = None
        best_delta_diff = float('inf')
        
        for strike, option_data in options.items():
            option_delta = abs(option_data.get('delta', 0))
            
            # For puts, delta is negative, so we compare absolute values
            if option_type == "put":
                delta_diff = abs(option_delta - target_delta)
            else:
                delta_diff = abs(option_delta - target_delta)
            
            if delta_diff < best_delta_diff:
                best_delta_diff = delta_diff
                best_strike = strike
        
        if best_strike is None:
            # Fallback to middle strike
            strikes = list(options.keys())
            best_strike = strikes[len(strikes) // 2]
        
        return best_strike
    
    def _build_trade_legs(self,
                         strategy_type: StrategyType,
                         strikes: Dict[str, float],
                         option_chain: OptionChain,
                         template: Dict) -> List[Dict]:
        """Build individual trade legs"""
        legs = []
        
        if strategy_type == StrategyType.IRON_CONDOR:
            legs = [
                {
                    "action": "sell",
                    "instrument": "put",
                    "strike": strikes["short_put"],
                    "expiration": option_chain.expiration,
                    "quantity": 1  # Will be sized later
                },
                {
                    "action": "buy",
                    "instrument": "put", 
                    "strike": strikes["long_put"],
                    "expiration": option_chain.expiration,
                    "quantity": 1
                },
                {
                    "action": "sell",
                    "instrument": "call",
                    "strike": strikes["short_call"],
                    "expiration": option_chain.expiration,
                    "quantity": 1
                },
                {
                    "action": "buy",
                    "instrument": "call",
                    "strike": strikes["long_call"],
                    "expiration": option_chain.expiration,
                    "quantity": 1
                }
            ]
            
        elif strategy_type == StrategyType.PUT_CREDIT_SPREAD:
            legs = [
                {
                    "action": "sell",
                    "instrument": "put",
                    "strike": strikes["short_put"],
                    "expiration": option_chain.expiration,
                    "quantity": 1
                },
                {
                    "action": "buy",
                    "instrument": "put",
                    "strike": strikes["long_put"],
                    "expiration": option_chain.expiration,
                    "quantity": 1
                }
            ]
            
        elif strategy_type == StrategyType.COVERED_CALL:
            legs = [
                {
                    "action": "buy",
                    "instrument": "stock",
                    "strike": strikes["stock"],
                    "quantity": 100  # Standard lot
                },
                {
                    "action": "sell",
                    "instrument": "call",
                    "strike": strikes["short_call"],
                    "expiration": option_chain.expiration,
                    "quantity": 1
                }
            ]
            
        # Add pricing data to legs
        for leg in legs:
            if leg["instrument"] in ["put", "call"]:
                leg.update(self._get_option_pricing(leg, option_chain))
        
        return legs
    
    def _get_option_pricing(self, leg: Dict, option_chain: OptionChain) -> Dict:
        """Get pricing data for option leg"""
        option_type = leg["instrument"]
        strike = leg["strike"]
        
        options = option_chain.calls if option_type == "call" else option_chain.puts
        option_data = options.get(strike, {})
        
        return {
            "bid": option_data.get("bid", 0),
            "ask": option_data.get("ask", 0),
            "last": option_data.get("last", 0),
            "volume": option_data.get("volume", 0),
            "open_interest": option_data.get("open_interest", 0),
            "delta": option_data.get("delta", 0),
            "gamma": option_data.get("gamma", 0),
            "theta": option_data.get("theta", 0),
            "vega": option_data.get("vega", 0),
            "implied_volatility": option_data.get("iv", 0)
        }
    
    def _calculate_position_size(self,
                                legs: List[Dict],
                                max_loss_pct: float,
                                account_equity: float,
                                market_data: MarketData) -> int:
        """Calculate appropriate position size based on risk constraints"""
        # Calculate max loss per unit
        max_loss_per_unit = self._calculate_max_loss_per_unit(legs)
        
        # Calculate max allowable loss
        max_allowable_loss = account_equity * (max_loss_pct / 100)
        
        # Calculate position size
        if max_loss_per_unit > 0:
            position_size = int(max_allowable_loss / max_loss_per_unit)
        else:
            # For strategies with undefined risk, use conservative sizing
            position_size = 1
        
        # Apply minimum/maximum constraints
        position_size = max(1, position_size)  # At least 1 contract
        position_size = min(position_size, 50)  # Max 50 contracts for safety
        
        logger.debug(f"Position sizing: max_loss_per_unit=${max_loss_per_unit:.2f}, "
                    f"max_allowable_loss=${max_allowable_loss:.2f}, "
                    f"position_size={position_size}")
        
        return position_size
    
    def _calculate_max_loss_per_unit(self, legs: List[Dict]) -> float:
        """Calculate maximum loss per unit for the strategy"""
        total_debit = 0
        total_credit = 0
        max_spread_width = 0
        
        for leg in legs:
            if leg["instrument"] in ["put", "call"]:
                price = (leg.get("bid", 0) + leg.get("ask", 0)) / 2
                if leg["action"] == "buy":
                    total_debit += price * 100  # Options are per 100 shares
                else:
                    total_credit += price * 100
                    
        # For spreads, calculate max spread width
        strikes = [leg.get("strike", 0) for leg in legs if leg["instrument"] in ["put", "call"]]
        if len(strikes) >= 2:
            max_spread_width = (max(strikes) - min(strikes)) * 100
        
        # Strategy-specific max loss calculation
        net_credit = total_credit - total_debit
        
        if net_credit > 0:
            # Credit strategy: max loss = spread width - credit received
            max_loss = max_spread_width - net_credit
        else:
            # Debit strategy: max loss = debit paid
            max_loss = abs(net_credit)
        
        return max(max_loss, 0)
    
    def _apply_position_sizing(self, legs: List[Dict], position_size: int) -> List[Dict]:
        """Apply position sizing to all legs"""
        sized_legs = []
        
        for leg in legs.copy():
            sized_leg = leg.copy()
            
            if leg["instrument"] == "stock":
                # Stock legs: scale by position size * 100
                sized_leg["quantity"] = leg["quantity"] * position_size
            else:
                # Option legs: scale by position size
                sized_leg["quantity"] = leg["quantity"] * position_size
            
            sized_legs.append(sized_leg)
        
        return sized_legs
    
    def _calculate_trade_metrics(self, legs: List[Dict], market_data: MarketData) -> Dict:
        """Calculate comprehensive trade metrics"""
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        net_credit = 0
        margin_requirement = 0
        
        for leg in legs:
            quantity = leg["quantity"]
            
            if leg["instrument"] in ["put", "call"]:
                # Option metrics
                delta = leg.get("delta", 0) * quantity
                gamma = leg.get("gamma", 0) * quantity
                theta = leg.get("theta", 0) * quantity
                vega = leg.get("vega", 0) * quantity
                
                # Adjust signs for buy/sell
                multiplier = -1 if leg["action"] == "sell" else 1
                total_delta += delta * multiplier
                total_gamma += gamma * multiplier
                total_theta += theta * multiplier
                total_vega += vega * multiplier
                
                # Calculate net credit/debit
                price = (leg.get("bid", 0) + leg.get("ask", 0)) / 2
                credit = price * quantity * 100 * multiplier * -1  # Sell = credit
                net_credit += credit
                
                # Estimate margin (simplified)
                if leg["action"] == "sell":
                    margin_requirement += price * quantity * 100 * 0.2  # 20% margin
                    
            elif leg["instrument"] == "stock":
                # Stock position
                total_delta += quantity  # 100 shares = 1.0 delta per contract
                net_credit -= market_data.current_price * quantity  # Stock purchase
        
        # Calculate probability of profit (simplified estimate)
        pop = 0.5  # Default 50%
        if abs(total_delta) < 10:  # Relatively delta neutral
            pop = 0.65
        elif total_delta > 0:  # Bullish
            pop = 0.55
        else:  # Bearish
            pop = 0.55
        
        max_loss = self._calculate_max_loss_per_unit([leg for leg in legs if leg["quantity"] == 1])
        max_loss *= legs[0]["quantity"]  # Scale by actual position size
        
        return {
            "net_credit": round(net_credit, 2),
            "total_delta": round(total_delta, 4),
            "total_gamma": round(total_gamma, 4),
            "total_theta": round(total_theta, 4),
            "total_vega": round(total_vega, 4),
            "max_loss": round(max_loss, 2),
            "margin_requirement": round(margin_requirement, 2),
            "probability_of_profit": round(pop, 3),
            "break_even_points": [],  # TODO: Calculate break-evens
            "days_to_expiration": legs[0].get("expiration", datetime.now()).day if legs else 0
        }
    
    def _generate_kill_switches(self, trade_plan: TradePlan, metrics: Dict) -> List[Dict]:
        """Generate automated kill switches for risk management"""
        kill_switches = []
        
        # Profit target
        if metrics.get("net_credit", 0) > 0:
            profit_target = metrics["net_credit"] * 0.5  # 50% profit target
            kill_switches.append({
                "type": "profit_target",
                "condition": f"unrealized_pnl >= {profit_target}",
                "action": "close_position",
                "description": f"Close at 50% profit (${profit_target:.2f})"
            })
        
        # Stop loss
        max_loss = metrics.get("max_loss", 0)
        if max_loss > 0:
            stop_loss = max_loss * 0.75  # Stop at 75% of max loss
            kill_switches.append({
                "type": "stop_loss",
                "condition": f"unrealized_loss >= {stop_loss}",
                "action": "close_position", 
                "description": f"Stop loss at ${stop_loss:.2f}"
            })
        
        # Time decay
        kill_switches.append({
            "type": "time_decay",
            "condition": "days_to_expiration <= 7",
            "action": "close_position",
            "description": "Close position with 7 days to expiration"
        })
        
        # Delta threshold
        if abs(metrics.get("total_delta", 0)) > 0:
            delta_threshold = abs(metrics["total_delta"]) * 2
            kill_switches.append({
                "type": "delta_threshold",
                "condition": f"abs(total_delta) >= {delta_threshold}",
                "action": "hedge_delta",
                "description": f"Hedge when delta exceeds ±{delta_threshold:.2f}"
            })
        
        return kill_switches

# Example usage
if __name__ == "__main__":
    # This would typically be called by the main system
    pass