"""
ML Outlook JSON Generator
Generates machine learning outlook data for agent integration.
"""

import json
import datetime as dt
import random
from pathlib import Path

def generate_ml_outlook(symbol: str = "SPY") -> dict:
    """Generate mock ML outlook data."""
    
    # Mock signals with some randomness
    signals = ["strong_bullish", "mild_bullish", "neutral", "mild_bearish", "strong_bearish"]
    signal = random.choice(signals)
    
    # Confidence based on signal strength
    if "strong" in signal:
        confidence = random.uniform(0.75, 0.95)
    elif "mild" in signal:
        confidence = random.uniform(0.55, 0.75)
    else:
        confidence = random.uniform(0.45, 0.65)
    
    # Generate outlook
    outlook = {
        "ts": dt.datetime.utcnow().isoformat(),
        "symbol": symbol,
        "signal": signal,
        "confidence": round(confidence, 2),
        "horizon": "1d",
        "price_target": round(450 + random.uniform(-20, 20), 2) if symbol == "SPY" else None,
        "volatility_regime": random.choice(["low", "moderate", "high"]),
        "trend_strength": round(random.uniform(0.1, 1.0), 2),
        "support_level": round(445 + random.uniform(-10, 5), 2) if symbol == "SPY" else None,
        "resistance_level": round(455 + random.uniform(-5, 10), 2) if symbol == "SPY" else None,
        "generated_by": "ml_outlook_generator",
        "model_version": "1.0.0"
    }
    
    return outlook

def save_ml_outlook(symbol: str = "SPY", output_dir: str = "ops"):
    """Save ML outlook to JSON file."""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate outlook
    outlook = generate_ml_outlook(symbol)
    
    # Save to file
    output_file = Path(output_dir) / "ml_outlook.json"
    with open(output_file, "w") as f:
        json.dump(outlook, f, indent=2)
    
    print(f"ML outlook saved to: {output_file}")
    print(f"Signal: {outlook['signal']} (confidence: {outlook['confidence']:.1%})")
    
    return outlook

if __name__ == "__main__":
    # Generate outlook for multiple symbols
    symbols = ["SPY", "QQQ", "AAPL"]
    
    for symbol in symbols:
        outlook = save_ml_outlook(symbol)
        
        # Also save symbol-specific file
        output_file = Path("ops") / f"ml_outlook_{symbol.lower()}.json"
        with open(output_file, "w") as f:
            json.dump(outlook, f, indent=2)
        
        print(f"  → {symbol}: {outlook['signal']} ({outlook['confidence']:.1%})")
    
    print(f"\nGenerated ML outlooks for {len(symbols)} symbols")