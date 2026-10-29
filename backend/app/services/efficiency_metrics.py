"""Unit-safe calculations used by the network efficiency simulator."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List

WEI_PER_ETH = Decimal("1000000000")  # Gwei per ETH


def decimal_value(value: Any) -> Decimal:
    return Decimal(str(value))


def calculate_gas_cost(gas_used: int, effective_gas_price_gwei: Decimal) -> Decimal:
    """Return ETH cost; gas * Gwei / 1e9 converts to ETH."""
    return (Decimal(gas_used) * effective_gas_price_gwei) / WEI_PER_ETH


def round_decimal(value: Decimal, places: int = 12) -> float:
    quantum = Decimal("1").scaleb(-places)
    return float(value.quantize(quantum, rounding=ROUND_HALF_UP))


def transaction_fee_profile(count: int, base_priority: Decimal, spread: Decimal) -> List[Dict[str, Any]]:
    """Generate a deterministic fee profile for educational simulation only."""
    return [
        {
            "transaction_id": f"tx_{index + 1:04d}",
            "priority_fee_gwei": base_priority + (Decimal(index % 5) * spread),
            "submission_index": index,
        }
        for index in range(count)
    ]
