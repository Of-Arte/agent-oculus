from __future__ import annotations

from core.schemas import ETFFlowSummary, parse_float
from core.worldmonitor.client import WorldMonitorClient


ETF_FLOWS_PATH = '/api/market/v1/list-etf-flows'


class WorldMonitorBtcEtfFlowService:
    def __init__(self, client: WorldMonitorClient) -> None:
        self.client = client

    async def list_etf_flows(self) -> list[ETFFlowSummary]:
        payload = await self.client.request('GET', ETF_FLOWS_PATH)
        timestamp = str(payload.get('timestamp', ''))
        results: list[ETFFlowSummary] = []
        for item in payload.get('etfs', []):
            if not isinstance(item, dict):
                continue
            direction = str(item.get('direction', 'NEUTRAL')).upper()
            if direction not in {'INFLOW', 'OUTFLOW', 'NEUTRAL'}:
                direction = 'NEUTRAL'
            results.append(
                ETFFlowSummary(
                    ticker=str(item.get('ticker', '')),
                    flow_direction=direction,
                    flow_magnitude=parse_float(item.get('estFlow')),
                    timestamp=timestamp,
                    metadata=item,
                )
            )
        return results
