#!/usr/bin/env python3
"""
Performance Monitoring System for EMO Options Bot
=================================================
Provides comprehensive performance tracking and optimization:
- Database query performance monitoring
- Order processing latency tracking
- Memory and CPU usage monitoring
- System health metrics collection
- Performance optimization suggestions
- Bottleneck identification and reporting

This system integrates with the health monitoring to provide detailed
performance insights for institutional deployments.
"""

import time
import psutil
import threading
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from collections import deque, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import functools

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Single performance measurement."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }

class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics = deque(maxlen=max_metrics)
        self.aggregations = defaultdict(list)
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Performance thresholds
        self.thresholds = {
            'db_query_ms': 100.0,        # Database queries > 100ms
            'order_processing_ms': 50.0,  # Order processing > 50ms
            'memory_usage_pct': 80.0,     # Memory usage > 80%
            'cpu_usage_pct': 90.0,        # CPU usage > 90%
        }
        
        # Start background monitoring
        self._start_system_monitoring()
    
    def record_metric(self, name: str, value: float, unit: str = "", tags: Dict[str, str] = None) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc),
            tags=tags or {}
        )
        
        with self.lock:
            self.metrics.append(metric)
            self.aggregations[name].append(value)
            
            # Keep only recent values for aggregations
            if len(self.aggregations[name]) > 1000:
                self.aggregations[name] = self.aggregations[name][-1000:]
    
    @contextmanager
    def measure_time(self, operation_name: str, tags: Dict[str, str] = None):
        """Context manager for measuring operation duration."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_metric(
                name=f"{operation_name}_duration",
                value=duration_ms,
                unit="ms",
                tags=tags or {}
            )
    
    def measure_function(self, func_name: str = None, tags: Dict[str, str] = None):
        """Decorator for measuring function execution time."""
        def decorator(func: Callable) -> Callable:
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.measure_time(name, tags):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_metrics_summary(self, last_minutes: int = 5) -> Dict[str, Any]:
        """Get performance metrics summary."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (last_minutes * 60)
        
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp.timestamp() > cutoff_time
        ]
        
        summary = {
            'total_metrics': len(self.metrics),
            'recent_metrics': len(recent_metrics),
            'uptime_seconds': time.time() - self.start_time,
            'performance_summary': {}
        }
        
        # Aggregate by metric name
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.name].append(metric.value)
        
        for name, values in metric_groups.items():
            if values:
                summary['performance_summary'][name] = {
                    'count': len(values),
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'unit': recent_metrics[0].unit if recent_metrics else ""
                }
        
        return summary
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on thresholds."""
        alerts = []
        
        # Check recent metrics against thresholds
        recent_summary = self.get_metrics_summary(last_minutes=2)
        
        for metric_name, stats in recent_summary['performance_summary'].items():
            threshold_key = metric_name.replace('_duration', '_ms')
            if threshold_key in self.thresholds:
                threshold = self.thresholds[threshold_key]
                if stats['avg'] > threshold:
                    alerts.append({
                        'metric': metric_name,
                        'current_value': stats['avg'],
                        'threshold': threshold,
                        'severity': 'warning' if stats['avg'] < threshold * 1.5 else 'critical',
                        'message': f"{metric_name} average ({stats['avg']:.1f}) exceeds threshold ({threshold})"
                    })
        
        return alerts
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get performance optimization suggestions."""
        suggestions = []
        alerts = self.get_performance_alerts()
        
        for alert in alerts:
            metric = alert['metric']
            if 'db_query' in metric:
                suggestions.append("Consider adding database indexes or optimizing queries")
            elif 'order_processing' in metric:
                suggestions.append("Consider batch processing or async order handling")
            elif 'memory_usage' in metric:
                suggestions.append("Consider implementing memory cleanup or increasing memory allocation")
            elif 'cpu_usage' in metric:
                suggestions.append("Consider implementing caching or horizontal scaling")
        
        return list(set(suggestions))  # Remove duplicates
    
    def _start_system_monitoring(self):
        """Start background system monitoring."""
        def monitor_system():
            while True:
                try:
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.record_metric('system_cpu_usage', cpu_percent, 'percent')
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.record_metric('system_memory_usage', memory.percent, 'percent')
                    self.record_metric('system_memory_available', memory.available / (1024**3), 'GB')
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    disk_percent = (disk.used / disk.total) * 100
                    self.record_metric('system_disk_usage', disk_percent, 'percent')
                    
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.warning(f"System monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def export_metrics(self, format_type: str = "json") -> Any:
        """Export metrics in specified format."""
        if format_type == "json":
            return {
                'metrics': [m.to_dict() for m in list(self.metrics)],
                'summary': self.get_metrics_summary(),
                'alerts': self.get_performance_alerts(),
                'suggestions': self.get_optimization_suggestions(),
                'export_timestamp': datetime.now(timezone.utc).isoformat()
            }
        else:
            raise ValueError(f"Unsupported format: {format_type}")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience functions
def record_metric(name: str, value: float, unit: str = "", tags: Dict[str, str] = None) -> None:
    """Record a performance metric."""
    performance_monitor.record_metric(name, value, unit, tags)

def measure_time(operation_name: str, tags: Dict[str, str] = None):
    """Context manager for measuring operation duration."""
    return performance_monitor.measure_time(operation_name, tags)

def measure_function(func_name: str = None, tags: Dict[str, str] = None):
    """Decorator for measuring function execution time."""
    return performance_monitor.measure_function(func_name, tags)

def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary."""
    return performance_monitor.get_metrics_summary()

def get_performance_alerts() -> List[Dict[str, Any]]:
    """Get performance alerts."""
    return performance_monitor.get_performance_alerts()

# Database monitoring helpers
@contextmanager
def monitor_db_query(query_type: str = "unknown"):
    """Monitor database query performance."""
    with measure_time("db_query_duration", {"query_type": query_type}):
        yield

def monitor_order_processing(operation: str = "unknown"):
    """Monitor order processing performance."""
    return measure_time("order_processing_duration", {"operation": operation})