from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import yaml

from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WMError, WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService

_CACHE: dict[str, Any] = {'timestamp': 0.0, 'value': None}


def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


async def _guard(coro):
    try:
        return await coro
    except WMError:
        return None


async def get_macro_context(config_path: str | Path = 'config.yaml') -> dict:
    if _CACHE['value'] is not None and (time.time() - _CACHE['timestamp']) < 900:
        return _CACHE['value']
    _ = load_config(config_path)
    client = WorldMonitorClient()
    try:
        market = WorldMonitorMarketRadarService(client)
        macro = WorldMonitorMacroService(client)
        stable = WorldMonitorStablecoinService(client)
        flows = WorldMonitorBtcEtfFlowService(client)
        supply = WorldMonitorSupplyChainService(client)
        trade = WorldMonitorTradePolicyService(client)

        market_radar = await _guard(market.get_market_radar_verdict())
        fear_greed = await _guard(market.get_fear_greed())
        stablecoins = await _guard(stable.list_stablecoin_markets())
        etf_flows = await _guard(flows.list_etf_flows())
        energy = await _guard(macro.get_energy_prices())
        chokepoints = await _guard(supply.get_chokepoint_status())
        trade_restrictions = await _guard(trade.get_trade_restrictions())
        bis_policy_rates = await _guard(macro.get_bis_policy_rates())

        result = {
            'market_radar': market_radar.to_dict() if market_radar else None,
            'fear_greed': fear_greed.to_dict() if fear_greed else None,
            'stablecoins': [item.to_dict() for item in (stablecoins or [])],
            'etf_flows': [item.to_dict() for item in (etf_flows or [])],
            'energy': energy.to_dict() if energy else None,
            'chokepoints': [item.to_dict() for item in (chokepoints or [])],
            'trade_restrictions': [item.to_dict() for item in (trade_restrictions or [])],
            'bis_policy_rates': [item.to_dict() for item in (bis_policy_rates or [])],
        }
        _CACHE['timestamp'] = time.time()
        _CACHE['value'] = result
        return result
    finally:
        await client.close()


def run(config_path: str | Path = 'config.yaml') -> dict:
    return asyncio.run(get_macro_context(config_path))
