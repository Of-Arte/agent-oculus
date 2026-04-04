from __future__ import annotations

from typing import Any

from core.schemas import FearGreedIndex, MarketRadarVerdict, Quote, RadarSignal, parse_float, parse_int
from core.worldmonitor.client import WorldMonitorClient


MARKET_QUOTES_PATH = '/api/market/v1/list-market-quotes'
FEAR_GREED_PATH = '/api/market/v1/get-fear-greed-index'
MACRO_SIGNALS_PATH = '/api/economic/v1/get-macro-signals'


class WorldMonitorMarketRadarService:
    def __init__(self, client: WorldMonitorClient) -> None:
        self.client = client

    async def get_fear_greed(self) -> FearGreedIndex:
        payload = await self.client.request('GET', FEAR_GREED_PATH)
        return FearGreedIndex(
            value=parse_int(payload.get('compositeScore')),
            classification=str(payload.get('compositeLabel', '')),
            timestamp=str(payload.get('seededAt', '')),
            metadata=payload,
        )

    async def get_market_quotes(self, symbols: list[str]) -> list[Quote]:
        params = {'symbols': ','.join(symbols)} if symbols else None
        payload = await self.client.request('GET', MARKET_QUOTES_PATH, params=params)
        return [
            Quote(
                symbol=str(item.get('symbol', '')),
                name=str(item.get('name', '')),
                price=parse_float(item.get('price')),
                change=parse_float(item.get('change')),
                display=item.get('display'),
                metadata={k: v for k, v in item.items() if k not in {'symbol', 'name', 'price', 'change', 'display'}},
            )
            for item in payload.get('quotes', [])
            if isinstance(item, dict)
        ]

    async def get_market_radar_verdict(self) -> MarketRadarVerdict:
        payload = await self.client.request('GET', MACRO_SIGNALS_PATH)
        raw_signals = payload.get('signals') or {}
        signals: dict[str, RadarSignal] = {}
        bullish_count = 0
        total_known = 0
        for key, item in raw_signals.items():
            if not isinstance(item, dict):
                continue
            status = str(item.get('status', 'UNKNOWN')).upper()
            if status == 'UNKNOWN':
                continue
            bullish = status == 'BULLISH'
            total_known += 1
            bullish_count += 1 if bullish else 0
            signals[key] = RadarSignal(value=item, bullish=bullish, source=key)
        mayer_multiple = None
        technical = raw_signals.get('technicalTrend') if isinstance(raw_signals, dict) else None
        if isinstance(technical, dict) and technical.get('mayerMultiple') is not None:
            mayer_multiple = parse_float(technical.get('mayerMultiple'))
        verdict = 'BUY' if total_known > 0 and (bullish_count / total_known) > 0.57 else 'CASH'
        return MarketRadarVerdict(
            verdict=verdict,
            bullish_count=bullish_count,
            total_known=total_known,
            signals=signals,
            mayer_multiple=mayer_multiple,
            timestamp=str(payload.get('timestamp', '')),
        )
