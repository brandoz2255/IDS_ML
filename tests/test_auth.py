import pytest
from fastapi.testclient import TestClient

def test_login_success(client):
    """Test successful login"""
    login_data = {"username": "admin", "password": "secret"}
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {"username": "admin", "password": "wrong"}
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    login_data = {"username": "nonexistent", "password": "secret"}
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 401

def test_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without token"""
    response = client.get("/api/alerts")
    assert response.status_code == 403

def test_protected_endpoint_with_token(client, auth_headers):
    """Test accessing protected endpoint with valid token"""
    response = client.get("/api/alerts", headers=auth_headers)
    assert response.status_code == 200

def test_admin_endpoint_as_user(client):
    """Test accessing admin endpoint as regular user"""
    # Login as analyst
    login_data = {"username": "analyst", "password": "secret"}
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access admin endpoint
    response = client.post("/api/retrain", headers=headers)
    assert response.status_code == 403

def test_admin_endpoint_as_admin(client, auth_headers):
    """Test accessing admin endpoint as admin"""
    response = client.post("/api/retrain", headers=auth_headers)
    assert response.status_code == 200

def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"