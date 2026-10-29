"""Trade Protection Engine.

Applies the chosen protection mechanism to the unprotected baseline metrics
and returns the resulting protected scenario.

Protection Mechanism Models
----------------------------

1. NONE  (no protection)
   Effectiveness: 0 %
   The protected result equals the unprotected result exactly.

2. PRIVATE_MEMPOOL  (e.g. Flashbots Protect, MEV Blocker)
   Mechanism: Trade is sent directly to block builders via a private RPC
   endpoint, bypassing the public mempool entirely. MEV bots watching the
   public mempool cannot see the transaction before it lands on-chain.
   Effectiveness: 90–95 %
   Residual risk: ~5 % — relay-level information leakage or builder collusion.
   Formula: mev_residual = unprotected_mev × 0.05
             user_loss_protected = user_loss_unprotected × 0.05

3. SLIPPAGE_GUARD  (tight on-chain max slippage parameter)
   Mechanism: The smart contract reverts the trade if the actual execution
   price deviates more than `slippage_tolerance_pct` from the quoted price.
   This forces a revert instead of an exploitable loss, but does NOT prevent
   the front-run transaction itself from landing.
   Effectiveness: variable — capped at slippage tolerance
   Formula: effective_loss_pct = min(user_loss_pct, slippage_tolerance_pct)
             savings = user_loss_eth - (trade_amount × effective_loss_pct/100)
   Limitation: If the attacker's front-run exceeds the tolerance, the user's
   trade simply reverts (they pay gas but avoid the loss).

4. COMMIT_REVEAL  (two-phase order commitment)
   Mechanism: In block N, the user posts a cryptographic commitment hash.
   In block N+1, they reveal the trade details and execute. By the time the
   attacker sees the details, it is too late to front-run (the commitment is
   already mined).
   Effectiveness: 75–85 % — partial because timing attacks are still possible
   if the attacker can bribe validators or exploit short block times.
   Formula: mev_residual = unprotected_mev × 0.20

5. TIME_LOCK  (TWAP / time-weighted order)
   Mechanism: The trade is split across multiple blocks and executed at the
   time-weighted average price. The sandwich profit collapses to near-zero
   because the attacker cannot back-run a single block with certainty.
   Effectiveness: 95–99 % against sandwich; 60 % against front-run.
   Formula: For sandwich attacks: mev_residual = unprotected_mev × 0.03
             For front-run only:  mev_residual = unprotected_mev × 0.40
"""

from app.services.trade_protection.models import (
    AttackType,
    MEVRisk,
    ProtectedScenario,
    ProtectionType,
    TradeParameters,
    UnprotectedScenario,
)


# Effectiveness residual multipliers (fraction of MEV/loss that remains)
_RESIDUAL: dict[ProtectionType, float] = {
    ProtectionType.NONE:              1.00,   # 0 % protection
    ProtectionType.PRIVATE_MEMPOOL:   0.05,   # 95 % effective (centralized private RPC)
    ProtectionType.SLIPPAGE_GUARD:    None,   # Computed dynamically (caps loss / causes revert)
    ProtectionType.COMMIT_REVEAL:     0.20,   # 80 % effective (two-phase latency)
    ProtectionType.TIME_LOCK:         None,   # Depends on attack type
    ProtectionType.ENCRYPTED_MEMPOOL: 0.00,   # 100 % effective (cryptographic threshold privacy)
    ProtectionType.BATCH_AUCTION:     0.00,   # 100 % effective (discrete uniform clearing price)
    ProtectionType.MEV_SHARE:         0.10,   # 90 % effective (90% MEV rebate distributed to user)
}


class ProtectionEngine:
    """Applies the chosen protection mechanism to compute the protected scenario."""

    @staticmethod
    def apply(
        params: TradeParameters,
        mev_risk: MEVRisk,
        unprotected: UnprotectedScenario,
    ) -> ProtectedScenario:
        """Compute the protected scenario metrics.

        Args:
            params:      Trade parameters including chosen protection type.
            mev_risk:    Risk assessment (needed for time-lock differentiation).
            unprotected: Baseline unprotected metrics.

        Returns:
            ProtectedScenario with all adjusted metrics.
        """
        ptype = params.protection_type

        # ------------------------------------------------------------------
        # Determine the residual multiplier for this protection/attack combo
        # ------------------------------------------------------------------
        if ptype == ProtectionType.SLIPPAGE_GUARD:
            residual = ProtectionEngine._slippage_guard_residual(params, unprotected)
        elif ptype == ProtectionType.TIME_LOCK:
            # Sandwich: near-total elimination; front-run: partial
            if mev_risk.attack_type == AttackType.SANDWICH:
                residual = 0.03
            elif mev_risk.attack_type == AttackType.FRONT_RUN:
                residual = 0.40
            else:
                residual = 0.0
        else:
            residual = _RESIDUAL[ptype]

        # ------------------------------------------------------------------
        # Compute protected metrics
        # ------------------------------------------------------------------
        mev_residual = round(unprotected.mev_extracted_eth * residual, 6)
        user_loss_protected = round(unprotected.user_loss_eth * residual, 6)
        user_savings = round(unprotected.user_loss_eth - user_loss_protected, 6)

        # Recompute execution price from the residual loss
        user_loss_pct_protected = round(unprotected.user_loss_pct * residual, 4)
        exec_price_protected = round(
            unprotected.expected_price_eth * (1 + user_loss_pct_protected / 100),
            6,
        )
        price_impact_protected = round(unprotected.price_impact_pct * residual, 4)

        # Protection effectiveness (how much of the original MEV was blocked)
        if unprotected.user_loss_eth > 0:
            effectiveness = round((1.0 - residual) * 100, 2)
        else:
            effectiveness = 100.0 if ptype != ProtectionType.NONE else 0.0

        user_rebate = 0.0
        if ptype == ProtectionType.MEV_SHARE:
            user_rebate = round(unprotected.mev_extracted_eth * 0.90, 6)

        return ProtectedScenario(
            user_execution_price_eth=exec_price_protected,
            price_impact_pct=price_impact_protected,
            mev_extracted_eth=mev_residual,
            user_loss_eth=user_loss_protected,
            user_loss_pct=user_loss_pct_protected,
            protection_effectiveness_pct=effectiveness,
            user_savings_eth=max(0.0, user_savings),
            user_rebate_eth=user_rebate,
        )

    @staticmethod
    def _slippage_guard_residual(
        params: TradeParameters,
        unprotected: UnprotectedScenario,
    ) -> float:
        """Compute the residual loss fraction under a slippage guard.

        If the unprotected price impact exceeds the user's slippage tolerance,
        the trade would have reverted — user loses nothing except gas (modelled
        as 0 loss).  If the impact is within tolerance, the loss is capped at
        the tolerance level.
        """
        if unprotected.user_loss_pct <= params.slippage_tolerance_pct:
            # Attack is within tolerance — guard does not help
            return 1.0

        # Guard triggers: cap loss at slippage tolerance
        if unprotected.user_loss_eth > 0:
            capped_loss = params.trade_amount_eth * (params.slippage_tolerance_pct / 100)
            residual = min(1.0, capped_loss / unprotected.user_loss_eth)
        else:
            residual = 0.0

        return round(residual, 4)
