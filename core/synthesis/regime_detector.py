from __future__ import annotations

from dataclasses import dataclass

from core.schemas import ChokepointStatus, FearGreedIndex, MarketRadarVerdict, StablecoinStatus


@dataclass(slots=True)
class RegimeResult:
    regime: str
    flags: list[str]

    def to_dict(self) -> dict[str, object]:
        return {'regime': self.regime, 'flags': self.flags}


def detect_regime(
    verdict: MarketRadarVerdict,
    fear_greed: FearGreedIndex,
    chokepoints: list[ChokepointStatus],
    stablecoins: list[StablecoinStatus],
) -> RegimeResult:
    if verdict.verdict == 'BUY' and fear_greed.value > 55 and verdict.bullish_count >= 5:
        regime = 'RISK_ON'
    elif verdict.verdict == 'CASH' and fear_greed.value < 50:
        regime = 'RISK_OFF'
    else:
        regime = 'TRANSITIONAL'

    flags: list[str] = []
    if any(item.score > 70 for item in chokepoints):
        flags.append('MACRO_SHOCK_RISK')
    if any(item.is_depegged for item in stablecoins):
        flags.append('LIQUIDITY_STRESS')
    return RegimeResult(regime=regime, flags=flags)
