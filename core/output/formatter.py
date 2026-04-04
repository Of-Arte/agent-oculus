from __future__ import annotations

from core.schemas import FinanceContext


def format_for_hermes(context: FinanceContext) -> dict:
    active_symbols = [position.symbol for position in context.positions]
    depegged = [item.symbol for item in (context.stablecoins or []) if item.is_depegged]
    critical_chokepoints = [item.name for item in (context.chokepoints or []) if item.score > 70]
    return {
        'agent': 'agent-finance',
        'timestamp': context.timestamp,
        'regime': context.regime,
        'regime_flags': context.regime_flags,
        'signals': [signal.to_dict() for signal in context.signals],
        'alerts': [alert.to_dict() for alert in context.alerts],
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
