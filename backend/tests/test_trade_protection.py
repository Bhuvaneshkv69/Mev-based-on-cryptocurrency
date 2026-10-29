"""Test Suite — Trade Protection Simulation Engine (Phase 3).

Covers:
  1. API endpoint smoke tests (POST /simulate, GET /scenarios)
  2. MEV risk detector unit tests
  3. Attack simulator unit tests
  4. Protection engine unit tests
  5. End-to-end simulation for each of the five protection types
  6. Boundary and validation tests
  7. Database persistence verification

All tests use the in-memory SQLite database configured in conftest.py.
No external services or real Ethereum nodes are required.
"""

import pytest
from fastapi.testclient import TestClient

from app.services.trade_protection.models import (
    AttackType,
    ProtectionType,
    RiskLevel,
    TradeParameters,
)
from app.services.trade_protection.mev_detector import MEVDetector
from app.services.trade_protection.attack_simulator import AttackSimulator
from app.services.trade_protection.protection_engine import ProtectionEngine
from app.services.trade_protection.trade_protection_service import TradeProtectionService


# ===========================================================================
# Helper factories
# ===========================================================================

def make_params(
    trade_amount_eth: float = 5.0,
    pool_liquidity_eth: float = 500.0,
    slippage_tolerance_pct: float = 0.5,
    protection_type: ProtectionType = ProtectionType.NONE,
    attacker_capital_eth: float = 50.0,
    token_pair: str = "ETH/USDC",
    scenario_label: str = "test_scenario",
    save_experiment: bool = False,
) -> TradeParameters:
    return TradeParameters(
        trade_amount_eth=trade_amount_eth,
        pool_liquidity_eth=pool_liquidity_eth,
        slippage_tolerance_pct=slippage_tolerance_pct,
        protection_type=protection_type,
        attacker_capital_eth=attacker_capital_eth,
        token_pair=token_pair,
        scenario_label=scenario_label,
        save_experiment=save_experiment,
    )


# ===========================================================================
# 1. API Endpoint Tests
# ===========================================================================

