from __future__ import annotations

from core.analytics.strategy_selector import select_strategy
from core.schemas import FinanceContext


def format_for_hermes(context: FinanceContext) -> dict:
    active_symbols = [position.symbol for position in context.positions]
    depegged = [item.symbol for item in (context.stablecoins or []) if item.is_depegged]
    critical_chokepoints = [item.name for item in (context.chokepoints or []) if item.score > 70]
    iv_analysis = []
    for item in context.iv_ranks:
        # Strategy selector is pure; keep simple inputs until portfolio greeks are wired.
        chain = context.options_chains.get(item.symbol)
        dte_available = 0
        if chain is not None:
            try:
                from datetime import date

                if chain.expiration:
                    y, m, d = chain.expiration.split('-')
                    exp = date(int(y), int(m), int(d))
                    dte_available = max(0, (exp - date.today()).days)
            except Exception:
                dte_available = 0

        buying_power = context.account.buying_power if context.account and context.account.buying_power is not None else 0.0
        rec = select_strategy(
            iv_rank=item.iv_rank,
            regime=context.regime,
            dte_available=dte_available or 45,
            buying_power=float(buying_power),
            net_delta=0.0,
            chain=chain,
        )
        iv_analysis.append({
            'symbol': item.symbol,
            'iv_rank': item.iv_rank,
            'iv_percentile': item.iv_percentile,
            'vol_regime': item.vol_regime,
            'strategy_recommendation': {
                'strategy_type': rec.strategy_type,
                'rationale': rec.rationale,
                'max_allocation': rec.max_allocation,
                'target_dte': rec.target_dte,
                'sizing_contracts': rec.sizing_contracts,
                'blocked': rec.blocked,
                'blocked_reason': rec.blocked_reason,
            },
        })

    return {
        'agent': 'agent-oculus-v1',
        'timestamp': context.timestamp,
        'regime': context.regime,
        'regime_flags': context.regime_flags,
        'signals': [signal.to_dict() for signal in context.signals],
        'alerts': [alert.to_dict() for alert in context.alerts],
        'iv_analysis': iv_analysis,
        'summary': {
            'position_count': len(context.positions),
            'active_symbols': active_symbols,
            'fear_greed': context.fear_greed.value if context.fear_greed else None,
            'verdict': context.market_radar.verdict if context.market_radar else None,
            'bullish_count': context.market_radar.bullish_count if context.market_radar else None,
            'depegged_stablecoins': depegged,
            'critical_chokepoints': critical_chokepoints,
        },
    }
