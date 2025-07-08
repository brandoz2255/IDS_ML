from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
import time

from ..db.database import get_db
from ..models.models import Alert
from ..services.detection import MLService
from ..auth.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    require_admin, fake_users_db, Token, User, ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..monitoring.metrics import get_metrics, REQUEST_COUNT, REQUEST_DURATION
from ..utils.logging import get_logger, log_api_request
from ..streaming.alert_processor import get_ingestion_service
from ..streaming.redis_client import get_redis_client

router = APIRouter()
logger = get_logger(__name__)

# Metrics endpoint
@router.get("/metrics")
def prometheus_metrics():
    """Expose Prometheus metrics"""
    return Response(get_metrics(), media_type="text/plain")

# Authentication endpoint
@router.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Protected endpoints
@router.get("/alerts", response_model=List[dict])
def get_alerts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    start_time = time.time()
    try:
        alerts = db.query(Alert).offset(skip).limit(limit).all()
        result = [alert.to_dict() for alert in alerts]
        
        # Log and track metrics
        duration = time.time() - start_time
        log_api_request(logger, "GET", "/alerts", current_user.username, duration, 200)
        REQUEST_COUNT.labels(method="GET", endpoint="get_alerts", status_code=200).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="get_alerts").observe(duration)
        
        return result
    except Exception as e:
        duration = time.time() - start_time
        log_api_request(logger, "GET", "/alerts", current_user.username, duration, 500)
        REQUEST_COUNT.labels(method="GET", endpoint="get_alerts", status_code=500).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="get_alerts").observe(duration)
        raise

@router.get("/alerts/recent", response_model=List[dict])
def get_recent_alerts(
    count: int = 10, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(count).all()
    return [alert.to_dict() for alert in alerts]

@router.post("/retrain")
def retrain_model(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    ml_service = MLService()
    background_tasks.add_task(ml_service.retrain_model)
    return {"message": "Model retraining initiated in the background."}

@router.get("/metrics")
def get_metrics(current_user: User = Depends(get_current_active_user)):
    # This would ideally fetch real-time metrics from the ML service
    return {"status": "Metrics endpoint not yet implemented. Placeholder data.", "accuracy": 0.95, "f1_score": 0.92}

@router.get("/status")
def get_status():
    try:
        redis_client = get_redis_client()
        redis_status = "connected"
        try:
            redis_client.redis_client.ping()
        except:
            redis_status = "disconnected"
        
        return {
            "status": "Backend is healthy", 
            "database": "connected", 
            "ml_model": "loaded",
            "redis": redis_status
        }
    except Exception as e:
        return {
            "status": "Backend is healthy", 
            "database": "connected", 
            "ml_model": "loaded",
            "redis": "error"
        }

# Stream management endpoints
@router.post("/alerts/ingest")
def ingest_alert(
    alert_data: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Manually ingest an alert into the processing stream"""
    try:
        ingestion_service = get_ingestion_service()
        success = ingestion_service.ingest_custom_alert(alert_data)
        
        if success:
            return {"message": "Alert ingested successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to ingest alert")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/streams/info")
def get_stream_info(current_user: User = Depends(get_current_active_user)):
    """Get information about processing streams"""
    try:
        redis_client = get_redis_client()
        
        raw_stream_info = redis_client.get_stream_info("raw_alerts")
        processed_stream_info = redis_client.get_stream_info("processed_alerts")
        
        return {
            "raw_alerts_stream": raw_stream_info,
            "processed_alerts_stream": processed_stream_info
        }
    except Exception as e:
        return {"error": str(e)}
