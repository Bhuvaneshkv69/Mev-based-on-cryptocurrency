"""Proposer-Builder Separation (PBS) and Outage Resilience Simulation Engine.

This module models two crucial architectural dynamics in Ethereum block production:
1. Multi-round PBS block construction auctions where builders submit candidate bids
   and the proposer selects the highest eligible bid using deterministic tie-breaking.
2. Resilience analysis under participant outages (builder or relay downtime/exclusion),
   evaluating how market shares re-normalize among surviving participants without division by zero.
"""

import math
import random
from typing import Any, Dict, List, Optional

from app.services.decentralization_metrics import (
    aggregate_observations,
    calculate_participant_metrics,
    round_float,
)


def run_pbs_auction_simulation(
    builder_ids: List[str],
    num_rounds: int = 100,
    seed: Optional[int] = 42,
    builder_bid_params: Optional[Dict[str, Dict[str, float]]] = None,
    include_round_details: bool = True,
) -> Dict[str, Any]:
    """Simulates a multi-round PBS block auction.

    In each round:
    1. Each eligible builder computes a candidate bid for block construction.
    2. The proposer evaluates all bids and selects the highest bid.
    3. Ties are resolved deterministically using lexicographical builder ID sorting.
    4. Win counts and win percentages are aggregated across all rounds.

    Args:
        builder_ids: List of builder identifiers participating in the auction.
        num_rounds: Number of simulation rounds (1 to 10,000).
        seed: Random seed for deterministic reproducibility.
        builder_bid_params: Optional custom mean/std_dev parameters per builder.
        include_round_details: Whether to return individual round data (capped at 100 rounds).

    Returns:
        Structured simulation results including win distribution, winning bids,
        and simulation assumptions.

    Raises:
        ValueError: If builder_ids is empty or num_rounds is invalid.
    """
    if not builder_ids:
        raise ValueError("At least one builder ID is required to simulate PBS block auctions.")

    cleaned_builders = sorted(list({str(b).strip() for b in builder_ids if str(b).strip()}))
    if len(cleaned_builders) < 2:
        raise ValueError("PBS simulation requires at least 2 distinct builder participants.")

    if not isinstance(num_rounds, int) or num_rounds < 1 or num_rounds > 10000:
        raise ValueError("Simulation rounds must be an integer between 1 and 10,000.")

    # Initialize deterministic random generator
    rng = random.Random(seed)

    # Setup baseline bid distributions if not provided
    # Synthetic model: each builder has a base valuation capability (e.g. 0.05 to 0.20 ETH)
    # with Gaussian variation representing dynamic MEV bundle value in each slot.
    bid_configs: Dict[str, Dict[str, float]] = {}
    for idx, b_id in enumerate(cleaned_builders):
        if builder_bid_params and b_id in builder_bid_params:
            mean = float(builder_bid_params[b_id].get("mean_bid_eth", 0.10))
            std_dev = float(builder_bid_params[b_id].get("std_dev_eth", 0.02))
        else:
            # Deterministic distinct gradient across builders so demo illustrates competitive differentiation
            mean = 0.08 + (idx * 0.03)  # e.g. 0.08, 0.11, 0.14...
            std_dev = 0.015
        bid_configs[b_id] = {"mean": max(0.001, mean), "std_dev": max(0.0, std_dev)}

    win_counts: Dict[str, int] = {b_id: 0 for b_id in cleaned_builders}
    total_winning_bid_eth: float = 0.0
    rounds_history: List[Dict[str, Any]] = []

    for round_num in range(1, num_rounds + 1):
        round_bids: Dict[str, float] = {}
        for b_id in cleaned_builders:
            cfg = bid_configs[b_id]
            if cfg["std_dev"] <= 1e-9:
                bid = max(0.001, cfg["mean"])
            else:
                bid = max(0.001, rng.gauss(cfg["mean"], cfg["std_dev"]))
            round_bids[b_id] = round_float(bid, 4)

        # Proposer Selection Rule:
        # Highest bid wins. Deterministic tie-breaker: lexicographical builder_id ascending.
        max_bid_val = max(round_bids.values())
        tied_candidates = sorted([b for b, val in round_bids.items() if math.isclose(val, max_bid_val, abs_tol=1e-6)])
        winning_builder = tied_candidates[0]
        winning_bid = round_bids[winning_builder]

        win_counts[winning_builder] += 1
        total_winning_bid_eth += winning_bid

        # Cap detailed per-round logs to prevent excessive payload sizes
        if include_round_details and num_rounds <= 100:
            rounds_history.append({
                "round": round_num,
                "winner_builder_id": winning_builder,
                "winning_bid_eth": winning_bid,
                "all_bids": round_bids,
            })

    # Summary win distribution
    win_distribution: List[Dict[str, Any]] = []
    for b_id in cleaned_builders:
        wins = win_counts[b_id]
        win_pct = round_float((wins / num_rounds) * 100.0, 2)
        win_distribution.append({
            "builder_id": b_id,
            "win_count": wins,
            "win_percentage": win_pct,
            "mean_configured_bid_eth": round_float(bid_configs[b_id]["mean"], 4),
        })

    # Sort distribution by win count descending, then builder_id
    win_distribution.sort(key=lambda x: (-x["win_count"], x["builder_id"]))

    avg_winning_bid = round_float(total_winning_bid_eth / num_rounds, 4)

    assumptions = [
        "SIMPLIFIED AUCTION MODEL: Proposers select blocks strictly based on the highest candidate bid value.",
        "DETERMINISTIC TIE-BREAKING: Ties with equal bids are broken lexicographically by builder identifier.",
        "SYNTHETIC BID GENERATION: Bids are generated via calibrated Gaussian distributions with a fixed random seed.",
        "ACADEMIC SCOPE: This simulation does not emulate Ethereum consensus latency, p2p gossip timing, "
        "relay signature verification, or proposer payload commitments.",
    ]

    return {
        "simulation_type": "pbs_auction_simulation",
        "total_rounds": num_rounds,
        "seed_used": seed,
        "distinct_builders_count": len(cleaned_builders),
        "average_winning_bid_eth": avg_winning_bid,
        "selection_rule": "First-price sealed auction (Highest eligible candidate bid; lexicographical tie-break)",
        "win_distribution": win_distribution,
        "round_details": rounds_history if (include_round_details and num_rounds <= 100) else [],
        "assumptions": assumptions,
    }


