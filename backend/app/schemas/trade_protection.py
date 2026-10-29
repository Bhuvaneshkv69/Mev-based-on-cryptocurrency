"""Trade Protection API Schemas.

Defines Pydantic v2 models for the Trade Protection simulation endpoint:
  - TradeProtectionRequest  : validated API input
  - MEVRiskResponse         : risk assessment block in the response
  - UnprotectedScenarioResponse : unprotected trade metrics
  - ProtectedScenarioResponse   : protected trade metrics
  - TradeProtectionResponse : complete simulation response
  - DemoScenario            : pre-built demo scenario entry
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schema
# ---------------------------------------------------------------------------

class TradeProtectionRequest(BaseModel):
    """Validated payload for running a trade protection simulation."""

    trade_amount_eth: float = Field(
        ...,
        gt=0,
        le=10_000,
        description="Size of the user's swap in ETH (must be > 0)",
        examples=[5.0],
    )
    token_pair: str = Field(
        default="ETH/USDC",
        min_length=1,
        max_length=20,
        description="Token pair label (informational only, e.g. 'ETH/USDC')",
        examples=["ETH/USDC"],
    )
    pool_liquidity_eth: float = Field(
        ...,
        gt=0,
        le=1_000_000,
        description="Total ETH-denominated liquidity depth in the AMM pool",
        examples=[1000.0],
    )
    slippage_tolerance_pct: float = Field(
        default=0.5,
        ge=0.0,
        le=50.0,
        description="Maximum acceptable price slippage as a percentage (0–50%)",
        examples=[0.5],
    )
    protection_type: str = Field(
        default="none",
        description=(
            "Protection mechanism to apply: "
            "'none', 'private_mempool', 'slippage_guard', 'commit_reveal', 'time_lock'"
        ),
        examples=["private_mempool"],
    )
    attacker_capital_eth: float = Field(
        default=50.0,
        gt=0,
        le=100_000,
        description="Capital the simulated MEV bot deploys for the attack (ETH)",
        examples=[50.0],
    )
    scenario_label: str = Field(
        default="Trade protection simulation",
        min_length=1,
        max_length=100,
        description="Human-readable label for this simulation run",
        examples=["Large ETH buy with private mempool"],
    )
    save_experiment: bool = Field(
        default=True,
        description="If true, saves the simulation result as a completed experiment in the database",
    )

    @field_validator("protection_type")
    @classmethod
    def validate_protection_type(cls, value: str) -> str:
        """Ensure protection_type is one of the five supported values."""
        allowed = {
            "none",
            "private_mempool",
            "slippage_guard",
            "commit_reveal",
            "time_lock",
            "encrypted_mempool",
            "batch_auction",
            "mev_share",
        }
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError(
                f"Invalid protection_type '{value}'. "
                f"Supported types: {', '.join(sorted(allowed))}"
            )
        return normalized

    @field_validator("token_pair")
    @classmethod
    def validate_token_pair(cls, value: str) -> str:
        return value.strip()

    @field_validator("scenario_label")
    @classmethod
    def validate_scenario_label(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("scenario_label cannot be empty or whitespace")
        return stripped

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trade_amount_eth": 5.0,
                "token_pair": "ETH/USDC",
                "pool_liquidity_eth": 1000.0,
                "slippage_tolerance_pct": 0.5,
                "protection_type": "private_mempool",
                "attacker_capital_eth": 50.0,
                "scenario_label": "Large ETH buy with private mempool",
                "save_experiment": True,
            }
        }
    )


# ---------------------------------------------------------------------------
# Response Sub-schemas
# ---------------------------------------------------------------------------

class MEVRiskResponse(BaseModel):
    """Risk assessment output from the MEV detector."""

    risk_level: str = Field(..., description="Categorical risk: 'low', 'medium', or 'high'")
    attack_type: str = Field(..., description="Attack type: 'none', 'front_run', or 'sandwich'")
    mev_probability: float = Field(..., description="Probability (0–1) a bot will attack this trade")


class UnprotectedScenarioResponse(BaseModel):
    """Metrics for the trade executed WITHOUT any protection."""

    expected_price_eth: float = Field(..., description="Baseline AMM price before any trade (ETH per token)")
    user_execution_price_eth: float = Field(..., description="Actual price user receives after front-run (ETH per token)")
    price_impact_pct: float = Field(..., description="Price impact caused by the front-run (%)")
    mev_extracted_eth: float = Field(..., description="Total ETH extracted by the MEV attacker")
    attacker_profit_eth: float = Field(..., description="Net ETH profit the attacker makes")
    user_loss_eth: float = Field(..., description="ETH the user loses relative to the expected price")
    user_loss_pct: float = Field(..., description="User loss as a percentage of the trade amount")


class ProtectedScenarioResponse(BaseModel):
    """Metrics for the same trade executed WITH the chosen protection."""

    user_execution_price_eth: float = Field(..., description="Execution price with protection applied")
    price_impact_pct: float = Field(..., description="Residual price impact after protection (%)")
    mev_extracted_eth: float = Field(..., description="Residual MEV remaining after protection")
    user_loss_eth: float = Field(..., description="Residual user loss in ETH after protection")
    user_loss_pct: float = Field(..., description="Residual user loss as % of trade amount")
    protection_effectiveness_pct: float = Field(..., description="How much MEV was eliminated by the protection (0–100%)")
    user_savings_eth: float = Field(..., description="ETH saved vs. the unprotected scenario")
    user_rebate_eth: float = Field(default=0.0, description="MEV refund rebated directly to the user (e.g. via MEV-Share)")


class TradeProtectionResponse(BaseModel):
    """Complete simulation response returned by POST /api/trade-protection/simulate."""

    experiment_id: Optional[int] = Field(
        None, description="Database ID of the persisted experiment, or null if save_experiment was false"
    )
    scenario_label: str = Field(..., description="Label for this simulation run")
    token_pair: str = Field(..., description="Token pair being traded")
    protection_type: str = Field(..., description="Applied protection mechanism")
    mev_risk: MEVRiskResponse = Field(..., description="MEV risk assessment")
    unprotected: UnprotectedScenarioResponse = Field(..., description="Unprotected trade metrics (baseline)")
    protected: ProtectedScenarioResponse = Field(..., description="Protected trade metrics")
    simulation_notes: List[str] = Field(default_factory=list, description="Human-readable explanation of results")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_id": 7,
                "scenario_label": "Large ETH buy with private mempool",
                "token_pair": "ETH/USDC",
                "protection_type": "private_mempool",
                "mev_risk": {
                    "risk_level": "high",
                    "attack_type": "sandwich",
                    "mev_probability": 0.87,
                },
                "unprotected": {
                    "expected_price_eth": 1.0,
                    "user_execution_price_eth": 1.0232,
                    "price_impact_pct": 2.32,
                    "mev_extracted_eth": 0.1418,
                    "attacker_profit_eth": 0.1418,
                    "user_loss_eth": 0.1139,
                    "user_loss_pct": 2.278,
                },
                "protected": {
                    "user_execution_price_eth": 1.0012,
                    "price_impact_pct": 0.116,
                    "mev_extracted_eth": 0.0071,
                    "user_loss_eth": 0.0057,
                    "user_loss_pct": 0.1139,
                    "protection_effectiveness_pct": 95.0,
                    "user_savings_eth": 0.1082,
                },
                "simulation_notes": [
                    "Order sent via a private RPC relay (e.g. Flashbots Protect / MEV Blocker).",
                    "Without protection: user loses ~0.1139 ETH (2.28% of trade amount) to MEV.",
                    "With private_mempool: saves ~0.1082 ETH (95.0% protection effectiveness).",
                ],
            }
        }
    )


# ---------------------------------------------------------------------------
# Demo Scenario Schema
# ---------------------------------------------------------------------------

class DemoScenario(BaseModel):
    """A pre-built demonstration scenario with a description."""

    name: str = Field(..., description="Short name of the demo scenario")
    description: str = Field(..., description="Explanation of what this scenario demonstrates")
    request: Dict[str, Any] = Field(..., description="Ready-to-use request body for /simulate")


class DemoScenariosResponse(BaseModel):
    """Response containing all built-in demo scenarios."""

    scenarios: List[DemoScenario]
    total: int
