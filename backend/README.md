# MEVShield Backend — Phases 1–5

Welcome to the backend of **MEVShield — Ethereum MEV Detection and Mitigation Platform**, an educational final-year academic case-study application.

MEVShield demonstrates the core systemic challenges of Maximal Extractable Value (MEV) in Ethereum:
1. **Trade Protection** (Front-running, sandwich attack detection, and slippage protection).
2. **Decentralization Analyzer** (Builder market shares, relay dependency, and PBS dynamics).
3. **Network Efficiency Analyzer** (Gas dynamics, priority fee auctions, and mempool competition).

This codebase contains **Backend Phase 1 (Foundation)**, **Backend Phase 2 (PostgreSQL Persistence & Experiments)**, **Backend Phase 3 (Trade Protection Engine)**, **Backend Phase 4 (Builder & Relay Decentralization Analyzer)**, and **Backend Phase 5 (Gas Cost & Network Efficiency Simulation)**.

---

## Table of Contents

- [1. Phase Scope and Objectives](#1-phase-scope-and-objectives)
- [2. Technology Stack](#2-technology-stack)
- [3. Complete Folder Structure](#3-complete-folder-structure)
- [4. Database Architecture & SQLAlchemy Models](#4-database-architecture--sqlalchemy-models)
- [5. Setting Up PostgreSQL](#5-setting-up-postgresql)
  - [Option A: Local PostgreSQL Installation](#option-a-local-postgresql-installation)
  - [Option B: PostgreSQL via Docker](#option-b-postgresql-via-docker)
- [6. Environment Configuration](#6-environment-configuration)
- [7. Database Migrations with Alembic](#7-database-migrations-with-alembic)
- [8. Windows PowerShell Setup & Run Commands](#8-windows-powershell-setup--run-commands)
- [9. API Contract & Endpoints](#9-api-contract--endpoints)
  - [Health & Readiness Probes](#health--readiness-probes)
  - [Experiment Management](#experiment-management)
  - [Reporting Summary](#reporting-summary)
- [10. Running Automated Tests](#10-running-automated-tests)
- [11. Troubleshooting & Common Database Issues](#11-troubleshooting--common-database-issues)
- [12. Transition to Backend Phase 3](#12-transition-to-backend-phase-3)

---

## 1. Phase Scope and Objectives

### What is Included in Backend Phase 2
- **PostgreSQL Database Integration**: Persistent storage using SQLAlchemy 2.x and `psycopg 3`.
- **Alembic Database Migrations**: Version-controlled DDL migrations tracking schema changes.
- **Experiment Management Layer**:
  - `POST /api/experiments`: Register simulation configurations in `pending` status.
  - `GET /api/experiments`: Paginated experiment history with module and status filtering.
  - `GET /api/experiments/{id}`: Fetch single experiment details.
  - `PATCH /api/experiments/{id}`: Update metadata (e.g., scenario label or assumptions).
  - `DELETE /api/experiments/{id}`: Delete an experiment record.
- **Reporting Summary**:
  - `GET /api/reports/summary`: Aggregate counts across modules and statuses, plus latest activity timestamp.
- **Health vs. Readiness Probes**:
  - `GET /api/health`: Service liveness (independent of database availability).
  - `GET /api/health/ready`: Database connectivity readiness check (`SELECT 1`).
- **Comprehensive Automated Tests**: 24 tests covering foundation, CORS, error sanitization, experiment lifecycle, and reporting.

### What is NOT in Phase 2 (Planned for Later Phases)
- Execution of real MEV front-running or sandwich simulation algorithms (Phase 3).
- Live Ethereum mempool listeners or Web3 RPC calls (Phase 3+).
- Fabricated simulation results (all results remain `null` until real simulation engines are added).
- User authentication and multi-tenancy (Phase 3+).

---

## 2. Technology Stack

| Technology | Purpose | Version |
| :--- | :--- | :--- |
| **Python** | Runtime Environment | 3.11+ |
| **FastAPI** | REST API Framework | >=0.110.0 |
| **Uvicorn** | Asynchronous ASGI Web Server | >=0.28.0 |
| **PostgreSQL** | Relational & JSONB Database | 15+ / 16+ |
| **SQLAlchemy** | Database ORM & Session Management | >=2.0.28 |
| **Alembic** | Database Schema Migrations | >=1.13.1 |
| **psycopg 3** | High-performance PostgreSQL Driver | >=3.1.18 |
| **Pydantic v2** | Request/Response Data Validation | >=2.6.0 |
| **pydantic-settings** | Type-safe Environment Settings | >=2.2.0 |
| **python-dotenv** | Local `.env` Configuration Loader | >=1.0.0 |
| **pytest & HTTPX** | In-memory and End-to-End API Testing | >=8.0.0 |

---

## 3. Complete Folder Structure

```
mevshield/
    backend/
        app/
            __init__.py          # Package initialization
            main.py              # Application entry point, CORS, error handling, & root route
            database.py          # SQLAlchemy engine, sessionmaker, get_db dependency, & readiness check
            core/
                __init__.py
                config.py        # Centralized settings & safe PostgreSQL URL builder
            api/
                __init__.py
                router.py        # Central API router aggregating all endpoints under /api
                routes/
                    __init__.py
                    health.py    # GET /health (liveness) & GET /health/ready (readiness)
                    experiments.py # CRUD routes for simulation experiments
                    reports.py   # GET /reports/summary endpoint
            schemas/
                __init__.py
                common.py        # HealthResponse, RootResponse, ErrorResponse schemas
                experiment.py    # ExperimentCreate, Update, Response, List, & Summary schemas
            models/
                __init__.py
                experiment.py    # SQLAlchemy 'experiments' table model
            services/
                __init__.py
                experiment_service.py # Database queries, transaction boundaries, & aggregation logic
        tests/
            __init__.py
            conftest.py          # Isolated test DB fixtures & get_db dependency overrides
            test_health.py       # Health checks, liveness, readiness, CORS, & 500 error tests
            test_experiments.py  # Full CRUD, pagination, validation, & safety tests
            test_reports.py      # Summary aggregation tests for empty & populated DB
        alembic/
            env.py               # Alembic runner reading database URL from app settings
            script.py.mako       # Migration template
            versions/
                0001_initial_experiments_table.py # Initial DDL migration
        alembic.ini              # Alembic migration configuration
        .env                     # Active local environment variables (ignored by Git)
        .env.example             # Documented template for environment settings
        .gitignore               # Git exclusions for Python cache, .venv, and .env
        requirements.txt         # Pinned project dependencies
        README.md                # Comprehensive documentation
```

---

## 4. Database Architecture & SQLAlchemy Models

The `experiments` table provides a unified storage schema for all three MEVShield modules:

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto-increment | Unique experiment ID |
| `module` | `VARCHAR(50)` | NOT NULL, Indexed | Module identifier: `protection`, `decentralization`, or `efficiency` |
| `scenario` | `VARCHAR(100)` | NOT NULL | Scenario title (e.g. `sandwich_v2_pool_sim`) |
| `status` | `VARCHAR(20)` | NOT NULL, Indexed | Lifecycle status: `pending`, `completed`, or `failed` |
| `input_parameters` | `JSONB` | NOT NULL | Simulation inputs (trade size, slippage, latency, etc.) |
| `results` | `JSONB` | NULLABLE | Simulation outputs (null until computed in Phase 3+) |
| `assumptions` | `JSONB` | NULLABLE | Metadata notes, assumptions, and synthetic data flags |
| `error_message` | `TEXT` | NULLABLE | Sanitized failure explanation if status is `failed` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, Default `now()`, Indexed | Audit creation timestamp (UTC) |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, Default `now()` | Audit update timestamp (UTC) |

### Supported Module Identifiers
- `protection`: Trade protection and sandwich attack detection.
- `decentralization`: Builder market share and relay concentration analysis.
- `efficiency`: Priority gas auctions and transaction queuing dynamics.

### Lifecycle Statuses
- `pending`: Registered experiment waiting for execution by a simulation engine.
- `completed`: Simulation engine finished execution; valid outputs populated in `results`.
- `failed`: Simulation engine encountered an error; explanation recorded in `error_message`.

---

## 5. Setting Up PostgreSQL

### Option A: Local PostgreSQL Installation

If PostgreSQL is installed locally on your Windows machine:

1. Open **psql** or pgAdmin:
   ```powershell
   psql -U postgres
   ```
2. Create the dedicated database and user:
   ```sql
   -- Create application database
   CREATE DATABASE mevshield;

   -- Create application user
   CREATE USER mevshield_user WITH PASSWORD 'your_secure_password';

   -- Grant permissions to database
   GRANT ALL PRIVILEGES ON DATABASE mevshield TO mevshield_user;

   -- Connect to mevshield database
   \c mevshield

   -- Grant schema permissions
   GRANT ALL ON SCHEMA public TO mevshield_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mevshield_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mevshield_user;
   ```
3. Update your `.env` file with matching credentials:
   ```env
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=mevshield
   DATABASE_USER=mevshield_user
   DATABASE_PASSWORD=your_secure_password
   ```

---

### Option B: PostgreSQL via Docker

If you have Docker Desktop installed, you can start a PostgreSQL container with a single command:

```powershell
docker run --name mevshield-postgres -e POSTGRES_DB=mevshield -e POSTGRES_USER=mevshield_user -e POSTGRES_PASSWORD=replace_with_local_password -p 5432:5432 -v mevshield_pgdata:/var/lib/postgresql/data -d postgres:16-alpine
```

### Explaining the Docker Flags:
- `--name mevshield-postgres`: Names the container.
- `-e POSTGRES_DB=mevshield`: Automatically creates the `mevshield` database.
- `-e POSTGRES_USER=mevshield_user`: Creates the database user.
- `-e POSTGRES_PASSWORD=...`: Sets the database password.
- `-p 5432:5432`: Maps host port 5432 to container port 5432.
- `-v mevshield_pgdata:/var/lib/postgresql/data`: **Persistent volume** ensuring data is preserved even when the container stops.
- `-d postgres:16-alpine`: Runs lightweight PostgreSQL 16 in the background.

To stop and start the container later:
```powershell
# Stop container (data is preserved in volume)
docker stop mevshield-postgres

# Restart container
docker start mevshield-postgres
```

---

## 6. Environment Configuration

All environment variables are declared in `.env`. Key database settings:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_HOST` | `localhost` | PostgreSQL host |
| `DATABASE_PORT` | `5432` | PostgreSQL port |
| `DATABASE_NAME` | `mevshield` | Target database name |
| `DATABASE_USER` | `mevshield_user` | Application username |
| `DATABASE_PASSWORD` | `replace_with_local_password` | Application user password |
| `DATABASE_URL` | *(optional)* | Full URL override if needed |
| `DB_POOL_SIZE` | `5` | Maximum persistent connections in pool |
| `DB_MAX_OVERFLOW` | `10` | Connections permitted above pool size during traffic spikes |
| `DB_POOL_TIMEOUT` | `30` | Seconds to wait before raising pool timeout error |

---

## 7. Database Migrations with Alembic

Alembic manages schema evolution without manually running raw SQL scripts.

### 1. Apply Migrations to Target Database
From `mevshield/backend`:
```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

### 2. Inspect Current Database Revision
```powershell
.\.venv\Scripts\alembic.exe current
```

### 3. Inspect Migration History
```powershell
.\.venv\Scripts\alembic.exe history --verbose
```

### 4. Dry-Run / Preview Migration SQL (Offline Mode)
To see the exact SQL Alembic will execute without touching the database:
```powershell
.\.venv\Scripts\alembic.exe upgrade --sql base:head
```

---

## 8. Windows PowerShell Setup & Run Commands

Follow these exact steps in **Windows PowerShell**:

```powershell
# 1. Navigate to backend directory
cd c:\Documents\Desktop\crypto_case_study(demo)\mevshield\backend

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1
# (Or use direct python: .\.venv\Scripts\python.exe)

# 3. Install/verify dependencies
pip install -r requirements.txt

# 4. Copy .env template if not already present
if (-not (Test-Path .env)) { Copy-Item .env.example .env }

# 5. Apply database migrations
.\.venv\Scripts\alembic.exe upgrade head

# 6. Start the FastAPI development server
python -m uvicorn app.main:app --reload
```

---

## 9. API Contract & Endpoints

### Health & Readiness Probes

#### 1. Liveness Probe
- **Endpoint**: `GET /api/health`
- **Purpose**: Confirms FastAPI server is online. Zero database dependency.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "MEVShield API",
  "version": "1.0.0",
  "environment": "development"
}
```

#### 2. Database Readiness Probe
- **Endpoint**: `GET /api/health/ready`
- **Purpose**: Executes `SELECT 1` to verify live PostgreSQL connection.
- **Response `200 OK`** (when connected):
```json
{
  "status": "ready",
  "database": "connected",
  "message": "Database reachable and operational"
}
```
- **Response `503 Service Unavailable`** (when disconnected):
```json
{
  "status": "not_ready",
  "database": "disconnected",
  "message": "Database unreachable: OperationalError"
}
```

---

### Experiment Management

#### 1. Create Experiment
- **Endpoint**: `POST /api/experiments`
- **Status**: `201 Created`
- **Request Body**:
```json
{
  "module": "protection",
  "scenario": "sandwich_dex_simulation",
  "input_parameters": {
    "trade_amount_eth": 10.0,
    "slippage_bps": 50,
    "target_pool": "UniswapV2_WETH_USDC"
  },
  "assumptions": {
    "mempool_latency_ms": 120,
    "data_source": "synthetic"
  }
}
```
- **Response Body**:
```json
{
  "id": 1,
  "module": "protection",
  "scenario": "sandwich_dex_simulation",
  "status": "pending",
  "input_parameters": {
    "trade_amount_eth": 10.0,
    "slippage_bps": 50,
    "target_pool": "UniswapV2_WETH_USDC"
  },
  "results": null,
  "assumptions": {
    "mempool_latency_ms": 120,
    "data_source": "synthetic"
  },
  "error_message": null,
  "created_at": "2026-10-11T10:15:00Z",
  "updated_at": "2026-10-11T10:15:00Z"
}
```

#### 2. List Experiments (Paginated + Filtered)
- **Endpoint**: `GET /api/experiments?page=1&page_size=20&module=protection&status=pending`
- **Status**: `200 OK`
- **Response Body**:
```json
{
  "items": [
    {
      "id": 1,
      "module": "protection",
      "scenario": "sandwich_dex_simulation",
      "status": "pending",
      "input_parameters": { ... },
      "results": null,
      "assumptions": { ... },
      "error_message": null,
      "created_at": "2026-10-11T10:15:00Z",
      "updated_at": "2026-10-11T10:15:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

#### 3. Get Single Experiment
- **Endpoint**: `GET /api/experiments/{id}`
- **Status**: `200 OK` (or `404 Not Found` if missing)

#### 4. Update Metadata
- **Endpoint**: `PATCH /api/experiments/{id}`
- **Status**: `200 OK`
- **Request Body**:
```json
{
  "scenario": "updated_sandwich_dex_simulation",
  "assumptions": {
    "mempool_latency_ms": 200,
    "notes": "Adjusted latency parameter"
  }
}
```

#### 5. Delete Experiment
- **Endpoint**: `DELETE /api/experiments/{id}`
- **Status**: `204 No Content`

---

### Reporting Summary

#### 1. Aggregate Statistics
- **Endpoint**: `GET /api/reports/summary`
- **Status**: `200 OK`
- **Response Body**:
```json
{
  "total_experiments": 4,
  "by_module": {
    "protection": 2,
    "decentralization": 1,
    "efficiency": 1
  },
  "by_status": {
    "pending": 4,
    "completed": 0,
    "failed": 0
  },
  "latest_experiment_at": "2026-10-11T10:20:00Z"
}
```

---

## 10. Running Automated Tests

MEVShield features a test suite of **24 automated tests**. Tests run using in-memory isolation, ensuring that developer databases are never wiped.

From `mevshield/backend`:

```powershell
# Run the complete test suite
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Run only experiment tests
.\.venv\Scripts\python.exe -m pytest tests/test_experiments.py -v

# Run only report tests
.\.venv\Scripts\python.exe -m pytest tests/test_reports.py -v

# Run only health & readiness tests
.\.venv\Scripts\python.exe -m pytest tests/test_health.py -v
```

### Test Coverage Breakdown:
- **`tests/test_experiments.py`** (12 tests):
  - Valid creation with `201 Created`
  - Enforced module validation (`422`)
  - Enforced non-empty input validation (`422`)
  - Prevention of client status injection or fabricated results
  - Retrieval by ID (`200`) and nonexistent ID (`404`)
  - Deterministic pagination (`items`, `total`, `total_pages`)
  - Filter by `module` and by `status`
  - Safe metadata patching (`200`) and nonexistent ID (`404`)
  - Deletion (`204`) and cascading 404 verification
- **`tests/test_reports.py`** (2 tests):
  - Zero counts and null timestamp on empty database
  - Correct aggregation across multiple modules and statuses
- **`tests/test_health.py`** (10 tests):
  - Root information (`200`)
  - Liveness probe (`200`)
  - Readiness probe (`/api/health/ready`)
  - Prefix routing enforcement (`/api/health` vs `/health`)
  - Unknown route 404
  - CORS header responses
  - Unhandled 500 error sanitization and logging

---

## 11. Troubleshooting & Common Database Issues

### 1. `psycopg.OperationalError: connection to server at "localhost" failed`
- **Cause**: PostgreSQL service is stopped or not running.
- **Fix**:
  - Local: Open Windows Services (`services.msc`) and start `postgresql-x64-16`.
  - Docker: Run `docker start mevshield-postgres`.

### 2. `password authentication failed for user "mevshield_user"`
- **Cause**: Password in `.env` does not match the PostgreSQL user password.
- **Fix**: Check `DATABASE_PASSWORD` in `.env`, or reset the password in psql:
  ```sql
  ALTER USER mevshield_user WITH PASSWORD 'correct_password';
  ```

### 3. `database "mevshield" does not exist`
- **Cause**: The database was not created yet.
- **Fix**: In psql run: `CREATE DATABASE mevshield;`.

### 4. `alembic.util.exc.CommandError: Can't locate revision identified by '...'`
- **Cause**: Migration versions folder is missing or out of sync.
- **Fix**: Verify file `alembic/versions/0001_initial_experiments_table.py` exists.

---

## 12. Transition from Phase 2 and Phase 3

Phase 2 established PostgreSQL persistence, Alembic migrations, and generic experiment lifecycle management.
Phase 3 introduced Module 1: the Trade Protection and MEV Simulation Engine (`/api/trade-protection`).

---

## 13. Phase 4: Builder & Relay Decentralization Analyzer

### 13.1 Academic Background & Problem Statement
Under Ethereum's **Proposer-Builder Separation (PBS)** model, block construction is decoupled from consensus validation:
- **Block Builders** bundle searcher orderflow, maximize MEV extraction, and construct full candidate blocks.
- **Relays** act as mutually trusted auction intermediaries between builders and validators (proposers), delivering payload headers and validating bids.
- **Proposers (Validators)** choose and sign the winning header without seeing payload transactions in advance.

While PBS shields solo validators from the computational overhead of block optimization, it concentrates block assembly among a tiny cluster of specialized builders and relays. If top builders or relays command excessive market share, the network faces:
1. **Censorship & Inclusion Fragility**: Leading builders can delay or omit transactions (e.g., regulatory compliance filtering).
2. **Infrastructure Dependency & Single Points of Failure**: Relay outages disrupt block production if proposers lack redundant relay configurations.
3. **Collusion & Monopoly Pricing**: Dominant builders can dictate bundle placement terms to searchers and extract supra-competitive margins.

---

### 13.2 Concentration Metrics & Formulas

All metrics are calculated on the server using pure, deterministic functions (`app/services/decentralization_metrics.py`):

| Metric | Formula | Description |
| :--- | :--- | :--- |
| **Total Observed Blocks** | \( \sum \text{block\_count}_i \) | Total volume of blocks analyzed in the observation window. |
| **Market Share (%)** | \( \frac{\text{block\_count}_i}{\text{total\_blocks}} \times 100 \) | Percentage of constructed/delivered blocks attributed to participant \(i\). |
| **Largest Share (%)** | \( \max(\text{share}_i) \) | Share of the single largest participant. Flags single-point-of-failure risks. |
| **Top-Three Share (%)** | \( \sum_{i=1}^{\min(3, N)} \text{share}_i \) | Combined concentration ratio (\(CR_3\)) of the top 3 participants. |
| **Herfindahl–Hirschman Index (HHI)** | \( \sum_{i=1}^N (\text{share}_i)^2 \) | Classical economic concentration index (theoretical scale: 0 to 10,000). |
| **Participant Diversity** | \( N \) | Count of unique, active participants in the dataset. |

#### Analytical HHI Thresholds (Application-Defined Reference):
- **Low Concentration (\(HHI < 1,500\))**: Activity is distributed among numerous competing participants.
- **Moderate Concentration (\(1,500 \le HHI \le 2,500\))**: Noticeable reliance on leading participants; potential operational bottleneck.
- **High Concentration (\(HHI > 2,500\))**: Severe concentration; dominant participants control the block flow.

> [!NOTE]
> These thresholds are illustrative academic analytical benchmarks (derived from antitrust references) and do NOT represent official Ethereum consensus rules.

---

### 13.3 Independent Dual-Dimension Accounting

MEVShield treats **Builders** and **Relays** as two fundamentally distinct dimensions:
- **Builders** construct blocks; **Relays** deliver payloads.
- Builder counts and relay counts are **never summed together**.
- The API supports builder-only, relay-only, or combined analyses.
- When relay observations are omitted, `relay_metrics` returns `null` (not zero).

---

### 13.4 Illustrative Academic Sample Dataset & Manual Verification

For classroom demonstrations and automated testing, MEVShield provides a pre-calibrated 1,000-block dataset (`app/services/decentralization_sample_data.py`):

#### Builder Distribution:
| Builder ID | Block Count | Market Share | \( (\text{Market Share})^2 \) |
| :--- | :--- | :--- | :--- |
| `builder_alpha` | 450 | **45.0%** | 2,025.0 |
| `builder_beta` | 280 | **28.0%** | 784.0 |
| `builder_gamma` | 150 | **15.0%** | 225.0 |
| `builder_delta` | 80 | **8.0%** | 64.0 |
| `builder_epsilon` | 30 | **3.0%** | 9.0 |
| `builder_zeta` | 10 | **1.0%** | 1.0 |
| **Total** | **1,000** | **100.0%** | **HHI = 3,108.0** |

- **Largest Share**: 45.0% (`builder_alpha`)
- **Top-3 Share**: 45.0% + 28.0% + 15.0% = **88.0%**
- **HHI**: 2025 + 784 + 225 + 64 + 9 + 1 = **3,108.0** (*High Concentration*)
- **Diversity**: 6 distinct builders

#### Relay Distribution:
| Relay ID | Block Count | Market Share | \( (\text{Market Share})^2 \) |
| :--- | :--- | :--- | :--- |
| `relay_one` | 600 | **60.0%** | 3,600.0 |
| `relay_two` | 250 | **25.0%** | 625.0 |
| `relay_three` | 150 | **15.0%** | 225.0 |
| **Total** | **1,000** | **100.0%** | **HHI = 4,450.0** |

- **Largest Share**: 60.0% (`relay_one`)
- **Top-3 Share**: 60.0% + 25.0% + 15.0% = **100.0%**
- **HHI**: 3600 + 625 + 225 = **4,450.0** (*High Concentration*)
- **Diversity**: 3 distinct relays

---

### 13.5 Proposer-Builder Separation (PBS) Simulation

Simulates a multi-round block construction auction (`app/services/pbs_simulation.py`):
1. **Candidate Bids**: In each slot/round, competing builders formulate candidate bids (sampled via calibrated Gaussian models with a deterministic random seed).
2. **Selection Rule**: The proposer selects the highest eligible bid (first-price sealed auction).
3. **Deterministic Tie-Breaking**: Equal bids resolve deterministically using ascending alphabetical builder ID sorting.
4. **Win Distribution**: Outputs win counts, win percentages, and per-round auction logs.

---

### 13.6 Participant Outage Resilience Simulation

Models network stability when a critical builder or relay fails or is censored:
1. Computes baseline metrics.
2. Removes the failing participant from the active set.
3. Re-normalizes market shares among surviving participants:
   \[ \text{Share}_{\text{new}, i} = \frac{\text{block\_count}_i}{\sum_{\text{surviving}} \text{block\_count}} \times 100 \]
4. **Division-by-Zero Safety**: If 0 participants remain, reports total workflow collapse safely without unhandled runtime exceptions.

---

### 13.7 API Endpoints & PowerShell Examples

#### 1. Retrieve Sample Dataset
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/decentralization/sample-data" -Method GET
```

#### 2. Analyze Concentration (POST `/api/decentralization/analyze`)
```powershell
$payload = @{
    source_type = "illustrative_sample"
    measurement_window = "Academic Demo Window (1,000 Blocks)"
    builder_observations = @(
        @{ builder_id = "builder_alpha"; block_count = 450 },
        @{ builder_id = "builder_beta"; block_count = 280 },
        @{ builder_id = "builder_gamma"; block_count = 150 },
        @{ builder_id = "builder_delta"; block_count = 80 },
        @{ builder_id = "builder_epsilon"; block_count = 30 },
        @{ builder_id = "builder_zeta"; block_count = 10 }
    )
    relay_observations = @(
        @{ relay_id = "relay_one"; block_count = 600 },
        @{ relay_id = "relay_two"; block_count = 250 },
        @{ relay_id = "relay_three"; block_count = 150 }
    )
    save_experiment = $true
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/decentralization/analyze" -Method POST -Body $payload -ContentType "application/json"
```

#### 3. PBS Auction Simulation (POST `/api/decentralization/pbs-simulate`)
```powershell
$pbsPayload = @{
    builder_ids = @("builder_alpha", "builder_beta", "builder_gamma", "builder_delta")
    num_rounds = 100
    seed = 42
    save_experiment = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/decentralization/pbs-simulate" -Method POST -Body $pbsPayload -ContentType "application/json"
```

#### 4. Participant Outage Resilience (POST `/api/decentralization/outage-simulate`)
```powershell
$outagePayload = @{
    participant_type = "builder"
    outage_participant_id = "builder_alpha"
    baseline_observations = @(
        @{ builder_id = "builder_alpha"; block_count = 450 },
        @{ builder_id = "builder_beta"; block_count = 280 },
        @{ builder_id = "builder_gamma"; block_count = 150 }
    )
    save_experiment = $true
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/decentralization/outage-simulate" -Method POST -Body $outagePayload -ContentType "application/json"
```

---

### 13.8 Automated Testing Suite

To run all decentralization tests:
```powershell
# In Windows PowerShell from mevshield/backend with .venv active:
.\.venv\Scripts\python.exe -m pytest tests/test_decentralization_metrics.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_pbs_simulation.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_decentralization.py -v

# Run the complete backend suite:
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

---

### 13.9 Academic Limitations & Boundaries
1. **Dataset Provenance**: Fictional/illustrative sample data is explicitly labeled `illustrative_sample`. It does not reflect live Ethereum mainnet statistics.
2. **Behavioral Attribution**: High HHI or single-builder dominance measures **structural concentration** only. It does not prove collusion, regulatory filtering, censorship, or malicious behavior.
3. **Consensus Abstraction**: The PBS auction model is an educational first-price mechanism. It does not emulate full Ethereum consensus latency, p2p gossip timing, or validator slashing rules.



---

## 14. Backend Phase 5 — Network Efficiency Simulation

### Endpoint

`POST /api/efficiency/simulate` runs a deterministic simulation comparing priority-fee ordering with a modeled private-bundle submission order. The API reports the selected strategy and both strategies for comparison. No live Ethereum RPC, wallet, or private relay is contacted.

### Example PowerShell request

```powershell
$payload = @{
    transaction_count = 60
    block_capacity = 10
    average_gas_used = 150000
    base_fee_gwei = 20
    priority_fee_gwei = 2
    priority_fee_spread_gwei = 1
    block_time_seconds = 12
    max_blocks = 4
    scenario = "submission_comparison"
    submission_method = "priority_fee_competition"
    save_experiment = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/efficiency/simulate" -Method POST -Body $payload -ContentType "application/json"
```

### Model and limitations

- Estimated transaction cost in ETH = gas used × effective gas price in Gwei ÷ 1,000,000,000.
- Effective gas price is modeled as base fee plus priority fee; the base fee is not a validator tip.
- Transactions are synthetic and receive a deterministic fee profile.
- The queue is limited by a configurable number of transactions per block and maximum number of simulated blocks.
- The priority-fee strategy sorts by descending priority fee; the private-bundle model preserves submission order. Both are simplified comparisons, not claims about real relay performance.
- Estimated delay is reported in block intervals; throughput uses the modeled processing window.
- If `save_experiment` is true, results are stored in the existing `experiments` table with module `efficiency`. No new database table or migration is required.
- The model does not reproduce the full Ethereum block gas limit, builder algorithm, network propagation, or real-time base-fee changes. It does not classify transactions as malicious based on fees alone.

### Phase 5 tests

```powershell
python -m pytest tests/test_efficiency.py -v
python -m pytest tests/ -v
```


## Working-directory note

Run `alembic upgrade head` only from this `backend` directory because `alembic.ini` and the migration folder are located here. From the project root, use `..\run-migrations.ps1`. The application loads `backend/.env` relative to this file, so its location no longer depends on the current working directory.
