"""Decentralization Analysis API Routes.

Exposes endpoints for:
1. POST /api/decentralization/analyze
   Calculates builder and/or relay market shares, top-3 concentration, HHI, and diversity.
2. POST /api/decentralization/pbs-simulate
   Simulates multi-round PBS block construction auctions with deterministic tie-breaking.
3. POST /api/decentralization/outage-simulate
   Simulates builder or relay downtime/exclusion and calculates share re-normalization.
4. GET /api/decentralization/sample-data
   Returns the built-in illustrative academic dataset with manual verification reference.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.decentralization import (
    DecentralizationAnalysisRequest,
    DecentralizationAnalysisResponse,
    PBSSimulationRequest,
    PBSSimulationResponse,
    OutageSimulationRequest,
    OutageSimulationResponse,
    EPBSComparisonRequest,
    EPBSComparisonResponse,
)
from app.services.decentralization import DecentralizationService
from app.services.decentralization_sample_data import get_illustrative_dataset

logger = logging.getLogger("mevshield.api.decentralization")
router = APIRouter()


@router.post(
    "/analyze",
    response_model=DecentralizationAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Builder and Relay Market Concentration",
    description=(
        "Calculates deterministic market share percentages, largest participant share, "
        "top-three concentration ratio, Herfindahl–Hirschman Index (HHI), and diversity counts "
        "for block builders and relays. Generates risk classifications and warnings."
    ),
)
def analyze_decentralization(
    request: DecentralizationAnalysisRequest,
    db: Session = Depends(get_db),
) -> DecentralizationAnalysisResponse:
    """Analyze builder and relay concentration from observed block distributions."""
    try:
        return DecentralizationService.analyze_concentration(request=request, db=db)
    except ValueError as e:
        logger.warning("Decentralization analysis validation error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Unexpected error in decentralization analysis: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during concentration analysis.",
        )


@router.post(
    "/pbs-simulate",
    response_model=PBSSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Multi-Round PBS Block Auction",
    description=(
        "Simulates a multi-round Proposer-Builder Separation (PBS) auction where competing "
        "builders submit candidate bids and the proposer selects the highest bid with "
        "deterministic tie-breaking. Returns win distributions and per-round summaries."
    ),
)
def simulate_pbs_auction(
    request: PBSSimulationRequest,
    db: Session = Depends(get_db),
) -> PBSSimulationResponse:
    """Run multi-round PBS block construction auction simulation."""
    try:
        return DecentralizationService.simulate_pbs(request=request, db=db)
    except ValueError as e:
        logger.warning("PBS simulation validation error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Unexpected error in PBS simulation: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during PBS auction simulation.",
        )


@router.post(
    "/outage-simulate",
    response_model=OutageSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Builder or Relay Outage Resilience",
    description=(
        "Evaluates system resilience by modeling the sudden downtime or exclusion of a specific "
        "builder or relay. Re-normalizes market shares among remaining participants and reports "
        "single-point-of-failure vulnerabilities."
    ),
)
def simulate_participant_outage(
    request: OutageSimulationRequest,
    db: Session = Depends(get_db),
) -> OutageSimulationResponse:
    """Simulate outage resilience impact for a builder or relay."""
    try:
        return DecentralizationService.simulate_outage(request=request, db=db)
    except ValueError as e:
        logger.warning("Outage simulation validation error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Unexpected error in outage simulation: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during outage resilience simulation.",
        )


@router.get(
    "/sample-data",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Retrieve Illustrative Academic Sample Dataset",
    description=(
        "Returns the synthetic 1,000-block academic demonstration dataset for builders and "
        "relays, complete with manual calculation reference metrics for classroom verification."
    ),
)
def get_sample_dataset() -> Dict[str, Any]:
    """Retrieve the pre-calibrated illustrative academic sample dataset."""
    return get_illustrative_dataset()


@router.post(
    "/epbs-compare",
    response_model=EPBSComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Proto-PBS, Enshrined PBS, Inclusion Lists, and SUAVE",
    description=(
        "Simulates architectural resilience, relay dependency, censorship vulnerability, "
        "and market concentration across four generations of PBS mechanisms."
    ),
)
def compare_epbs_architectures(
    request: EPBSComparisonRequest,
    db: Session = Depends(get_db),
) -> EPBSComparisonResponse:
    """Compare PBS architectural paradigms and how they overcome limitations."""
    try:
        return DecentralizationService.simulate_epbs_comparison(request=request, db=db)
    except ValueError as e:
        logger.warning("ePBS comparison validation error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Unexpected error in ePBS comparison: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during ePBS architecture comparison.",
        )
