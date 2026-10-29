"""Central API Router.

Consolidates and organizes all sub-routers across MEVShield modules.
Mounts operational health probes, experiment management, and report endpoints.
"""

from fastapi import APIRouter

from app.api.routes import (
    health,
    experiments,
    reports,
    trade_protection,
    decentralization,
    efficiency,
)

# Central API router instance
api_router = APIRouter()

# ------------------------------------------------------------------------------
# 1. Operational & Health Routes (Phase 1 & 2)
# ------------------------------------------------------------------------------
# Resolves to:
#   GET /api/health       (Liveness check)
#   GET /api/health/ready (Database readiness check)
api_router.include_router(
    health.router,
    prefix="",
    tags=["Health & Monitoring"],
)

# ------------------------------------------------------------------------------
# 2. Experiment Management Routes (Phase 2)
# ------------------------------------------------------------------------------
# Resolves to:
#   POST   /api/experiments
#   GET    /api/experiments
#   GET    /api/experiments/{id}
#   PATCH  /api/experiments/{id}
#   DELETE /api/experiments/{id}
api_router.include_router(
    experiments.router,
    prefix="/experiments",
    tags=["Experiments"],
)

# ------------------------------------------------------------------------------
# 3. Report & Summary Routes (Phase 2)
# ------------------------------------------------------------------------------
# Resolves to:
#   GET /api/reports/summary
api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports & Analytics"],
)

# ------------------------------------------------------------------------------
# 4. Trade Protection Simulation Engine Routes (Phase 3)
# ------------------------------------------------------------------------------
# Resolves to:
#   POST /api/trade-protection/simulate
#   GET  /api/trade-protection/scenarios
api_router.include_router(
    trade_protection.router,
    prefix="/trade-protection",
    tags=["Trade Protection"],
)

# ------------------------------------------------------------------------------
# 5. Builder & Relay Decentralization Analyzer Routes (Phase 4)
# ------------------------------------------------------------------------------
# Resolves to:
#   POST /api/decentralization/analyze
#   POST /api/decentralization/pbs-simulate
#   POST /api/decentralization/outage-simulate
#   GET  /api/decentralization/sample-data
api_router.include_router(
    decentralization.router,
    prefix="/decentralization",
    tags=["Decentralization"],
)

# ------------------------------------------------------------------------------
# 6. Network Efficiency Simulation Routes (Phase 5)
# ------------------------------------------------------------------------------
# Resolves to:
#   POST /api/efficiency/simulate
api_router.include_router(
    efficiency.router,
    prefix="/efficiency",
    tags=["Network Efficiency"],
)
