from __future__ import annotations

import math

from core.schemas import OptionsChain, StrategyRecommendation


def select_strategy(
    *,
    iv_rank: float,
    regime: str,
    dte_available: int,
    buying_power: float,
    net_delta: float,
    chain: OptionsChain | None = None,
) -> StrategyRecommendation:
    """Selects a strategy recommendation using ATHENA framework rules.

    Pure function: no I/O, no async.
    """

    if dte_available < 21:
        return StrategyRecommendation(
            strategy_type='manage_only',
            rationale='No new entries: nearest liquid expiry is under 21 DTE.',
            max_allocation=0.0,
            target_dte=dte_available,
            target_delta_short=0.0,
            sizing_contracts=0,
            blocked=True,
            blocked_reason='DTE_AVAILABLE_LT_21',
        )

    if buying_power < 500:
        return StrategyRecommendation(
            strategy_type='manage_only',
            rationale='No new entries: buying power under $500.',
            max_allocation=0.0,
            target_dte=dte_available,
            target_delta_short=0.0,
            sizing_contracts=0,
            blocked=True,
            blocked_reason='BUYING_POWER_LT_500',
        )

    max_allocation = float(buying_power) * 0.15
    target_dte = 45
    target_delta_short = 0.15

    # Wire real mid-price from options chain if available.
    sizing_contracts = 0
    mid_price_found = 0.0
    if chain and chain.contracts:
        best_diff = float('inf')
        for c in chain.contracts:
            if c.delta is not None and c.bid is not None and c.ask is not None:
                diff = abs(abs(c.delta) - abs(target_delta_short))
                if diff < best_diff:
                    best_diff = diff
                    mid_price_found = (c.bid + c.ask) / 2.0
        
        if mid_price_found > 0:
            # Conservative sizing: use mid-price as a proxy for per-contract cost/credit units.
            # For credit spreads, this is a floor on buying power used.
            sizing_contracts = int(max_allocation // (mid_price_found * 100))

    strategy_type = 'calendar_spread'
    if iv_rank >= 60:
        if regime == 'RISK_OFF':
            strategy_type = 'iron_condor'
        elif regime == 'RISK_ON':
            strategy_type = 'bull_put_spread'
        else:
            strategy_type = 'iron_condor'
    elif 40 <= iv_rank < 60:
        strategy_type = 'calendar_spread'
    else:
        strategy_type = 'debit_spread'

    rationale = (
        f'IV rank {iv_rank:.1f} with regime {regime} suggests {strategy_type}. '
        f'(net_delta={net_delta:.2f}, dte_available={dte_available})'
    )
    if mid_price_found > 0:
        rationale += f' Estimated mid-price: ${mid_price_found:.2f}.'

    return StrategyRecommendation(
        strategy_type=strategy_type,
        rationale=rationale,
        max_allocation=max_allocation,
        target_dte=target_dte,
        target_delta_short=target_delta_short,
        sizing_contracts=sizing_contracts,
        blocked=False,
        blocked_reason=None,
    )
