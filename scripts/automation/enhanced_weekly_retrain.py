"""
Enhanced Weekly Retrain System
Automated ML model retraining with performance monitoring and alerting.
Integrates with Windows Task Scheduler and supports email notifications.
"""
import os
import sys
import subprocess
import logging
import json
import smtplib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from dataclasses import dataclass

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.database.enhanced_router import DBRouter

logger = logging.getLogger(__name__)

@dataclass
class RetrainConfig:
    """Configuration for automated retraining"""
    symbols: List[str]
    models: List[str] = None
    performance_threshold: float = 0.6  # Minimum acceptable performance
    max_retrain_time_minutes: int = 120  # 2 hours max
    email_notifications: bool = True
    email_recipients: List[str] = None
    backup_models: bool = True
    cleanup_old_models: bool = True
    max_model_age_days: int = 30

@dataclass
class RetrainResult:
    """Result of model retraining"""
    symbol: str
    model: str
    success: bool
    performance_score: float = 0.0
    training_time_seconds: float = 0.0
    error_message: str = ""
    timestamp: datetime = None

class ModelPerformanceMonitor:
    """Monitor ML model performance over time"""
    
    def __init__(self):
        pass
    
    def get_model_performance(self, symbol: str, model: str, days: int = 7) -> Dict[str, Any]:
        """Get recent model performance metrics"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            sql = """
            SELECT 
                AVG(confidence) as avg_confidence,
                COUNT(*) as prediction_count,
                AVG(ABS(signal)) as avg_signal_strength,
                MAX(ts) as latest_prediction
            FROM ml_signals 
            WHERE symbol = :symbol 
                AND model = :model 
                AND ts >= :start_date
            """
            
            result = DBRouter.execute(sql, symbol=symbol, model=model, start_date=start_date)
            row = result.fetchone()
            
            if row and row[1] > 0:  # prediction_count > 0
                return {
                    "avg_confidence": float(row[0] or 0),
                    "prediction_count": int(row[1]),
                    "avg_signal_strength": float(row[2] or 0),
                    "latest_prediction": row[3],
                    "performance_score": float(row[0] or 0) * (1 + min(float(row[2] or 0), 0.5))  # Composite score
                }
            else:
                return {
                    "avg_confidence": 0.0,
                    "prediction_count": 0,
                    "avg_signal_strength": 0.0,
                    "latest_prediction": None,
                    "performance_score": 0.0
                }
                
        except Exception as e:
            logger.error(f"Failed to get performance for {symbol}_{model}: {e}")
            return {"performance_score": 0.0}
    
    def needs_retraining(self, symbol: str, model: str, threshold: float = 0.6) -> bool:
        """Determine if model needs retraining based on performance"""
        performance = self.get_model_performance(symbol, model)
        
        # Check multiple criteria
        needs_retrain = (
            performance["performance_score"] < threshold or
            performance["prediction_count"] == 0 or
            (performance["latest_prediction"] and 
             (datetime.now(timezone.utc) - performance["latest_prediction"]).days > 3)
        )
        
        logger.info(f"{symbol}_{model} performance: {performance['performance_score']:.3f}, "
                   f"needs_retrain: {needs_retrain}")
        
        return needs_retrain
    
    def get_all_model_status(self, symbols: List[str], models: List[str]) -> Dict[str, Dict]:
        """Get performance status for all models"""
        status = {}
        
        for symbol in symbols:
            for model in models:
                key = f"{symbol}_{model}"
                status[key] = self.get_model_performance(symbol, model)
                status[key]["needs_retraining"] = self.needs_retraining(
                    symbol, model, threshold=0.6
                )
        
        return status

class EmailNotifier:
    """Send email notifications about retraining results"""
    
    def __init__(self, config: RetrainConfig):
        self.config = config
        self.smtp_server = os.getenv("EMO_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMO_SMTP_PORT", "587"))
        self.email_user = os.getenv("EMO_EMAIL_USER")
        self.email_password = os.getenv("EMO_EMAIL_PASSWORD")
        self.from_email = os.getenv("EMO_FROM_EMAIL", self.email_user)
        
        self.enabled = (
            config.email_notifications and 
            self.email_user and 
            self.email_password and
            config.email_recipients
        )
    
    def send_notification(self, results: List[RetrainResult], performance_status: Dict[str, Dict]):
        """Send email notification with retraining results"""
        if not self.enabled:
            logger.info("Email notifications disabled or not configured")
            return
        
        try:
            # Create email content
            subject = f"EMO ML Retraining Report - {datetime.now().strftime('%Y-%m-%d')}"
            body = self._create_email_body(results, performance_status)
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ", ".join(self.config.email_recipients)
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                text = msg.as_string()
                server.sendmail(self.from_email, self.config.email_recipients, text)
            
            logger.info(f"Email notification sent to {len(self.config.email_recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _create_email_body(self, results: List[RetrainResult], performance_status: Dict[str, Dict]) -> str:
        """Create HTML email body"""
        total_models = len(results)
        successful = len([r for r in results if r.success])
        failed = total_models - successful
        
        # Summary
        summary_color = "green" if failed == 0 else "orange" if failed < total_models / 2 else "red"
        
        html = f"""
        <html>
        <body>
            <h2>EMO ML Model Retraining Report</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            
            <h3 style="color: {summary_color}">Summary</h3>
            <ul>
                <li><strong>Total Models:</strong> {total_models}</li>
                <li><strong>Successful:</strong> {successful}</li>
                <li><strong>Failed:</strong> {failed}</li>
                <li><strong>Success Rate:</strong> {(successful/total_models*100):.1f}%</li>
            </ul>
        """
        
        # Detailed results
        if results:
            html += "<h3>Detailed Results</h3>"
            html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            html += "<tr><th>Symbol</th><th>Model</th><th>Status</th><th>Performance</th><th>Training Time</th><th>Notes</th></tr>"
            
            for result in results:
                status_color = "green" if result.success else "red"
                status_text = "✅ Success" if result.success else "❌ Failed"
                
                html += f"""
                <tr>
                    <td>{result.symbol}</td>
                    <td>{result.model}</td>
                    <td style="color: {status_color}">{status_text}</td>
                    <td>{result.performance_score:.3f}</td>
                    <td>{result.training_time_seconds:.1f}s</td>
                    <td>{result.error_message or 'OK'}</td>
                </tr>
                """
            
            html += "</table>"
        
        # Performance status
        if performance_status:
            html += "<h3>Model Performance Status</h3>"
            html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            html += "<tr><th>Model</th><th>Confidence</th><th>Predictions</th><th>Needs Retrain</th></tr>"
            
            for model_key, status in performance_status.items():
                retrain_color = "red" if status.get("needs_retraining") else "green"
                retrain_text = "Yes" if status.get("needs_retraining") else "No"
                
                html += f"""
                <tr>
                    <td>{model_key}</td>
                    <td>{status.get('avg_confidence', 0):.3f}</td>
                    <td>{status.get('prediction_count', 0)}</td>
                    <td style="color: {retrain_color}">{retrain_text}</td>
                </tr>
                """
            
            html += "</table>"
        
        html += """
            <hr>
            <p><small>This is an automated message from the EMO Options Bot ML system.</small></p>
        </body>
        </html>
        """
        
        return html

class WeeklyRetrainEngine:
    """Main weekly retraining engine"""
    
    def __init__(self, config: RetrainConfig):
        self.config = config
        self.config.models = config.models or ["rf", "lstm"]
        self.performance_monitor = ModelPerformanceMonitor()
        self.email_notifier = EmailNotifier(config)
        
        # Create directories
        self.backup_dir = Path("data/model_backups")
        self.log_dir = Path("logs")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def run_weekly_retrain(self) -> Dict[str, Any]:
        """Run complete weekly retraining process"""
        start_time = datetime.now(timezone.utc)
        logger.info("Starting weekly ML model retraining")
        
        results = []
        performance_status = {}
        
        try:
            # Get current performance status
            performance_status = self.performance_monitor.get_all_model_status(
                self.config.symbols, self.config.models
            )
            
            # Backup existing models
            if self.config.backup_models:
                self._backup_models()
            
            # Retrain models that need it
            for symbol in self.config.symbols:
                for model in self.config.models:
                    if self.performance_monitor.needs_retraining(
                        symbol, model, self.config.performance_threshold
                    ):
                        result = self._retrain_model(symbol, model)
                        results.append(result)
                    else:
                        logger.info(f"Skipping {symbol}_{model} - performance acceptable")
            
            # Cleanup old models
            if self.config.cleanup_old_models:
                self._cleanup_old_models()
            
            # Send notifications
            self.email_notifier.send_notification(results, performance_status)
            
            # Generate summary
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            successful = len([r for r in results if r.success])
            
            summary = {
                "start_time": start_time.isoformat(),
                "duration_seconds": duration,
                "total_models_retrained": len(results),
                "successful_retrains": successful,
                "failed_retrains": len(results) - successful,
                "results": [r.__dict__ for r in results],
                "performance_status": performance_status
            }
            
            logger.info(f"Weekly retraining completed: {successful}/{len(results)} successful in {duration:.1f}s")
            
            # Save summary
            self._save_retrain_summary(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Weekly retraining failed: {e}")
            return {
                "error": str(e),
                "start_time": start_time.isoformat(),
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
    
    def _retrain_model(self, symbol: str, model: str) -> RetrainResult:
        """Retrain a single model"""
        start_time = datetime.now(timezone.utc)
        logger.info(f"⏳ Retraining {symbol}_{model}")
        
        try:
            # Run ML training script
            script_path = ROOT / "scripts" / "ml" / "enhanced_ml_outlook.py"
            
            cmd = [
                sys.executable, 
                str(script_path),
                "--symbol", symbol,
                "--train",
                "--save-db"
            ]
            
            # Set model-specific environment
            env = os.environ.copy()
            env["EMO_ML_MODELS"] = model
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.config.max_retrain_time_minutes * 60,
                env=env
            )
            
            training_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            if result.returncode == 0:
                # Get performance score
                performance = self.performance_monitor.get_model_performance(symbol, model, days=1)
                performance_score = performance.get("performance_score", 0.0)
                
                logger.info(f"✅ {symbol}_{model} retrained successfully (score: {performance_score:.3f})")
                
                return RetrainResult(
                    symbol=symbol,
                    model=model,
                    success=True,
                    performance_score=performance_score,
                    training_time_seconds=training_time,
                    timestamp=start_time
                )
            else:
                error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                logger.error(f"❌ {symbol}_{model} retraining failed: {error_msg}")
                
                return RetrainResult(
                    symbol=symbol,
                    model=model,
                    success=False,
                    error_message=error_msg,
                    training_time_seconds=training_time,
                    timestamp=start_time
                )
                
        except subprocess.TimeoutExpired:
            error_msg = f"Training timeout ({self.config.max_retrain_time_minutes}min)"
            logger.error(f"❌ {symbol}_{model}: {error_msg}")
            
            return RetrainResult(
                symbol=symbol,
                model=model,
                success=False,
                error_message=error_msg,
                training_time_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
                timestamp=start_time
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ {symbol}_{model}: {error_msg}")
            
            return RetrainResult(
                symbol=symbol,
                model=model,
                success=False,
                error_message=error_msg,
                training_time_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
                timestamp=start_time
            )
    
    def _backup_models(self):
        """Backup existing models"""
        try:
            model_dir = Path("data/models")
            if not model_dir.exists():
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"models_backup_{timestamp}"
            
            # Create backup using subprocess to handle cross-platform
            if os.name == 'nt':  # Windows
                subprocess.run(["xcopy", str(model_dir), str(backup_path), "/E", "/I"], check=True)
            else:  # Unix-like
                subprocess.run(["cp", "-r", str(model_dir), str(backup_path)], check=True)
            
            logger.info(f"Models backed up to {backup_path}")
            
        except Exception as e:
            logger.warning(f"Model backup failed: {e}")
    
    def _cleanup_old_models(self):
        """Remove old model backups"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.max_model_age_days)
            
            for backup_dir in self.backup_dir.glob("models_backup_*"):
                try:
                    # Parse timestamp from directory name
                    timestamp_str = backup_dir.name.replace("models_backup_", "")
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if backup_date < cutoff_date:
                        if backup_dir.is_dir():
                            import shutil
                            shutil.rmtree(backup_dir)
                            logger.info(f"Removed old backup: {backup_dir}")
                            
                except Exception as e:
                    logger.warning(f"Failed to cleanup {backup_dir}: {e}")
                    
        except Exception as e:
            logger.warning(f"Model cleanup failed: {e}")
    
    def _save_retrain_summary(self, summary: Dict[str, Any]):
        """Save retraining summary to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_path = self.log_dir / f"retrain_summary_{timestamp}.json"
            
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Retrain summary saved to {summary_path}")
            
        except Exception as e:
            logger.warning(f"Failed to save retrain summary: {e}")

def create_config_from_env() -> RetrainConfig:
    """Create retrain config from environment variables"""
    symbols = os.getenv("EMO_SYMBOLS", "SPY,QQQ").split(",")
    symbols = [s.strip().upper() for s in symbols]
    
    email_recipients = os.getenv("EMO_EMAIL_RECIPIENTS", "").split(",")
    email_recipients = [email.strip() for email in email_recipients if email.strip()]
    
    return RetrainConfig(
        symbols=symbols,
        models=os.getenv("EMO_ML_MODELS", "rf,lstm").split(","),
        performance_threshold=float(os.getenv("EMO_PERFORMANCE_THRESHOLD", "0.6")),
        max_retrain_time_minutes=int(os.getenv("EMO_MAX_RETRAIN_MINUTES", "120")),
        email_notifications=os.getenv("EMO_EMAIL_NOTIFICATIONS", "true").lower() == "true",
        email_recipients=email_recipients,
        backup_models=os.getenv("EMO_BACKUP_MODELS", "true").lower() == "true",
        cleanup_old_models=os.getenv("EMO_CLEANUP_OLD_MODELS", "true").lower() == "true",
        max_model_age_days=int(os.getenv("EMO_MAX_MODEL_AGE_DAYS", "30"))
    )

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Weekly ML Retraining")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--force", action="store_true", help="Force retrain all models")
    parser.add_argument("--status", action="store_true", help="Show model status only")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path("logs") / f"retrain_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
    
    # Initialize database
    try:
        DBRouter.init()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Create config
    config = create_config_from_env()
    
    # Create retraining engine
    engine = WeeklyRetrainEngine(config)
    
    try:
        if args.status:
            # Show model status only
            status = engine.performance_monitor.get_all_model_status(
                config.symbols, config.models
            )
            print(json.dumps(status, indent=2, default=str))
            
        elif args.dry_run:
            # Show what would be retrained
            logger.info("DRY RUN - Models that would be retrained:")
            for symbol in config.symbols:
                for model in config.models:
                    needs_retrain = engine.performance_monitor.needs_retraining(
                        symbol, model, config.performance_threshold
                    )
                    status = "RETRAIN" if needs_retrain else "SKIP"
                    logger.info(f"  {symbol}_{model}: {status}")
            
        else:
            # Run actual retraining
            if args.force:
                # Override performance monitoring
                engine.performance_monitor.needs_retraining = lambda s, m, t=None: True
                logger.info("FORCE MODE - All models will be retrained")
            
            summary = engine.run_weekly_retrain()
            
            if "error" in summary:
                logger.error(f"Retraining failed: {summary['error']}")
                sys.exit(1)
            else:
                logger.info("🏁 Weekly retrain completed successfully")
                
    except Exception as e:
        logger.error(f"Weekly retrain failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()