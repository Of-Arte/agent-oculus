from __future__ import annotations

from core.schemas import ChokepointStatus, CriticalMineral, ShippingRate, ShippingStress, parse_float
from core.worldmonitor.client import WorldMonitorClient


CHOKEPOINT_STATUS_PATH = '/api/supply-chain/v1/get-chokepoint-status'
SHIPPING_RATES_PATH = '/api/supply-chain/v1/get-shipping-rates'
CRITICAL_MINERALS_PATH = '/api/supply-chain/v1/get-critical-minerals'
SHIPPING_STRESS_PATH = '/api/supply-chain/v1/get-shipping-stress'


def _normalize_disruption_level(value: str) -> str:
    upper = value.upper()
    mapping = {
        'NORMAL': 'LOW',
        'LOW': 'LOW',
        'MEDIUM': 'MEDIUM',
        'HIGH': 'HIGH',
        'CRITICAL': 'CRITICAL',
    }
    return mapping.get(upper, 'LOW')


class WorldMonitorSupplyChainService:
    def __init__(self, client: WorldMonitorClient) -> None:
        self.client = client

    async def get_chokepoint_status(self) -> list[ChokepointStatus]:
        payload = await self.client.request('GET', CHOKEPOINT_STATUS_PATH)
        return [
            ChokepointStatus(
                name=str(item.get('name', '')),
                score=parse_float(item.get('disruptionScore')),
                disruption_level=_normalize_disruption_level(str(item.get('status', 'LOW'))),
                metadata=item,
            )
            for item in payload.get('chokepoints', [])
            if isinstance(item, dict)
        ]

    async def get_shipping_rates(self) -> list[ShippingRate]:
        payload = await self.client.request('GET', SHIPPING_RATES_PATH)
        timestamp = payload.get('fetchedAt')
        return [
            ShippingRate(
                route=str(item.get('name', '')),
                rate=parse_float(item.get('currentValue')),
                timestamp=str(timestamp) if timestamp is not None else None,
                metadata=item,
            )
            for item in payload.get('indices', [])
            if isinstance(item, dict)
        ]

    async def get_critical_minerals(self) -> list[CriticalMineral]:
        payload = await self.client.request('GET', CRITICAL_MINERALS_PATH)
        return [
            CriticalMineral(
                mineral=str(item.get('mineral', '')),
                hhi=parse_float(item.get('hhi')),
                risk_rating=str(item.get('riskRating', '')),
                global_production=parse_float(item.get('globalProduction')),
                metadata=item,
            )
            for item in payload.get('minerals', [])
            if isinstance(item, dict)
        ]

    async def get_shipping_stress(self) -> ShippingStress:
        payload = await self.client.request('GET', SHIPPING_STRESS_PATH)
        return ShippingStress(
            stress_score=parse_float(payload.get('stressScore')),
            stress_level=str(payload.get('stressLevel', '')),
            timestamp=str(payload.get('fetchedAt', '')),
            metadata=payload,
        )
