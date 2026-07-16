# Realty Service API

A high-performance, asynchronous REST API built with FastAPI and PostgreSQL. This service manages real estate operations across three distinct domains: `customers`, `properties`, and `leads`. It features a fully decoupled architecture, asynchronous database I/O, strict referential integrity, and advanced query filtering.

## Technology Stack

* **Framework:** FastAPI, Uvicorn (ASGI)
* **Database & ORM:** PostgreSQL, SQLAlchemy 2.0 (`Mapped` / `mapped_column` paradigms)
* **Database Driver:** `asyncpg` for non-blocking I/O
* **Migrations:** Alembic (configured for async execution)
* **Validation & Config:** Pydantic, `pydantic-settings`
* **Language:** Python 3.12

---

## Architectural Decisions

This project strictly adheres to a domain-driven, vertical-slice architecture to ensure the service remains scalable, maintainable, and ready for CI/CD pipelines.

### Feature-Based Folder Structure

Instead of grouping files by their technical layer (e.g., placing all models in a `models/` directory and all routers in a `routers/` directory), the codebase is organized by business domain: `leads`, `properties`, and `customers`. Each domain encapsulates its own complete stack:

* `models.py`: SQLAlchemy database schemas.
* `schemas.py`: Pydantic data transfer objects (DTOs).
* `service.py`: Core business logic and database queries.
* `router.py`: HTTP endpoint definitions.

**Why this shape:** This strict boundary management prevents tight coupling across unrelated entities. It ensures that logic remains cohesive and makes it significantly easier to extract a specific domain into an independent microservice in the future if traffic requirements scale unevenly.

### Decoupled Service Layer

The `service.py` files encapsulate all business rules and database transactions without importing a single dependency from FastAPI. When a business rule is violated, the service raises an agnostic custom Python exception (`ConflictError`, `NotFoundError`). The `router.py` catches these and translates them to HTTP status codes.

**Why this matters:** Separating HTTP concerns from business logic makes the service layer highly testable. It allows the core logic to be invoked via background tasks, CLI commands, or data pipelines without requiring an active ASGI application context.

### Delete Protections & Constraint Safety Nets

Deleting a customer who still has active leads presents a significant data integrity risk. This application implements a dual-layer safeguard:

1. **Application Layer Guard:** The service actively evaluates a configured business rule to restrict deletion if the user holds active leads (`new`, `contacted`, `qualified`). If violated, it gracefully raises a 409 Conflict.
2. **Database Layer Constraint:** To prevent race conditions or integrity failures related to terminal leads, `ON DELETE RESTRICT` foreign key constraints are enforced directly at the PostgreSQL level. The SQLAlchemy models are configured with `passive_deletes="all"` to delegate this enforcement to the database engine. If triggered, the application catches the resulting `IntegrityError` and maps it to a 409 Conflict rather than allowing the server to crash with a 500 error.

### Local Postgres Integration

The application connects to the database asynchronously via the `asyncpg` driver, maximizing concurrency under high throughput. Local connection settings are dynamically loaded from a `.env` file via Pydantic's `BaseSettings`, ensuring secure, environment-agnostic deployment configurations that align with Twelve-Factor App principles.

---

## Local Setup & Installation

### 1. Environment Preparation

Ensure you have Python 3.12 installed. Create and activate a virtual environment:

```bash
python -m venv env
# Windows: env\Scripts\activate
# Mac/Linux: source env/bin/activate
```

Install the dependencies:

```bash
pip install fastapi uvicorn "sqlalchemy>=2.0" alembic asyncpg pydantic-settings "pydantic[email]"
```

### 2. Database Provisioning

Ensure PostgreSQL is running locally and execute the following SQL to provision the user and database:

```sql
CREATE DATABASE realty;
CREATE USER realty_app WITH PASSWORD 'zunaira';
GRANT ALL PRIVILEGES ON DATABASE realty TO realty_app;
ALTER DATABASE realty OWNER TO realty_app;
```

### 3. Configuration File

Create a `.env` file in the root of the project to securely inject environment variables:

```env
DATABASE_URL=postgresql+asyncpg://realty_app:zunaira@localhost:5432/realty
ENFORCE_CUSTOMER_DELETE_GUARD=true
DEBUG=true
```

### 4. Database Migrations

Initialize the schema using Alembic. This will automatically execute the DDL to create the domains and their foreign key constraints.

```bash
python -m alembic upgrade head
```

### 5. Running the Application

Start the ASGI server with hot-reloading enabled for development:

```bash
python -m uvicorn app.main:app --reload
```

Navigate to `http://localhost:8000/docs` to view the interactive Swagger UI and test the API endpoints.

---

## API Capabilities

* **Full CRUD:** Comprehensive POST, GET, PATCH, and DELETE operations across all three domains.
* **Nested Reads:** The `GET /leads/{id}` endpoint natively embeds the related Customer and Property data. This is achieved using SQLAlchemy's `selectinload` strategy to execute the retrieval without triggering an N+1 query performance bottleneck.
* **Advanced Filtering:** List endpoints (`GET /`) support complex query parameters combined with `AND` logic, including:
  * Partial text matching (`.ilike`) for customer names and emails.
  * Relational subqueries (e.g., filtering customers by `has_active_leads`).
  * Numerical and chronological boundary operators (`min_price`, `created_after`).