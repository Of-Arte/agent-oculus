from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from core.public_api.account import PublicAccountService
from core.public_api.market_data import PublicMarketDataService
from core.public_api.options import PublicOptionsService
from core.schemas import FinanceContext, MarketRadarVerdict, FearGreedIndex, utc_now_iso
from core.synthesis.alert_engine import build_normalized_signals, evaluate_alerts
from core.synthesis.regime_detector import detect_regime
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WMError, WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService

logger = logging.getLogger(__name__)


async def _guard(coro, label: str):
    try:
        return await coro
    except WMError as exc:
        logger.warning('WorldMonitor fetch failed for %s: %s', label, exc)
        print(f'[WM WARNING] {label} failed: {exc}', file=sys.stderr)
        return None


async def build_finance_context(
    *,
    public_account_service: PublicAccountService,
    public_market_data_service: PublicMarketDataService,
    public_options_service: PublicOptionsService,
    wm_market_radar_service: WorldMonitorMarketRadarService,
    wm_stablecoin_service: WorldMonitorStablecoinService,
    wm_etf_flow_service: WorldMonitorBtcEtfFlowService,
    wm_macro_service: WorldMonitorMacroService,
    wm_supply_chain_service: WorldMonitorSupplyChainService,
    wm_trade_policy_service: WorldMonitorTradePolicyService,
    previous_regime: str | None = None,
) -> FinanceContext:
    account = await public_account_service.get_account_snapshot()
    positions = await public_account_service.list_positions()
    active_symbols = [position.symbol for position in positions if position.quantity]
    quotes = await public_market_data_service.get_quotes(active_symbols) if active_symbols else {}

    options_tasks = {symbol: asyncio.create_task(public_options_service.get_normalized_chain(symbol)) for symbol in active_symbols}

    wm_tasks = await asyncio.gather(
        _guard(wm_macro_service.get_macro_signals(), 'macro'),
        _guard(wm_market_radar_service.get_market_radar_verdict(), 'market_radar'),
        _guard(wm_market_radar_service.get_fear_greed(), 'fear_greed'),
        _guard(wm_stablecoin_service.list_stablecoin_markets(), 'stablecoins'),
        _guard(wm_etf_flow_service.list_etf_flows(), 'etf_flows'),
        _guard(wm_macro_service.get_energy_prices(), 'energy'),
        _guard(wm_supply_chain_service.get_chokepoint_status(), 'chokepoints'),
        _guard(wm_trade_policy_service.get_trade_restrictions(), 'trade_restrictions'),
        _guard(wm_macro_service.get_bis_policy_rates(), 'bis_policy_rates'),
    )
    macro, market_radar, fear_greed, stablecoins, etf_flows, energy, chokepoints, trade_restrictions, bis_policy_rates = wm_tasks

    options_chains = {}
    for symbol, task in options_tasks.items():
        try:
            options_chains[symbol] = await task
        except Exception as exc:
            logger.warning('Options chain fetch failed for %s: %s', symbol, exc)

    default_verdict = MarketRadarVerdict(verdict='CASH', bullish_count=0, total_known=0, signals={}, mayer_multiple=None, timestamp=utc_now_iso())
    default_fg = FearGreedIndex(value=50, classification='UNKNOWN', timestamp=utc_now_iso())
    default_chokepoints = chokepoints or []
    default_stablecoins = stablecoins or []

    regime_result = detect_regime(market_radar or default_verdict, fear_greed or default_fg, default_chokepoints, default_stablecoins)

    context = FinanceContext(
        account=account,
        positions=positions,
        quotes=quotes,
        options_chains=options_chains,
        macro=macro,
        market_radar=market_radar,
        fear_greed=fear_greed,
        stablecoins=stablecoins,
        etf_flows=etf_flows,
        energy=energy,
        chokepoints=chokepoints,
        trade_restrictions=trade_restrictions,
        bis_policy_rates=bis_policy_rates,
        signals=[],
        regime=regime_result.regime,
        regime_flags=regime_result.flags,
        timestamp=utc_now_iso(),
        previous_regime=previous_regime,
    )
    context.signals = build_normalized_signals(context)
    context.alerts = evaluate_alerts(context)
    return context
