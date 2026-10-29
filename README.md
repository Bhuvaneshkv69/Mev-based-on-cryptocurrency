# MEVShield — Ethereum MEV Detection and Mitigation Platform

MEVShield is an educational full-stack application for exploring three Ethereum MEV problem areas in one interface:

1. **Trade protection:** simulated sandwich-attack risk, user loss, and protection-mechanism comparisons.
2. **Builder and relay decentralization:** market shares, top-three concentration, HHI, PBS auctions, and outage scenarios.
3. **Network efficiency:** estimated gas costs, transaction queue delay, throughput, priority-fee ordering, and a modeled private-bundle alternative.

The project is simulation-first. It does not submit live Ethereum transactions, connect to private relays, or claim to eliminate MEV. The built-in decentralization dataset is explicitly illustrative.

## Project structure

```text
mevshield/
├── backend/                 # FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pytest
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
└── frontend/                # React + Vite + Tailwind CSS + Recharts
    ├── src/
    ├── package.json
    └── vite.config.js
```

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer and npm
- PostgreSQL 15+ for persistent experiment history (optional if simulations are run with saving disabled)

## 1. One-time setup (Windows PowerShell)

Open PowerShell in the extracted `MEVShield` project root (the folder containing this README). Do not run `alembic` from this root folder directly; use the supplied helper script so it runs from the correct backend directory.

```powershell
.\setup.ps1
```

The script creates `backend\.venv`, installs Python requirements, creates `backend\.env` from `backend\.env.example` only if it does not already exist, creates `frontend\.env`, and runs `npm install`. It does not overwrite existing environment files. Internet access is required to install packages.

If PowerShell blocks scripts, open a PowerShell session and run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then run ` .\setup.ps1 ` again.

## 2. Configure PostgreSQL

The default persistent database is PostgreSQL. Start a local PostgreSQL server or use Docker: 

```powershell
docker run --name mevshield-postgres -e POSTGRES_DB=mevshield -e POSTGRES_USER=mevshield_user -e POSTGRES_PASSWORD=replace_with_local_password -p 5432:5432 -v mevshield_pgdata:/var/lib/postgresql/data -d postgres:16-alpine
```

If the container already exists, use `docker start mevshield-postgres`. Edit `backend\.env` and set `DATABASE_PASSWORD` to the password configured for PostgreSQL. Ensure the database and user exist. The values in `.env.example` are placeholders and must match your local setup.

## 3. Apply database migrations

From the project root, run the helper script: 

```powershell
.\run-migrations.ps1
```

This runs Alembic from `backend`, where `alembic.ini` is located. If you prefer manual commands, use:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

## 4. Start the backend

Open a terminal in the project root and run:

```powershell
.\start-backend.ps1
```

Alternatively, from `backend` with its virtual environment activated:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify the API at `http://127.0.0.1:8000/api/health`; Swagger is at `http://127.0.0.1:8000/docs`. Keep the backend terminal running.

## 5. Start the frontend

Open a second terminal in the project root and run:

```powershell
.\start-frontend.ps1
```

Alternatively, use `cd frontend`, `npm install`, and `npm run dev`. Open the URL shown by Vite, normally `http://localhost:5173`. Vite proxies `/api` requests to FastAPI at `http://127.0.0.1:8000`.

If the backend is hosted elsewhere, set `VITE_API_BASE_URL` in `frontend\.env` to the backend origin and add that origin to `ALLOWED_ORIGINS` in `backend\.env`.

## 6. Run backend tests

From the project root, after setup, run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

Tests default to an isolated in-memory SQLite database through test fixtures. PostgreSQL is used for normal local persistence.

## Main API endpoints

| Feature | Endpoint | Purpose |
|---|---|---|
| Health | `GET /api/health` | Backend liveness |
| Readiness | `GET /api/health/ready` | Database connectivity |
| Experiments | `/api/experiments` | Persisted simulation history |
| Reports | `GET /api/reports/summary` | Counts by module and status |
| Trade protection | `POST /api/trade-protection/simulate` | Simulated attack/protection comparison |
| Decentralization | `POST /api/decentralization/analyze` | Builder and relay concentration |
| PBS | `POST /api/decentralization/pbs-simulate` | Simulated builder auction |
| Outage | `POST /api/decentralization/outage-simulate` | Builder/relay outage scenario |
| Sample data | `GET /api/decentralization/sample-data` | Clearly labeled synthetic observations |
| Network efficiency | `POST /api/efficiency/simulate` | Gas costs, queue delay, throughput, and submission comparison |

## Network efficiency calculations

The Phase 5 endpoint accepts transaction count, modeled block capacity, average gas use, base fee, priority fee, fee spread, block interval, and simulation limit. The estimated transaction cost is:

`cost (ETH) = gas used × effective gas price (Gwei) / 1,000,000,000`

The simulation uses deterministic synthetic fee profiles. Priority-fee competition sorts by fee; the modeled private-bundle strategy preserves submission order. These are educational comparisons, not predictions of actual Ethereum relay or builder behavior.

## Data and security notes

- Never commit `.env` or real credentials. The ZIP supplied for this update had a local `.env`; it has intentionally not been included in the rebuilt deliverable. Create a local `.env` from `.env.example`.
- Do not enter wallet seed phrases or private keys. The application does not need them.
- Use only synthetic or appropriately authorized data.
- No real transactions are broadcast by this application.
