from __future__ import annotations

from core.schemas import TariffTrend, TradeBarrier, TradeFlow, TradeRestriction, parse_float, parse_int
from core.worldmonitor.client import WorldMonitorClient


TRADE_RESTRICTIONS_PATH = '/api/trade/v1/get-trade-restrictions'
TARIFF_TRENDS_PATH = '/api/trade/v1/get-tariff-trends'
TRADE_FLOWS_PATH = '/api/trade/v1/get-trade-flows'
TRADE_BARRIERS_PATH = '/api/trade/v1/get-trade-barriers'


class WorldMonitorTradePolicyService:
    def __init__(self, client: WorldMonitorClient) -> None:
        self.client = client

    async def get_trade_restrictions(self) -> list[TradeRestriction]:
        payload = await self.client.request('GET', TRADE_RESTRICTIONS_PATH)
        return [
            TradeRestriction(
                country=str(item.get('reportingCountry', '')),
                restriction_type=str(item.get('measureType', '')),
                status=str(item.get('status', '')),
                metadata=item,
            )
            for item in payload.get('restrictions', [])
            if isinstance(item, dict)
        ]

    async def get_tariff_trends(self) -> list[TariffTrend]:
        payload = await self.client.request('GET', TARIFF_TRENDS_PATH)
        return [
            TariffTrend(
                country=str(item.get('reportingCountry', '')),
                partner_country=str(item.get('partnerCountry', '')),
                product_sector=str(item.get('productSector', '')),
                year=parse_int(item.get('year')),
                tariff_rate=parse_float(item.get('tariffRate')),
                metadata=item,
            )
            for item in payload.get('datapoints', [])
            if isinstance(item, dict)
        ]

    async def get_trade_flows(self) -> list[TradeFlow]:
        payload = await self.client.request('GET', TRADE_FLOWS_PATH)
        return [
            TradeFlow(
                country=str(item.get('reportingCountry', '')),
                partner_country=str(item.get('partnerCountry', '')),
                year=parse_int(item.get('year')),
                export_value_usd=parse_float(item.get('exportValueUsd')),
                import_value_usd=parse_float(item.get('importValueUsd')),
                metadata=item,
            )
            for item in payload.get('flows', [])
            if isinstance(item, dict)
        ]

    async def get_trade_barriers(self) -> list[TradeBarrier]:
        payload = await self.client.request('GET', TRADE_BARRIERS_PATH)
        return [
            TradeBarrier(
                country=str(item.get('notifyingCountry', '')),
                barrier_type=str(item.get('measureType', '')),
                status=str(item.get('status', '')),
                metadata=item,
            )
            for item in payload.get('barriers', [])
            if isinstance(item, dict)
        ]
