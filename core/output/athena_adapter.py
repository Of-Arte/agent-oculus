from __future__ import annotations

from core.schemas import FinanceContext


def package_for_athena(context: FinanceContext) -> dict:
    bis_rates = sorted(context.bis_policy_rates or [], key=lambda item: item.rate, reverse=True)[:5]
    positions = []
    for position in context.positions:
        chain = context.options_chains.get(position.symbol)
        positions.append({
            'symbol': position.symbol,
            'asset_type': position.asset_type,
            'market_value': position.market_value,
            'unrealized_pnl_pct': position.unrealized_pnl_pct,
            'iv_rank': chain.iv_rank if chain else None,
        })
    return {
        'regime': context.regime,
        'regime_flags': context.regime_flags,
        'market_radar': {
            'verdict': context.market_radar.verdict if context.market_radar else None,
            'bullish_count': context.market_radar.bullish_count if context.market_radar else None,
            'total_known': context.market_radar.total_known if context.market_radar else None,
            'fear_greed_value': context.fear_greed.value if context.fear_greed else None,
            'fear_greed_label': context.fear_greed.classification if context.fear_greed else None,
        },
        'portfolio': {
            'equity': context.account.equity if context.account else None,
            'cash': context.account.cash if context.account else None,
            'buying_power': context.account.buying_power if context.account else None,
            'position_count': len(context.positions),
            'positions': positions,
        },
        'macro': {
            'energy': {
                'wti': context.energy.wti if context.energy else None,
                'brent': context.energy.brent if context.energy else None,
            },
            'bis_rates_snapshot': [item.to_dict() for item in bis_rates],
            'active_trade_restrictions': len(context.trade_restrictions or []),
        },
        'alerts': [alert.to_dict() for alert in context.alerts],
        'timestamp': context.timestamp,
    }
