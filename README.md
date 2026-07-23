# Realty Service & AI Copilot Platform

A high-performance, asynchronous real estate operations platform built with a **FastAPI** backend, **PostgreSQL** database, **Streamlit** multi-role frontend, and an integrated **Agentic AI Copilot**. The system features role-based access control (RBAC), secure client-server communication, real-time lead tracking, and autonomous tool execution via LLMs.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#-technology-stack)
- [AI Copilot Architecture](#ai-copilot-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup & Installation](#local-setup--installation)
  - [Configuration](#configuration)
  - [Database Migrations](#database-migrations)
  - [Running the Application](#running-the-application)
- [Frontend Dashboards](#-frontend-dashboards)
- [Testing & Load Testing](#testing--load-testing)
- [Operational & DevOps](#️-operational--devops)
- [API Health & Verification](#api-health--verification)
- [Production Readiness Roadmap](#-production-readiness-roadmap)
- [Contributing](#contributing)
- [License](#-license)

---

## Overview

The Realty Service platform provides a complete ecosystem for managing real estate properties, customer inquiries, and agent workflows. Alongside traditional REST operations, it incorporates an **AI Copilot assistant** capable of securely executing backend actions (such as fetching listings, updating lead statuses, and inspecting profiles) via a strictly controlled tool-dispatch framework.

---

## Key Features

- **Multi-Role Frontend (Streamlit)** — Dedicated dashboards for **Customers**, **Agents**, and **Admins** featuring responsive card-based layouts and data visualization.
- **Agentic AI Copilot** — Integrated LLM assistant that adheres to enterprise guardrails (never talks directly to the database; routes all actions through the service layer and RBAC checks).
- **Secure Authentication & RBAC** — JWT-based stateless authentication with strict role enforcement (`Customer`, `Agent`, `Admin`) and secure backend agent provisioning.
- **Domain-Driven Backend (FastAPI)** — Modular domain design separating concerns across `leads`, `properties`, `customers`, `auth`, and `copilot`.
- **Asynchronous Operations** — SQLAlchemy 2.0 with `asyncpg` for non-blocking database queries and high-concurrency throughput.

---

## 🛠 Technology Stack

| Category | Technology |
|---|---|
| **Backend Framework** | FastAPI, Uvicorn (ASGI) |
| **Frontend Framework** | Streamlit |
| **Database & ORM** | PostgreSQL, SQLAlchemy 2.0 (`asyncpg` driver) |
| **Migrations** | Alembic (async) |
| **AI / LLM Integration** | Pydantic v2, Custom Tool Dispatch Registry, Ollama / LLM Backend |
| **Testing & Load Testing** | Pytest, Locust, Newman (Postman) |
| **Infrastructure** | Docker, Docker Compose, Cloudflare Tunnel |

---

## AI Copilot Architecture

The AI Copilot operates under a strict isolation guarantee. The LLM never communicates directly with the database. Instead, requests follow a secure governance pipeline:

```text
LLM (Intent & Arguments)
    ↓
Tool Dispatch Registry & Pydantic Validation (tools.py)
    ↓
Service Layer (service.py) — enforces business rules & RBAC
    ↓
Database (PostgreSQL)
```

### Supported Copilot Capabilities

| Tool | Description |
|---|---|
| `list_properties` | Browse and filter real estate inventory by city. |
| `update_lead_status` | Safely update CRM lead lifecycle statuses with fallback ID resolution and parameter normalization. |
| `get_user_leads` | Retrieve role-filtered lead lists depending on whether the actor is an Agent, Customer, or Admin. |
| `get_customer` | Retrieve customer details securely. |

---

## 📂 Project Structure

```
realty_service/
├── app/
│   ├── main.py                  # FastAPI application entrypoint
│   ├── core/                    # Config, security, exception handlers
│   ├── auth/                    # Authentication, schemas, and models
│   ├── db/                      # Database session and base configuration
│   ├── properties/              # Property domain (router, service, models)
│   ├── leads/                   # Lead management domain
│   ├── customers/               # Customer domain
│   └── copilot/                 # AI Copilot service, tools registry, and execution engine
├── frontend/
│   ├── app.py                   # Main Streamlit router/entrypoint
│   ├── api_client.py            # HTTP communication wrapper with JWT attachment
│   ├── config.py                # Frontend configuration constants
│   ├── views/
│   │   ├── admin.py             # Admin Control Center (Analytics, Properties, Agent Provisioning)
│   │   ├── agent.py             # Agent Dashboard (Assigned Leads management)
│   │   └── customer.py          # Customer Portal (Property browser, Lead interest registry)
│   └── components/
│       └── copilot_ui.py        # Embedded Streamlit chat interface for the AI Copilot
├── alembic/                     # Database migrations
├── tests/                       # Pytest and Locust load testing scripts
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional, for containerized setup)

### Local Setup & Installation

**1. Clone and enter the repository**

```bash
git clone <repository-url>
cd realty_service
```

**2. Create and activate a virtual environment**

```bash
python -m venv env

# Windows
env\Scripts\activate

# Linux / Mac
source env/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/realty_db
SECRET_KEY=your_super_secret_jwt_key
```

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:yourpassword@localhost:5432/realty_db` |
| `SECRET_KEY` | Secret used to sign and verify JWTs | `your_super_secret_jwt_key` |

> Never commit `.env` files to version control. Use a `.env.example` template for collaborators, and rotate `SECRET_KEY` before any production deployment.

### Database Migrations

Apply asynchronous schema migrations:

```bash
python -m alembic upgrade head
```

### Running the Application

**1. Start the FastAPI backend:**

```bash
python -m uvicorn app.main:app --reload --port 8000
```

**2. Start the Streamlit frontend** (in a separate terminal window):

```bash
streamlit run frontend/app.py
```

The application interfaces will be available at:

| Interface | URL |
|---|---|
| Frontend UI | `http://localhost:8501` |
| FastAPI Docs (Swagger) | `http://localhost:8000/docs` |
| FastAPI Docs (ReDoc) | `http://localhost:8000/redoc` |

---

## 🎨 Frontend Dashboards

- **Customer Dashboard** — Browse available properties with city filters, view rich property cards, register interest to create leads, track personal lead statuses, and interact with the AI assistant.
- **Agent Dashboard** — Inspect assigned leads organized in card grids with status color-coding and run copilot queries.
- **Admin Control Center** — Access system-wide analytics, inspect the entire real estate portfolio and system lead overview, provision secure agent accounts via form interfaces, and utilize a privileged global AI Copilot.

---

## Testing & Load Testing

### 1. Unit & Integration Tests (Pytest)

Run the full test suite to verify business logic and integrity guards:

```bash
pytest tests/
```

### 2. API Contract Tests (Newman / Postman)

Ensure your Postman collection and environment are exported as `collection.json` and `environment.json`, then run:

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
| **LLM Backend** | Local (Ollama) | Evaluate hosted/production-grade LLM provider with SLA guarantees |

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

<p align="center"><sub>Built with FastAPI, PostgreSQL, Streamlit, and a domain-driven, agentic mindset.</sub></p>