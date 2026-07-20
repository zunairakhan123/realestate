#  Realty Service API

A high-performance, asynchronous, event-driven REST API built with **FastAPI** and **PostgreSQL** for managing real estate operations — customers, properties, and leads — with a focus on decoupling, security, and scalability.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

##  Table of Contents

- [Overview](#-overview)
- [Technology Stack](#-technology-stack)
- [Architectural Decisions](#-architectural-decisions)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup--installation)
  - [Configuration](#configuration)
  - [Database Migrations](#database-migrations)
  - [Running the Application](#running-the-application)
- [Testing & Load Testing](#-testing--load-testing)
- [Operational & DevOps](#-operational--devops)
- [API Health & Verification](#-api-health--verification)
- [Production Readiness Roadmap](#-production-readiness-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## Overview

The Realty Service API is a backend service designed to power real estate platforms. It handles the full lifecycle of **leads**, **properties**, and **customers**, exposing a clean REST interface alongside real-time WebSocket notifications for state changes. The system is built to be modular, testable, and container-ready for cloud deployment.

---

## 🛠 Technology Stack

| Category | Technology |
|---|---|
| **Framework** | FastAPI, Uvicorn (ASGI), Gunicorn |
| **Database & ORM** | PostgreSQL, SQLAlchemy 2.0 (`asyncpg` driver) |
| **Migrations** | Alembic (async) |
| **Real-time** | WebSockets (Connection Manager pattern) |
| **Testing** | Pytest, Postman / Newman, Locust |
| **Infrastructure** | Docker, Docker Compose, Cloudflare Tunnel |

---

## Architectural Decisions

- **Domain-Driven Structure** — Codebase is organized by business domain (`leads`, `properties`, `customers`) to ensure module isolation and simplified maintenance.
- **Decoupled Service Layer** — Business logic lives in `service.py`, separated from HTTP concerns, allowing execution via background tasks or CLI.
- **Event-Driven Real-time** — A centralized `ConnectionManager` pushes WebSocket notifications on state changes (e.g., status updates).
- **Security** — HMAC-SHA256 signature verification for inbound webhooks; containers run as non-root.
- **Resiliency** — Implements the **Accept-Now / Callback-Later** pattern to bypass gateway timeout limits for long-running AI processing tasks.

---
## 📂 Project Structure
realty/
├── app/
│   ├── main.py                  # FastAPI application entrypoint
│   ├── core/                    # Config, security, connection manager
│   ├── auth/                    # Authentication & authorization logic
│   ├── notifications/           # WebSocket / notification dispatch
│   ├── webhooks/                # Inbound webhook handlers (HMAC verification)
│   ├── domains/
│   │   ├── leads/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   ├── properties/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   └── customers/
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── models.py
│   │       └── schemas.py
│   └── db/
│       ├── session.py
│       └── base.py
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── locustfile.py
│   └── ...
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md

> Adjust this tree to match your actual repository layout as the project evolves.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional, for containerized setup)

### Local Setup & Installation

**1. Create and activate a virtual environment**

```bash
python -m venv env

# Windows
env\Scripts\activate

# Linux / Mac
source env/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/db_name
```

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:password@db:5432/db_name` |

> Never commit `.env` files to version control. Use `.env.example` as a template for collaborators.

### Database Migrations

Apply schema migrations:

```bash
python -m alembic upgrade head
```

### Running the Application

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs are auto-generated by FastAPI at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Testing & Load Testing

### 1. Unit & Integration Tests (Pytest)

Run the full test suite to verify business logic and integrity guards:

```bash
pytest tests/
```

### 2. API Contract Tests (Newman / Postman)

Ensure your Postman collection and environment is exported as `collection.json`, `environment.json` then run:

```bash
newman run collection.json -e environment.json --env-var "baseUrl=http://localhost:8000" > newman_evidence.txt
```

### 3. Load Testing (Locust)

Simulate concurrent, high-traffic scenarios:

```bash
locust -f tests/locustfile.py --host=http://localhost:8000
```

Access the Locust UI at `http://localhost:8089`.

---

## ⚙️ Operational & DevOps

### Webhook Integration

Expose your local service for external webhook testing using `cloudflared`:

```bash
.\cloudflared.exe tunnel --url http://127.0.0.1:8000
```

### Containerization (Docker)

Build and run the full stack (App + PostgreSQL) using Docker Compose:

```bash
docker-compose up --build
```

---

## API Health & Verification

Once the service is running, verify system integrity via the following endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check — confirms the application process is running |
| `GET /ready` | Readiness check — confirms dependencies (e.g., database) are reachable |

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

---

## 🗺 Production Readiness Roadmap

The following areas are identified for refinement before a full production deployment:

| Area | Current State | Recommended Improvement |
|---|---|---|
| **Observability** | Basic logging | Structured logging (`structlog`) + distributed tracing |
| **Secret Management** | `.env` file | Secure vault (AWS Secrets Manager, HashiCorp Vault) |
| **Task Queues** | FastAPI `BackgroundTasks` | Distributed queue (Celery or ARQ with Redis) for persistent, retryable tasks |
| **Rate Limiting** | Not implemented | `slowapi` to protect against brute force / DDoS |
| **Schema Versioning** | Manual `alembic upgrade` | Automate migrations within CI/CD pipeline |

---

## Contributing

Contributions are welcome. Please:

1. Fork the repository and create a feature branch.
2. Follow the existing domain-driven structure for new modules.
3. Add or update tests under `tests/` for any behavioral change.
4. Run `pytest tests/` and ensure all checks pass before opening a pull request.
5. Submit a PR with a clear description of the change and its motivation.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — feel free to use, modify, and distribute with attribution.

---

<p align="center"><sub>Built with FastAPI, PostgreSQL, and a domain-driven mindset.</sub></p>