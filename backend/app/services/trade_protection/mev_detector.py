"""MEV Risk Detector.

Analyses trade parameters to assess the likelihood and type of MEV attack
that a searcher bot would execute if this order were broadcast to the public
Ethereum mempool.

Algorithm
---------
We model the bot's decision as a function of two ratios:

  1. trade_ratio  = trade_amount / pool_liquidity
     → Larger trades move the price more, offering a bigger price-impact
       arbitrage opportunity for the attacker.

  2. capital_ratio = attacker_capital / pool_liquidity
     → Determines the attacker's ability to execute both the front-run buy
       and back-run sell within the same block.

The raw MEV probability is:

  P_mev = min(1.0, base_prob × trade_weight × capital_weight)

where:
  base_prob      = 0.4  (40 % baseline – bots watch every public mempool tx)
  trade_weight   = 1 + 4 × trade_ratio   (amplified by relative trade size)
  capital_weight = 1 + 2 × capital_ratio (amplified by attacker capital depth)

Attack type classification:
  trade_ratio < 0.005  → NONE      (micro trade, not profitable after gas)
  trade_ratio < 0.03   → FRONT_RUN (worth a simple front-run only)
  else                 → SANDWICH  (full sandwich profitable)
"""

from app.services.trade_protection.models import (
    AttackType,
    MEVRisk,
    RiskLevel,
    TradeParameters,
)


# Probability thresholds for categorical classification
_LOW_THRESHOLD = 0.30
_HIGH_THRESHOLD = 0.70

# Minimum trade size (as fraction of pool) to make an attack gas-profitable
_MIN_ATTACK_THRESHOLD = 0.005
_SANDWICH_THRESHOLD = 0.03


class MEVDetector:
    """Stateless classifier that evaluates MEV risk for a given trade."""

    @staticmethod
    def assess(params: TradeParameters) -> MEVRisk:
        """Compute MEV risk level, attack type, and probability.

        Args:
            params: Validated trade simulation inputs.

        Returns:
            MEVRisk dataclass with risk_level, attack_type, mev_probability.
        """
        trade_ratio = params.trade_amount_eth / params.pool_liquidity_eth
        capital_ratio = params.attacker_capital_eth / params.pool_liquidity_eth

        # --- Attack type ---
        if trade_ratio < _MIN_ATTACK_THRESHOLD:
            attack_type = AttackType.NONE
        elif trade_ratio < _SANDWICH_THRESHOLD:
            attack_type = AttackType.FRONT_RUN
        else:
            attack_type = AttackType.SANDWICH

        # --- Raw probability ---
        base_prob = 0.40
        trade_weight = 1.0 + (4.0 * trade_ratio)
        capital_weight = 1.0 + (2.0 * min(capital_ratio, 1.0))
        raw_prob = base_prob * trade_weight * capital_weight
        mev_probability = round(min(1.0, raw_prob), 4)

        # --- Categorical risk level ---
        if mev_probability < _LOW_THRESHOLD:
            risk_level = RiskLevel.LOW
        elif mev_probability < _HIGH_THRESHOLD:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        # If no attack is warranted, probability is effectively near-zero
        if attack_type == AttackType.NONE:
            mev_probability = round(min(0.10, mev_probability), 4)
            risk_level = RiskLevel.LOW

        return MEVRisk(
            risk_level=risk_level,
            attack_type=attack_type,
            mev_probability=mev_probability,
        )
