"""Schemas for deterministic gas-cost and transaction-queue simulations."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EfficiencySimulationRequest(BaseModel):
    transaction_count: int = Field(default=40, ge=0, le=10000)
    block_capacity: int = Field(default=10, ge=1, le=1000)
    average_gas_used: int = Field(default=150000, ge=21000, le=30000000)
    base_fee_gwei: float = Field(default=20.0, ge=0, le=1_000_000)
    priority_fee_gwei: float = Field(default=2.0, ge=0, le=1_000_000)
    priority_fee_spread_gwei: float = Field(default=1.0, ge=0, le=1_000_000)
    block_time_seconds: float = Field(default=12.0, gt=0, le=3600)
    max_blocks: int = Field(default=20, ge=1, le=1000)
    scenario: Literal["normal_load", "congested_network", "priority_fee_competition", "submission_comparison"] = "submission_comparison"
    submission_method: Literal["priority_fee_competition", "private_bundle_simulation"] = "priority_fee_competition"
    save_experiment: bool = False

    @field_validator("base_fee_gwei", "priority_fee_gwei", "priority_fee_spread_gwei", "block_time_seconds")
    @classmethod
    def finite_numbers(cls, value: float) -> float:
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("Numeric inputs must be finite.")
        return value


class EfficiencySimulationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    experiment_id: Optional[int] = None
    simulation_type: str = "network_efficiency_simulation"
    selected_submission_method: str
    scenario: str
    input_assumptions: Dict[str, Any]
    selected_result: Dict[str, Any]
    priority_fee_competition: Dict[str, Any]
    private_bundle_simulation: Dict[str, Any]
    comparison: Dict[str, Any]
    warnings: List[str]


# ---------------------------------------------------------------------------
# Problem Statement 3: MEV Smoothing, Reorg Prevention & Taxonomy Schemas
# ---------------------------------------------------------------------------

class ReorgRiskSimulationRequest(BaseModel):
    """Payload to simulate consensus reorg risk under MEV spikes and smoothing."""

    mev_spike_eth: float = Field(
        default=50.0,
        gt=0.0,
        le=5000.0,
        description="Magnitude of an unexpected MEV opportunity spike in a single block (ETH)",
    )
    validator_stake_pct: float = Field(
        default=15.0,
        ge=1.0,
        le=49.0,
        description="Percentage of network stake controlled by the potential reorganizing validator",
    )
    block_subsidy_eth: float = Field(
        default=0.06,
        gt=0.0,
        le=10.0,
        description="Standard consensus block subsidy (ETH)",
    )
    save_experiment: bool = Field(
        default=False,
        description="Whether to persist the result in the database",
    )


class ReorgRegimeEvaluation(BaseModel):
    """Evaluation of consensus security under a specific MEV distribution regime."""

    regime_name: str
    proposer_payoff_eth: float
    reorg_incentive_ratio: float
    reorg_threat_score_pct: float
    consensus_risk_level: str
    validator_yield_variance: str
    mitigation_mechanism: str
    how_it_overcomes_limitation: str


class ReorgRiskSimulationResponse(BaseModel):
    """Response payload for consensus reorg and MEV smoothing simulation."""

    simulation_type: str = "consensus_reorg_and_smoothing_simulation"
    mev_spike_eth: float
    validator_stake_pct: float
    unsmoothed_status_quo: ReorgRegimeEvaluation
    mev_smoothing_pool: ReorgRegimeEvaluation
    mev_burn_eip7545: ReorgRegimeEvaluation
    summary_findings: List[str]
    experiment_id: Optional[int] = None


class MEVCategoryDetail(BaseModel):
    category_name: str
    mev_type: str
    economic_role: str
    user_impact: str
    network_impact: str
    overall_assessment: str
    recommendation: str


class MEVTaxonomyResponse(BaseModel):
    """Response classifying MEV types into beneficial vs toxic."""

    taxonomy: List[MEVCategoryDetail]
    summary_insight: str
