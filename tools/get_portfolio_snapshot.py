from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import yaml

from core.output.formatter import format_for_hermes
from core.public_api.account import PublicAccountService
from core.public_api.client import PublicApiClient
from core.public_api.market_data import PublicMarketDataService
from core.public_api.options import PublicOptionsService
from core.synthesis.context_builder import build_finance_context
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService

# TODO: HERMES REGISTRATION — wire this tool through tools/registry.py -> model_tools.py -> toolsets.py.

_CACHE: dict[str, Any] = {'timestamp': 0.0, 'value': None}


def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


async def get_portfolio_snapshot(config_path: str | Path = 'config.yaml') -> dict:
    if _CACHE['value'] is not None and (time.time() - _CACHE['timestamp']) < 300:
        return _CACHE['value']
    config = load_config(config_path)
    public_client = PublicApiClient(config['public'])
    wm_client = WorldMonitorClient()
    try:
        context = await build_finance_context(
            public_account_service=PublicAccountService(public_client),
            public_market_data_service=PublicMarketDataService(public_client),
            public_options_service=PublicOptionsService(public_client),
            wm_market_radar_service=WorldMonitorMarketRadarService(wm_client),
            wm_stablecoin_service=WorldMonitorStablecoinService(wm_client),
            wm_etf_flow_service=WorldMonitorBtcEtfFlowService(wm_client),
            wm_macro_service=WorldMonitorMacroService(wm_client),
            wm_supply_chain_service=WorldMonitorSupplyChainService(wm_client),
            wm_trade_policy_service=WorldMonitorTradePolicyService(wm_client),
        )
        result = format_for_hermes(context)
        _CACHE['timestamp'] = time.time()
        _CACHE['value'] = result
        return result
    finally:
        await public_client.close()
        await wm_client.close()


def run(config_path: str | Path = 'config.yaml') -> dict:
    return asyncio.run(get_portfolio_snapshot(config_path))
