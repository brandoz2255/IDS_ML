# Development Guide

This guide covers development workflows, testing procedures, and deployment instructions for the AI-Enhanced IDS system.

## Quick Start

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Git

### Setup Development Environment

1. **Clone and Setup**:
```bash
git clone <repository>
cd ai_ids_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start Services**:
```bash
# Start full stack
docker-compose up --build -d

# Or start individual services for development
docker-compose up -d db redis  # Just database and Redis
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. **Verify Setup**:
```bash
# Check API health
curl http://localhost/api/status

# Get authentication token
curl -X POST "http://localhost/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

## Development Workflow

### Code Organization

```
app/
├── auth/           # Authentication and authorization
├── api/            # REST API endpoints
├── core/           # Core business logic (ML, Snort integration)
├── db/             # Database models and connections
├── models/         # Data models
├── services/       # Business services
├── streaming/      # Stream processing components
├── monitoring/     # Metrics and observability
├── utils/          # Utility functions
└── main.py         # Application entry point

tests/              # Test suite
├── conftest.py     # Test configuration
├── test_auth.py    # Authentication tests
├── test_api.py     # API tests
└── test_ml_engine.py # ML model tests

docs/               # Documentation
├── ENHANCEMENTS.md # Production enhancement details
├── DEVELOPMENT_GUIDE.md # This file
└── NOTES.md        # Original scaffolding notes
```

### Adding New Features

1. **Create Feature Branch**:
```bash
git checkout -b feature/new-feature-name
```

2. **Implement Feature**:
   - Add business logic in appropriate modules
   - Update API endpoints if needed
   - Add comprehensive tests
   - Update documentation

3. **Testing**:
```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=app tests/

# Run specific test categories
pytest tests/test_auth.py -v
```

4. **Code Quality**:
```bash
# Format code (future enhancement)
black app/ tests/

# Lint code (future enhancement)
flake8 app/ tests/
```

## Testing Guide

### Test Categories

#### 1. Authentication Tests (`test_auth.py`)
- Login success/failure scenarios
- Token validation and expiration
- Permission enforcement
- Role-based access control

```bash
pytest tests/test_auth.py::test_login_success -v
```

#### 2. API Tests (`test_api.py`)
- CRUD operations on alerts
- Pagination and filtering
- Error handling
- Stream processing endpoints

```bash
pytest tests/test_api.py::test_get_alerts_with_data -v
```

#### 3. ML Engine Tests (`test_ml_engine.py`)
- Model initialization and loading
- Inference accuracy and performance
- Training pipeline validation
- CUDA/CPU compatibility

```bash
pytest tests/test_ml_engine.py::test_ml_service_prediction -v
```

### Writing Tests

#### Test Structure
```python
def test_feature_name(client, auth_headers, db_session):
    """Test description"""
    # Arrange
    test_data = {"key": "value"}
    
    # Act
    response = client.post("/api/endpoint", 
                          json=test_data, 
                          headers=auth_headers)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["key"] == "expected_value"
```

#### Using Fixtures
```python
# Use auth_headers fixture for authenticated requests
def test_protected_endpoint(client, auth_headers):
    response = client.get("/api/alerts", headers=auth_headers)
    assert response.status_code == 200

# Use db_session fixture for database tests
def test_database_operation(db_session, sample_alert_data):
    alert = Alert(**sample_alert_data)
    db_session.add(alert)
    db_session.commit()
    
    retrieved = db_session.query(Alert).first()
    assert retrieved.source_ip == sample_alert_data["source_ip"]
