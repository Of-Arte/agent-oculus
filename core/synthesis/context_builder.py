from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from core.public_api.account import PublicAccountService
from core.public_api.market_data import PublicMarketDataService
from core.public_api.options import PublicOptionsService
from core.schemas import FinanceContext, MarketRadarVerdict, FearGreedIndex, Quote, utc_now_iso
from core.synthesis.alert_engine import build_normalized_signals, evaluate_alerts
from core.synthesis.regime_detector import detect_regime
from core.analytics.iv_rank import IVRankEngine
from core.analytics.strategy_selector import select_strategy
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WMError, WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService

logger = logging.getLogger(__name__)

_IV_ENGINE = IVRankEngine(lookback_days=252)


def _parse_dte(expiration: str | None) -> int:
    if not expiration:
        return 0
    try:
        # expiration is typically YYYY-MM-DD
        from datetime import date

        y, m, d = expiration.split('-')
        exp = date(int(y), int(m), int(d))
        today = date.today()
        return max(0, (exp - today).days)
    except Exception:
        return 0


def _estimate_atm_iv(*, quote: Quote | None, chain) -> float | None:
    """Estimate current ATM IV from a normalized options chain.

    Prefer:
    - nearest-strike contract IV vs underlying last price
    Fallback:
    - chain.iv_metrics.implied_volatility (avg)
    """

    underlying = None
    if quote is not None:
        underlying = quote.price

    contracts = getattr(chain, 'contracts', None) or []
    if underlying is not None and contracts:
        best = None
        best_dist = None
        for c in contracts:
            if c.strike is None or c.iv is None:
                continue
            dist = abs(float(c.strike) - float(underlying))
            if best_dist is None or dist < best_dist:
                best = c
                best_dist = dist
        if best is not None and best.iv is not None:
            return float(best.iv)

    iv_metrics = getattr(chain, 'iv_metrics', None)
    if iv_metrics is not None and getattr(iv_metrics, 'implied_volatility', None) is not None:
        return float(iv_metrics.implied_volatility)
    return None


async def _yfinance_atm_iv(symbol: str, quote: Quote | None) -> float | None:
    """Fallback: derive ATM IV from yfinance options chain.

    This keeps read-only IV analysis working even when broker credentials
    aren't available. Runs in an executor to avoid blocking the event loop.
    """

    loop = asyncio.get_running_loop()

    def _fetch() -> float | None:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        expirations = list(getattr(ticker, 'options', []) or [])
        if not expirations:
            return None
        exp = expirations[0]

        underlying = None
        if quote is not None:
            underlying = quote.price
        if underlying is None:
            hist = ticker.history(period='5d', interval='1d')
            if hasattr(hist, 'empty') and not hist.empty and 'Close' in hist.columns:
                underlying = float(hist['Close'].dropna().iloc[-1])

        chain = ticker.option_chain(exp)
        calls = getattr(chain, 'calls', None)
        puts = getattr(chain, 'puts', None)
        frames = [df for df in [calls, puts] if df is not None]
        if not frames:
            return None

        best_iv = None
        best_dist = None
        for df in frames:
            if 'strike' not in df.columns or 'impliedVolatility' not in df.columns:
                continue
            for _, row in df.iterrows():
                strike = row.get('strike')
                iv = row.get('impliedVolatility')
                if strike is None or iv is None:
                    continue
                if underlying is None:
                    continue
                dist = abs(float(strike) - float(underlying))
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_iv = float(iv)

        return best_iv

    return await loop.run_in_executor(None, _fetch)


async def _noop_list() -> list:
    return []


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
    account = None
    positions = []
    try:
        account = await public_account_service.get_account_snapshot()
        positions = await public_account_service.list_positions()
    except Exception as exc:
        logger.warning('Public account fetch failed (continuing read-only): %s', exc)

    active_symbols = [position.symbol for position in positions if position.quantity]
    analysis_symbols = active_symbols or ['SPY', 'QQQ', 'XLE']

    quotes = {}
    if analysis_symbols:
        try:
            quotes = await public_market_data_service.get_quotes(analysis_symbols)
        except Exception as exc:
            logger.warning('Quote fetch failed (continuing): %s', exc)
            quotes = {}

    # Fire off options chain fetches alongside WM fetches — all I/O concurrent.
    options_tasks = [
        asyncio.create_task(public_options_service.get_normalized_chain(symbol))
        for symbol in analysis_symbols
    ]

    wm_tasks_coro = asyncio.gather(
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

    options_results, wm_tasks = await asyncio.gather(
        asyncio.gather(*options_tasks, return_exceptions=True) if options_tasks else _noop_list(),
        wm_tasks_coro,
    )
    macro, market_radar, fear_greed, stablecoins, etf_flows, energy, chokepoints, trade_restrictions, bis_policy_rates = wm_tasks

    options_chains = {}
    for symbol, result in zip(analysis_symbols, options_results):
        if isinstance(result, Exception):
            logger.warning('Options chain fetch failed for %s: %s', symbol, result)
        else:
            options_chains[symbol] = result

    # IV rank analysis (yfinance realized-vol proxy + current ATM IV from chain)
    iv_rank_tasks = []
    for symbol in analysis_symbols:
        chain = options_chains.get(symbol)
        quote = quotes.get(symbol)
        current_iv = _estimate_atm_iv(quote=quote, chain=chain) if chain is not None else None
        if current_iv is None:
            try:
                current_iv = await _yfinance_atm_iv(symbol, quote)
            except Exception as exc:
                logger.warning('yfinance ATM IV fetch failed for %s: %s', symbol, exc)
                current_iv = None
        if current_iv is None:
            continue
        iv_rank_tasks.append(asyncio.create_task(_IV_ENGINE.compute(symbol, float(current_iv))))

    iv_ranks = []
    if iv_rank_tasks:
        for item in await asyncio.gather(*iv_rank_tasks, return_exceptions=True):
            if isinstance(item, Exception):
                logger.warning('IV rank compute failed: %s', item)
                continue
            iv_ranks.append(item)

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
        iv_ranks=iv_ranks,
        signals=[],
        regime=regime_result.regime,
        regime_flags=regime_result.flags,
        timestamp=utc_now_iso(),
        previous_regime=previous_regime,
    )
    context.signals = build_normalized_signals(context)
    context.alerts = evaluate_alerts(context)
    return context
