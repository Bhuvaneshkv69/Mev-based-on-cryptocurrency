"""API endpoints for gas-cost and transaction queue efficiency simulations."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.efficiency import (
    EfficiencySimulationRequest,
    EfficiencySimulationResponse,
    ReorgRiskSimulationRequest,
    ReorgRiskSimulationResponse,
    MEVTaxonomyResponse,
)
from app.services.efficiency import EfficiencyService

logger = logging.getLogger("mevshield.api.efficiency")
router = APIRouter()


@router.post(
    "/simulate",
    response_model=EfficiencySimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Gas Cost, Queue Delay, and Submission Strategies",
    description=(
        "Runs a deterministic educational model of gas expenditure, transaction ordering, "
        "block capacity, queue delay, throughput, and a modeled private-bundle alternative. "
        "No live Ethereum RPC or private relay is contacted."
    ),
)
def simulate_efficiency(
    payload: EfficiencySimulationRequest,
    db: Session = Depends(get_db),
) -> EfficiencySimulationResponse:
    try:
        result = EfficiencyService.simulate(payload, db=db if payload.save_experiment else None)
        return EfficiencySimulationResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Network efficiency simulation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Network efficiency simulation failed. Check backend logs for details.",
        ) from exc


@router.post(
    "/reorg-smoothing-simulate",
    response_model=ReorgRiskSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Consensus Reorg Risk vs MEV Smoothing & Burn",
    description=(
        "Simulates the 'Time-Bandit' chain reorganization incentive created by large MEV spikes, "
        "and demonstrates how MEV Smoothing and MEV Burn eliminate this consensus vulnerability."
    ),
)
def simulate_reorg_and_smoothing(
    payload: ReorgRiskSimulationRequest,
    db: Session = Depends(get_db),
) -> ReorgRiskSimulationResponse:
    try:
        return EfficiencyService.simulate_reorg_risk(payload, db=db if payload.save_experiment else None)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Reorg smoothing simulation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Reorg smoothing simulation failed. Check backend logs for details.",
        ) from exc


@router.get(
    "/taxonomy",
    response_model=MEVTaxonomyResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve MEV Taxonomy Analysis",
    description=(
        "Classifies MEV activities into Beneficial (DEX Arbitrage, Lending Liquidations) "
        "and Toxic (Sandwich Attacks, Priority Gas Auctions) with economic recommendations."
    ),
)
def get_mev_taxonomy() -> MEVTaxonomyResponse:
    return EfficiencyService.get_taxonomy()
