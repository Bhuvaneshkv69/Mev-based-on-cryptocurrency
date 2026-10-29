"""Trade Protection API Routes.

Provides two endpoints for the MEV Detection and Trade Protection Simulation Engine:

  POST /api/trade-protection/simulate
    Runs the full simulation pipeline and returns unprotected vs. protected
    trade metrics for the requested scenario.

  GET /api/trade-protection/scenarios
    Returns a list of pre-built demo scenarios with ready-to-use request bodies.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.trade_protection import (
    DemoScenario,
    DemoScenariosResponse,
    MEVRiskResponse,
    ProtectedScenarioResponse,
    TradeProtectionRequest,
    TradeProtectionResponse,
    UnprotectedScenarioResponse,
)
from app.services.trade_protection.models import ProtectionType, TradeParameters
from app.services.trade_protection.trade_protection_service import TradeProtectionService

logger = logging.getLogger("mevshield.api.trade_protection")
router = APIRouter()


# ---------------------------------------------------------------------------
# Pre-built demo scenarios (one per protection type)
# ---------------------------------------------------------------------------
_DEMO_SCENARIOS: List[DemoScenario] = [
    DemoScenario(
        name="No Protection — Large Sandwich Attack",
        description=(
            "A 10 ETH trade in a shallow 500 ETH pool with no protection. "
            "Demonstrates the worst-case sandwich attack on an unprotected trade."
        ),
        request={
            "trade_amount_eth": 10.0,
            "token_pair": "ETH/USDC",
            "pool_liquidity_eth": 500.0,
            "slippage_tolerance_pct": 1.0,
            "protection_type": "none",
            "attacker_capital_eth": 100.0,
            "scenario_label": "No protection — large sandwich attack",
            "save_experiment": True,
        },
    ),
    DemoScenario(
        name="Private Mempool — Flashbots Protect",
        description=(
            "Same 10 ETH trade routed through a private RPC relay. "
            "Shows how hiding the transaction from public mempool eliminates ~95% of MEV."
        ),
        request={
            "trade_amount_eth": 10.0,
            "token_pair": "ETH/USDC",
            "pool_liquidity_eth": 500.0,
            "slippage_tolerance_pct": 1.0,
            "protection_type": "private_mempool",
            "attacker_capital_eth": 100.0,
            "scenario_label": "Private mempool — Flashbots Protect",
            "save_experiment": True,
        },
    ),
    DemoScenario(
        name="Slippage Guard — On-Chain Revert Protection",
        description=(
            "A 5 ETH trade with a tight 0.3% slippage tolerance. "
            "If the front-run moves the price beyond tolerance, the trade reverts on-chain."
        ),
        request={
            "trade_amount_eth": 5.0,
            "token_pair": "ETH/DAI",
            "pool_liquidity_eth": 800.0,
            "slippage_tolerance_pct": 0.3,
            "protection_type": "slippage_guard",
            "attacker_capital_eth": 50.0,
            "scenario_label": "Slippage guard — on-chain revert protection",
            "save_experiment": True,
        },
    ),
    DemoScenario(
        name="Commit-Reveal — Two-Phase Order",
        description=(
            "A 20 ETH trade committed in block N and revealed in block N+1. "
            "The front-runner cannot act on hidden order details in time."
        ),
        request={
            "trade_amount_eth": 20.0,
            "token_pair": "ETH/WBTC",
            "pool_liquidity_eth": 2000.0,
            "slippage_tolerance_pct": 0.5,
            "protection_type": "commit_reveal",
            "attacker_capital_eth": 200.0,
            "scenario_label": "Commit-reveal — two-phase order",
            "save_experiment": True,
        },
    ),
    DemoScenario(
        name="Time-Lock TWAP — Large Swap with Minimal MEV",
        description=(
            "A 50 ETH swap executed as a TWAP order across multiple blocks. "
            "Sandwich profit collapses to near-zero because no single block can be exploited."
        ),
        request={
            "trade_amount_eth": 50.0,
            "token_pair": "ETH/USDC",
            "pool_liquidity_eth": 5000.0,
            "slippage_tolerance_pct": 1.0,
            "protection_type": "time_lock",
            "attacker_capital_eth": 500.0,
            "scenario_label": "Time-lock TWAP — large swap with minimal MEV",
            "save_experiment": True,
        },
    ),
    DemoScenario(
        name="Encrypted Mempool — Cryptographic Threshold Privacy",
        description=(
            "A 15 ETH swap using threshold encryption. Order payload remains confidential until "
            "ordering commitment is mined, neutralizing sandwich attacks with 0 trust in private relays."
        ),
        request={
            "trade_amount_eth": 15.0,
            "token_pair": "ETH/USDC",
            "pool_liquidity_eth": 600.0,
            "slippage_tolerance_pct": 1.0,
            "protection_type": "encrypted_mempool",
            "attacker_capital_eth": 120.0,
            "scenario_label": "Encrypted mempool — threshold encryption",
            "save_experiment": True,
        },
    ),
    DemoScenario(
        name="Batch Auction — Uniform Clearing Price (CoW Swap)",
        description=(
            "A 25 ETH swap cleared in a discrete batch where all orders receive the identical "
            "clearing price p*, completely eliminating intra-batch ordering advantage."
        ),
        request={
            "trade_amount_eth": 25.0,
            "token_pair": "ETH/USDC",
            "pool_liquidity_eth": 1000.0,
            "slippage_tolerance_pct": 0.8,
            "protection_type": "batch_auction",
            "attacker_capital_eth": 200.0,
            "scenario_label": "Batch auction — uniform clearing price",
            "save_experiment": True,
        },
    ),
    DemoScenario(
        name="MEV-Share — 90% User MEV Rebate",
        description=(
            "A 12 ETH swap using MEV-Share order flow. Extracted back-running MEV is programmatically "
            "rebated 90% back to the trader as an on-chain cash refund."
        ),
        request={
            "trade_amount_eth": 12.0,
            "token_pair": "ETH/USDT",
            "pool_liquidity_eth": 500.0,
            "slippage_tolerance_pct": 1.5,
            "protection_type": "mev_share",
            "attacker_capital_eth": 100.0,
            "scenario_label": "MEV-Share — 90% user MEV rebate",
            "save_experiment": True,
        },
    ),
]


# ---------------------------------------------------------------------------
# Endpoint: POST /api/trade-protection/simulate
# ---------------------------------------------------------------------------

@router.post(
    "/simulate",
    response_model=TradeProtectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Trade Protection Simulation",
    description=(
        "Runs the full MEV detection and trade protection simulation. "
        "Returns unprotected trade metrics (sandwich attack baseline) alongside "
        "protected trade metrics for the chosen protection mechanism. "
        "Optionally saves the result as a completed 'protection' experiment."
    ),
    responses={
        200: {"description": "Simulation completed successfully"},
        422: {"description": "Validation error in request payload"},
        500: {"description": "Unexpected simulation error"},
    },
)
def simulate_trade_protection(
    payload: TradeProtectionRequest,
    db: Session = Depends(get_db),
) -> TradeProtectionResponse:
    """Execute the MEV detection and trade protection simulation.

    The simulation uses the Uniswap v2 constant-product AMM formula to model
    a sandwich attack and compute how much MEV each protection mechanism prevents.
    All calculations are deterministic and use synthetic data only.
    """
    logger.info(
        "Simulation request | protection='%s' trade=%.2f ETH pool=%.0f ETH",
        payload.protection_type,
        payload.trade_amount_eth,
        payload.pool_liquidity_eth,
    )

    # Build domain parameters from the API request
    params = TradeParameters(
        trade_amount_eth=payload.trade_amount_eth,
        pool_liquidity_eth=payload.pool_liquidity_eth,
        slippage_tolerance_pct=payload.slippage_tolerance_pct,
        protection_type=ProtectionType(payload.protection_type),
        attacker_capital_eth=payload.attacker_capital_eth,
        token_pair=payload.token_pair,
        scenario_label=payload.scenario_label,
        save_experiment=payload.save_experiment,
    )

    try:
        result = TradeProtectionService.simulate(
            params=params,
            db=db if payload.save_experiment else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Unexpected simulation error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during simulation. Please try again.",
        ) from exc

    # Map domain result → response schema
    return TradeProtectionResponse(
        experiment_id=result.experiment_id,
        scenario_label=result.scenario_label,
        token_pair=result.token_pair,
        protection_type=result.protection_type.value,
        mev_risk=MEVRiskResponse(
            risk_level=result.mev_risk.risk_level.value,
            attack_type=result.mev_risk.attack_type.value,
            mev_probability=result.mev_risk.mev_probability,
        ),
        unprotected=UnprotectedScenarioResponse(
            expected_price_eth=result.unprotected.expected_price_eth,
            user_execution_price_eth=result.unprotected.user_execution_price_eth,
            price_impact_pct=result.unprotected.price_impact_pct,
            mev_extracted_eth=result.unprotected.mev_extracted_eth,
            attacker_profit_eth=result.unprotected.attacker_profit_eth,
            user_loss_eth=result.unprotected.user_loss_eth,
            user_loss_pct=result.unprotected.user_loss_pct,
        ),
        protected=ProtectedScenarioResponse(
            user_execution_price_eth=result.protected.user_execution_price_eth,
            price_impact_pct=result.protected.price_impact_pct,
            mev_extracted_eth=result.protected.mev_extracted_eth,
            user_loss_eth=result.protected.user_loss_eth,
            user_loss_pct=result.protected.user_loss_pct,
            protection_effectiveness_pct=result.protected.protection_effectiveness_pct,
            user_savings_eth=result.protected.user_savings_eth,
            user_rebate_eth=result.protected.user_rebate_eth,
        ),
        simulation_notes=result.simulation_notes,
    )


# ---------------------------------------------------------------------------
# Endpoint: GET /api/trade-protection/scenarios
# ---------------------------------------------------------------------------

@router.get(
    "/scenarios",
    response_model=DemoScenariosResponse,
    status_code=status.HTTP_200_OK,
    summary="List Demo Scenarios",
    description=(
        "Returns a list of pre-built demo scenarios — one for each protection type. "
        "Each entry includes a ready-to-use request body that can be pasted directly "
        "into the POST /api/trade-protection/simulate endpoint."
    ),
)
def list_demo_scenarios() -> DemoScenariosResponse:
    """Return all built-in demonstration scenarios."""
    return DemoScenariosResponse(
        scenarios=_DEMO_SCENARIOS,
        total=len(_DEMO_SCENARIOS),
    )