```

## API Development

### Authentication Flow

All API endpoints (except `/api/status` and `/api/auth/login`) require authentication:

```python
# Get token
@router.post("/auth/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authenticate user and return JWT token

# Protected endpoint
@router.get("/alerts")
def get_alerts(current_user: User = Depends(get_current_active_user)):
    # Only accessible with valid JWT token
```

### Adding New Endpoints

1. **Define Route**:
```python
@router.get("/new-endpoint")
def new_endpoint(
    param: str = Query(..., description="Parameter description"),
    current_user: User = Depends(get_current_active_user)
):
    """Endpoint description"""
    # Implementation
    return {"result": "data"}
```

2. **Add Tests**:
```python
def test_new_endpoint(client, auth_headers):
    response = client.get("/api/new-endpoint?param=value", 
                         headers=auth_headers)
    assert response.status_code == 200
```

3. **Update Documentation**:
   - Add endpoint to API documentation
   - Update CLAUDE.md with usage examples

### Error Handling

```python
from fastapi import HTTPException

@router.get("/endpoint")
def endpoint(current_user: User = Depends(get_current_active_user)):
    try:
        # Business logic
        result = process_data()
        return {"result": result}
    except SpecificError as e:
        logger.error("Specific error occurred", error=str(e))
        raise HTTPException(status_code=400, detail="Specific error message")
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
```

## ML Model Development

### Model Architecture

The system supports two model types:

1. **SimpleMLP**: Basic multi-layer perceptron
2. **EnhancedMLP**: Advanced model with batch normalization and residual connections

```python
# Use enhanced model (recommended)
ml_service = MLService(use_enhanced=True)

# Model configuration
input_size = 25     # Number of features
hidden_size = 64    # Hidden layer size
num_classes = 2     # Binary classification (normal/anomaly)
```

### Feature Engineering

Features are extracted using `NetworkFeatureExtractor`:

```python
extractor = NetworkFeatureExtractor()
features = extractor.extract_features({
    'source_ip': '192.168.1.100',
    'destination_ip': '10.0.0.1',
    'source_port': 12345,
    'destination_port': 80,
    'protocol': 'TCP',
    'alert_message': 'Suspicious activity detected'
})
# Returns 25 numerical features
```

### Model Training

```python
# Initialize ML service
ml_service = MLService()

# Retrain model (currently uses dummy data)
ml_service.retrain_model()

# In production, this would:
# 1. Load historical data from database
# 2. Extract features using NetworkFeatureExtractor
# 3. Train model with proper train/validation split
# 4. Evaluate performance and save metrics
# 5. Save trained model and preprocessing components
```

### Adding New Features

1. **Extend Feature Extractor**:
```python
def _extract_new_features(self, alert_data):
    """Extract new type of features"""
    features = []
    # Add feature extraction logic
    return features

def extract_features(self, alert_data):
    # Add to existing feature extraction
    features.extend(self._extract_new_features(alert_data))
```

2. **Update Model Input Size**:
```python
# Update in MLService.__init__
self.input_size = 30  # Updated feature count
```

3. **Test New Features**:
```python
def test_new_feature_extraction():
    extractor = NetworkFeatureExtractor()
    features = extractor.extract_features(sample_data)
    assert len(features) == 30  # Updated count
    assert all(isinstance(f, (int, float)) for f in features)
```

## Stream Processing Development

### Architecture Overview

```
Snort/External → Redis Stream → Alert Processor → Database
                     ↓              ↓
                 Raw Alerts    Feature Extraction
                                     ↓
                              ML Inference
                                     ↓
                             Enhanced Alerts
```

### Adding Alert Sources

1. **Implement Ingestion**:
```python
def ingest_new_source_alert(self, alert_data: Dict[str, Any]) -> bool:
    """Ingest alert from new source"""
    try:
        # Add source metadata
        alert_data['source'] = 'new_source'
        alert_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
        
        # Publish to stream
        message_id = self.redis_client.publish_alert(
            self.raw_alerts_stream,
            alert_data
        )
        return True
    except Exception as e:
        logger.error("Failed to ingest alert", error=str(e))
        return False
```

2. **Add API Endpoint**:
```python
@router.post("/alerts/ingest-new-source")
def ingest_new_source(
    alert_data: dict,
    current_user: User = Depends(get_current_active_user)
):
    ingestion_service = get_ingestion_service()
    success = ingestion_service.ingest_new_source_alert(alert_data)
    if success:
        return {"message": "Alert ingested successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to ingest alert")
```

### Processing Customization

1. **Custom Processing Logic**:
```python
async def _process_custom_alert(self, alert_data: Dict[str, Any]):
    """Custom processing for specific alert types"""
    if alert_data.get('source') == 'custom_source':
        # Apply custom processing logic
        alert_data = self._apply_custom_transformations(alert_data)
    
    # Continue with standard processing
    return await self._process_single_alert(alert_data)
```

2. **Custom Feature Extraction**:
```python
def extract_custom_features(self, alert_data: Dict[str, Any]) -> List[float]:
    """Extract features specific to custom alert types"""
    if alert_data.get('source') == 'custom_source':
        return self._extract_custom_source_features(alert_data)
    else:
        return self.extract_features(alert_data)
```

## Monitoring and Debugging

### Structured Logging

```python
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Log with context
logger.info("Processing started", 
           user_id=user.id, 
           endpoint="/api/alerts",
           request_id=request_id)

# Log errors with context
logger.error("Processing failed", 
            error=str(e),
            context={"user_id": user.id, "data": alert_data})
```

### Metrics Collection

```python
from app.monitoring.metrics import record_alert_processed, ML_INFERENCE_DURATION

# Record business metrics
record_alert_processed(alert_type="scan", ml_prediction=1)

# Record performance metrics
@track_ml_inference
def process_ml_inference(data):
    return ml_model.predict(data)

# Custom metrics
from prometheus_client import Counter
CUSTOM_METRIC = Counter('custom_events_total', 'Custom events')
CUSTOM_METRIC.inc()
```

### Debugging Tools

1. **Database Inspection**:
```python
# Check recent alerts
curl -H "Authorization: Bearer <token>" \
  "http://localhost/api/alerts/recent?count=5"

# Check stream status
curl -H "Authorization: Bearer <token>" \
  "http://localhost/api/streams/info"
```

2. **Redis Debugging**:
```bash
# Connect to Redis container
docker exec -it <redis-container> redis-cli

# Check streams
XINFO STREAM raw_alerts
XINFO STREAM processed_alerts

# Monitor stream activity
MONITOR
```

3. **Log Analysis**:
```bash
# Follow application logs
docker-compose logs -f backend

# Filter specific log types
docker-compose logs backend | grep "ERROR"
docker-compose logs backend | grep "ML inference"
```

## Deployment

### Development Deployment

```bash
# Start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Production Considerations

1. **Environment Variables**:
```bash
# Required for production
export SECRET_KEY="your-production-secret-key-256-bits"
export DATABASE_URL="postgresql://user:pass@prod-host:5432/db"
export REDIS_HOST="prod-redis-host"
export REDIS_PASSWORD="redis-password"
```

2. **Security**:
   - Use strong JWT secret keys
   - Enable Redis authentication
   - Configure HTTPS with reverse proxy
   - Set up proper firewall rules

3. **Monitoring**:
   - Configure Prometheus to scrape `/api/metrics`
   - Set up log aggregation (ELK stack)
   - Configure alerting rules
   - Set up health check monitoring

4. **Scaling**:
   - Use multiple alert processor instances
   - Configure Redis clustering
   - Set up database read replicas
   - Implement load balancing

### Health Checks

```bash
# API health
curl http://localhost/api/status

# Prometheus metrics
curl http://localhost/api/metrics

# Database connectivity
docker exec <postgres-container> pg_isready

# Redis connectivity
docker exec <redis-container> redis-cli ping
```

## Contributing

### Code Standards

1. **Follow existing patterns**:
   - Use dependency injection with FastAPI
   - Implement comprehensive error handling
   - Add structured logging to all operations
   - Include metrics for performance tracking

2. **Testing Requirements**:
   - Write tests for all new functionality
   - Maintain >80% code coverage
   - Include integration tests for API endpoints
   - Test error conditions and edge cases

3. **Documentation**:
   - Update API documentation
   - Add docstrings to all functions
   - Update CLAUDE.md with new features
   - Include usage examples

### Pull Request Process

1. Create feature branch from main
2. Implement feature with tests
3. Run full test suite: `pytest tests/ -v`
4. Update documentation
5. Submit pull request with detailed description
6. Address code review feedback
7. Merge after approval

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
```bash
# Check token validity
curl -H "Authorization: Bearer <token>" "http://localhost/api/auth/me"

# Refresh token
curl -X POST "http://localhost/api/auth/login" \
  -d "username=admin&password=secret"
```

2. **Database Connection Issues**:
```bash
# Check database container
docker-compose logs db

# Test connection
docker exec <postgres-container> psql -U user -d snortdb -c "\dt"
```

3. **Redis Connection Issues**:
```bash
# Check Redis container
docker-compose logs redis

# Test connection
docker exec <redis-container> redis-cli ping
```

4. **ML Model Issues**:
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Test model loading
python -c "from app.core.ml_engine import MLService; ml = MLService()"
```

### Performance Issues

1. **Slow API Responses**:
   - Check Prometheus metrics at `/api/metrics`
   - Review structured logs for slow operations
   - Monitor database query performance

2. **High Memory Usage**:
   - Monitor ML model memory usage
   - Check for memory leaks in alert processing
   - Review Redis memory usage

3. **Stream Processing Lag**:
   - Check Redis stream backlog
   - Monitor alert processing metrics
   - Scale alert processor instances

For additional support, refer to the research documentation in `/research/` directory.