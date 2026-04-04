from __future__ import annotations

from core.schemas import StablecoinStatus, parse_float
from core.worldmonitor.client import WorldMonitorClient


STABLECOINS_PATH = '/api/market/v1/list-stablecoin-markets'


class WorldMonitorStablecoinService:
    def __init__(self, client: WorldMonitorClient) -> None:
        self.client = client

    async def list_stablecoin_markets(self) -> list[StablecoinStatus]:
        payload = await self.client.request('GET', STABLECOINS_PATH)
        results: list[StablecoinStatus] = []
        for item in payload.get('stablecoins', []):
            if not isinstance(item, dict):
                continue
            price = parse_float(item.get('price'))
            deviation = parse_float(item.get('deviation'))
            deviation_pct = deviation * 100.0
            results.append(
                StablecoinStatus(
                    symbol=str(item.get('symbol', '')).upper(),
                    price=price,
                    peg=1.0,
                    peg_deviation_pct=deviation_pct,
                    is_depegged=abs(deviation_pct) > 0.5,
                    metadata=item,
                )
            )
        return results
