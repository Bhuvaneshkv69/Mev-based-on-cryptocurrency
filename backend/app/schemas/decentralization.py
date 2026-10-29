"""Decentralization Analyzer Pydantic Schemas.

Defines Pydantic v2 models for:
- Builder and Relay observation inputs
- Decentralization concentration analysis requests and responses
- PBS multi-round block auction requests and responses
- Participant outage resilience requests and responses
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Basic Observation Schemas
# ---------------------------------------------------------------------------

class BuilderObservation(BaseModel):
    """Observation record for a block builder."""

    builder_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the block builder (e.g. 'builder_alpha', 'builder0x123')",
        examples=["builder_alpha"],
    )
    block_count: int = Field(
        ...,
        ge=0,
        description="Number of blocks constructed by this builder in the measurement window",
        examples=[450],
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Human-readable label or display alias for the builder",
        examples=["Alpha Block Construction"],
    )

    @field_validator("builder_id")
    @classmethod
    def validate_builder_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("builder_id cannot be blank or whitespace.")
        return clean


class RelayObservation(BaseModel):
    """Observation record for a PBS relay."""

    relay_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the relay (e.g. 'relay_one', 'relay_flashbots')",
        examples=["relay_one"],
    )
    block_count: int = Field(
        ...,
        ge=0,
        description="Number of blocks delivered/associated with this relay in the measurement window",
        examples=[600],
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Human-readable label or display alias for the relay",
        examples=["Prime Relay Network"],
    )

    @field_validator("relay_id")
    @classmethod
    def validate_relay_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("relay_id cannot be blank or whitespace.")
        return clean


# ---------------------------------------------------------------------------
# Analysis Request & Response Schemas
# ---------------------------------------------------------------------------

class DecentralizationAnalysisRequest(BaseModel):
    """Validated request body for builder and relay concentration analysis."""

    source_type: str = Field(
        default="user_supplied",
        description="Data provenance type: 'illustrative_sample', 'user_supplied', or 'historical_dataset'",
        examples=["illustrative_sample"],
    )
    measurement_window: Optional[str] = Field(
        default="Default Analysis Window",
        max_length=200,
        description="Description of the observation timeframe, epoch range, or block sample window",
        examples=["Synthetic Academic Demo Window (1,000 Sample Blocks)"],
    )
    builder_observations: Optional[List[BuilderObservation]] = Field(
        default=None,
        description="Observed block construction counts attributed to distinct builders",
    )
    relay_observations: Optional[List[RelayObservation]] = Field(
        default=None,
        description="Observed block delivery counts attributed to distinct relays (measured independently)",
    )
    save_experiment: bool = Field(
        default=True,
        description="Whether to persist the calculated analysis in the PostgreSQL database",
    )

    @model_validator(mode="after")
    def validate_observations_present(self) -> "DecentralizationAnalysisRequest":
        b_obs = self.builder_observations or []
        r_obs = self.relay_observations or []

        if not b_obs and not r_obs:
            raise ValueError(
                "At least one of 'builder_observations' or 'relay_observations' must be provided."
            )

        if len(b_obs) > 200:
            raise ValueError("builder_observations exceeds maximum allowed limit of 200 items.")
        if len(r_obs) > 200:
            raise ValueError("relay_observations exceeds maximum allowed limit of 200 items.")

        if b_obs:
            total_b = sum(b.block_count for b in b_obs)
            if total_b <= 0:
                raise ValueError("Total observed builder block count must be greater than zero.")

        if r_obs:
            total_r = sum(r.block_count for r in r_obs)
            if total_r <= 0:
                raise ValueError("Total observed relay block count must be greater than zero.")

        return self


class ParticipantShare(BaseModel):
    """Detailed breakdown for a single participant."""

    builder_id: Optional[str] = None
    relay_id: Optional[str] = None
    display_name: Optional[str] = None
    block_count: int
    market_share_percentage: float


class MarketMetricsResponse(BaseModel):
    """Summary and concentration metrics for builders or relays."""

    participant_label: str
    total_observed_blocks: int
    distinct_participants_count: int
    largest_participant_id: Optional[str] = None
    largest_share_percentage: float
    top_three_share_percentage: float
    hhi: float
    hhi_category: str
    hhi_interpretation: str
    participants: List[Dict[str, Any]]


class DecentralizationAnalysisResponse(BaseModel):
    """Top-level response payload for builder and relay concentration analysis."""

    model_config = ConfigDict(from_attributes=True)

    experiment_id: Optional[int] = Field(
        default=None,
        description="Database experiment ID if persisted, null otherwise",
    )
    simulation_type: str = "decentralization_analysis"
    source_type: str
    measurement_window: Optional[str] = None
    builder_metrics: Optional[MarketMetricsResponse] = None
    relay_metrics: Optional[MarketMetricsResponse] = None
    warnings: List[str]
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# PBS Simulation Schemas
# ---------------------------------------------------------------------------

class PBSSimulationRequest(BaseModel):
    """Payload to simulate a multi-round PBS block construction auction."""

    builder_ids: List[str] = Field(
        ...,
        min_length=2,
        max_length=50,
        description="List of participating builder identifiers (minimum 2 builders)",
        examples=[["builder_alpha", "builder_beta", "builder_gamma", "builder_delta"]],
    )
    num_rounds: int = Field(
        default=100,
        ge=1,
        le=10_000,
        description="Number of simulation rounds/slots to execute",
        examples=[100],
    )
    seed: Optional[int] = Field(
        default=42,
        description="Deterministic random seed for reproducible auction bids",
        examples=[42],
    )
    include_round_details: bool = Field(
        default=True,
        description="Whether to include per-round logs (only returned when num_rounds <= 100)",
    )
    save_experiment: bool = Field(
        default=True,
        description="Whether to persist the auction simulation in PostgreSQL",
    )

    @field_validator("builder_ids")
    @classmethod
    def validate_unique_builders(cls, v: List[str]) -> List[str]:
        cleaned = [b.strip() for b in v if b.strip()]
        unique_builders = sorted(list(set(cleaned)))
        if len(unique_builders) < 2:
            raise ValueError("PBS simulation requires at least 2 distinct, non-empty builder IDs.")
        return unique_builders


class BuilderWinStat(BaseModel):
    """PBS simulation win statistic for a builder."""

    builder_id: str
    win_count: int
    win_percentage: float
    mean_configured_bid_eth: float


class PBSSimulationResponse(BaseModel):
    """Response payload from a PBS auction simulation."""

    model_config = ConfigDict(from_attributes=True)

    experiment_id: Optional[int] = None
    simulation_type: str = "pbs_auction_simulation"
    total_rounds: int
    seed_used: Optional[int] = None
    distinct_builders_count: int
    average_winning_bid_eth: float
    selection_rule: str
    win_distribution: List[Dict[str, Any]]
    round_details: List[Dict[str, Any]]
    assumptions: List[str]
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Outage Resilience Schemas
# ---------------------------------------------------------------------------

class OutageSimulationRequest(BaseModel):
    """Payload to simulate a participant downtime or censorship outage."""

    participant_type: Literal["builder", "relay"] = Field(
        ...,
        description="Category of participant undergoing outage ('builder' or 'relay')",
        examples=["builder"],
    )
    outage_participant_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identifier of the specific builder or relay failing",
        examples=["builder_alpha"],
    )
    baseline_observations: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Baseline observations containing participant block counts",
    )
    save_experiment: bool = Field(
        default=True,
        description="Whether to persist the outage simulation in PostgreSQL",
    )

    @field_validator("outage_participant_id")
    @classmethod
    def validate_outage_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("outage_participant_id cannot be blank.")
        return clean


class OutageImpactSummary(BaseModel):
    """Resilience metrics comparing baseline to post-outage state."""

    baseline_blocks_lost: int
    baseline_share_lost_pct: float
    has_eligible_participants: bool
    surviving_participants_count: int


class OutageSimulationResponse(BaseModel):
    """Response payload for participant outage resilience simulation."""

    model_config = ConfigDict(from_attributes=True)

    experiment_id: Optional[int] = None
    simulation_type: str = "participant_outage_simulation"
    participant_type: str
    outage_participant_id: str
    impact_summary: OutageImpactSummary
    baseline_metrics: MarketMetricsResponse
    surviving_metrics: Optional[MarketMetricsResponse] = None
    resilience_notes: List[str]
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Enshrined PBS & Inclusion Lists (Overcoming Limitations) Schemas
# ---------------------------------------------------------------------------

class EPBSComparisonRequest(BaseModel):
    """Payload to simulate architectural comparison between Proto-PBS and ePBS."""

    num_simulated_slots: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Number of validator proposal slots to simulate",
    )
    relay_failure_probability: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Probability of off-chain relay downtime or timeout per slot",
    )
    builder_censorship_rate: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        description="Proportion of builders filtering OFAC/censored transactions",
    )
    save_experiment: bool = Field(
        default=False,
        description="Whether to persist the result in the database",
    )


class ArchitectureEvaluation(BaseModel):
    """Detailed architectural and security assessment of a block building paradigm."""

    architecture_name: str
    relay_dependency: bool
    dominant_relays_count: int
    relay_hhi: float
    missed_slots_count: int
    missed_slot_rate_pct: float
    censored_transactions_pct: float
    builder_hhi: float
    average_latency_ms: float
    trust_model: str
    key_limitation: str
    how_it_overcomes: str


class EPBSComparisonResponse(BaseModel):
    """Response payload for Enshrined PBS vs Proto-PBS architectural comparison."""

    simulation_type: str = "epbs_resilience_comparison"
    num_simulated_slots: int
    proto_pbs_mev_boost: ArchitectureEvaluation
    enshrined_pbs_eip7732: ArchitectureEvaluation
    epbs_with_inclusion_lists: ArchitectureEvaluation
    suave_decentralized_builder: ArchitectureEvaluation
    summary_findings: List[str]
    experiment_id: Optional[int] = None
    created_at: Optional[datetime] = None
