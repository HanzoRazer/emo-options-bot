#!/usr/bin/env python3
"""
Enhanced ML Retraining with Risk Management Integration
Incorporates risk metrics and market regime into ML predictions.
"""

from __future__ import annotations
import sqlite3, json, os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Import risk management
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.logic.risk_manager import RiskManager, OrderIntent
from src.database.enhanced_data_collector import EnhancedDataCollector

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "emo.sqlite"
ML_OUTPUT = DATA / "ml_outlook.json"

class EnhancedMLTrainer:
    """Enhanced ML trainer with risk management integration."""
    
    def __init__(self):
        self.risk_manager = RiskManager()
        self.data_collector = EnhancedDataCollector()
        self.symbols = ["SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
    
    def load_enhanced_features(self, symbol: str, limit: int = 1000) -> pd.DataFrame:
        """Load price data with enhanced technical features."""
        try:
            with sqlite3.connect(DB) as conn:
                # Get price and volume data
                df = pd.read_sql_query("""
                    SELECT t, o, h, l, c, v FROM bars
                    WHERE symbol=? AND tf='1Min'
                    ORDER BY t DESC
                    LIMIT ?
                """, conn, params=[symbol, limit])
                
                if df.empty:
                    return df
                
                # Sort chronologically
                df = df.sort_values("t").reset_index(drop=True)
                df["ts"] = pd.to_datetime(df["t"], unit="ms", utc=True)
                
                # Basic technical indicators
                df["returns"] = df["c"].pct_change()
                df["log_returns"] = np.log(df["c"] / df["c"].shift(1))
                
                # Moving averages
                df["sma_5"] = df["c"].rolling(5).mean()
                df["sma_10"] = df["c"].rolling(10).mean()
                df["sma_20"] = df["c"].rolling(20).mean()
                df["sma_50"] = df["c"].rolling(50).mean()
                
                # Volatility measures
                df["volatility_5"] = df["returns"].rolling(5).std()
                df["volatility_20"] = df["returns"].rolling(20).std()
                df["volatility_ratio"] = df["volatility_5"] / df["volatility_20"]
                
                # Volume indicators
                df["volume_sma"] = df["v"].rolling(20).mean()
                df["volume_ratio"] = df["v"] / df["volume_sma"]
                
                # Price position indicators
                df["price_position"] = (df["c"] - df["l"].rolling(20).min()) / (df["h"].rolling(20).max() - df["l"].rolling(20).min())
                
                # Momentum indicators
                df["momentum_5"] = (df["c"] / df["c"].shift(5)) - 1
                df["momentum_10"] = (df["c"] / df["c"].shift(10)) - 1
                
                # RSI approximation
                gain = df["returns"].where(df["returns"] > 0, 0)
                loss = -df["returns"].where(df["returns"] < 0, 0)
                avg_gain = gain.rolling(14).mean()
                avg_loss = loss.rolling(14).mean()
                rs = avg_gain / avg_loss
                df["rsi"] = 100 - (100 / (1 + rs))
                
                # Trend strength
                df["trend_strength"] = (df["sma_5"] - df["sma_20"]) / df["sma_20"]
                
                return df.dropna()
                
        except Exception as e:
            print(f"[ml] Error loading features for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_market_regime_features(self) -> Dict[str, float]:
        """Get current market regime features."""
        try:
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT regime, vix_level, trend_strength, volatility_regime
                    FROM market_regime 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if not row:
                    return {"regime_bull": 0, "regime_bear": 0, "vix_level": 20, "trend_strength": 0, "vol_high": 0}
                
                regime, vix_level, trend_strength, vol_regime = row
                
                return {
                    "regime_bull": 1 if regime == "bull" else 0,
                    "regime_bear": 1 if regime == "bear" else 0,
                    "regime_sideways": 1 if regime == "sideways" else 0,
                    "vix_level": vix_level or 20,
                    "trend_strength": trend_strength or 0,
                    "vol_high": 1 if vol_regime == "high" else 0,
                    "vol_medium": 1 if vol_regime == "medium" else 0
                }
                
        except Exception as e:
            print(f"[ml] Error getting market regime: {e}")
            return {"regime_bull": 0, "regime_bear": 0, "vix_level": 20, "trend_strength": 0, "vol_high": 0}
    
    def get_risk_context_features(self, symbol: str) -> Dict[str, float]:
        """Get risk context features for a symbol."""
        try:
            # Get current portfolio
            portfolio = self.data_collector.get_mock_portfolio()
            
            # Check if symbol is currently held
            is_held = any(pos.symbol == symbol for pos in portfolio.positions)
            
            # Calculate portfolio metrics
            total_risk = sum(pos.max_loss for pos in portfolio.positions)
            portfolio_heat = (total_risk / portfolio.equity * 100) if portfolio.equity > 0 else 0
            
            # Estimate position size for this symbol
            mock_order = OrderIntent(
                symbol=symbol,
                side="buy",
                est_max_loss=1000,  # Mock $1000 risk
                est_value=5000      # Mock $5000 position
            )
            
            # Check if this order would be allowed
            can_add_position = len(self.risk_manager.validate_order(portfolio, mock_order)) == 0
            
            return {
                "is_held": 1 if is_held else 0,
                "portfolio_heat": portfolio_heat,
                "can_add_position": 1 if can_add_position else 0,
                "current_positions": len(portfolio.positions),
                "available_capacity": max(0, 5 - len(portfolio.positions))  # Assuming max 5 positions
            }
            
        except Exception as e:
            print(f"[ml] Error getting risk context for {symbol}: {e}")
            return {"is_held": 0, "portfolio_heat": 0, "can_add_position": 1, "current_positions": 0, "available_capacity": 5}
    
    def enhanced_predict(self, symbol: str, features: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced prediction with risk management integration."""
        if features.empty or len(features) < 50:
            return {
                "direction": "neutral",
                "confidence": 0.0,
                "score": 0.0,
                "signal_strength": "weak",
                "risk_adjusted_score": 0.0,
                "reasoning": "Insufficient data"
            }
        
        try:
            # Get latest features
            latest = features.iloc[-1]
            recent = features.tail(10)
            
            # Get market regime and risk context
            market_regime = self.get_market_regime_features()
            risk_context = self.get_risk_context_features(symbol)
            
            # Technical signal scoring
            technical_score = 0.0
            reasoning_parts = []
            
            # Trend signals
            if latest["trend_strength"] > 0.02:
                technical_score += 0.3
                reasoning_parts.append("Strong uptrend")
            elif latest["trend_strength"] < -0.02:
                technical_score -= 0.3
                reasoning_parts.append("Strong downtrend")
            
            # Momentum signals
            if latest["momentum_5"] > 0.01:
                technical_score += 0.2
                reasoning_parts.append("Positive momentum")
            elif latest["momentum_5"] < -0.01:
                technical_score -= 0.2
                reasoning_parts.append("Negative momentum")
            
            # Volume confirmation
            if latest["volume_ratio"] > 1.5:
                technical_score += 0.1 if technical_score > 0 else -0.1
                reasoning_parts.append("High volume confirmation")
            
            # RSI signals
            if latest["rsi"] < 30:
                technical_score += 0.2
                reasoning_parts.append("Oversold (RSI)")
            elif latest["rsi"] > 70:
                technical_score -= 0.2
                reasoning_parts.append("Overbought (RSI)")
            
            # Price position
            if latest["price_position"] < 0.2:
                technical_score += 0.1
                reasoning_parts.append("Near lows")
            elif latest["price_position"] > 0.8:
                technical_score -= 0.1
                reasoning_parts.append("Near highs")
            
            # Market regime adjustments
            regime_multiplier = 1.0
            if market_regime["regime_bull"]:
                regime_multiplier = 1.2 if technical_score > 0 else 0.8
                reasoning_parts.append("Bull market bias")
            elif market_regime["regime_bear"]:
                regime_multiplier = 0.8 if technical_score > 0 else 1.2
                reasoning_parts.append("Bear market bias")
            
            # High volatility adjustment
            if market_regime["vol_high"]:
                regime_multiplier *= 0.7  # Reduce confidence in high vol
                reasoning_parts.append("High volatility environment")
            
            # Apply regime adjustment
            adjusted_score = technical_score * regime_multiplier
            
            # Risk-based adjustments
            risk_multiplier = 1.0
            
            # If already held, reduce buy signals
            if risk_context["is_held"] and adjusted_score > 0:
                risk_multiplier *= 0.5
                reasoning_parts.append("Already held")
            
            # If portfolio is hot, reduce new position signals
            if risk_context["portfolio_heat"] > 20 and adjusted_score > 0:
                risk_multiplier *= 0.6
                reasoning_parts.append("High portfolio heat")
            
            # If can't add position, zero out buy signals
            if not risk_context["can_add_position"] and adjusted_score > 0:
                risk_multiplier = 0.0
                reasoning_parts.append("Risk limits prevent new position")
            
            # Final risk-adjusted score
            risk_adjusted_score = adjusted_score * risk_multiplier
            
            # Determine direction and confidence
            direction = "up" if risk_adjusted_score > 0.1 else "down" if risk_adjusted_score < -0.1 else "neutral"
            confidence = min(0.95, abs(risk_adjusted_score))
            
            # Signal strength
            signal_strength = "strong" if confidence > 0.7 else "medium" if confidence > 0.4 else "weak"
            
            return {
                "direction": direction,
                "confidence": round(confidence, 3),
                "score": round(risk_adjusted_score, 3),
                "signal_strength": signal_strength,
                "risk_adjusted_score": round(risk_adjusted_score, 3),
                "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "No clear signals",
                "technical_score": round(technical_score, 3),
                "regime_multiplier": round(regime_multiplier, 3),
                "risk_multiplier": round(risk_multiplier, 3),
                "market_regime": market_regime["regime_bull"] + market_regime["regime_bear"] * -1,
                "risk_context": risk_context
            }
            
        except Exception as e:
            print(f"[ml] Prediction error for {symbol}: {e}")
            return {
                "direction": "neutral",
                "confidence": 0.0,
                "score": 0.0,
                "signal_strength": "weak",
                "risk_adjusted_score": 0.0,
                "reasoning": f"Error: {e}"
            }
    
    def generate_trading_opportunities(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific trading opportunities based on predictions and risk management."""
        opportunities = []
        
        # Get current portfolio for context
        portfolio = self.data_collector.get_mock_portfolio()
        current_symbols = {pos.symbol for pos in portfolio.positions}
        
        for pred in predictions:
            symbol = pred["symbol"]
            direction = pred["direction"]
            confidence = pred["confidence"]
            risk_score = pred.get("risk_adjusted_score", 0)
            
            # Skip low-confidence signals
            if confidence < 0.5:
                continue
            
            opportunity = {
                "symbol": symbol,
                "action": "hold",
                "priority": "low",
                "reasoning": pred.get("reasoning", ""),
                "confidence": confidence,
                "risk_score": risk_score
            }
            
            # Determine action
            if symbol in current_symbols:
                if direction == "down" and confidence > 0.7:
                    opportunity["action"] = "consider_exit"
                    opportunity["priority"] = "high" if confidence > 0.8 else "medium"
                elif direction == "up" and confidence > 0.6:
                    opportunity["action"] = "hold_strong"
                    opportunity["priority"] = "medium"
            else:
                if direction == "up" and confidence > 0.7 and risk_score > 0.5:
                    opportunity["action"] = "consider_entry"
                    opportunity["priority"] = "high" if confidence > 0.8 and risk_score > 0.7 else "medium"
            
            # Add risk considerations
            risk_context = pred.get("risk_context", {})
            if not risk_context.get("can_add_position", True) and opportunity["action"] == "consider_entry":
                opportunity["action"] = "wait"
                opportunity["reasoning"] += "; Risk limits prevent new position"
            
            opportunities.append(opportunity)
        
        # Sort by priority and confidence
        priority_order = {"high": 3, "medium": 2, "low": 1}
        opportunities.sort(key=lambda x: (priority_order.get(x["priority"], 0), x["confidence"]), reverse=True)
        
        return opportunities
    
    def run_enhanced_training(self) -> Dict[str, Any]:
        """Run enhanced ML training with risk integration."""
        print("[ml] Starting enhanced ML training...")
        
        # Ensure we have fresh market data
        self.data_collector.full_collection_cycle(self.symbols)
        
        predictions = []
        
        for symbol in self.symbols:
            print(f"[ml] Processing {symbol}...")
            
            # Load enhanced features
            features = self.load_enhanced_features(symbol, limit=1000)
            
            if features.empty:
                print(f"[ml] No data for {symbol}, skipping")
                continue
            
            # Generate prediction
            pred = self.enhanced_predict(symbol, features)
            pred["symbol"] = symbol
            pred["horizon"] = "next_30min"
            
            predictions.append(pred)
            print(f"[ml] {symbol}: {pred['direction']} (conf: {pred['confidence']:.3f}, risk_adj: {pred.get('risk_adjusted_score', 0):.3f})")
        
        # Generate trading opportunities
        opportunities = self.generate_trading_opportunities(predictions)
        
        # Create output payload
        market_regime = self.get_market_regime_features()
        risk_summary = self.data_collector.generate_risk_summary()
        
        output = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "models": ["Enhanced Technical + Risk Management v2.0"],
            "market_regime": {
                "current": "bull" if market_regime.get("regime_bull") else "bear" if market_regime.get("regime_bear") else "sideways",
                "vix_level": market_regime.get("vix_level", 20),
                "trend_strength": market_regime.get("trend_strength", 0)
            },
            "portfolio_status": {
                "heat_pct": risk_summary.get("portfolio", {}).get("heat_pct", 0),
                "positions": risk_summary.get("portfolio", {}).get("num_positions", 0),
                "status": risk_summary.get("risk_status", {}).get("overall_status", "unknown")
            },
            "predictions": predictions,
            "trading_opportunities": opportunities[:10],  # Top 10
            "risk_notes": risk_summary.get("risk_status", {}).get("violations", []) + 
                         risk_summary.get("risk_status", {}).get("warnings", [])
        }
        
        # Save to file
        ML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        ML_OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
        
        print(f"[ml] Enhanced ML outlook saved to {ML_OUTPUT}")
        print(f"[ml] Generated {len(predictions)} predictions, {len(opportunities)} opportunities")
        
        return output

def main():
    """Main entry point for enhanced ML training."""
    trainer = EnhancedMLTrainer()
    
    try:
        result = trainer.run_enhanced_training()
        
        print("\n" + "="*60)
        print("ENHANCED ML OUTLOOK SUMMARY")
        print("="*60)
        
        market = result.get("market_regime", {})
        portfolio = result.get("portfolio_status", {})
        
        print(f"Market Regime: {market.get('current', 'unknown').upper()}")
        print(f"VIX Level: {market.get('vix_level', 0):.1f}%")
        print(f"Portfolio Heat: {portfolio.get('heat_pct', 0):.1f}%")
        print(f"Portfolio Status: {portfolio.get('status', 'unknown').upper()}")
        
        opportunities = result.get("trading_opportunities", [])
        if opportunities:
            print(f"\nTop Trading Opportunities:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"{i}. {opp['symbol']}: {opp['action'].upper()} (Priority: {opp['priority']}, Conf: {opp['confidence']:.3f})")
        
        risks = result.get("risk_notes", [])
        if risks:
            print(f"\nRisk Notes:")
            for risk in risks:
                print(f"  ⚠️  {risk}")
        
    except Exception as e:
        print(f"[ml] Error in enhanced training: {e}")
        raise

if __name__ == "__main__":
    main()