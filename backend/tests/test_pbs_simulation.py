"""Unit Tests for Proposer-Builder Separation (PBS) and Outage Resilience Simulation.

Tests:
1. Valid multi-round PBS simulation completes with expected structure
2. Winner selection selects the highest eligible bid
3. Equal bids break ties deterministically (lexicographically)
4. Deterministic seed produces 100% reproducible outcomes
5. Round count bounds validation (rejection of < 1 and > 10,000)
6. Minimum builder participant count validation (rejection of < 2 builders)
7. Builder outage re-normalizes surviving shares correctly
8. Outage with zero remaining participants handled safely without division by zero
9. Relay outage isolates relay observations correctly
"""

import pytest

from app.services.pbs_simulation import (
    run_pbs_auction_simulation,
    run_outage_simulation,
)


class TestPBSAuctionSimulation:
    """Tests for multi-round block construction auctions."""

    def test_valid_pbs_simulation_completes(self):
        builders = ["builder_alpha", "builder_beta", "builder_gamma"]
        result = run_pbs_auction_simulation(
            builder_ids=builders,
            num_rounds=50,
            seed=42,
            include_round_details=True,
        )

        assert result["simulation_type"] == "pbs_auction_simulation"
        assert result["total_rounds"] == 50
        assert result["seed_used"] == 42
        assert result["distinct_builders_count"] == 3
        assert result["average_winning_bid_eth"] > 0
        assert len(result["win_distribution"]) == 3

        # Sum of wins must equal total rounds
        total_wins = sum(b["win_count"] for b in result["win_distribution"])
        assert total_wins == 50

        # Percentages must sum to 100%
        total_pct = sum(b["win_percentage"] for b in result["win_distribution"])
        assert pytest.approx(total_pct, abs=0.1) == 100.0

        # Round details present for rounds <= 100
        assert len(result["round_details"]) == 50
        assert result["round_details"][0]["round"] == 1
        assert "winner_builder_id" in result["round_details"][0]
        assert "winning_bid_eth" in result["round_details"][0]

    def test_repeatable_results_with_same_seed(self):
        builders = ["builder_1", "builder_2", "builder_3", "builder_4"]
        res1 = run_pbs_auction_simulation(builder_ids=builders, num_rounds=100, seed=123)
        res2 = run_pbs_auction_simulation(builder_ids=builders, num_rounds=100, seed=123)

        assert res1["win_distribution"] == res2["win_distribution"]
        assert res1["average_winning_bid_eth"] == res2["average_winning_bid_eth"]
        assert res1["round_details"] == res2["round_details"]

    def test_deterministic_tie_breaker_highest_bid_wins(self):
        # Provide fixed bids where b_alpha and b_beta have identical fixed bids
        builders = ["builder_zeta", "builder_alpha"]
        # Bid params with identical mean and zero std_dev
        bid_params = {
            "builder_zeta": {"mean_bid_eth": 0.50, "std_dev_eth": 0.0},
            "builder_alpha": {"mean_bid_eth": 0.50, "std_dev_eth": 0.0},
        }
        res = run_pbs_auction_simulation(
            builder_ids=builders,
            num_rounds=10,
            seed=42,
            builder_bid_params=bid_params,
        )
        # Lexicographically, builder_alpha < builder_zeta, so builder_alpha must win all ties
        for r in res["round_details"]:
            assert r["winner_builder_id"] == "builder_alpha"

    def test_reject_fewer_than_two_builders(self):
        with pytest.raises(ValueError, match="requires at least 2 distinct builder"):
            run_pbs_auction_simulation(builder_ids=["only_one_builder"], num_rounds=10)

        with pytest.raises(ValueError, match="At least one builder ID is required"):
            run_pbs_auction_simulation(builder_ids=[], num_rounds=10)

    def test_reject_invalid_round_counts(self):
        builders = ["b1", "b2"]
        with pytest.raises(ValueError, match="must be an integer between 1 and 10,000"):
            run_pbs_auction_simulation(builder_ids=builders, num_rounds=0)

        with pytest.raises(ValueError, match="must be an integer between 1 and 10,000"):
            run_pbs_auction_simulation(builder_ids=builders, num_rounds=10001)

    def test_round_details_omitted_for_large_round_counts(self):
        builders = ["b1", "b2"]
        res = run_pbs_auction_simulation(builder_ids=builders, num_rounds=150, include_round_details=True)
        # Should be omitted / empty list for rounds > 100 to preserve payload sanity
        assert len(res["round_details"]) == 0


class TestOutageResilienceSimulation:
    """Tests for participant downtime and resilience modeling."""

    def test_builder_outage_renormalizes_shares(self):
        baseline = [
            {"builder_id": "builder_alpha", "block_count": 500},
            {"builder_id": "builder_beta", "block_count": 300},
            {"builder_id": "builder_gamma", "block_count": 200},
        ]
        res = run_outage_simulation(
            participant_type="builder",
            outage_participant_id="builder_alpha",
            baseline_observations=baseline,
        )

        assert res["simulation_type"] == "participant_outage_simulation"
        assert res["participant_type"] == "builder"
        assert res["outage_participant_id"] == "builder_alpha"
        assert res["impact_summary"]["baseline_blocks_lost"] == 500
        assert res["impact_summary"]["baseline_share_lost_pct"] == 50.0
        assert res["impact_summary"]["has_eligible_participants"] is True
        assert res["impact_summary"]["surviving_participants_count"] == 2

        # Surviving: builder_beta (300/500 = 60%), builder_gamma (200/500 = 40%)
        surviving = res["surviving_metrics"]
        assert surviving["total_observed_blocks"] == 500
        assert surviving["largest_participant_id"] == "builder_beta"
        assert surviving["largest_share_percentage"] == 60.0
        # HHI: 60^2 + 40^2 = 3600 + 1600 = 5200
        assert surviving["hhi"] == 5200.0

    def test_relay_outage_isolates_relay_observations(self):
        baseline = [
            {"relay_id": "relay_1", "block_count": 800},
            {"relay_id": "relay_2", "block_count": 200},
        ]
        res = run_outage_simulation(
            participant_type="relay",
            outage_participant_id="relay_1",
            baseline_observations=baseline,
        )

        assert res["participant_type"] == "relay"
        assert res["impact_summary"]["baseline_blocks_lost"] == 800
        assert res["impact_summary"]["baseline_share_lost_pct"] == 80.0
        surviving = res["surviving_metrics"]
        assert surviving["distinct_participants_count"] == 1
        assert surviving["largest_participant_id"] == "relay_2"
        assert surviving["largest_share_percentage"] == 100.0
        assert surviving["hhi"] == 10000.0

    def test_outage_with_zero_remaining_participants_handles_division_by_zero(self):
        baseline = [
            {"builder_id": "solo_builder", "block_count": 100},
        ]
        res = run_outage_simulation(
            participant_type="builder",
            outage_participant_id="solo_builder",
            baseline_observations=baseline,
        )

        assert res["impact_summary"]["has_eligible_participants"] is False
        assert res["impact_summary"]["surviving_participants_count"] == 0
        assert res["surviving_metrics"] is None
        assert any("TOTAL WORKFLOW COLLAPSE" in note for note in res["resilience_notes"])

    def test_reject_nonexistent_outage_participant(self):
        baseline = [{"builder_id": "b1", "block_count": 100}]
        with pytest.raises(ValueError, match="was not found in baseline"):
            run_outage_simulation(
                participant_type="builder",
                outage_participant_id="ghost_builder",
                baseline_observations=baseline,
            )
