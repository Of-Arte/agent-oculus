from __future__ import annotations

from core.schemas import BISCreditData, BISExchangeRate, BISPolicyRate, CrudeInventories, EnergyPrices, MacroSignals, parse_float, parse_int
from core.worldmonitor.client import WorldMonitorClient


MACRO_SIGNALS_PATH = '/api/economic/v1/get-macro-signals'
BIS_POLICY_PATH = '/api/economic/v1/get-bis-policy-rates'
BIS_EXCHANGE_PATH = '/api/economic/v1/get-bis-exchange-rates'
BIS_CREDIT_PATH = '/api/economic/v1/get-bis-credit'
ENERGY_PRICES_PATH = '/api/economic/v1/get-energy-prices'
CRUDE_INVENTORIES_PATH = '/api/economic/v1/get-crude-inventories'


class WorldMonitorMacroService:
    def __init__(self, client: WorldMonitorClient) -> None:
        self.client = client

    async def get_macro_signals(self) -> MacroSignals:
        payload = await self.client.request('GET', MACRO_SIGNALS_PATH)
        return MacroSignals(
            timestamp=str(payload.get('timestamp', '')),
            verdict=str(payload.get('verdict', '')),
            bullish_count=parse_int(payload.get('bullishCount')),
            total_count=parse_int(payload.get('totalCount')),
            signals=payload.get('signals') or {},
            meta=payload.get('meta') or {},
            unavailable=bool(payload.get('unavailable', False)),
        )

    async def get_bis_policy_rates(self) -> list[BISPolicyRate]:
        payload = await self.client.request('GET', BIS_POLICY_PATH)
        return [
            BISPolicyRate(
                country=str(item.get('countryName', '')),
                rate=parse_float(item.get('rate')),
                timestamp=str(item.get('date', '')),
                metadata=item,
            )
            for item in payload.get('rates', [])
            if isinstance(item, dict)
        ]

    async def get_bis_exchange_rates(self) -> list[BISExchangeRate]:
        payload = await self.client.request('GET', BIS_EXCHANGE_PATH)
        return [
            BISExchangeRate(
                country=str(item.get('countryName', '')),
                real_eer=parse_float(item.get('realEer')),
                nominal_eer=parse_float(item.get('nominalEer')),
                change=parse_float(item.get('realChange')),
                timestamp=str(item.get('date', '')),
                metadata=item,
            )
            for item in payload.get('rates', [])
            if isinstance(item, dict)
        ]

    async def get_bis_credit(self) -> list[BISCreditData]:
        payload = await self.client.request('GET', BIS_CREDIT_PATH)
        return [
            BISCreditData(
                country=str(item.get('countryName', '')),
                credit_gdp_ratio=parse_float(item.get('creditGdpRatio')),
                previous_ratio=parse_float(item.get('previousRatio')),
                timestamp=str(item.get('date', '')),
                metadata=item,
            )
            for item in payload.get('entries', [])
            if isinstance(item, dict)
        ]

    async def get_energy_prices(self) -> EnergyPrices:
        payload = await self.client.request('GET', ENERGY_PRICES_PATH)
        prices = payload.get('prices', [])
        wti = None
        brent = None
        timestamp = None
        for item in prices:
            if not isinstance(item, dict):
                continue
            commodity = str(item.get('commodity', '')).lower()
            name = str(item.get('name', '')).lower()
            if 'wti' in commodity or 'wti' in name:
                wti = parse_float(item.get('price'))
                timestamp = str(item.get('priceAt', timestamp or ''))
            if 'brent' in commodity or 'brent' in name:
                brent = parse_float(item.get('price'))
                timestamp = str(item.get('priceAt', timestamp or ''))
        return EnergyPrices(wti=wti, brent=brent, timestamp=timestamp, metadata=payload)

    async def get_crude_inventories(self) -> CrudeInventories:
        payload = await self.client.request('GET', CRUDE_INVENTORIES_PATH)
        return CrudeInventories(
            latest_period=payload.get('latestPeriod'),
            weeks=[item for item in payload.get('weeks', []) if isinstance(item, dict)],
            metadata=payload,
        )
