"""Unit Tests for Decentralization Metrics Engine.

Tests:
1. Total block count calculation
2. Market-share percentages
3. Largest builder share
4. Top-three builder share (including cases with < 3 builders)
5. Herfindahl-Hirschman Index (HHI) computation and thresholds
6. Deterministic sorting (descending blocks, ascending ID tie-breaker)
7. Empty dataset rejection
8. All-zero dataset rejection
9. Negative count rejection
10. Duplicate identifier aggregation
11. Independent relay calculation (no cross-contamination with builder numbers)
12. Warning and limitation generation
13. Exact verification against the illustrative academic dataset
"""

import pytest

from app.services.decentralization_metrics import (
    aggregate_observations,
    calculate_participant_metrics,
    classify_hhi,
    generate_decentralization_warnings,
    round_float,
)
from app.services.decentralization_sample_data import (
    ILLUSTRATIVE_BUILDERS,
    ILLUSTRATIVE_RELAYS,
)


class TestObservationAggregation:
    """Tests for raw observation aggregation and input sanitization."""

    def test_aggregate_distinct_observations(self):
        obs = [
            {"builder_id": "b1", "block_count": 10},
            {"builder_id": "b2", "block_count": 20},
        ]
        result = aggregate_observations(obs, id_field="builder_id")
        assert len(result) == 2
        id_map = {r["builder_id"]: r["block_count"] for r in result}
        assert id_map["b1"] == 10
        assert id_map["b2"] == 20

    def test_aggregate_duplicate_identifiers_sums_counts(self):
        obs = [
            {"builder_id": "builder_alpha", "block_count": 300, "display_name": "Alpha 1"},
            {"builder_id": "builder_beta", "block_count": 200},
            {"builder_id": "builder_alpha", "block_count": 150, "display_name": "Alpha 2"},
        ]
        result = aggregate_observations(obs, id_field="builder_id")
        assert len(result) == 2
        alpha = next(r for r in result if r["builder_id"] == "builder_alpha")
        beta = next(r for r in result if r["builder_id"] == "builder_beta")
        assert alpha["block_count"] == 450
        assert alpha["display_name"] == "Alpha 2"
        assert beta["block_count"] == 200

    def test_reject_empty_observations_list(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            aggregate_observations([], id_field="builder_id")

    def test_reject_blank_or_whitespace_identifier(self):
        obs = [{"builder_id": "   ", "block_count": 100}]
        with pytest.raises(ValueError, match="cannot be empty or blank"):
            aggregate_observations(obs, id_field="builder_id")

    def test_reject_negative_block_count(self):
        obs = [{"builder_id": "builder_neg", "block_count": -5}]
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            aggregate_observations(obs, id_field="builder_id")


class TestMetricCalculations:
    """Tests for pure concentration metric formulas."""

    def test_total_observed_blocks(self):
        obs = [
            {"builder_id": "b1", "block_count": 50},
            {"builder_id": "b2", "block_count": 30},
            {"builder_id": "b3", "block_count": 20},
        ]
        metrics = calculate_participant_metrics(obs, id_field="builder_id", participant_label="builder")
        assert metrics["total_observed_blocks"] == 100
        assert metrics["distinct_participants_count"] == 3

    def test_market_share_percentages(self):
        obs = [
            {"builder_id": "b1", "block_count": 60},
            {"builder_id": "b2", "block_count": 40},
        ]
        metrics = calculate_participant_metrics(obs, id_field="builder_id")
        assert metrics["participants"][0]["market_share_percentage"] == 60.0
        assert metrics["participants"][1]["market_share_percentage"] == 40.0

    def test_largest_and_top_three_share(self):
        obs = [
            {"builder_id": "b1", "block_count": 500},
            {"builder_id": "b2", "block_count": 250},
            {"builder_id": "b3", "block_count": 150},
            {"builder_id": "b4", "block_count": 100},
        ]
        metrics = calculate_participant_metrics(obs, id_field="builder_id")
        assert metrics["largest_participant_id"] == "b1"
        assert metrics["largest_share_percentage"] == 50.0
        # Top 3: 50% + 25% + 15% = 90%
        assert metrics["top_three_share_percentage"] == 90.0

    def test_top_three_share_with_fewer_than_three_builders(self):
        obs = [
            {"builder_id": "b1", "block_count": 70},
            {"builder_id": "b2", "block_count": 30},
        ]
        metrics = calculate_participant_metrics(obs, id_field="builder_id")
        assert metrics["largest_share_percentage"] == 70.0
        assert metrics["top_three_share_percentage"] == 100.0

    def test_hhi_calculation_and_classification(self):
        # 2 equal participants: 50% each
        # HHI = 50^2 + 50^2 = 2500 + 2500 = 5000 (high concentration)
        obs = [
            {"builder_id": "b1", "block_count": 50},
            {"builder_id": "b2", "block_count": 50},
        ]
        metrics = calculate_participant_metrics(obs, id_field="builder_id")
        assert metrics["hhi"] == 5000.0
        assert metrics["hhi_category"] == "high"

    def test_hhi_low_concentration(self):
        # 10 equal participants: 10% each
        # HHI = 10 * (10^2) = 1000 (< 1500 -> low)
        obs = [{"builder_id": f"b{i}", "block_count": 10} for i in range(10)]
        metrics = calculate_participant_metrics(obs, id_field="builder_id")
        assert metrics["hhi"] == 1000.0
        assert metrics["hhi_category"] == "low"

    def test_deterministic_sorting_with_tie_breaker(self):
        # Equal block count: b_zeta vs b_alpha vs b_gamma
        obs = [
            {"builder_id": "b_zeta", "block_count": 100},
            {"builder_id": "b_alpha", "block_count": 100},
            {"builder_id": "b_gamma", "block_count": 100},
        ]
        metrics = calculate_participant_metrics(obs, id_field="builder_id")
        ids = [p["builder_id"] for p in metrics["participants"]]
        # Alphabetical tie-breaker: b_alpha, b_gamma, b_zeta
        assert ids == ["b_alpha", "b_gamma", "b_zeta"]

    def test_reject_zero_total_blocks(self):
        obs = [
            {"builder_id": "b1", "block_count": 0},
            {"builder_id": "b2", "block_count": 0},
        ]
        with pytest.raises(ValueError, match="must be greater than zero"):
            calculate_participant_metrics(obs, id_field="builder_id")


class TestIndependentRelayCalculations:
    """Verifies relay calculations are completely independent from builder counts."""

    def test_relay_metrics_structure(self):
        obs = [
            {"relay_id": "relay_A", "block_count": 700},
            {"relay_id": "relay_B", "block_count": 300},
        ]
        metrics = calculate_participant_metrics(obs, id_field="relay_id", participant_label="relay")
        assert metrics["participant_label"] == "relay"
        assert metrics["total_observed_blocks"] == 1000
        assert metrics["largest_participant_id"] == "relay_A"
        assert metrics["largest_share_percentage"] == 70.0
        assert metrics["top_three_share_percentage"] == 100.0
        # HHI = 70^2 + 30^2 = 4900 + 900 = 5800
        assert metrics["hhi"] == 5800.0


class TestIllustrativeSampleDatasetVerification:
    """Verifies that the built-in illustrative dataset produces the exact hand-calculated metrics."""

    def test_illustrative_builders_hand_calculation(self):
        metrics = calculate_participant_metrics(
            ILLUSTRATIVE_BUILDERS,
            id_field="builder_id",
            participant_label="builder",
        )
        assert metrics["total_observed_blocks"] == 1000
        assert metrics["distinct_participants_count"] == 6
        assert metrics["largest_participant_id"] == "builder_alpha"
        assert metrics["largest_share_percentage"] == 45.0
        # Top-3: 450 + 280 + 150 = 880 blocks = 88.0%
        assert metrics["top_three_share_percentage"] == 88.0
        # HHI = 45^2 + 28^2 + 15^2 + 8^2 + 3^2 + 1^2 = 2025 + 784 + 225 + 64 + 9 + 1 = 3108
        assert metrics["hhi"] == 3108.0
        assert metrics["hhi_category"] == "high"

    def test_illustrative_relays_hand_calculation(self):
        metrics = calculate_participant_metrics(
            ILLUSTRATIVE_RELAYS,
            id_field="relay_id",
            participant_label="relay",
        )
        assert metrics["total_observed_blocks"] == 1000
        assert metrics["distinct_participants_count"] == 3
        assert metrics["largest_participant_id"] == "relay_one"
        assert metrics["largest_share_percentage"] == 60.0
        # Top-3: 600 + 250 + 150 = 1000 = 100.0%
        assert metrics["top_three_share_percentage"] == 100.0
        # HHI = 60^2 + 25^2 + 15^2 = 3600 + 625 + 225 = 4450
        assert metrics["hhi"] == 4450.0
        assert metrics["hhi_category"] == "high"


class TestWarningsGeneration:
    """Tests that contextual warnings and boundary notices are properly attached."""

    def test_small_sample_and_dominant_builder_warnings(self):
        builder_metrics = {
            "total_observed_blocks": 50,
            "distinct_participants_count": 2,
            "largest_share_percentage": 60.0,
            "top_three_share_percentage": 100.0,
            "hhi": 5200.0,
        }
        warnings = generate_decentralization_warnings(
            builder_metrics=builder_metrics,
            source_type="illustrative_sample",
            measurement_window=None,
        )
        assert any("ILLUSTRATIVE SAMPLE" in w for w in warnings)
        assert any("UNSPECIFIED WINDOW" in w for w in warnings)
        assert any("SMALL SAMPLE (Builders)" in w for w in warnings)
        assert any("DOMINANT BUILDER RISK" in w for w in warnings)
        assert any("METHODOLOGICAL DISCLAIMER" in w for w in warnings)

    def test_relay_warnings_include_attribution_note(self):
        relay_metrics = {
            "total_observed_blocks": 500,
            "distinct_participants_count": 3,
            "largest_share_percentage": 55.0,
            "top_three_share_percentage": 100.0,
            "hhi": 3800.0,
        }
        warnings = generate_decentralization_warnings(
            relay_metrics=relay_metrics,
            source_type="user_supplied",
            measurement_window="Blocks 18,000,000 - 18,000,500",
        )
        assert any("RELAY ATTRIBUTION NOTE" in w for w in warnings)
        assert any("CRITICAL RELAY DEPENDENCY" in w for w in warnings)
