# Backend Scaffolding Notes

This document outlines the steps taken to scaffold the AI-Powered IDS Backend, adhering to the provided requirements and incorporating the user's specific hardware (RTX 3070).

## 1. Initial Setup and Directory Structure

-   **Action**: Created the main project directory `ai_ids_backend` and its subdirectories as per the `PRP.txt`.
-   **Rationale**: Established a clear and organized project structure to facilitate development and maintainability.

    ```bash
    mkdir -p ai_ids_backend/app/api \
             ai_ids_backend/app/core \
             ai_ids_backend/app/models \
             ai_ids_backend/app/services \
             ai_ids_backend/app/db \
             ai_ids_backend/app/utils \
             ai_ids_backend/nginx \
             ai_ids_backend/docker
    ```

## 2. Docker Compose Configuration (`docker-compose.yml`)

-   **Action**: Created `docker-compose.yml` to define and link all services.
-   **Rationale**: Enables easy orchestration of FastAPI, PostgreSQL, PgAdmin, NGINX, and Snort containers, ensuring a consistent development and deployment environment.
-   **Key configurations**:
    -   `backend`: FastAPI application, depends on `db`.
    -   `snort`: Custom Dockerfile for Snort, with `NET_ADMIN` capability and a command to run Snort and tail its alert log.
    -   `db`: PostgreSQL 15 image with environment variables for database name, user, and password.
    -   `pgadmin`: PgAdmin 4 for database management, exposed on port 8081.
    -   `nginx`: NGINX latest image, configured as a reverse proxy for the `backend`.

## 3. Dependency Management (`requirements.txt`)

-   **Action**: Created `requirements.txt` with necessary Python packages.
-   **Rationale**: Ensures all Python dependencies (FastAPI, Uvicorn, SQLAlchemy, psycopg2-binary, PyTorch, pydantic-settings, python-dotenv) are explicitly listed for consistent installations.

## 4. NGINX Configuration (`nginx/default.conf`)

-   **Action**: Created `nginx/default.conf`.
-   **Rationale**: Configures NGINX to listen on port 80 and proxy requests to `/api/` to the FastAPI `backend` service, providing a single entry point and potentially handling SSL termination in a production environment.

## 5. Dockerfiles (`docker/Dockerfile.backend`, `docker/Dockerfile.snort`)

-   **Action**: Created `Dockerfile.backend` and `Dockerfile.snort`.
-   **Rationale**: Defines how the FastAPI application and Snort environment are built into Docker images, ensuring portability and isolation.
    -   `Dockerfile.backend`: Python 3.9 slim image, installs dependencies, copies application code, and runs Uvicorn.
    -   `Dockerfile.snort`: Ubuntu 22.04 base, installs Snort and its dependencies, sets up Snort directories, and includes a basic `snort.conf` and a local rule.

## 6. Snort Configuration (`snort.conf`)

-   **Action**: Created a basic `snort.conf`.
-   **Rationale**: Provides a minimal configuration for Snort within its Docker container, including rule paths and alert output settings.

## 7. FastAPI Application Structure (`app/` directory)

-   **Action**: Populated the `app/` directory with initial Python files as per the `PRP.txt`.
-   **Rationale**: Implements the core logic of the FastAPI application.
    -   `main.py`: FastAPI application entry point, includes router and initializes the database on startup.
    -   `config.py`: Handles environment variable loading for database URL using `pydantic-settings`.
    -   `api/routes.py`: Defines REST API endpoints for alerts (fetching recent, all), retraining the ML model, and health checks.
    -   `core/snort_wrapper.py`: Manages Snort subprocess, tails the alert log, and prints new alerts. (Note: Integration with `log_parser` and `detection` service is commented out for now, to be uncommented once fully implemented).
    -   `core/ml_engine.py`: Contains the PyTorch model (`SimpleMLP`), handles model loading, saving, prediction, and a dummy retraining process.
        -   **CUDA Integration**: Modified to detect and utilize CUDA (your RTX 3070) if available, otherwise falls back to CPU. This was done by adding `self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")` and moving tensors/models to this device.
    -   `models/models.py`: Defines the SQLAlchemy `Alert` model for PostgreSQL, including fields for alert details, ML prediction, and Snort SID.
    -   `db/database.py`: Sets up SQLAlchemy engine, session management, and a function to initialize the database schema.
    -   `services/detection.py`: Contains `DetectionService` to process Snort log lines, perform ML inference, and save alerts to the database.
    -   `utils/log_parser.py`: Provides a `parse_snort_log` function to extract structured data from Snort alert lines using regular expressions.

## 8. README.md

-   **Action**: Created a comprehensive `README.md`.
-   **Rationale**: Provides an overview of the project, features, setup instructions, usage details, and future enhancements, serving as the primary documentation for users and developers.

## 9. Docs Directory

-   **Action**: Created a `docs` directory.
-   **Rationale**: To store additional documentation, such as this `NOTES.md` file, providing a detailed record of the scaffolding process and design decisions.

This completes the initial scaffolding of the backend. The next steps would involve further refinement of the ML model, more robust error handling, and comprehensive testing.