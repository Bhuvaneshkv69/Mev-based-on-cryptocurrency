"""Unprotected Trade Attack Simulator.

Simulates what happens to the user's trade when it is broadcast to the
PUBLIC Ethereum mempool WITHOUT any protection mechanism.

AMM Model (Uniswap v2 Constant-Product)
----------------------------------------
The pool holds reserves (R_a, R_b) satisfying R_a × R_b = k (constant).
For simplicity we normalise the token B price so that the baseline price:

    P_base = 1.0 ETH per unit of token B

and compute price AFTER each swap using the constant-product invariant.

Step-by-step Simulation
------------------------
1. INITIAL STATE
   R_a = pool_liquidity_eth          (ETH reserve in the pool)
   R_b = pool_liquidity_eth          (token-B reserve, normalised so price = 1)
   k   = R_a × R_b

2. FRONT-RUN (attacker buys token B with ETH)
   Attacker buys Δ_atk ETH worth of token B.
   Δ_atk = min(attacker_capital_eth, 0.15 × pool_liquidity_eth)
     (cap at 15 % of pool — realistic MEV bot sizing)

   New ETH reserve after attacker buy:
     R_a' = R_a + Δ_atk
   New token-B reserve (constant product):
     R_b' = k / R_a'
   Attacker receives:
     token_b_gained_atk = R_b - R_b'
   New price after front-run (ETH per token B):
     P_after_frontrun = R_a' / R_b'

3. USER TRADE (buys token B with ETH at inflated price)
   User spends trade_amount_eth ETH.
   R_a'' = R_a' + trade_amount_eth
   R_b'' = k / R_a''
   User receives:
     token_b_gained_user = R_b' - R_b''
   User's effective execution price (ETH paid per token B received):
     P_user = trade_amount_eth / token_b_gained_user

4. BACK-RUN (attacker sells token B for ETH)
   Attacker sells all token_b_gained_atk back into the now-depleted pool.
   R_b''' = R_b'' + token_b_gained_atk
   R_a''' = k / R_b'''
   Attacker receives ETH:
     eth_from_backrun = R_a'' - R_a'''
   Attacker profit:
     attacker_profit = eth_from_backrun - Δ_atk

5. USER LOSS
   Expected tokens at baseline price (P_base = 1.0):
     expected_tokens = trade_amount_eth / P_base
   User received:
     token_b_gained_user
   Token shortfall:
     shortfall = expected_tokens - token_b_gained_user
   User loss in ETH (valued at baseline price):
     user_loss_eth = shortfall × P_base

   Price impact percentage:
     price_impact_pct = (P_user - P_base) / P_base × 100
"""

from app.services.trade_protection.models import (
    AttackType,
    MEVRisk,
    TradeParameters,
    UnprotectedScenario,
)


# Maximum fraction of pool the attacker bot uses (realistic cap)
_MAX_ATTACK_FRACTION = 0.15


class AttackSimulator:
    """Computes the unprotected trade metrics using the AMM sandwich model."""

    @staticmethod
    def simulate(params: TradeParameters, mev_risk: MEVRisk) -> UnprotectedScenario:
        """Run the full sandwich attack simulation.

        Args:
            params:   Trade and pool parameters.
            mev_risk: Pre-computed risk assessment (determines attack size).

        Returns:
            UnprotectedScenario with all computed metrics.
        """
        # ------------------------------------------------------------------ #
        # 1. Initial pool state                                                #
        # ------------------------------------------------------------------ #
        R_a = params.pool_liquidity_eth   # ETH reserve
        R_b = params.pool_liquidity_eth   # Token-B reserve (normalised → price = 1)
        k = R_a * R_b
        P_base = R_a / R_b               # Baseline price = 1.0

        # ------------------------------------------------------------------ #
        # 2. Determine attacker size (capped at 15 % of pool)                 #
        # ------------------------------------------------------------------ #
        if mev_risk.attack_type == AttackType.NONE:
            # No meaningful attack possible — return baseline metrics
            return UnprotectedScenario(
                expected_price_eth=round(P_base, 6),
                user_execution_price_eth=round(P_base, 6),
                price_impact_pct=0.0,
                mev_extracted_eth=0.0,
                attacker_profit_eth=0.0,
                user_loss_eth=0.0,
                user_loss_pct=0.0,
            )

        delta_atk = min(
            params.attacker_capital_eth,
            _MAX_ATTACK_FRACTION * params.pool_liquidity_eth,
        )

        # For front-run only (no sandwich back-run) use half the capital
        if mev_risk.attack_type == AttackType.FRONT_RUN:
            delta_atk *= 0.5

        # ------------------------------------------------------------------ #
        # 3. Front-run: attacker buys token B                                 #
        # ------------------------------------------------------------------ #
        R_a_1 = R_a + delta_atk
        R_b_1 = k / R_a_1
        token_b_atk = R_b - R_b_1          # Token B attacker receives

        # ------------------------------------------------------------------ #
        # 4. User trade: buys token B at inflated price                       #
        # ------------------------------------------------------------------ #
        R_a_2 = R_a_1 + params.trade_amount_eth
        R_b_2 = k / R_a_2
        token_b_user = R_b_1 - R_b_2       # Token B user receives

        # Execution price (ETH paid per token B)
        P_user = params.trade_amount_eth / token_b_user if token_b_user > 0 else P_base

        # ------------------------------------------------------------------ #
        # 5. Back-run (sandwich only): attacker sells token B                 #
        # ------------------------------------------------------------------ #
        attacker_profit = 0.0
        mev_extracted = 0.0

        if mev_risk.attack_type == AttackType.SANDWICH:
            R_b_3 = R_b_2 + token_b_atk
            R_a_3 = k / R_b_3
            eth_from_backrun = R_a_2 - R_a_3
            attacker_profit = max(0.0, eth_from_backrun - delta_atk)
            mev_extracted = attacker_profit

        elif mev_risk.attack_type == AttackType.FRONT_RUN:
            # Front-run only: profit = (P_user - P_base) × token_b_atk
            # Attacker's tokens are now worth more at post-user-trade price
            P_after_user = R_a_2 / R_b_2
            eth_value_atk_tokens = token_b_atk * P_after_user
            attacker_profit = max(0.0, eth_value_atk_tokens - delta_atk)
            mev_extracted = attacker_profit

        # ------------------------------------------------------------------ #
        # 6. User loss calculation                                             #
        # ------------------------------------------------------------------ #
        expected_tokens = params.trade_amount_eth / P_base  # What user expected
        shortfall = max(0.0, expected_tokens - token_b_user)
        user_loss_eth = shortfall * P_base
        user_loss_pct = (user_loss_eth / params.trade_amount_eth) * 100 if params.trade_amount_eth > 0 else 0.0
        price_impact_pct = ((P_user - P_base) / P_base) * 100 if P_base > 0 else 0.0

        return UnprotectedScenario(
            expected_price_eth=round(P_base, 6),
            user_execution_price_eth=round(P_user, 6),
            price_impact_pct=round(price_impact_pct, 4),
            mev_extracted_eth=round(mev_extracted, 6),
            attacker_profit_eth=round(attacker_profit, 6),
            user_loss_eth=round(user_loss_eth, 6),
            user_loss_pct=round(user_loss_pct, 4),
        )
