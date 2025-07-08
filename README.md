# AI-Powered Intrusion Detection System (IDS) Backend

This project implements the backend for an AI-powered Intrusion Detection System, integrating Snort for signature-based detection with a PyTorch-based machine learning engine for anomaly detection. The system is orchestrated using Docker Compose, with FastAPI providing the RESTful API and PostgreSQL as the primary database.

## Features

- **FastAPI**: High-performance web framework for building APIs.
- **PyTorch**: Machine learning engine for anomaly detection and behavior-based classification.
- **PostgreSQL**: Robust relational database for storing alerts and system data.
- **PgAdmin**: Web-based administration tool for PostgreSQL.
- **Snort Integration**: Real-time processing of network traffic and alerts.
- **Docker Compose**: For easy setup and orchestration of all services.
- **NGINX**: Reverse proxy for routing API requests to the FastAPI backend.
- **MLSecOps Pipeline**: Designed for secure, automated, and reproducible ML lifecycle.

## Project Structure

```
ai_ids_backend/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── snort_wrapper.py
│   │   └── ml_engine.py
│   ├── models/
│   │   └── models.py
│   ├── services/
│   │   └── detection.py
│   ├── db/
│   │   └── database.py
│   ├── utils/
│   │   └── log_parser.py
│   ├── main.py
│   └── config.py
├── nginx/
│   └── default.conf
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.snort
├── snort.conf
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd ai_ids_backend
    ```

2.  **Build and run with Docker Compose:**

    ```bash
    docker-compose up --build -d
    ```

    This command will:
    - Build the `backend` (FastAPI) and `snort` Docker images.
    - Start the PostgreSQL database, PgAdmin, NGINX, FastAPI backend, and Snort services.

3.  **Access Services:**

    - **FastAPI**: Accessible via NGINX at `http://localhost/api/`
    - **PgAdmin**: Accessible at `http://localhost:8081` (default email: `admin@ids.local`, password: `admin`)

## Usage

### FastAPI Endpoints

-   `GET /api/alerts`: Get all alerts.
-   `GET /api/alerts/recent`: Get recent N alerts.
-   `POST /api/retrain`: Trigger ML model retraining (runs in background).
-   `GET /api/metrics`: Placeholder for ML performance metrics.
-   `GET /api/status`: System health check.

### Snort

The Snort container runs Snort in IDS mode, logging alerts to `/var/log/snort/alert`. The `snort_wrapper.py` in the backend tails this log file and processes new alerts.

### Machine Learning

The `ml_engine.py` handles PyTorch model loading, inference, and retraining. It is configured to use CUDA if available on your system (e.g., RTX 3070).

## Development

### Running Locally (without Docker)

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run FastAPI:**

    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

3.  **Run Snort Wrapper (for log processing):**

    ```bash
    python app/core/snort_wrapper.py
    ```

    *Note: You will need Snort installed and configured on your host system for this to work.*

### Retraining the ML Model

You can trigger model retraining via the API:

```bash
curl -X POST http://localhost/api/retrain
```

## Future Enhancements

-   Implement robust feature engineering for ML model.
-   Integrate MLflow or DVC for model versioning and experiment tracking.
-   Add Prometheus and Grafana for comprehensive monitoring.
-   Develop a user interface for alert visualization and feedback.
-   Implement more sophisticated Snort rule management.

