# JHA ML Platform

A comprehensive machine learning model management and monitoring platform with a rich UI for experimentation, evaluation, and production monitoring.

## Overview

The JHA ML Platform provides:
- **Project Management** - Create and manage ML model projects
- **Experiment Tracking** - Monitor experiment runs with detailed metrics
- **Model Evaluation** - Comprehensive evaluation views including confusion matrices, ROC curves, and feature importance
- **Monitoring & Alerts** - Real-time prediction monitoring, drift detection, and performance tracking
- **Explainability** - Global and local model explainability with SHAP values
- **Deployment** - Model endpoints, version management, and champion/challenger testing
- **Governance** - Bias & fairness analysis, calibration, and compliance tracking

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (handled by Docker Compose)

### Running with Docker

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/jha_ml_platform
   ```

2. **Copy the environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Build and start the containers:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   Open your browser and navigate to: `http://localhost:8000`

5. **Stop the containers:**
   ```bash
   docker-compose down
   ```

### Makefile Commands

Convenient development commands are available:

```bash
make build          # Build Docker image
make up             # Start containers
make down           # Stop containers
make logs           # View container logs
make test           # Run tests
make db-reset       # Reset database
make db-migrate     # Run migrations
make install        # Install Python dependencies
make clean          # Clean up artifacts
```

Example:
```bash
make up             # Start the application
make logs           # Watch the logs
```

## Development

### Local Python Setup (without Docker)

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Project Structure

```
jha_ml_platform/
├── backend/              # FastAPI application
│   ├── main.py          # Main application entry point
│   ├── config.py        # Configuration management
│   ├── models.py        # ORM models (SQLAlchemy)
│   ├── schemas.py       # Pydantic request/response models
│   └── api/             # API route modules
├── frontend/            # Web UI assets
│   ├── index.html       # Main HTML file
│   └── static/
│       ├── css/         # Stylesheets
│       ├── js/          # JavaScript files
│       └── assets/      # Images and other assets
├── database/            # Database-related files
│   └── init.sql         # Database schema
├── docker/              # Docker configuration
├── storage/             # File storage (models, datasets)
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
├── Makefile             # Development commands
└── .env.example         # Environment variables template
```

## API Documentation

### Auto-Generated Docs

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy", "service": "JHA ML Platform"}
```

## Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Key variables:
- `DB_USER` - PostgreSQL username (default: admin)
- `DB_PASSWORD` - PostgreSQL password (default: password)
- `DB_NAME` - Database name (default: jha_ml_platform)
- `DEBUG` - Debug mode (default: True)
- `APP_PORT` - Application port (default: 8000)

## Database

### Schema

The platform uses PostgreSQL with the following main tables:
- `projects` - ML model projects
- `datasets` - Training datasets
- `experiments` - Model training runs
- `predictions` - Real-time predictions
- `models` - Trained model artifacts

### Migrations

Database schema is initialized automatically on container startup via `database/init.sql`.

For schema changes, update `database/init.sql` and restart the containers:
```bash
make db-reset       # Full reset
```

## Architecture

### Components

1. **Frontend** - React-based UI with comprehensive ML workflow views
2. **Backend API** - FastAPI REST API
3. **Database** - PostgreSQL for persistent storage
4. **Storage** - Local file system or S3 for models/datasets

### Data Flow

```
Frontend (HTML/CSS/JS)
    ↓
FastAPI Backend
    ↓
PostgreSQL Database
    ↓
File Storage (models, datasets)
```

## Features by Section

### Dashboard
- Project overview and statistics
- Quick access to all projects
- Project creation wizard

### Project Views
Each project provides:
- Dataset management
- Experiment tracking and history
- Model evaluation (confusion matrix, ROC, precision-recall)
- Feature importance and SHAP explainability
- Bias & fairness analysis
- Calibration metrics
- Champion/challenger comparison
- Live prediction monitoring
- Model drift detection
- Labeling and feedback loops

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, modify `.env`:
```bash
APP_PORT=8001
```

### Database Connection Error
Ensure PostgreSQL container is healthy:
```bash
docker-compose ps        # Check container status
docker-compose logs db   # View database logs
```

### Frontend Not Loading
Check that static files are properly mounted:
```bash
docker-compose logs app  # Check application logs
```

## Contributing

To contribute to the JHA ML Platform:

1. Create a branch for your feature
2. Make changes and test locally
3. Commit with clear messages
4. Submit a pull request

## License

[Add license information here]

## Support

For issues, questions, or feature requests, please contact the JHA team.

---

**Version**: 0.1.0
**Last Updated**: March 2026
