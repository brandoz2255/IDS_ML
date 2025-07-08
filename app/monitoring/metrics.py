from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from functools import wraps
from typing import Callable

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ALERT_COUNT = Counter(
    'alerts_total',
    'Total alerts processed',
    ['alert_type', 'ml_prediction']
)

ML_INFERENCE_DURATION = Histogram(
    'ml_inference_duration_seconds',
    'ML inference duration in seconds'
)

ML_MODEL_ACCURACY = Gauge(
    'ml_model_accuracy',
    'Current ML model accuracy'
)

ACTIVE_CONNECTIONS = Gauge(
    'active_database_connections',
    'Active database connections'
)

SNORT_ALERTS_PROCESSED = Counter(
    'snort_alerts_processed_total',
    'Total Snort alerts processed'
)

def track_request_metrics(func: Callable) -> Callable:
    """Decorator to track HTTP request metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(
                method="GET",  # This would be dynamic in a real implementation
                endpoint=func.__name__,
                status_code=200
            ).inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(
                method="GET",
                endpoint=func.__name__,
                status_code=500
            ).inc()
            raise
        finally:
            REQUEST_DURATION.labels(
                method="GET",
                endpoint=func.__name__
            ).observe(time.time() - start_time)
    
    return wrapper

def track_ml_inference(func: Callable) -> Callable:
    """Decorator to track ML inference metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            ML_INFERENCE_DURATION.observe(time.time() - start_time)
            return result
        except Exception as e:
            ML_INFERENCE_DURATION.observe(time.time() - start_time)
            raise
    
    return wrapper

def record_alert_processed(alert_type: str, ml_prediction: int):
    """Record an alert being processed"""
    prediction_label = "anomaly" if ml_prediction == 1 else "normal"
    ALERT_COUNT.labels(
        alert_type=alert_type,
        ml_prediction=prediction_label
    ).inc()

def record_snort_alert():
    """Record a Snort alert being processed"""
    SNORT_ALERTS_PROCESSED.inc()

def update_model_accuracy(accuracy: float):
    """Update the current model accuracy metric"""
    ML_MODEL_ACCURACY.set(accuracy)

def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest()