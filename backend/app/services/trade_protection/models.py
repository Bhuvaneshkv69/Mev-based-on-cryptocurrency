"""Trade Protection Simulation — Domain Models.

Pure Python dataclasses representing all domain objects used throughout
the simulation pipeline. No SQLAlchemy, no Pydantic — these are plain
in-memory value objects passed between the service layers.

Terminology:
  - Pool: an AMM liquidity pool (e.g. Uniswap v2 ETH/USDC pair)
  - Trade: the honest user's swap order
  - Attacker: a searcher bot that detects the trade in the mempool and
    inserts transactions before (front-run) and after (back-run) it
  - MEV: Maximal Extractable Value captured by the attacker
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ProtectionType(str, Enum):
    """Supported trade protection mechanisms."""

    NONE = "none"
    PRIVATE_MEMPOOL = "private_mempool"
    SLIPPAGE_GUARD = "slippage_guard"
    COMMIT_REVEAL = "commit_reveal"
    TIME_LOCK = "time_lock"
    ENCRYPTED_MEMPOOL = "encrypted_mempool"
    BATCH_AUCTION = "batch_auction"
    MEV_SHARE = "mev_share"


class RiskLevel(str, Enum):
    """Categorical MEV risk classification."""

    LOW = "low"        # < 30 % probability
    MEDIUM = "medium"  # 30 – 69 %
    HIGH = "high"      # ≥ 70 %


class AttackType(str, Enum):
    """Type of MEV attack applicable to this trade."""

    NONE = "none"              # Trade too small to be worth attacking
    FRONT_RUN = "front_run"   # Simple front-run only (medium-sized trade)
    SANDWICH = "sandwich"      # Full sandwich: front-run + back-run


# ---------------------------------------------------------------------------
# Input Domain Object
# ---------------------------------------------------------------------------

@dataclass
class TradeParameters:
    """Validated simulation inputs supplied by the API caller.

    All monetary amounts are denominated in ETH for simplicity.
    The "token_pair" field is informational only and does not affect math.
    """

    trade_amount_eth: float          # Size of the user's swap (ETH in)
    pool_liquidity_eth: float        # Total ETH liquidity depth in the AMM pool
    slippage_tolerance_pct: float    # Maximum price slippage the user accepts (%)
    protection_type: ProtectionType  # Chosen protection mechanism
    attacker_capital_eth: float      # Capital the MEV bot deploys
    token_pair: str                  # Human-readable label e.g. "ETH/USDC"
    scenario_label: str              # Free-text label for the experiment record
    save_experiment: bool            # Whether to persist results to the DB


# ---------------------------------------------------------------------------
# Intermediate Computation Objects
# ---------------------------------------------------------------------------

@dataclass
class MEVRisk:
    """Output of the MEV risk detector.

    risk_level:     categorical LOW / MEDIUM / HIGH
    attack_type:    none / front_run / sandwich
    mev_probability: float in [0, 1] – probability a bot will attack this trade
    """

    risk_level: RiskLevel
    attack_type: AttackType
    mev_probability: float


@dataclass
class UnprotectedScenario:
    """Metrics for the trade executed WITHOUT any protection.

    All price fields are in ETH (price of 1 unit of the bought token,
    expressed as the ETH cost). Loss fields are in ETH.
    """

    expected_price_eth: float        # Baseline price before any trade lands
    user_execution_price_eth: float  # Actual price user gets after front-run
    price_impact_pct: float          # Price movement caused by front-run (%)
    mev_extracted_eth: float         # ETH profit captured by the attacker
    attacker_profit_eth: float       # Alias for mev_extracted_eth (clearer label)
    user_loss_eth: float             # ETH the user loses relative to expected
    user_loss_pct: float             # User loss as a % of trade amount


@dataclass
class ProtectedScenario:
    """Metrics for the same trade executed WITH the chosen protection.

    protection_effectiveness_pct: how much of the unprotected MEV was removed
    user_savings_eth: absolute ETH saved vs. the unprotected scenario
    """

    user_execution_price_eth: float
    price_impact_pct: float
    mev_extracted_eth: float
    user_loss_eth: float
    user_loss_pct: float
    protection_effectiveness_pct: float
    user_savings_eth: float
    user_rebate_eth: float = 0.0


# ---------------------------------------------------------------------------
# Final Output Object
# ---------------------------------------------------------------------------

@dataclass
class SimulationResult:
    """Complete output of one simulation run.

    Combines MEV risk assessment, unprotected scenario metrics, protected
    scenario metrics, a human-readable notes list, and the database ID of
    the persisted experiment (None if save_experiment was False).
    """

    scenario_label: str
    token_pair: str
    protection_type: ProtectionType
    mev_risk: MEVRisk
    unprotected: UnprotectedScenario
    protected: ProtectedScenario
    simulation_notes: List[str] = field(default_factory=list)
    experiment_id: int | None = None
