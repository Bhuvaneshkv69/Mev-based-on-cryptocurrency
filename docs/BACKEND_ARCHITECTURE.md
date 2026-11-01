# MEVShield Backend Architecture

## 1. Introduction

The MEVShield backend is responsible for processing application requests and executing the simulations required by the MEVShield platform.

It acts as the communication layer between the frontend interface and the backend simulation logic.

## 2. Technology Stack

- Python – Backend programming language
- FastAPI – API framework
- PostgreSQL – Relational database
- SQLAlchemy – Database interaction
- Alembic – Database schema migration management

## 3. Backend Architecture

The backend is organized into different components to separate API handling, business logic, database operations, and configuration.

### 3.1 API Layer

The API layer receives requests from the frontend application.

Its responsibilities include:
- Accepting incoming HTTP requests.
- Validating request parameters.
- Calling the appropriate simulation functionality.
- Returning structured responses.

### 3.2 Trade Protection Module

This module demonstrates protection against MEV-related trading risks.

Its capabilities include:
- Sandwich attack simulation.
- Slippage tolerance validation.
- Private mempool protection simulation.
- Commit-reveal simulation.
- Time-lock simulation.

### 3.3 Decentralization Analysis Module

This module evaluates builder and relay concentration using supplied observations.

Its capabilities include:
- Builder market-share analysis.
- Relay concentration analysis.
- Herfindahl-Hirschman Index (HHI) calculation.
- PBS auction simulation.
- Builder outage simulation.

### 3.4 Network Efficiency Module

This module demonstrates transaction processing and network efficiency scenarios.

Its capabilities include:
- Transaction queue simulation.
- Block capacity analysis.
- Gas cost estimation.
- Transaction submission strategy comparison.

### 3.5 Database Layer

The database layer supports storing and retrieving application data and experiment records where persistence is configured.

PostgreSQL is used as the relational database.

SQLAlchemy supports database interactions, while Alembic manages database schema migrations.

## 4. API Documentation

FastAPI provides an interactive Swagger UI interface for exploring and testing available API endpoints.

Default URL:

http://127.0.0.1:8000/docs

## 5. Database Migration

Alembic is used to manage database schema changes.

The migration command should be executed from the backend directory:

```powershell
alembic upgrade head
```

## 6. Backend Startup

The backend can be started from the project root using:

```powershell
.\start-backend.ps1
```

Default backend address:

http://127.0.0.1:8000

## 7. Environment Configuration

Backend environment variables are maintained in:

backend/.env

Sensitive information such as database credentials and secret keys should not be committed to the GitHub repository.

## 8. Conclusion

The MEVShield backend provides the API and simulation functionality required by the frontend application.

Its modular organization supports trade protection, decentralization analysis, and network efficiency simulations.