"""Trade Protection Simulation Orchestrator.

Coordinates the full simulation pipeline:
  1. Build domain model from API request schema
  2. Assess MEV risk (MEVDetector)
  3. Simulate unprotected attack (AttackSimulator)
  4. Apply protection mechanism (ProtectionEngine)
  5. Generate human-readable notes
  6. Optionally persist the completed experiment to the database
  7. Return the assembled SimulationResult

This service is the only public interface for the trade_protection package.
Route handlers should import and call TradeProtectionService.simulate().
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.services.trade_protection.models import (
    AttackType,
    MEVRisk,
    ProtectedScenario,
    ProtectionType,
    SimulationResult,
    TradeParameters,
    UnprotectedScenario,
)
from app.services.trade_protection.mev_detector import MEVDetector
from app.services.trade_protection.attack_simulator import AttackSimulator
from app.services.trade_protection.protection_engine import ProtectionEngine
from app.schemas.experiment import ExperimentCreate
from app.services.experiment_service import ExperimentService

logger = logging.getLogger("mevshield.trade_protection")


# ---------------------------------------------------------------------------
# Human-readable note templates
# ---------------------------------------------------------------------------

_NOTES: dict[ProtectionType, list[str]] = {
    ProtectionType.NONE: [
        "No protection applied — trade is visible in the public Ethereum mempool.",
        "MEV bots continuously monitor the mempool and can reorder transactions.",
        "This scenario represents the baseline risk all unprotected DeFi trades face.",
    ],
    ProtectionType.PRIVATE_MEMPOOL: [
        "Order sent via a private RPC relay (e.g. Flashbots Protect / MEV Blocker).",
        "Transaction bypasses the public mempool, hiding it from searcher bots.",
        "Residual MEV risk ≈ 5 % — relay-level leakage or builder collusion.",
        "No change in on-chain execution mechanics — same gas cost as a public tx.",
    ],
    ProtectionType.SLIPPAGE_GUARD: [
        "Tight slippage tolerance enforced at the smart-contract level.",
        "If actual price impact exceeds the tolerance, the trade reverts on-chain.",
        "User loses gas cost on a revert but avoids the MEV loss.",
        "Does NOT hide the transaction from the mempool — bot can still front-run.",
        "Most effective for trades where pool liquidity is high relative to size.",
    ],
    ProtectionType.COMMIT_REVEAL: [
        "Two-phase scheme: commit hash in block N, reveal & execute in block N+1.",
        "By the time the attacker sees trade details, the commitment is already mined.",
        "Residual risk ≈ 20 % — timing attacks and validator/builder bribery still possible.",
        "Adds one block of latency (~12 s on mainnet) and one extra transaction.",
    ],
    ProtectionType.TIME_LOCK: [
        "TWAP (time-weighted) order splits execution across multiple blocks.",
        "Average price over N blocks makes sandwich profit collapse to near-zero.",
        "Highly effective against sandwich attacks; partially effective against front-runs.",
        "Trade may take several minutes to fully execute — suitable for large swaps.",
    ],
    ProtectionType.ENCRYPTED_MEMPOOL: [
        "Cryptographic threshold encryption (e.g., Shutter Network / EIP-7732).",
        "Overcomes limitation: Completely eliminates reliance on trusting private RPC operators.",
        "Trade contents and swap amounts are concealed until the block ordering is finalized.",
        "Mempool searchers see zero calldata — sandwich attack probability drops to 0.0%.",
    ],
    ProtectionType.BATCH_AUCTION: [
        "Discrete batch clearing mechanism (e.g., CoW Swap / Gnosis Protocol).",
        "Overcomes limitation: Removes intra-block transaction ordering advantage entirely.",
        "All trades in the batch execute at a single, uniform clearing price p*.",
        "Front-running and sandwiching are mathematically neutralized without latency penalty.",
    ],
    ProtectionType.MEV_SHARE: [
        "Programmable order flow and intent auction (e.g., Flashbots MEV-Share).",
        "Overcomes limitation: Transforms user extraction loss into a programmatic 90% cashback rebate.",
        "Searchers compete to back-run and return the extracted spread directly to the trade sender.",
        "User retains full trading liquidity while turning adversarial MEV into user surplus.",
    ],
}


class TradeProtectionService:
    """Orchestrates the full MEV detection and trade protection simulation."""

    @staticmethod
    def simulate(
        params: TradeParameters,
        db: Optional[Session] = None,
    ) -> SimulationResult:
        """Run the complete simulation pipeline.

        Args:
            params: Validated trade simulation parameters.
            db:     SQLAlchemy session (required if params.save_experiment is True).

        Returns:
            SimulationResult with all computed metrics and optional experiment ID.

        Raises:
            ValueError: If save_experiment is True but no db session is provided.
        """
        if params.save_experiment and db is None:
            raise ValueError(
                "A database session is required when save_experiment is True."
            )

        logger.info(
            "Starting trade protection simulation | scenario='%s' protection='%s'",
            params.scenario_label,
            params.protection_type.value,
        )

        # ------------------------------------------------------------------
        # Step 1: Assess MEV risk
        # ------------------------------------------------------------------
        mev_risk: MEVRisk = MEVDetector.assess(params)

        # ------------------------------------------------------------------
        # Step 2: Simulate unprotected attack
        # ------------------------------------------------------------------
        unprotected: UnprotectedScenario = AttackSimulator.simulate(params, mev_risk)

        # ------------------------------------------------------------------
        # Step 3: Apply protection mechanism
        # ------------------------------------------------------------------
        protected: ProtectedScenario = ProtectionEngine.apply(params, mev_risk, unprotected)

        # ------------------------------------------------------------------
        # Step 4: Assemble human-readable notes
        # ------------------------------------------------------------------
        notes: List[str] = TradeProtectionService._build_notes(
            params, mev_risk, unprotected, protected
        )

        # ------------------------------------------------------------------
        # Step 5: Persist experiment to database (if requested)
        # ------------------------------------------------------------------
        experiment_id: Optional[int] = None
        if params.save_experiment and db is not None:
            experiment_id = TradeProtectionService._persist_experiment(
                db, params, mev_risk, unprotected, protected
            )

        logger.info(
            "Simulation complete | experiment_id=%s mev_prob=%.2f effectiveness=%.1f%%",
            experiment_id,
            mev_risk.mev_probability,
            protected.protection_effectiveness_pct,
        )

        return SimulationResult(
            scenario_label=params.scenario_label,
            token_pair=params.token_pair,
            protection_type=params.protection_type,
            mev_risk=mev_risk,
            unprotected=unprotected,
            protected=protected,
            simulation_notes=notes,
            experiment_id=experiment_id,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_notes(
        params: TradeParameters,
        mev_risk: MEVRisk,
        unprotected: UnprotectedScenario,
        protected: ProtectedScenario,
    ) -> List[str]:
        """Build contextual notes for the simulation result."""
        notes = list(_NOTES.get(params.protection_type, []))

        # Add dynamic summary note
        if unprotected.user_loss_eth > 0:
            notes.append(
                f"Without protection: user loses ~{unprotected.user_loss_eth:.4f} ETH "
                f"({unprotected.user_loss_pct:.2f}% of trade amount) to MEV."
            )

        if protected.user_savings_eth > 0:
            notes.append(
                f"With {params.protection_type.value}: saves ~{protected.user_savings_eth:.4f} ETH "
                f"({protected.protection_effectiveness_pct:.1f}% protection effectiveness)."
            )

        if mev_risk.attack_type == AttackType.NONE:
            notes.append(
                "Trade size is below the MEV profitability threshold after gas costs — "
                "a bot attack is unlikely for this specific trade."
            )

        return notes

    @staticmethod
    def _persist_experiment(
        db: Session,
        params: TradeParameters,
        mev_risk: MEVRisk,
        unprotected: UnprotectedScenario,
        protected: ProtectedScenario,
    ) -> int:
        """Persist the simulation as a completed experiment and return its ID."""
        input_parameters = {
            "trade_amount_eth": params.trade_amount_eth,
            "pool_liquidity_eth": params.pool_liquidity_eth,
            "slippage_tolerance_pct": params.slippage_tolerance_pct,
            "protection_type": params.protection_type.value,
            "attacker_capital_eth": params.attacker_capital_eth,
            "token_pair": params.token_pair,
        }

        results = {
            "mev_risk": {
                "risk_level": mev_risk.risk_level.value,
                "attack_type": mev_risk.attack_type.value,
                "mev_probability": mev_risk.mev_probability,
            },
            "unprotected": {
                "expected_price_eth": unprotected.expected_price_eth,
                "user_execution_price_eth": unprotected.user_execution_price_eth,
                "price_impact_pct": unprotected.price_impact_pct,
                "mev_extracted_eth": unprotected.mev_extracted_eth,
                "user_loss_eth": unprotected.user_loss_eth,
                "user_loss_pct": unprotected.user_loss_pct,
            },
            "protected": {
                "user_execution_price_eth": protected.user_execution_price_eth,
                "price_impact_pct": protected.price_impact_pct,
                "mev_extracted_eth": protected.mev_extracted_eth,
                "user_loss_eth": protected.user_loss_eth,
                "user_loss_pct": protected.user_loss_pct,
                "protection_effectiveness_pct": protected.protection_effectiveness_pct,
                "user_savings_eth": protected.user_savings_eth,
            },
        }

        assumptions = {
            "simulation_engine": "MEVShield AMM constant-product model v1",
            "data_source": "synthetic",
            "notes": (
                "Results are computed deterministically using the Uniswap v2 "
                "constant-product formula. No external blockchain data used."
            ),
        }

        experiment_data = ExperimentCreate(
            module="protection",
            scenario=params.scenario_label,
            input_parameters=input_parameters,
            assumptions=assumptions,
        )

        # Create the experiment and immediately mark it as completed with results
        experiment = ExperimentService.create_experiment(db, experiment_data)
        experiment.status = "completed"
        experiment.results = results
        db.commit()
        db.refresh(experiment)

        return experiment.id