def run_outage_simulation(
    participant_type: str,
    outage_participant_id: str,
    baseline_observations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Simulates the resilience impact of an individual builder or relay outage.

    Evaluates:
    1. Baseline market shares of all participants.
    2. Exclusion of the target participant (modeling operational failure, network partition, or filtering).
    3. Re-normalization of shares among surviving participants.
    4. Handles complete outage (0 remaining participants) gracefully without division by zero.

    Args:
        participant_type: 'builder' or 'relay'.
        outage_participant_id: The identifier of the participant undergoing the outage.
        baseline_observations: Validated baseline observation records.

    Returns:
        Comparative dictionary containing baseline metrics, outage impact,
        re-normalized surviving metrics, and architectural resilience caveats.

    Raises:
        ValueError: If participant_type is invalid, ID is blank, or baseline is invalid.
    """
    clean_type = str(participant_type).strip().lower()
    if clean_type not in ("builder", "relay"):
        raise ValueError("participant_type must be either 'builder' or 'relay'.")

    target_id = str(outage_participant_id).strip()
    if not target_id:
        raise ValueError("outage_participant_id cannot be blank.")

    id_field = "builder_id" if clean_type == "builder" else "relay_id"

    # 1. Calculate baseline metrics
    baseline_metrics = calculate_participant_metrics(
        observations=baseline_observations,
        id_field=id_field,
        participant_label=clean_type,
    )

    total_baseline_blocks = baseline_metrics["total_observed_blocks"]

    # Locate target participant in baseline
    target_in_baseline = None
    for p in baseline_metrics["participants"]:
        if p[f"{clean_type}_id"] == target_id:
            target_in_baseline = p
            break

    if target_in_baseline is None:
        raise ValueError(
            f"Participant '{target_id}' was not found in baseline {clean_type} observations."
        )

    blocks_lost = target_in_baseline["block_count"]
    share_lost_pct = target_in_baseline["market_share_percentage"]

    # 2. Filter out the failing participant
    surviving_observations = [
        obs for obs in baseline_observations
        if str(obs.get(id_field, "")).strip() != target_id
    ]

    has_surviving = len(surviving_observations) > 0 and sum(obs.get("block_count", 0) for obs in surviving_observations) > 0

    surviving_metrics: Optional[Dict[str, Any]] = None
    if has_surviving:
        surviving_metrics = calculate_participant_metrics(
            observations=surviving_observations,
            id_field=id_field,
            participant_label=clean_type,
        )

    # 3. Resilience notes
    resilience_notes: List[str] = [
        f"OUTAGE SIMULATION: Modeling sudden unavailability or exclusion of {clean_type} '{target_id}'.",
        f"BASELINE EXPOSURE: The target participant accounted for {blocks_lost} of {total_baseline_blocks} "
        f"baseline blocks ({share_lost_pct}%).",
    ]

    if not has_surviving:
        resilience_notes.append(
            f"TOTAL WORKFLOW COLLAPSE: No eligible {clean_type}s remain after this outage. "
            "Block construction or delivery through this simulated pathway halts completely."
        )
    else:
        new_top = surviving_metrics["largest_participant_id"]  # type: ignore
        new_top_share = surviving_metrics["largest_share_percentage"]  # type: ignore
        new_hhi = surviving_metrics["hhi"]  # type: ignore
        resilience_notes.append(
            f"RE-NORMALIZATION: Market share redistributes among remaining {surviving_metrics['distinct_participants_count']} "  # type: ignore
            f"{clean_type}(s). New leading participant is '{new_top}' with {new_top_share}%, resulting in HHI of {new_hhi}."
        )

    if clean_type == "relay":
        resilience_notes.append(
            "RELAY FALLBACK CAVEAT: In live Ethereum PBS, relay unavailability does not inevitably stop block "
            "production if proposers fall back to local block building or alternative multi-relay configurations."
        )
    else:
        resilience_notes.append(
            "BUILDER RESILIENCE CAVEAT: Builder outages shift searcher orderflow and MEV extraction "
            "to remaining active builders, potentially increasing concentration in remaining top builders."
        )

    return {
        "simulation_type": "participant_outage_simulation",
        "participant_type": clean_type,
        "outage_participant_id": target_id,
        "impact_summary": {
            "baseline_blocks_lost": blocks_lost,
            "baseline_share_lost_pct": share_lost_pct,
            "has_eligible_participants": has_surviving,
            "surviving_participants_count": len(surviving_metrics["participants"]) if surviving_metrics else 0,
        },
        "baseline_metrics": baseline_metrics,
        "surviving_metrics": surviving_metrics,
        "resilience_notes": resilience_notes,
    }
