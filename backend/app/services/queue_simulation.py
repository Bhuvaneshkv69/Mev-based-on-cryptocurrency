"""Deterministic capacity-based transaction queue simulation."""
from decimal import Decimal
from typing import Any, Dict, List

from app.services.efficiency_metrics import calculate_gas_cost, round_decimal


def simulate_queue(
    transactions: List[Dict[str, Any]],
    block_capacity: int,
    max_blocks: int,
    block_time_seconds: float,
    base_fee_gwei: Decimal,
    average_gas_used: int,
    submission_method: str,
) -> Dict[str, Any]:
    """Process transactions by fee priority or original order up to a block limit."""
    if submission_method == "priority_fee_competition":
        ordered = sorted(transactions, key=lambda tx: (-tx["priority_fee_gwei"], tx["transaction_id"]))
        ordering_rule = "Highest priority fee first; transaction ID ascending breaks ties."
    else:
        ordered = sorted(transactions, key=lambda tx: tx["submission_index"])
        ordering_rule = "Original submission order is preserved in the modeled private bundle."

    included: List[Dict[str, Any]] = []
    deferred: List[Dict[str, Any]] = []
    block_assignments: Dict[str, int] = {}
    max_inclusions = block_capacity * max_blocks
    selected = ordered[:max_inclusions]
    deferred = ordered[max_inclusions:]

    for index, tx in enumerate(selected):
        block_number = (index // block_capacity) + 1
        block_assignments[tx["transaction_id"]] = block_number
        effective_price = base_fee_gwei + tx["priority_fee_gwei"]
        cost = calculate_gas_cost(average_gas_used, effective_price)
        included.append({
            "transaction_id": tx["transaction_id"],
            "submission_index": tx["submission_index"],
            "priority_fee_gwei": round_decimal(tx["priority_fee_gwei"], 6),
            "effective_gas_price_gwei": round_decimal(effective_price, 6),
            "gas_used": average_gas_used,
            "estimated_cost_eth": round_decimal(cost),
            "included_in_block": block_number,
            "estimated_delay_seconds": round_decimal(Decimal(block_number - 1) * Decimal(str(block_time_seconds)), 3),
        })

    deferred_rows = [
        {
            "transaction_id": tx["transaction_id"],
            "submission_index": tx["submission_index"],
            "priority_fee_gwei": round_decimal(tx["priority_fee_gwei"], 6),
            "reason": "Deferred because the configured block-processing limit was reached.",
        }
        for tx in deferred
    ]

    total_cost = sum((Decimal(str(row["estimated_cost_eth"])) for row in included), Decimal("0"))
    total_gas = len(included) * average_gas_used
    blocks_used = ((len(included) + block_capacity - 1) // block_capacity) if included else 0
    simulated_seconds = max(0, blocks_used - 1) * block_time_seconds
    processing_window_seconds = blocks_used * block_time_seconds
    total_count = len(transactions)
    return {
        "submission_method": submission_method,
        "ordering_rule": ordering_rule,
        "submitted_transactions": total_count,
        "included_transactions": len(included),
        "deferred_transactions": len(deferred_rows),
        "remaining_queue": len(deferred_rows),
        "inclusion_rate_pct": round((len(included) / total_count * 100) if total_count else 100.0, 2),
        "blocks_used": blocks_used,
        "max_blocks": max_blocks,
        "simulation_complete": len(deferred_rows) == 0,
        "estimated_queue_delay_seconds": round(simulated_seconds, 3),
        "throughput_transactions_per_block": round(len(included) / blocks_used, 3) if blocks_used else 0.0,
        "throughput_transactions_per_second": round(len(included) / processing_window_seconds, 6) if processing_window_seconds > 0 else 0.0,
        "total_gas_used": total_gas,
        "estimated_total_cost_eth": round_decimal(total_cost),
        "average_included_cost_eth": round_decimal(total_cost / len(included)) if included else 0.0,
        "included": included,
        "deferred": deferred_rows,
    }
