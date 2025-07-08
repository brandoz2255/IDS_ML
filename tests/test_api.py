import pytest
from app.models.models import Alert

def test_get_alerts_empty(client, auth_headers):
    """Test getting alerts when database is empty"""
    response = client.get("/api/alerts", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_get_alerts_with_data(client, auth_headers, db_session, sample_alert_data):
    """Test getting alerts with sample data"""
    # Insert sample alert
    alert = Alert(**sample_alert_data)
    db_session.add(alert)
    db_session.commit()
    
    response = client.get("/api/alerts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source_ip"] == sample_alert_data["source_ip"]

def test_get_alerts_pagination(client, auth_headers, db_session, sample_alert_data):
    """Test alert pagination"""
    # Insert multiple alerts
    for i in range(15):
        alert_data = sample_alert_data.copy()
        alert_data["source_ip"] = f"192.168.1.{i}"
        alert = Alert(**alert_data)
        db_session.add(alert)
    db_session.commit()
    
    # Test default limit
    response = client.get("/api/alerts", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 15
    
    # Test custom limit
    response = client.get("/api/alerts?limit=5", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 5
    
    # Test skip
    response = client.get("/api/alerts?skip=10&limit=5", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 5

def test_get_recent_alerts(client, auth_headers, db_session, sample_alert_data):
    """Test getting recent alerts"""
    # Insert sample alerts
    for i in range(5):
        alert_data = sample_alert_data.copy()
        alert_data["source_ip"] = f"192.168.1.{i}"
        alert = Alert(**alert_data)
        db_session.add(alert)
    db_session.commit()
    
    response = client.get("/api/alerts/recent", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

def test_get_recent_alerts_custom_count(client, auth_headers, db_session, sample_alert_data):
    """Test getting recent alerts with custom count"""
    # Insert sample alerts
    for i in range(10):
        alert_data = sample_alert_data.copy()
        alert_data["source_ip"] = f"192.168.1.{i}"
        alert = Alert(**alert_data)
        db_session.add(alert)
    db_session.commit()
    
    response = client.get("/api/alerts/recent?count=3", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_retrain_model_as_admin(client, auth_headers):
    """Test model retraining as admin"""
    response = client.post("/api/retrain", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "retraining initiated" in data["message"].lower()

def test_get_metrics_placeholder(client, auth_headers):
    """Test getting metrics (placeholder)"""
    response = client.get("/api/metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "f1_score" in data

def test_get_status(client):
    """Test status endpoint (public)"""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Backend is healthy"

def test_prometheus_metrics(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]