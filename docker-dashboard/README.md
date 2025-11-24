# Docker Multi-Container Dashboard

A three-tier web application demonstrating Docker fundamentals including custom images, container orchestration, networking, and persistent storage.

## Architecture
```
Frontend (nginx:alpine) :8080
    ↓
Backend (Python/Flask) :5000
    ↓
Database (PostgreSQL) :5432
```

## Features

- **Frontend**: Static HTML dashboard served by nginx
- **Backend**: Python Flask REST API
- **Database**: PostgreSQL with persistent volume storage
- **Networking**: Custom bridge network for inter-container communication
- **Configuration**: Environment variables for database credentials

## Technologies Used

- Docker & Docker Compose
- nginx (Alpine Linux)
- Python 3.11 / Flask
- PostgreSQL 16
- HTML/JavaScript

## Quick Start
```bash
cd docker-dashboard

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

Access the dashboard at: `http://192.168.2.30:8080`

## What I Learned

- Writing custom Dockerfiles
- Multi-container orchestration with docker-compose
- Docker networking and service discovery
- Volume management for data persistence
- Environment-based configuration
- Debugging containerized applications

## Project Structure
```
docker-dashboard/
├── docker-compose.yml       # Orchestration configuration
├── frontend/
│   ├── Dockerfile          # nginx container definition
│   └── index.html          # Dashboard UI
└── backend/
    ├── Dockerfile          # Python container definition
    ├── app.py              # Flask API
    └── requirements.txt    # Python dependencies
```

## Future Enhancements

- Add user authentication
- Implement additional API endpoints
- Enhanced UI with data visualization
- Deploy to Kubernetes cluster
- CI/CD pipeline with GitHub Actions
# Dashboard Project
