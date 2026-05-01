from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml

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

# HERMES_REGISTRATION_COMPLETE
# ============================
# This tool is now registered in the Hermes backend via:
#   /home/agentv/.hermes/hermes-agent/tools/finance_tools.py
#   → tools/registry.py register() calls
#   → model_tools.py _discover_tools() import
#   → toolsets.py "finance" toolset definition
#
# Toolset: finance
# Gating: place_order is execution-gated (EXECUTION_ENABLED=false by default)



def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


async def get_signals(symbols: list[str] | None = None, config_path: str | Path = 'config.yaml') -> dict:
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
        signals = context.signals
        alerts = context.alerts
        if symbols:
            symbol_set = {symbol.upper() for symbol in symbols}
            signals = [signal for signal in signals if signal.symbol is None or signal.symbol.upper() in symbol_set]
            alerts = [alert for alert in alerts if alert.ticker is None or alert.ticker.upper() in symbol_set]
        return {
            'regime': context.regime,
            'regime_flags': context.regime_flags,
            'signals': [signal.to_dict() for signal in signals],
            'alerts': [alert.to_dict() for alert in alerts],
        }
    finally:
        await public_client.close()
        await wm_client.close()


def run(symbols: list[str] | None = None, config_path: str | Path = 'config.yaml') -> dict:
    return asyncio.run(get_signals(symbols, config_path))
