"""Integration Tests for Decentralization Analyzer API Endpoints.

Tests:
1. POST /api/decentralization/analyze (Builder + Relay combined analysis)
2. POST /api/decentralization/analyze (Builder-only analysis: relay_metrics is null)
3. POST /api/decentralization/analyze (Relay-only analysis: builder_metrics is null)
4. POST /api/decentralization/analyze validation errors (empty, 0 total, negative)
5. POST /api/decentralization/analyze with save_experiment=True persists retrievable experiment
6. POST /api/decentralization/analyze with save_experiment=False does not persist
7. POST /api/decentralization/pbs-simulate returns expected structure and deterministic seed
8. POST /api/decentralization/pbs-simulate validation (min builders, round bounds)
9. POST /api/decentralization/outage-simulate returns resilience comparison
10. POST /api/decentralization/outage-simulate handles 0 remaining participants safely
11. GET /api/decentralization/sample-data returns illustrative academic dataset
"""

import pytest
from fastapi.testclient import TestClient

from app.services.decentralization_sample_data import (
    ILLUSTRATIVE_BUILDERS,
    ILLUSTRATIVE_RELAYS,
)


class TestDecentralizationAnalyzeEndpoint:
    """Tests for POST /api/decentralization/analyze."""

    def test_combined_analysis_returns_200_and_expected_metrics(self, client: TestClient):
        payload = {
            "source_type": "illustrative_sample",
            "measurement_window": "Academic Demo Block Range",
            "builder_observations": ILLUSTRATIVE_BUILDERS,
            "relay_observations": ILLUSTRATIVE_RELAYS,
            "save_experiment": False,
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_type"] == "decentralization_analysis"
        assert data["source_type"] == "illustrative_sample"
        assert data["measurement_window"] == "Academic Demo Block Range"
        assert data["experiment_id"] is None

        # Builders check
        bm = data["builder_metrics"]
        assert bm is not None
        assert bm["total_observed_blocks"] == 1000
        assert bm["largest_participant_id"] == "builder_alpha"
        assert bm["largest_share_percentage"] == 45.0
        assert bm["top_three_share_percentage"] == 88.0
        assert bm["hhi"] == 3108.0
        assert bm["distinct_participants_count"] == 6

        # Relays check
        rm = data["relay_metrics"]
        assert rm is not None
        assert rm["total_observed_blocks"] == 1000
        assert rm["largest_participant_id"] == "relay_one"
        assert rm["largest_share_percentage"] == 60.0
        assert rm["top_three_share_percentage"] == 100.0
        assert rm["hhi"] == 4450.0
        assert rm["distinct_participants_count"] == 3

        # Warnings check
        warnings = data["warnings"]
        assert any("ILLUSTRATIVE SAMPLE" in w for w in warnings)
        assert any("METHODOLOGICAL DISCLAIMER" in w for w in warnings)

    def test_builder_only_leaves_relay_metrics_null(self, client: TestClient):
        payload = {
            "source_type": "user_supplied",
            "builder_observations": [
                {"builder_id": "b1", "block_count": 60},
                {"builder_id": "b2", "block_count": 40},
            ],
            "save_experiment": False,
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["builder_metrics"] is not None
        assert data["builder_metrics"]["total_observed_blocks"] == 100
        assert data["relay_metrics"] is None

    def test_relay_only_leaves_builder_metrics_null(self, client: TestClient):
        payload = {
            "source_type": "user_supplied",
            "relay_observations": [
                {"relay_id": "r1", "block_count": 75},
                {"relay_id": "r2", "block_count": 25},
            ],
            "save_experiment": False,
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["builder_metrics"] is None
        assert data["relay_metrics"] is not None
        assert data["relay_metrics"]["total_observed_blocks"] == 100
        assert data["relay_metrics"]["largest_share_percentage"] == 75.0

    def test_empty_observations_returns_422(self, client: TestClient):
        payload = {
            "source_type": "user_supplied",
            "builder_observations": [],
            "relay_observations": [],
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 422

    def test_zero_total_blocks_returns_422(self, client: TestClient):
        payload = {
            "source_type": "user_supplied",
            "builder_observations": [
                {"builder_id": "b1", "block_count": 0},
                {"builder_id": "b2", "block_count": 0},
            ],
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 422

    def test_negative_block_count_returns_422(self, client: TestClient):
        payload = {
            "source_type": "user_supplied",
            "builder_observations": [
                {"builder_id": "b1", "block_count": -10},
            ],
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 422

    def test_duplicate_builder_ids_aggregated_correctly(self, client: TestClient):
        payload = {
            "source_type": "user_supplied",
            "builder_observations": [
                {"builder_id": "builder_dup", "block_count": 30},
                {"builder_id": "builder_dup", "block_count": 20},
                {"builder_id": "builder_other", "block_count": 50},
            ],
            "save_experiment": False,
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        participants = data["builder_metrics"]["participants"]
        assert len(participants) == 2
        dup = next(p for p in participants if p["builder_id"] == "builder_dup")
        assert dup["block_count"] == 50
        assert dup["market_share_percentage"] == 50.0

    def test_save_experiment_creates_retrievable_record(self, client: TestClient):
        payload = {
            "source_type": "user_supplied",
            "measurement_window": "Persistent Test Window",
            "builder_observations": [
                {"builder_id": "builder_p1", "block_count": 70},
                {"builder_id": "builder_p2", "block_count": 30},
            ],
            "save_experiment": True,
        }
        response = client.post("/api/decentralization/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        exp_id = data["experiment_id"]
        assert exp_id is not None
        assert exp_id > 0

        # Retrieve experiment via Phase 2 API
        get_res = client.get(f"/api/experiments/{exp_id}")
        assert get_res.status_code == 200
        exp_data = get_res.json()
        assert exp_data["id"] == exp_id
        assert exp_data["module"] == "decentralization"
        assert exp_data["scenario"] == "builder_analysis"
        assert exp_data["status"] == "completed"
        assert exp_data["results"]["builder_metrics"]["hhi"] == 5800.0


class TestPBSSimulateEndpoint:
    """Tests for POST /api/decentralization/pbs-simulate."""

    def test_pbs_simulation_success(self, client: TestClient):
        payload = {
            "builder_ids": ["builder_a", "builder_b", "builder_c"],
            "num_rounds": 40,
            "seed": 999,
            "save_experiment": True,
        }
        response = client.post("/api/decentralization/pbs-simulate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_type"] == "pbs_auction_simulation"
        assert data["total_rounds"] == 40
        assert data["seed_used"] == 999
        assert data["distinct_builders_count"] == 3
        assert len(data["win_distribution"]) == 3
        assert len(data["round_details"]) == 40
        assert data["experiment_id"] is not None

        # Verify experiment in DB
        exp_res = client.get(f"/api/experiments/{data['experiment_id']}")
        assert exp_res.status_code == 200
        assert exp_res.json()["module"] == "decentralization"
        assert exp_res.json()["scenario"] == "pbs_simulation"

    def test_pbs_simulation_rejects_single_builder(self, client: TestClient):
        payload = {
            "builder_ids": ["lonely_builder"],
            "num_rounds": 10,
        }
        response = client.post("/api/decentralization/pbs-simulate", json=payload)
        assert response.status_code == 422

    def test_pbs_simulation_rejects_zero_rounds(self, client: TestClient):
        payload = {
            "builder_ids": ["b1", "b2"],
            "num_rounds": 0,
        }
        response = client.post("/api/decentralization/pbs-simulate", json=payload)
        assert response.status_code == 422


class TestOutageSimulateEndpoint:
    """Tests for POST /api/decentralization/outage-simulate."""

    def test_builder_outage_simulation_success(self, client: TestClient):
        payload = {
            "participant_type": "builder",
            "outage_participant_id": "builder_alpha",
            "baseline_observations": [
                {"builder_id": "builder_alpha", "block_count": 400},
                {"builder_id": "builder_beta", "block_count": 300},
                {"builder_id": "builder_gamma", "block_count": 300},
            ],
            "save_experiment": True,
        }
        response = client.post("/api/decentralization/outage-simulate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_type"] == "participant_outage_simulation"
        assert data["participant_type"] == "builder"
        assert data["outage_participant_id"] == "builder_alpha"
        assert data["impact_summary"]["baseline_blocks_lost"] == 400
        assert data["impact_summary"]["baseline_share_lost_pct"] == 40.0
        assert data["impact_summary"]["has_eligible_participants"] is True

        surviving = data["surviving_metrics"]
        assert surviving["total_observed_blocks"] == 600
        assert surviving["distinct_participants_count"] == 2
        assert surviving["largest_share_percentage"] == 50.0

    def test_outage_total_collapse_handled_safely(self, client: TestClient):
        payload = {
            "participant_type": "relay",
            "outage_participant_id": "solo_relay",
            "baseline_observations": [
                {"relay_id": "solo_relay", "block_count": 500},
            ],
            "save_experiment": False,
        }
        response = client.post("/api/decentralization/outage-simulate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["impact_summary"]["has_eligible_participants"] is False
        assert data["impact_summary"]["surviving_participants_count"] == 0
        assert data["surviving_metrics"] is None

    def test_outage_invalid_participant_type_returns_422(self, client: TestClient):
        payload = {
            "participant_type": "validator",  # Invalid type (only builder or relay permitted)
            "outage_participant_id": "val1",
            "baseline_observations": [{"builder_id": "val1", "block_count": 100}],
        }
        response = client.post("/api/decentralization/outage-simulate", json=payload)
        assert response.status_code == 422


class TestSampleDataEndpoint:
    """Tests for GET /api/decentralization/sample-data."""

    def test_get_sample_data_returns_200_and_payload(self, client: TestClient):
        response = client.get("/api/decentralization/sample-data")
        assert response.status_code == 200
        data = response.json()

        assert data["source_type"] == "illustrative_sample"
        assert len(data["builder_observations"]) == 6
        assert len(data["relay_observations"]) == 3
        assert data["verification_reference"]["builders"]["hhi"] == 3108.0
        assert data["verification_reference"]["relays"]["hhi"] == 4450.0


class TestEPBSCompareEndpoint:
    """Tests for POST /api/decentralization/epbs-compare."""

    def test_epbs_compare_success(self, client: TestClient):
        payload = {
            "num_simulated_slots": 100,
            "relay_failure_probability": 0.05,
            "builder_censorship_rate": 0.45,
            "save_experiment": True,
        }
        response = client.post("/api/decentralization/epbs-compare", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_type"] == "epbs_resilience_comparison"
        assert data["num_simulated_slots"] == 100
        assert data["proto_pbs_mev_boost"]["relay_dependency"] is True
        assert data["proto_pbs_mev_boost"]["missed_slots_count"] == 5
        assert data["enshrined_pbs_eip7732"]["relay_dependency"] is False
        assert data["enshrined_pbs_eip7732"]["missed_slots_count"] == 0
        assert data["epbs_with_inclusion_lists"]["censored_transactions_pct"] == 0.0
        assert data["suave_decentralized_builder"]["builder_hhi"] < 1000.0
        assert len(data["summary_findings"]) >= 3
        assert data["experiment_id"] is not None
