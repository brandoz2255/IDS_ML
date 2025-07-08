import structlog
import logging
import sys
from typing import Any, Dict

def setup_logging():
    """Setup structured logging configuration"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)

def log_api_request(logger: structlog.stdlib.BoundLogger, 
                   method: str, 
                   endpoint: str, 
                   user: str = None,
                   duration: float = None,
                   status_code: int = None):
    """Log API request with structured data"""
    logger.info(
        "API request",
        method=method,
        endpoint=endpoint,
        user=user,
        duration=duration,
        status_code=status_code
    )

def log_ml_inference(logger: structlog.stdlib.BoundLogger,
                    model_name: str,
                    input_features: int,
                    prediction: int,
                    confidence: float = None,
                    duration: float = None):
    """Log ML inference with structured data"""
    logger.info(
        "ML inference",
        model_name=model_name,
        input_features=input_features,
        prediction=prediction,
        confidence=confidence,
        duration=duration
    )

def log_alert_processed(logger: structlog.stdlib.BoundLogger,
                       alert_id: str,
                       source_ip: str,
                       destination_ip: str,
                       alert_type: str,
                       ml_prediction: int,
                       snort_sid: int = None):
    """Log alert processing with structured data"""
    logger.info(
        "Alert processed",
        alert_id=alert_id,
        source_ip=source_ip,
        destination_ip=destination_ip,
        alert_type=alert_type,
        ml_prediction=ml_prediction,
        snort_sid=snort_sid
    )

def log_error(logger: structlog.stdlib.BoundLogger,
              error_type: str,
              error_message: str,
              context: Dict[str, Any] = None):
    """Log error with structured data"""
    logger.error(
        "Error occurred",
        error_type=error_type,
        error_message=error_message,
        context=context or {}
    )