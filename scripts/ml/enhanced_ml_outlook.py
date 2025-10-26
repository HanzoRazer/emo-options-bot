"""
Enhanced ML Outlook System
Integrates with Phase 3 LLM system for intelligent market analysis.
Supports multiple models and exports results for dashboard integration.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pickle
import warnings

import pandas as pd
import numpy as np
from dataclasses import dataclass

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.database.enhanced_router import DBRouter

# ML imports (with fallbacks)
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MLOutlookConfig:
    """Configuration for ML outlook generation"""
    symbols: List[str]
    lookback_days: int = 30
    forecast_horizons: List[str] = None  # ["1h", "1d", "5d"]
    models: List[str] = None  # ["rf", "lstm", "ensemble"]
    min_data_points: int = 100
    retrain_threshold_days: int = 7
    confidence_threshold: float = 0.6
    feature_windows: List[int] = None  # [5, 10, 20] periods

@dataclass
class MLPrediction:
    """Single ML prediction result"""
    symbol: str
    model: str
    horizon: str
    signal: float  # -1 to 1 (bearish to bullish)
    confidence: float  # 0 to 1
    timestamp: datetime
    features_used: List[str]
    model_version: str
    metadata: Dict[str, Any]

class FeatureEngineer:
    """Feature engineering for market data"""
    
    def __init__(self, config: MLOutlookConfig):
        self.config = config
        self.feature_windows = config.feature_windows or [5, 10, 20]
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical features from price data"""
        if df.empty:
            return df
        
        features_df = df.copy()
        
        # Price-based features
        features_df['returns'] = features_df['close'].pct_change()
        features_df['log_returns'] = np.log(features_df['close'] / features_df['close'].shift(1))
        
        # Volume features
        features_df['volume_sma_20'] = features_df['volume'].rolling(20).mean()
        features_df['volume_ratio'] = features_df['volume'] / features_df['volume_sma_20']
        
        # Volatility features
        features_df['volatility_5'] = features_df['returns'].rolling(5).std()
        features_df['volatility_20'] = features_df['returns'].rolling(20).std()
        features_df['volatility_ratio'] = features_df['volatility_5'] / features_df['volatility_20']
        
        # Price position features
        features_df['high_low_ratio'] = features_df['high'] / features_df['low']
        features_df['close_position'] = (features_df['close'] - features_df['low']) / (features_df['high'] - features_df['low'])
        
        # Multiple timeframe features
        for window in self.feature_windows:
            # Moving averages
            features_df[f'sma_{window}'] = features_df['close'].rolling(window).mean()
            features_df[f'price_vs_sma_{window}'] = features_df['close'] / features_df[f'sma_{window}'] - 1
            
            # Momentum
            features_df[f'momentum_{window}'] = features_df['close'] / features_df['close'].shift(window) - 1
            
            # RSI-like indicator
            gains = features_df['returns'].where(features_df['returns'] > 0, 0)
            losses = -features_df['returns'].where(features_df['returns'] < 0, 0)
            avg_gain = gains.rolling(window).mean()
            avg_loss = losses.rolling(window).mean()
            rs = avg_gain / avg_loss
            features_df[f'rsi_{window}'] = 100 - (100 / (1 + rs))
            
            # Bollinger Band position
            sma = features_df['close'].rolling(window).mean()
            std = features_df['close'].rolling(window).std()
            features_df[f'bb_position_{window}'] = (features_df['close'] - sma) / (2 * std)
        
        # Market regime features
        features_df['trend_strength'] = abs(features_df['price_vs_sma_20'])
        features_df['is_trending'] = features_df['trend_strength'] > 0.05
        
        # Time-based features
        features_df['hour'] = features_df.index.hour if hasattr(features_df.index, 'hour') else 0
        features_df['day_of_week'] = features_df.index.dayofweek if hasattr(features_df.index, 'dayofweek') else 0
        
        return features_df
    
    def create_targets(self, df: pd.DataFrame, horizons: List[str]) -> pd.DataFrame:
        """Create target variables for different forecast horizons"""
        targets_df = pd.DataFrame(index=df.index)
        
        for horizon in horizons:
            # Parse horizon (e.g., "1h", "1d", "5d")
            if horizon.endswith('h'):
                periods = int(horizon[:-1])
                # For hour horizons, assume we have minute data
                target_col = f'target_{horizon}'
            elif horizon.endswith('d'):
                periods = int(horizon[:-1])
                # For day horizons, shift by days worth of periods
                # Assume 390 minutes per trading day (6.5 hours)
                periods = periods * 390
                target_col = f'target_{horizon}'
            else:
                continue
            
            # Future return target
            future_return = df['close'].shift(-periods) / df['close'] - 1
            
            # Classify into signal: -1 (bearish), 0 (neutral), 1 (bullish)
            signal = np.where(future_return > 0.01, 1,  # >1% = bullish
                    np.where(future_return < -0.01, -1,  # <-1% = bearish
                           0))  # neutral
            
            targets_df[target_col] = signal
            targets_df[f'{target_col}_return'] = future_return
        
        return targets_df

