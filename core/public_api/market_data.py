from __future__ import annotations

from core.public_api.client import PublicApiClient
from core.schemas import Quote, parse_float, utc_now_iso


class PublicMarketDataService:
    def __init__(self, client: PublicApiClient) -> None:
        self.client = client

    async def get_quotes(self, symbols: list[str], instrument_type: str = 'EQUITY') -> dict[str, Quote]:
        payload = await self.client.get_quotes(symbols, instrument_type)
        quote_items = payload.get('quotes') or payload.get('data') or payload.get('results') or []
        quotes: dict[str, Quote] = {}
        for item in quote_items:
            if not isinstance(item, dict):
                continue
            symbol = str(item.get('symbol', ''))
            if not symbol:
                continue
            quotes[symbol] = Quote(
                symbol=symbol,
                name=str(item.get('name', symbol)),
                price=parse_float(item.get('price') or item.get('last') or item.get('lastPrice')),
                change=parse_float(item.get('change') or item.get('changePercent')),
                display=item.get('display'),
                timestamp=str(item.get('timestamp') or utc_now_iso()),
                metadata=item,
            )
        return quotes
