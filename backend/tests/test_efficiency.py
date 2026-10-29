from decimal import Decimal

from app.schemas.efficiency import EfficiencySimulationRequest
from app.services.efficiency import EfficiencyService
from app.models.experiment import Experiment
from app.services.efficiency_metrics import calculate_gas_cost, transaction_fee_profile
from app.services.queue_simulation import simulate_queue


def test_gas_cost_conversion():
    assert calculate_gas_cost(21000, Decimal("20")) == Decimal("0.00042")


def test_queue_capacity_and_deferred_transactions():
    txs = transaction_fee_profile(7, Decimal("2"), Decimal("1"))
    result = simulate_queue(
        transactions=txs,
        block_capacity=2,
        max_blocks=2,
        block_time_seconds=12,
        base_fee_gwei=Decimal("20"),
        average_gas_used=21000,
        submission_method="priority_fee_competition",
    )
    assert result["included_transactions"] == 4
    assert result["deferred_transactions"] == 3
    assert result["simulation_complete"] is False
    assert result["blocks_used"] == 2


def test_priority_fee_order_is_deterministic():
    txs = transaction_fee_profile(10, Decimal("2"), Decimal("1"))
    kwargs = dict(
        transactions=txs,
        block_capacity=4,
        max_blocks=1,
        block_time_seconds=12,
        base_fee_gwei=Decimal("20"),
        average_gas_used=21000,
        submission_method="priority_fee_competition",
    )
    first = simulate_queue(**kwargs)
    second = simulate_queue(**kwargs)
    assert first == second
    fees = [row["priority_fee_gwei"] for row in first["included"]]
    assert fees == sorted(fees, reverse=True)


def test_zero_transactions_is_safe():
    request = EfficiencySimulationRequest(transaction_count=0, save_experiment=False)
    result = EfficiencyService.simulate(request)
    assert result["selected_result"]["included_transactions"] == 0
    assert result["selected_result"]["inclusion_rate_pct"] == 100.0
    assert result["selected_result"]["estimated_total_cost_eth"] == 0.0


def test_service_returns_both_submission_methods():
    request = EfficiencySimulationRequest(
        transaction_count=25,
        block_capacity=5,
        max_blocks=2,
        submission_method="private_bundle_simulation",
        save_experiment=False,
    )
    result = EfficiencyService.simulate(request)
    assert result["selected_submission_method"] == "private_bundle_simulation"
    assert result["selected_result"] == result["private_bundle_simulation"]
    assert result["priority_fee_competition"]["included_transactions"] == 10
    assert result["private_bundle_simulation"]["included_transactions"] == 10


def test_api_efficiency_endpoint(client):
    response = client.post(
        "/api/efficiency/simulate",
        json={
            "transaction_count": 12,
            "block_capacity": 4,
            "average_gas_used": 21000,
            "base_fee_gwei": 20,
            "priority_fee_gwei": 2,
            "priority_fee_spread_gwei": 1,
            "max_blocks": 2,
            "submission_method": "priority_fee_competition",
            "save_experiment": False,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["selected_result"]["included_transactions"] == 8
    assert payload["selected_result"]["deferred_transactions"] == 4
    assert payload["experiment_id"] is None


def test_api_rejects_invalid_capacity(client):
    response = client.post(
        "/api/efficiency/simulate",
        json={"transaction_count": 10, "block_capacity": 0, "save_experiment": False},
    )
    assert response.status_code == 422


def test_efficiency_experiment_is_persisted_when_requested(db_session):
    request = EfficiencySimulationRequest(
        transaction_count=5,
        block_capacity=2,
        max_blocks=3,
        save_experiment=True,
    )
    result = EfficiencyService.simulate(request, db=db_session)
    assert result["experiment_id"] is not None
    record = db_session.query(Experiment).filter_by(id=result["experiment_id"]).one()
    assert record.module == "efficiency"
    assert record.status == "completed"
    assert record.results["selected_result"]["included_transactions"] == 5


def test_api_reorg_and_smoothing_simulate(client):
    response = client.post(
        "/api/efficiency/reorg-smoothing-simulate",
        json={
            "mev_spike_eth": 50.0,
            "validator_stake_pct": 20.0,
            "block_subsidy_eth": 0.06,
            "save_experiment": False,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["simulation_type"] == "consensus_reorg_and_smoothing_simulation"
    assert data["unsmoothed_status_quo"]["reorg_incentive_ratio"] > 100.0
    assert data["mev_smoothing_pool"]["reorg_threat_score_pct"] < 10.0
    assert data["mev_burn_eip7545"]["reorg_threat_score_pct"] == 0.0
    assert len(data["summary_findings"]) >= 3


def test_api_mev_taxonomy(client):
    response = client.get("/api/efficiency/taxonomy")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "taxonomy" in data
    assert len(data["taxonomy"]) == 4
    types = {item["mev_type"] for item in data["taxonomy"]}
    assert "Beneficial" in types
    assert "Toxic" in types