class RandomForestModel:
    """Random Forest model for market prediction"""
    
    def __init__(self, config: MLOutlookConfig):
        self.config = config
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = "rf_v1.0"
        
    def train(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, 
              target_col: str) -> Dict[str, Any]:
        """Train Random Forest model"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn not available")
        
        # Prepare data
        feature_cols = self._select_features(features_df)
        X = features_df[feature_cols].dropna()
        y = targets_df[target_col].loc[X.index]
        
        # Remove rows with missing targets
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]
        
        if len(X) < self.config.min_data_points:
            raise ValueError(f"Insufficient data: {len(X)} < {self.config.min_data_points}")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        )
        
        self.model.fit(X_scaled, y)
        self.feature_names = feature_cols
        
        # Calculate performance metrics
        y_pred = self.model.predict(X_scaled)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        
        # Feature importance
        feature_importance = dict(zip(feature_cols, self.model.feature_importances_))
        
        return {
            "mse": mse,
            "mae": mae,
            "n_samples": len(X),
            "feature_importance": feature_importance,
            "model_version": self.model_version
        }
    
    def predict(self, features_df: pd.DataFrame) -> Tuple[float, float]:
        """Make prediction and return (signal, confidence)"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        # Get latest features
        latest_features = features_df[self.feature_names].iloc[-1:].dropna()
        if latest_features.empty:
            return 0.0, 0.0
        
        # Scale and predict
        X_scaled = self.scaler.transform(latest_features)
        prediction = self.model.predict(X_scaled)[0]
        
        # Convert to signal (-1 to 1)
        signal = np.clip(prediction, -1, 1)
        
        # Estimate confidence based on feature quality and model certainty
        # This is a simplified confidence estimation
        confidence = min(0.95, abs(signal) + 0.3)
        
        return float(signal), float(confidence)
    
    def _select_features(self, df: pd.DataFrame) -> List[str]:
        """Select relevant features for training"""
        # Exclude target columns and non-numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        feature_cols = [col for col in numeric_cols 
                       if not col.startswith('target_') 
                       and col not in ['open', 'high', 'low', 'close', 'volume']]
        
        return feature_cols

class MockLSTMModel:
    """Mock LSTM model when TensorFlow not available"""
    
    def __init__(self, config: MLOutlookConfig):
        self.config = config
        self.model_version = "lstm_v1.0_mock"
        
    def train(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, 
              target_col: str) -> Dict[str, Any]:
        """Mock training"""
        return {
            "mse": 0.5,
            "mae": 0.3,
            "n_samples": len(features_df),
            "feature_importance": {},
            "model_version": self.model_version,
            "note": "Mock LSTM - TensorFlow not available"
        }
        
    def predict(self, features_df: pd.DataFrame) -> Tuple[float, float]:
        """Mock prediction"""
        # Generate deterministic "prediction" based on recent price action
        if len(features_df) > 0:
            recent_return = features_df['returns'].iloc[-5:].mean() if 'returns' in features_df else 0
            signal = np.clip(recent_return * 10, -1, 1)  # Amplify signal
            confidence = 0.5  # Mock confidence
        else:
            signal, confidence = 0.0, 0.0
            
        return float(signal), float(confidence)

