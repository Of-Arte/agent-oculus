from __future__ import annotations

from core.public_api.client import PublicApiClient
from core.schemas import IVMetrics, OptionContract, OptionsChain, parse_float


class PublicOptionsService:
    def __init__(self, client: PublicApiClient) -> None:
        self.client = client

    async def get_expirations(self, underlying_symbol: str) -> dict:
        return await self.client.get_option_expirations(underlying_symbol)

    async def get_chain(self, underlying_symbol: str, expiration: str | None = None) -> dict:
        return await self.client.get_option_chain(underlying_symbol, expiration)

    def normalize_chain(self, underlying_symbol: str, payload: dict) -> list[OptionContract]:
        contracts: list[OptionContract] = []
        containers = []
        if isinstance(payload.get('contracts'), list):
            containers.extend(payload['contracts'])
        for side in ('calls', 'puts', 'data'):
            side_payload = payload.get(side)
            if isinstance(side_payload, list):
                containers.extend(side_payload)
        for item in containers:
            if isinstance(item, dict):
                contracts.append(OptionContract.from_api_payload(underlying_symbol, item))
        return contracts

    def build_options_chain(self, symbol: str, expiration: str | None, payload: dict) -> OptionsChain:
        contracts = self.normalize_chain(symbol, payload)
        iv_values = [contract.iv for contract in contracts if contract.iv is not None]
        avg_iv = (sum(iv_values) / len(iv_values)) if iv_values else None
        iv_rank = min(100.0, max(0.0, parse_float(avg_iv) * 100.0)) if avg_iv is not None else None
        return OptionsChain(
            symbol=symbol,
            expiration=expiration,
            contracts=contracts,
            iv_metrics=IVMetrics(iv_rank=iv_rank, implied_volatility=avg_iv),
        )

    async def get_nearest_expiration(self, symbol: str) -> str | None:
        payload = await self.get_expirations(symbol)
        expirations = payload.get('expirations') or payload.get('data') or payload.get('dates') or []
        if not expirations:
            return None
        if isinstance(expirations[0], dict):
            return str(expirations[0].get('date') or expirations[0].get('expiration') or '') or None
        return str(expirations[0])

    async def get_normalized_chain(self, symbol: str, expiration: str | None = None) -> OptionsChain:
        resolved_expiration = expiration or await self.get_nearest_expiration(symbol)
        payload = await self.get_chain(symbol, resolved_expiration)
        return self.build_options_chain(symbol, resolved_expiration, payload)
