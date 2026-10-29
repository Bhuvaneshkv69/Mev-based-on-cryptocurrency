"""Pure Mathematical and Statistical Metrics Engine for Decentralization Analysis.

This module provides pure, testable mathematical functions to calculate market shares,
concentration metrics (Herfindahl–Hirschman Index, top-k shares), diversity counts,
and interpretative risk classifications for Ethereum block construction participants.

No database calls, network I/O, or framework-dependent logic exist in this module.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple


# Analytical thresholds for HHI interpretation (illustrative application thresholds)
# Note: These are academic reference categories adapted from antitrust guidelines (e.g. US DOJ/FTC)
# and do NOT represent an official Ethereum protocol classification or consensus threshold.
HHI_THRESHOLD_LOW: float = 1500.0
HHI_THRESHOLD_MODERATE: float = 2500.0


def round_float(val: float, places: int = 2) -> float:
    """Helper to round float values deterministically to avoid floating-point artifacts."""
    d = Decimal(str(val))
    rounded = d.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
    return float(rounded)


def aggregate_observations(
    observations: List[Dict[str, Any]],
    id_field: str,
    count_field: str = "block_count",
    name_field: str = "display_name",
) -> List[Dict[str, Any]]:
    """Aggregates duplicate participant observations by summing block counts.

    If multiple observations share the same ID, their block counts are accumulated
    unambiguously, and the latest non-empty display name is preserved.

    Args:
        observations: Raw list of participant observation dictionaries.
        id_field: Key name for participant identifier ('builder_id' or 'relay_id').
        count_field: Key name for count ('block_count').
        name_field: Key name for display name ('display_name').

    Returns:
        Consolidated list of participant dictionaries with unique IDs.

    Raises:
        ValueError: If observations list is empty or any ID/count is invalid.
    """
    if not observations:
        raise ValueError("Observations list cannot be empty.")

    aggregated: Dict[str, Dict[str, Any]] = {}

    for obs in observations:
        raw_id = obs.get(id_field)
        if not raw_id or not str(raw_id).strip():
            raise ValueError(f"Participant identifier '{id_field}' cannot be empty or blank.")
        
        participant_id = str(raw_id).strip()
        count = obs.get(count_field, 0)

        if not isinstance(count, int) or count < 0:
            raise ValueError(f"Block count for '{participant_id}' must be a non-negative integer (got {count}).")

        display_name = obs.get(name_field)
        if display_name is not None:
            display_name = str(display_name).strip() or None

        if participant_id in aggregated:
            aggregated[participant_id]["block_count"] += count
            if display_name:
                aggregated[participant_id]["display_name"] = display_name
        else:
            aggregated[participant_id] = {
                id_field: participant_id,
                name_field: display_name,
                "block_count": count,
            }

    return list(aggregated.values())


def classify_hhi(hhi: float) -> Tuple[str, str]:
    """Classifies Herfindahl–Hirschman Index into analytical categories.

    Returns:
        Tuple of (category, descriptive_note)
    """
    if hhi < HHI_THRESHOLD_LOW:
        return (
            "low",
            "Low concentration: block construction activity is relatively distributed among multiple participants.",
        )
    elif hhi <= HHI_THRESHOLD_MODERATE:
        return (
            "moderate",
            "Moderate concentration: noticeable reliance on leading participants; potential operational bottleneck.",
        )
    else:
        return (
            "high",
            "High concentration: a small cluster of participants dominates observed block construction.",
        )


def calculate_participant_metrics(
    observations: List[Dict[str, Any]],
    id_field: str,
    participant_label: str = "builder",
    count_field: str = "block_count",
    name_field: str = "display_name",
) -> Dict[str, Any]:
    """Calculates comprehensive decentralization and concentration metrics.

    Args:
        observations: List of observation dictionaries.
        id_field: Key for participant id ('builder_id' or 'relay_id').
        participant_label: Human-readable label ('builder' or 'relay').
        count_field: Key for block count.
        name_field: Key for optional display name.

    Returns:
        Dictionary containing total observed blocks, sorted participant breakdown,
        largest share, top-3 share, HHI, HHI category, and diversity count.

    Raises:
        ValueError: If total observed blocks is zero or input is invalid.
    """
    aggregated = aggregate_observations(
        observations=observations,
        id_field=id_field,
        count_field=count_field,
        name_field=name_field,
    )

    total_observed_blocks = sum(item[count_field] for item in aggregated)
    if total_observed_blocks <= 0:
        raise ValueError(
            f"Total observed blocks across all {participant_label}s must be greater than zero."
        )

    # Sort deterministically: descending block count, ascending ID tie-breaker
    sorted_items = sorted(
        aggregated,
        key=lambda x: (-x[count_field], x[id_field]),
    )

    # Calculate individual percentage shares
    participants_detail: List[Dict[str, Any]] = []
    raw_shares: List[float] = []

    for item in sorted_items:
        count = item[count_field]
        share_pct = (count / total_observed_blocks) * 100.0
        raw_shares.append(share_pct)
        participants_detail.append({
            f"{participant_label}_id": item[id_field],
            "display_name": item.get(name_field),
            "block_count": count,
            "market_share_percentage": round_float(share_pct, 2),
        })

    # Summary metrics
    distinct_count = len(sorted_items)
    largest_share_pct = round_float(raw_shares[0], 2) if raw_shares else 0.0

    # Top-three share: sum available top 3 (or fewer if less than 3 participants)
    top_three_raw = sum(raw_shares[:3])
    top_three_share_pct = round_float(top_three_raw, 2)

    # Herfindahl-Hirschman Index (HHI)
    # HHI = sum of squared percentage market shares (0 to 10,000)
    hhi_raw = sum(s ** 2 for s in raw_shares)
    hhi = round_float(hhi_raw, 2)
    hhi_category, hhi_interpretation = classify_hhi(hhi)

    largest_participant_id = sorted_items[0][id_field] if sorted_items else None

    return {
        "participant_label": participant_label,
        "total_observed_blocks": total_observed_blocks,
        "distinct_participants_count": distinct_count,
        "largest_participant_id": largest_participant_id,
        "largest_share_percentage": largest_share_pct,
        "top_three_share_percentage": top_three_share_pct,
        "hhi": hhi,
        "hhi_category": hhi_category,
        "hhi_interpretation": hhi_interpretation,
        "participants": participants_detail,
    }


def generate_decentralization_warnings(
    builder_metrics: Optional[Dict[str, Any]] = None,
    relay_metrics: Optional[Dict[str, Any]] = None,
    source_type: str = "user_supplied",
    measurement_window: Optional[str] = None,
) -> List[str]:
    """Generates analytical and methodology warnings for the concentration report.

    Args:
        builder_metrics: Calculated builder metrics dictionary (if present).
        relay_metrics: Calculated relay metrics dictionary (if present).
        source_type: Dataset source type indicator.
        measurement_window: Description or timeframe of the dataset.

    Returns:
        List of warning and limitation strings.
    """
    warnings: List[str] = []

    # 1. Source type transparency
    if source_type == "illustrative_sample":
        warnings.append(
            "ILLUSTRATIVE SAMPLE: The dataset contains synthetic demonstration data. "
            "It does NOT reflect live or historical Ethereum mainnet builder or relay distributions."
        )

    # 2. Measurement window notice
    if not measurement_window or not measurement_window.strip():
        warnings.append(
            "UNSPECIFIED WINDOW: No measurement window or block range was specified. "
            "Temporal variance in builder/relay shares cannot be evaluated."
        )

    # 3. Builder-specific warnings
    if builder_metrics:
        total_blocks = builder_metrics.get("total_observed_blocks", 0)
        distinct = builder_metrics.get("distinct_participants_count", 0)
        largest_share = builder_metrics.get("largest_share_percentage", 0.0)
        top_three = builder_metrics.get("top_three_share_percentage", 0.0)
        hhi = builder_metrics.get("hhi", 0.0)

        if total_blocks < 100:
            warnings.append(
                f"SMALL SAMPLE (Builders): Only {total_blocks} blocks observed. Small sample sizes "
                "can exaggerate concentration statistics and HHI values."
            )
        if distinct < 3:
            warnings.append(
                f"LOW DIVERSITY: Only {distinct} distinct builders observed in dataset."
            )
        if largest_share >= 50.0:
            warnings.append(
                f"DOMINANT BUILDER RISK: The leading builder controls {largest_share}% of observed blocks "
                "(majority share). This creates severe single-point-of-failure and transaction inclusion risks."
            )
        elif largest_share >= 33.3:
            warnings.append(
                f"ELEVATED BUILDER CONCENTRATION: The leading builder controls {largest_share}% (> 1/3) "
                "of observed blocks."
            )
        if top_three >= 80.0 and distinct >= 3:
            warnings.append(
                f"OLIGOPOLY CONCENTRATION: Top 3 builders command {top_three}% of block construction."
            )
        if hhi > HHI_THRESHOLD_MODERATE:
            warnings.append(
                f"HIGH HHI CONCENTRATION: Builder HHI of {hhi} exceeds the high concentration threshold (2,500)."
            )

    # 4. Relay-specific warnings
    if relay_metrics:
        relay_blocks = relay_metrics.get("total_observed_blocks", 0)
        relay_distinct = relay_metrics.get("distinct_participants_count", 0)
        relay_largest = relay_metrics.get("largest_share_percentage", 0.0)
        relay_top_three = relay_metrics.get("top_three_share_percentage", 0.0)

        warnings.append(
            "RELAY ATTRIBUTION NOTE: Relay observations measure relay-associated payload deliveries. "
            "Relays act as trusted intermediaries and do not construct blocks themselves."
        )

        if relay_blocks < 100:
            warnings.append(
                f"SMALL SAMPLE (Relays): Only {relay_blocks} relay-associated blocks observed."
            )
        if relay_largest >= 50.0:
            warnings.append(
                f"CRITICAL RELAY DEPENDENCY: Leading relay handles {relay_largest}% of observed blocks. "
                "Outage or regulatory compliance filters at this relay could impact substantial block flow."
            )
        if relay_top_three >= 90.0 and relay_distinct >= 3:
            warnings.append(
                f"EXTREME RELAY CLUSTERING: Top 3 relays mediate {relay_top_three}% of delivered blocks."
            )

    # 5. Methodological and behavioral boundary disclaimer
    warnings.append(
        "METHODOLOGICAL DISCLAIMER: Concentration metrics measure structural distribution only. "
        "High concentration does NOT prove collusion, censorship, or malicious behavior."
    )

    return warnings