class TestSimulateEndpoint:
    """POST /api/trade-protection/simulate"""

    def test_simulate_returns_200(self, client: TestClient) -> None:
        """Valid request returns HTTP 200 with a complete response."""
        payload = {
            "trade_amount_eth": 5.0,
            "token_pair": "ETH/USDC",
            "pool_liquidity_eth": 500.0,
            "slippage_tolerance_pct": 0.5,
            "protection_type": "none",
            "attacker_capital_eth": 50.0,
            "scenario_label": "api smoke test",
            "save_experiment": False,
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        assert response.status_code == 200

    def test_simulate_response_has_required_fields(self, client: TestClient) -> None:
        """Response body contains all required top-level fields."""
        payload = {
            "trade_amount_eth": 5.0,
            "pool_liquidity_eth": 500.0,
            "protection_type": "none",
            "save_experiment": False,
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        data = response.json()
        assert "mev_risk" in data
        assert "unprotected" in data
        assert "protected" in data
        assert "simulation_notes" in data
        assert "protection_type" in data

    def test_simulate_saves_experiment_when_requested(self, client: TestClient) -> None:
        """When save_experiment=True, response includes a non-null experiment_id."""
        payload = {
            "trade_amount_eth": 5.0,
            "pool_liquidity_eth": 500.0,
            "protection_type": "none",
            "save_experiment": True,
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["experiment_id"] is not None
        assert isinstance(data["experiment_id"], int)
        assert data["experiment_id"] > 0

    def test_simulate_no_experiment_when_save_false(self, client: TestClient) -> None:
        """When save_experiment=False, experiment_id is null."""
        payload = {
            "trade_amount_eth": 5.0,
            "pool_liquidity_eth": 500.0,
            "protection_type": "none",
            "save_experiment": False,
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        assert response.status_code == 200
        assert response.json()["experiment_id"] is None

    def test_simulate_invalid_protection_type_returns_422(self, client: TestClient) -> None:
        """Invalid protection_type returns HTTP 422 Unprocessable Entity."""
        payload = {
            "trade_amount_eth": 5.0,
            "pool_liquidity_eth": 500.0,
            "protection_type": "teleportation",
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        assert response.status_code == 422

    def test_simulate_zero_trade_amount_returns_422(self, client: TestClient) -> None:
        """trade_amount_eth must be > 0."""
        payload = {
            "trade_amount_eth": 0.0,
            "pool_liquidity_eth": 500.0,
            "protection_type": "none",
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        assert response.status_code == 422

    def test_simulate_negative_pool_liquidity_returns_422(self, client: TestClient) -> None:
        """pool_liquidity_eth must be > 0."""
        payload = {
            "trade_amount_eth": 5.0,
            "pool_liquidity_eth": -100.0,
            "protection_type": "none",
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        assert response.status_code == 422

    def test_simulate_all_five_protection_types(self, client: TestClient) -> None:
        """All five protection types succeed and return HTTP 200."""
        for ptype in ["none", "private_mempool", "slippage_guard", "commit_reveal", "time_lock"]:
            payload = {
                "trade_amount_eth": 10.0,
                "pool_liquidity_eth": 500.0,
                "protection_type": ptype,
                "save_experiment": False,
            }
            response = client.post("/api/trade-protection/simulate", json=payload)
            assert response.status_code == 200, (
                f"protection_type='{ptype}' returned {response.status_code}"
            )

    def test_simulate_protection_type_case_insensitive(self, client: TestClient) -> None:
        """Protection type normalisation (uppercase input accepted)."""
        payload = {
            "trade_amount_eth": 5.0,
            "pool_liquidity_eth": 500.0,
            "protection_type": "PRIVATE_MEMPOOL",
            "save_experiment": False,
        }
        response = client.post("/api/trade-protection/simulate", json=payload)
        assert response.status_code == 200


class TestDemoScenariosEndpoint:
    """GET /api/trade-protection/scenarios"""

    def test_scenarios_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/trade-protection/scenarios")
        assert response.status_code == 200

    def test_scenarios_response_structure(self, client: TestClient) -> None:
        response = client.get("/api/trade-protection/scenarios")
        data = response.json()
        assert "scenarios" in data
        assert "total" in data
        assert isinstance(data["scenarios"], list)
        assert data["total"] == len(data["scenarios"])

    def test_scenarios_contains_all_protection_types(self, client: TestClient) -> None:
        """Every protection type is represented in the demo scenarios."""
        response = client.get("/api/trade-protection/scenarios")
        scenarios = response.json()["scenarios"]
        types_present = {s["request"]["protection_type"] for s in scenarios}
        expected = {
            "none",
            "private_mempool",
            "slippage_guard",
            "commit_reveal",
            "time_lock",
            "encrypted_mempool",
            "batch_auction",
            "mev_share",
        }
        assert expected == types_present

    def test_each_scenario_has_valid_request_body(self, client: TestClient) -> None:
        """Every demo scenario request body is executable against /simulate."""
        scenarios_resp = client.get("/api/trade-protection/scenarios")
        for scenario in scenarios_resp.json()["scenarios"]:
            req_body = scenario["request"]
            req_body["save_experiment"] = False  # don't clutter test DB
            resp = client.post("/api/trade-protection/simulate", json=req_body)
            assert resp.status_code == 200, (
                f"Demo scenario '{scenario['name']}' failed: {resp.text}"
            )


# ===========================================================================
# 2. MEV Detector Unit Tests
# ===========================================================================

class TestMEVDetector:
    """Unit tests for MEVDetector.assess()"""

    def test_micro_trade_is_no_attack(self) -> None:
        """A trade smaller than 0.5% of the pool has attack type NONE."""
        params = make_params(trade_amount_eth=0.1, pool_liquidity_eth=1000.0)
        risk = MEVDetector.assess(params)
        assert risk.attack_type == AttackType.NONE
        assert risk.risk_level == RiskLevel.LOW

    def test_small_trade_is_front_run(self) -> None:
        """A trade of ~1% of pool qualifies as front-run only."""
        params = make_params(trade_amount_eth=10.0, pool_liquidity_eth=1000.0)
        risk = MEVDetector.assess(params)
        assert risk.attack_type == AttackType.FRONT_RUN

    def test_large_trade_is_sandwich(self) -> None:
        """A trade of 5% or more of pool qualifies as a full sandwich."""
        params = make_params(trade_amount_eth=50.0, pool_liquidity_eth=1000.0)
        risk = MEVDetector.assess(params)
        assert risk.attack_type == AttackType.SANDWICH

    def test_probability_bounded(self) -> None:
        """MEV probability is always in [0, 1]."""
        for trade in [0.01, 1.0, 100.0, 10000.0]:
            params = make_params(trade_amount_eth=trade, pool_liquidity_eth=100.0)
            risk = MEVDetector.assess(params)
            assert 0.0 <= risk.mev_probability <= 1.0

    def test_high_risk_large_trade(self) -> None:
        """Very large trade vs. pool yields HIGH risk."""
        params = make_params(trade_amount_eth=200.0, pool_liquidity_eth=1000.0)
        risk = MEVDetector.assess(params)
        assert risk.risk_level == RiskLevel.HIGH

    def test_low_capital_reduces_probability(self) -> None:
        """Lower attacker capital yields lower MEV probability."""
        params_low = make_params(attacker_capital_eth=0.1)
        params_high = make_params(attacker_capital_eth=1000.0)
        risk_low = MEVDetector.assess(params_low)
        risk_high = MEVDetector.assess(params_high)
        assert risk_low.mev_probability < risk_high.mev_probability


# ===========================================================================
# 3. Attack Simulator Unit Tests
# ===========================================================================

class TestAttackSimulator:
    """Unit tests for AttackSimulator.simulate()"""

    def test_no_attack_returns_baseline(self) -> None:
        """NONE attack type returns baseline price and zero losses."""
        from app.services.trade_protection.models import MEVRisk
        params = make_params(trade_amount_eth=0.1, pool_liquidity_eth=1000.0)
        mev_risk = MEVRisk(
            risk_level=RiskLevel.LOW,
            attack_type=AttackType.NONE,
            mev_probability=0.05,
        )
        result = AttackSimulator.simulate(params, mev_risk)
        assert result.user_loss_eth == 0.0
        assert result.mev_extracted_eth == 0.0
        assert result.price_impact_pct == 0.0

    def test_sandwich_inflates_execution_price(self) -> None:
        """Sandwich attack makes the user's execution price higher than expected."""
        from app.services.trade_protection.models import MEVRisk
        params = make_params(trade_amount_eth=50.0, pool_liquidity_eth=500.0)
        mev_risk = MEVRisk(
            risk_level=RiskLevel.HIGH,
            attack_type=AttackType.SANDWICH,
            mev_probability=0.9,
        )
        result = AttackSimulator.simulate(params, mev_risk)
        assert result.user_execution_price_eth > result.expected_price_eth
        assert result.price_impact_pct > 0.0
        assert result.user_loss_eth > 0.0
        assert result.mev_extracted_eth > 0.0

    def test_attacker_profit_non_negative(self) -> None:
        """Attacker profit is always >= 0 (bots don't run at a loss)."""
        from app.services.trade_protection.models import MEVRisk
        for attack_type in [AttackType.FRONT_RUN, AttackType.SANDWICH]:
            params = make_params(trade_amount_eth=10.0, pool_liquidity_eth=500.0)
            mev_risk = MEVRisk(
                risk_level=RiskLevel.HIGH,
                attack_type=attack_type,
                mev_probability=0.8,
            )
            result = AttackSimulator.simulate(params, mev_risk)
            assert result.attacker_profit_eth >= 0.0

    def test_larger_trade_higher_impact(self) -> None:
        """Larger trade vs. same pool → higher price impact."""
        from app.services.trade_protection.models import MEVRisk
        risk = MEVRisk(
            risk_level=RiskLevel.HIGH,
            attack_type=AttackType.SANDWICH,
            mev_probability=0.9,
        )
        small = AttackSimulator.simulate(make_params(trade_amount_eth=10.0), risk)
        large = AttackSimulator.simulate(make_params(trade_amount_eth=100.0), risk)
        assert large.price_impact_pct > small.price_impact_pct

    def test_user_loss_pct_reasonable(self) -> None:
        """User loss pct is between 0 and 100."""
        from app.services.trade_protection.models import MEVRisk
        params = make_params(trade_amount_eth=50.0, pool_liquidity_eth=500.0)
        risk = MEVRisk(
            risk_level=RiskLevel.HIGH,
            attack_type=AttackType.SANDWICH,
            mev_probability=0.9,
        )
        result = AttackSimulator.simulate(params, risk)
        assert 0.0 <= result.user_loss_pct <= 100.0


# ===========================================================================
# 4. Protection Engine Unit Tests
# ===========================================================================

class TestProtectionEngine:
    """Unit tests for ProtectionEngine.apply()"""

    def _run_unprotected(self, trade: float = 50.0, pool: float = 500.0):
        """Helper to get an unprotected scenario for a sandwich attack."""
        from app.services.trade_protection.models import MEVRisk
        params = make_params(trade_amount_eth=trade, pool_liquidity_eth=pool)
        risk = MEVRisk(
            risk_level=RiskLevel.HIGH,
            attack_type=AttackType.SANDWICH,
            mev_probability=0.9,
        )
        unprotected = AttackSimulator.simulate(params, risk)
        return params, risk, unprotected

    def test_no_protection_effectiveness_is_zero(self) -> None:
        """NONE protection → 0% effectiveness."""
        params, risk, unprotected = self._run_unprotected()
        params.protection_type = ProtectionType.NONE
        result = ProtectionEngine.apply(params, risk, unprotected)
        assert result.protection_effectiveness_pct == 0.0
        assert result.user_savings_eth == 0.0

    def test_private_mempool_effectiveness_near_95(self) -> None:
        """Private mempool reduces MEV by approximately 95%."""
        params, risk, unprotected = self._run_unprotected()
        params.protection_type = ProtectionType.PRIVATE_MEMPOOL
        result = ProtectionEngine.apply(params, risk, unprotected)
        # 95% effectiveness with exact 0.05 residual multiplier
        assert abs(result.protection_effectiveness_pct - 95.0) < 0.01

    def test_commit_reveal_effectiveness_near_80(self) -> None:
        """Commit-reveal reduces MEV by approximately 80%."""
        params, risk, unprotected = self._run_unprotected()
        params.protection_type = ProtectionType.COMMIT_REVEAL
        result = ProtectionEngine.apply(params, risk, unprotected)
        assert abs(result.protection_effectiveness_pct - 80.0) < 0.01

    def test_time_lock_effectiveness_near_97_for_sandwich(self) -> None:
        """Time-lock reduces sandwich MEV by approximately 97%."""
        params, risk, unprotected = self._run_unprotected()
        params.protection_type = ProtectionType.TIME_LOCK
        result = ProtectionEngine.apply(params, risk, unprotected)
        assert abs(result.protection_effectiveness_pct - 97.0) < 0.01

    def test_user_savings_equal_loss_difference(self) -> None:
        """user_savings_eth = unprotected_loss - protected_loss."""
        params, risk, unprotected = self._run_unprotected()
        params.protection_type = ProtectionType.PRIVATE_MEMPOOL
        result = ProtectionEngine.apply(params, risk, unprotected)
        expected_savings = round(unprotected.user_loss_eth - result.user_loss_eth, 6)
        assert abs(result.user_savings_eth - expected_savings) < 1e-5

    def test_protection_effectiveness_bounded(self) -> None:
        """Effectiveness is always in [0, 100]."""
        params, risk, unprotected = self._run_unprotected()
        for ptype in ProtectionType:
            params.protection_type = ptype
            result = ProtectionEngine.apply(params, risk, unprotected)
            assert 0.0 <= result.protection_effectiveness_pct <= 100.0

    def test_slippage_guard_no_help_within_tolerance(self) -> None:
        """Slippage guard doesn't help if attack stays within tolerance."""
        from app.services.trade_protection.models import MEVRisk
        # Very small trade → very small price impact
        params = make_params(
            trade_amount_eth=1.0,
            pool_liquidity_eth=5000.0,
            slippage_tolerance_pct=50.0,  # Wide tolerance
            protection_type=ProtectionType.SLIPPAGE_GUARD,
        )
        risk = MEVRisk(
            risk_level=RiskLevel.LOW,
            attack_type=AttackType.FRONT_RUN,
            mev_probability=0.3,
        )
        unprotected = AttackSimulator.simulate(params, risk)
        result = ProtectionEngine.apply(params, risk, unprotected)
        # With 50% tolerance, the loss is within tolerance → no savings
        assert result.user_savings_eth == 0.0 or result.protection_effectiveness_pct < 50.0


# ===========================================================================
# 5. Full End-to-End Simulation Tests
# ===========================================================================

class TestFullSimulation:
    """End-to-end service tests (no DB) for each protection type."""

    def _run(self, protection: ProtectionType, trade: float = 50.0, pool: float = 500.0):
        params = make_params(
            trade_amount_eth=trade,
            pool_liquidity_eth=pool,
            protection_type=protection,
            save_experiment=False,
        )
        return TradeProtectionService.simulate(params, db=None)

    def test_none_simulation_completes(self) -> None:
        result = self._run(ProtectionType.NONE)
        assert result.protected.protection_effectiveness_pct == 0.0

    def test_private_mempool_simulation_completes(self) -> None:
        result = self._run(ProtectionType.PRIVATE_MEMPOOL)
        assert result.protected.protection_effectiveness_pct >= 90.0

    def test_slippage_guard_simulation_completes(self) -> None:
        result = self._run(ProtectionType.SLIPPAGE_GUARD)
        assert result.experiment_id is None

    def test_commit_reveal_simulation_completes(self) -> None:
        result = self._run(ProtectionType.COMMIT_REVEAL)
        assert result.protected.protection_effectiveness_pct >= 75.0

    def test_time_lock_simulation_completes(self) -> None:
        result = self._run(ProtectionType.TIME_LOCK)
        assert result.protected.protection_effectiveness_pct >= 90.0

    def test_result_has_simulation_notes(self) -> None:
        result = self._run(ProtectionType.PRIVATE_MEMPOOL)
        assert len(result.simulation_notes) > 0
        assert all(isinstance(n, str) for n in result.simulation_notes)

    def test_experiment_id_none_when_save_false(self) -> None:
        result = self._run(ProtectionType.NONE)
        assert result.experiment_id is None

    def test_simulation_with_db_saves_experiment(self, db_session) -> None:
        """When save_experiment=True with a db session, an experiment is created."""
        params = make_params(
            trade_amount_eth=10.0,
            pool_liquidity_eth=500.0,
            protection_type=ProtectionType.PRIVATE_MEMPOOL,
            save_experiment=True,
        )
        result = TradeProtectionService.simulate(params, db=db_session)
        assert result.experiment_id is not None
        assert isinstance(result.experiment_id, int)

    def test_simulation_persisted_with_completed_status(self, db_session) -> None:
        """Persisted experiment has status 'completed' and module 'protection'."""
        from app.models.experiment import Experiment
        params = make_params(
            trade_amount_eth=10.0,
            pool_liquidity_eth=500.0,
            save_experiment=True,
        )
        result = TradeProtectionService.simulate(params, db=db_session)
        exp = db_session.query(Experiment).filter(
            Experiment.id == result.experiment_id
        ).first()
        assert exp is not None
        assert exp.status == "completed"
        assert exp.module == "protection"
        assert exp.results is not None


# ===========================================================================
# 6. Consistency and Boundary Tests
# ===========================================================================

class TestConsistency:
    """Verify mathematical consistency of simulation results."""

    def test_protected_loss_never_exceeds_unprotected(self) -> None:
        """Protected user loss ≤ unprotected user loss for all protection types."""
        for ptype in ProtectionType:
            params = make_params(
                trade_amount_eth=20.0,
                pool_liquidity_eth=500.0,
                protection_type=ptype,
                save_experiment=False,
            )
            result = TradeProtectionService.simulate(params, db=None)
            assert result.protected.user_loss_eth <= result.unprotected.user_loss_eth + 1e-9, (
                f"{ptype.value}: protected loss {result.protected.user_loss_eth} > "
                f"unprotected {result.unprotected.user_loss_eth}"
            )

    def test_private_mempool_better_than_none(self) -> None:
        """Private mempool always outperforms no protection for a large trade."""
        params_none = make_params(
            trade_amount_eth=50.0, protection_type=ProtectionType.NONE
        )
        params_pm = make_params(
            trade_amount_eth=50.0, protection_type=ProtectionType.PRIVATE_MEMPOOL
        )
        result_none = TradeProtectionService.simulate(params_none, db=None)
        result_pm = TradeProtectionService.simulate(params_pm, db=None)
        assert result_pm.protected.user_loss_eth < result_none.unprotected.user_loss_eth

    def test_very_small_trade_low_risk(self) -> None:
        """A micro trade (0.001 ETH in a deep pool) has LOW risk."""
        params = make_params(trade_amount_eth=0.001, pool_liquidity_eth=10_000.0)
        result = TradeProtectionService.simulate(params, db=None)
        assert result.mev_risk.risk_level == RiskLevel.LOW