class MLOutlookEngine:
    """Main ML outlook engine"""
    
    def __init__(self, config: MLOutlookConfig):
        self.config = config
        self.config.forecast_horizons = config.forecast_horizons or ["1h", "1d", "5d"]
        self.config.models = config.models or ["rf", "lstm"]
        
        self.feature_engineer = FeatureEngineer(config)
        self.models = {}
        self.model_cache_dir = Path("data/models")
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_market_data(self, symbol: str, days: int = None) -> pd.DataFrame:
        """Get market data for symbol"""
        days = days or self.config.lookback_days
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        try:
            sql = """
            SELECT ts, symbol, open, high, low, close, volume
            FROM bars 
            WHERE symbol = :symbol 
                AND ts >= :start_date
                AND timeframe = '1Min'
            ORDER BY ts
            """
            
            df = DBRouter.fetch_df(sql, symbol=symbol, start_date=start_date)
            
            if not df.empty:
                df['ts'] = pd.to_datetime(df['ts'])
                df = df.set_index('ts')
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return pd.DataFrame()
    
    def train_models(self, symbol: str) -> Dict[str, Any]:
        """Train all models for a symbol"""
        logger.info(f"Training models for {symbol}")
        
        # Get market data
        df = self.get_market_data(symbol, days=self.config.lookback_days * 2)  # Extra data for training
        
        if len(df) < self.config.min_data_points:
            raise ValueError(f"Insufficient data for {symbol}: {len(df)} < {self.config.min_data_points}")
        
        # Feature engineering
        features_df = self.feature_engineer.create_features(df)
        targets_df = self.feature_engineer.create_targets(df, self.config.forecast_horizons)
        
        training_results = {}
        
        for model_name in self.config.models:
            for horizon in self.config.forecast_horizons:
                target_col = f"target_{horizon}"
                
                if target_col not in targets_df.columns:
                    continue
                
                try:
                    # Create model
                    if model_name == "rf" and SKLEARN_AVAILABLE:
                        model = RandomForestModel(self.config)
                    elif model_name == "lstm":
                        model = MockLSTMModel(self.config)  # Use mock for now
                    else:
                        continue
                    
                    # Train model
                    train_result = model.train(features_df, targets_df, target_col)
                    
                    # Cache model
                    model_key = f"{symbol}_{model_name}_{horizon}"
                    self.models[model_key] = model
                    self._save_model(model, model_key)
                    
                    training_results[model_key] = train_result
                    logger.info(f"✅ Trained {model_key}: MAE={train_result['mae']:.3f}")
                    
                except Exception as e:
                    logger.error(f"❌ Training failed for {model_name}_{horizon}: {e}")
                    training_results[f"{symbol}_{model_name}_{horizon}"] = {"error": str(e)}
        
        return training_results
    
    def generate_outlook(self, symbol: str) -> List[MLPrediction]:
        """Generate ML outlook for a symbol"""
        logger.info(f"Generating outlook for {symbol}")
        
        # Get recent market data
        df = self.get_market_data(symbol, days=self.config.lookback_days)
        
        if df.empty:
            logger.warning(f"No market data available for {symbol}")
            return []
        
        # Feature engineering
        features_df = self.feature_engineer.create_features(df)
        
        predictions = []
        
        for model_name in self.config.models:
            for horizon in self.config.forecast_horizons:
                model_key = f"{symbol}_{model_name}_{horizon}"
                
                try:
                    # Load or train model
                    model = self._load_or_train_model(symbol, model_name, horizon)
                    
                    if model is None:
                        continue
                    
                    # Generate prediction
                    signal, confidence = model.predict(features_df)
                    
                    # Only include high-confidence predictions
                    if confidence >= self.config.confidence_threshold:
                        prediction = MLPrediction(
                            symbol=symbol,
                            model=model_name,
                            horizon=horizon,
                            signal=signal,
                            confidence=confidence,
                            timestamp=datetime.now(timezone.utc),
                            features_used=getattr(model, 'feature_names', []),
                            model_version=getattr(model, 'model_version', 'unknown'),
                            metadata={
                                "data_points": len(df),
                                "latest_price": float(df['close'].iloc[-1]),
                                "latest_volume": int(df['volume'].iloc[-1])
                            }
                        )
                        
                        predictions.append(prediction)
                        logger.info(f"✅ {model_key}: signal={signal:.3f}, confidence={confidence:.3f}")
                    else:
                        logger.debug(f"⚠️ {model_key}: low confidence {confidence:.3f}")
                
                except Exception as e:
                    logger.error(f"❌ Prediction failed for {model_key}: {e}")
        
        return predictions
    
    def _load_or_train_model(self, symbol: str, model_name: str, horizon: str):
        """Load cached model or train if needed"""
        model_key = f"{symbol}_{model_name}_{horizon}"
        
        # Check if model is already in memory
        if model_key in self.models:
            return self.models[model_key]
        
        # Try to load from cache
        model = self._load_model(model_key)
        if model is not None:
            self.models[model_key] = model
            return model
        
        # Train new model
        try:
            self.train_models(symbol)
            return self.models.get(model_key)
        except Exception as e:
            logger.error(f"Failed to train model {model_key}: {e}")
            return None
    
    def _save_model(self, model, model_key: str):
        """Save model to cache"""
        try:
            cache_path = self.model_cache_dir / f"{model_key}.pkl"
            with open(cache_path, 'wb') as f:
                pickle.dump(model, f)
        except Exception as e:
            logger.warning(f"Failed to cache model {model_key}: {e}")
    
    def _load_model(self, model_key: str):
        """Load model from cache"""
        try:
            cache_path = self.model_cache_dir / f"{model_key}.pkl"
            if cache_path.exists():
                # Check if model is recent enough
                age_days = (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).days
                if age_days <= self.config.retrain_threshold_days:
                    with open(cache_path, 'rb') as f:
                        return pickle.load(f)
            return None
        except Exception as e:
            logger.warning(f"Failed to load cached model {model_key}: {e}")
            return None
    
    def export_outlook_json(self, predictions: List[MLPrediction], symbol: str) -> Path:
        """Export outlook to JSON for dashboard integration"""
        if not predictions:
            summary = f"No high-confidence predictions available for {symbol}"
            models_data = []
        else:
            # Calculate ensemble signal
            signals = [p.signal for p in predictions]
            confidences = [p.confidence for p in predictions]
            
            # Weighted average signal
            ensemble_signal = np.average(signals, weights=confidences)
            ensemble_confidence = np.mean(confidences)
            
            # Generate summary
            direction = "bullish" if ensemble_signal > 0.1 else "bearish" if ensemble_signal < -0.1 else "neutral"
            summary = f"{symbol} outlook: {direction} (signal: {ensemble_signal:.2f}, confidence: {ensemble_confidence:.2f})"
            
            # Model details
            models_data = []
            for pred in predictions:
                models_data.append({
                    "name": f"{pred.model}_{pred.horizon}",
                    "signal": round(pred.signal, 3),
                    "conf": round(pred.confidence, 3),
                    "horizon": pred.horizon,
                    "model_version": pred.model_version
                })
        
        # Create output
        output = {
            "ts": datetime.now(timezone.utc).isoformat() + "Z",
            "symbol": symbol,
            "models": models_data,
            "summary": summary,
            "ensemble": {
                "signal": round(ensemble_signal if predictions else 0.0, 3),
                "confidence": round(ensemble_confidence if predictions else 0.0, 3),
                "model_count": len(predictions)
            }
        }
        
        # Save to file
        output_path = Path("data") / "ml_outlook.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"✅ ML outlook exported: {output_path}")
        return output_path
    
    def save_predictions_to_db(self, predictions: List[MLPrediction]):
        """Save predictions to database"""
        if not predictions:
            return
        
        try:
            records = []
            for pred in predictions:
                records.append({
                    "ts": pred.timestamp,
                    "symbol": pred.symbol,
                    "model": pred.model,
                    "horizon": pred.horizon,
                    "signal": pred.signal,
                    "confidence": pred.confidence,
                    "meta": json.dumps(pred.metadata),
                    "features_hash": str(hash(tuple(pred.features_used))),
                    "model_version": pred.model_version,
                    "prediction_target": f"signal_{pred.horizon}"
                })
            
            df = pd.DataFrame(records)
            DBRouter.upsert_df(df, "ml_signals", conflict_columns=["symbol", "ts", "model", "horizon"])
            
            logger.info(f"✅ Saved {len(predictions)} predictions to database")
            
        except Exception as e:
            logger.error(f"Failed to save predictions to database: {e}")

def create_config_from_env() -> MLOutlookConfig:
    """Create ML config from environment variables"""
    symbols = os.getenv("EMO_SYMBOLS", "SPY,QQQ").split(",")
    symbols = [s.strip().upper() for s in symbols]
    
    return MLOutlookConfig(
        symbols=symbols,
        lookback_days=int(os.getenv("EMO_ML_LOOKBACK_DAYS", "30")),
        forecast_horizons=os.getenv("EMO_ML_HORIZONS", "1h,1d,5d").split(","),
        models=os.getenv("EMO_ML_MODELS", "rf,lstm").split(","),
        min_data_points=int(os.getenv("EMO_ML_MIN_DATA", "100")),
        retrain_threshold_days=int(os.getenv("EMO_ML_RETRAIN_DAYS", "7")),
        confidence_threshold=float(os.getenv("EMO_ML_CONFIDENCE_THRESHOLD", "0.6"))
    )

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO ML Outlook Engine")
    parser.add_argument("--symbol", help="Symbol to process")
    parser.add_argument("--train", action="store_true", help="Force retrain models")
    parser.add_argument("--export", action="store_true", help="Export outlook to JSON")
    parser.add_argument("--save-db", action="store_true", help="Save predictions to database")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # Initialize database
    try:
        DBRouter.init()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Create config
    config = create_config_from_env()
    
    # Override symbol if specified
    if args.symbol:
        config.symbols = [args.symbol.upper()]
    
    # Create ML engine
    engine = MLOutlookEngine(config)
    
    try:
        for symbol in config.symbols:
            logger.info(f"Processing {symbol}")
            
            # Train models if requested
            if args.train:
                engine.train_models(symbol)
            
            # Generate outlook
            predictions = engine.generate_outlook(symbol)
            
            if predictions:
                logger.info(f"Generated {len(predictions)} predictions for {symbol}")
                
                # Export to JSON
                if args.export:
                    engine.export_outlook_json(predictions, symbol)
                
                # Save to database
                if args.save_db:
                    engine.save_predictions_to_db(predictions)
            else:
                logger.warning(f"No predictions generated for {symbol}")
                
                # Export empty outlook
                if args.export:
                    engine.export_outlook_json([], symbol)
    
    except Exception as e:
        logger.error(f"ML outlook generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()