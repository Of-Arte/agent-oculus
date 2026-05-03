from __future__ import annotations

import asyncio

from core.exceptions import ExecutionDisabledError
from core.output.formatter import format_for_hermes
from core.schemas import (
    AccountSnapshot,
    BISPolicyRate,
    ChokepointStatus,
    ETFFlowSummary,
    EnergyPrices,
    FearGreedIndex,
    MacroSignals,
    MarketRadarVerdict,
    OptionsChain,
    PositionSnapshot,
    Quote,
    RadarSignal,
    StablecoinStatus,
    TradeRestriction,
    IVMetrics,
)
from core.synthesis.context_builder import build_finance_context
from core.synthesis.regime_detector import detect_regime
from core.synthesis.alert_engine import evaluate_alerts
from tools.place_order import place_order


class StubPublicAccountService:
    def __init__(self, account, positions):
        self._account = account
        self._positions = positions

    async def get_account_snapshot(self):
        return self._account

    async def list_positions(self):
        return self._positions


class StubPublicMarketDataService:
    def __init__(self, quotes):
        self._quotes = quotes

    async def get_quotes(self, symbols, instrument_type='EQUITY'):
        return {symbol: self._quotes[symbol] for symbol in symbols if symbol in self._quotes}


class StubPublicOptionsService:
    def __init__(self, chains):
        self._chains = chains

    async def get_normalized_chain(self, symbol, expiration=None):
        return self._chains[symbol]


class StubMethodService:
    def __init__(self, **methods):
        for key, value in methods.items():
            setattr(self, key, value)


def make_context_fixture():
    account = AccountSnapshot(account_id='acct-1', buying_power=1000, cash=500, equity=1500)
    positions = [
        PositionSnapshot(symbol='AAPL', asset_type='EQUITY', quantity=2, market_value=400, average_cost=180),
        PositionSnapshot(symbol='TSLA', asset_type='EQUITY', quantity=1, market_value=250, average_cost=260),
    ]
    quotes = {
        'AAPL': Quote(symbol='AAPL', name='Apple', price=200, change=1),
        'TSLA': Quote(symbol='TSLA', name='Tesla', price=250, change=-1),
    }
    chains = {
        'AAPL': OptionsChain(symbol='AAPL', expiration='2026-01-16', contracts=[], iv_metrics=IVMetrics(iv_rank=75, implied_volatility=0.75)),
        'TSLA': OptionsChain(symbol='TSLA', expiration='2026-01-16', contracts=[], iv_metrics=IVMetrics(iv_rank=40, implied_volatility=0.40)),
    }
    macro = MacroSignals(timestamp='2026-01-01T00:00:00Z', verdict='BUY', bullish_count=5, total_count=7, signals={}, meta={}, unavailable=False)
    verdict = MarketRadarVerdict(verdict='BUY', bullish_count=5, total_known=7, signals={'liq': RadarSignal(value=1, bullish=True, source='liq')}, mayer_multiple=1.1, timestamp='2026-01-01T00:00:00Z')
    fear_greed = FearGreedIndex(value=65, classification='Greed', timestamp='2026-01-01T00:00:00Z')
    stablecoins = [StablecoinStatus(symbol='USDC', price=1.0, peg=1.0, peg_deviation_pct=0.0, is_depegged=False)]
    etf_flows = [ETFFlowSummary(ticker='IBIT', flow_direction='INFLOW', flow_magnitude=120_000_000, timestamp='2026-01-01T00:00:00Z')]
    energy = EnergyPrices(wti=70.0, brent=74.0, timestamp='2026-01-01T00:00:00Z')
    chokepoints = [ChokepointStatus(name='Suez Canal', score=40, disruption_level='LOW')]
    trade_restrictions = [TradeRestriction(country='US', restriction_type='tariff', status='ACTIVE')]
    bis_rates = [BISPolicyRate(country='US', rate=5.5, timestamp='2026-01-01')]
    return account, positions, quotes, chains, macro, verdict, fear_greed, stablecoins, etf_flows, energy, chokepoints, trade_restrictions, bis_rates


def test_context_builder_assembles_finance_context():
    async def scenario():
        account, positions, quotes, chains, macro, verdict, fear_greed, stablecoins, etf_flows, energy, chokepoints, trade_restrictions, bis_rates = make_context_fixture()
        context = await build_finance_context(
            public_account_service=StubPublicAccountService(account, positions),
            public_market_data_service=StubPublicMarketDataService(quotes),
            public_options_service=StubPublicOptionsService(chains),
            wm_market_radar_service=StubMethodService(get_market_radar_verdict=lambda: _ret(verdict), get_fear_greed=lambda: _ret(fear_greed)),
            wm_stablecoin_service=StubMethodService(list_stablecoin_markets=lambda: _ret(stablecoins)),
            wm_etf_flow_service=StubMethodService(list_etf_flows=lambda: _ret(etf_flows)),
            wm_macro_service=StubMethodService(get_macro_signals=lambda: _ret(macro), get_energy_prices=lambda: _ret(energy), get_bis_policy_rates=lambda: _ret(bis_rates)),
            wm_supply_chain_service=StubMethodService(get_chokepoint_status=lambda: _ret(chokepoints)),
            wm_trade_policy_service=StubMethodService(get_trade_restrictions=lambda: _ret(trade_restrictions)),
        )
        assert context.account is not None
        assert len(context.positions) == 2
        assert context.macro is not None
        assert context.market_radar is not None
    asyncio.run(scenario())


def test_context_builder_tolerates_wm_failure():
    async def scenario():
        from core.worldmonitor.client import WMError
        account, positions, quotes, chains, macro, verdict, fear_greed, stablecoins, etf_flows, energy, chokepoints, trade_restrictions, bis_rates = make_context_fixture()
        async def fail():
            raise WMError('boom')
        context = await build_finance_context(
            public_account_service=StubPublicAccountService(account, positions),
            public_market_data_service=StubPublicMarketDataService(quotes),
            public_options_service=StubPublicOptionsService(chains),
            wm_market_radar_service=StubMethodService(get_market_radar_verdict=lambda: _ret(verdict), get_fear_greed=lambda: _ret(fear_greed)),
            wm_stablecoin_service=StubMethodService(list_stablecoin_markets=fail),
            wm_etf_flow_service=StubMethodService(list_etf_flows=lambda: _ret(etf_flows)),
            wm_macro_service=StubMethodService(get_macro_signals=lambda: _ret(macro), get_energy_prices=lambda: _ret(energy), get_bis_policy_rates=lambda: _ret(bis_rates)),
            wm_supply_chain_service=StubMethodService(get_chokepoint_status=lambda: _ret(chokepoints)),
            wm_trade_policy_service=StubMethodService(get_trade_restrictions=lambda: _ret(trade_restrictions)),
        )
        assert context is not None
        assert context.stablecoins is None
    asyncio.run(scenario())


def test_regime_risk_on():
    result = detect_regime(MarketRadarVerdict('BUY', 5, 7, {}, None, 't'), FearGreedIndex(65, 'Greed', 't'), [], [])
    assert result.regime == 'RISK_ON'


def test_regime_risk_off():
    result = detect_regime(MarketRadarVerdict('CASH', 3, 7, {}, None, 't'), FearGreedIndex(45, 'Fear', 't'), [], [])
    assert result.regime == 'RISK_OFF'


def test_regime_transitional():
    result = detect_regime(MarketRadarVerdict('BUY', 4, 7, {}, None, 't'), FearGreedIndex(45, 'Fear', 't'), [], [])
    assert result.regime == 'TRANSITIONAL'


def test_regime_flag_macro_shock():
    result = detect_regime(MarketRadarVerdict('BUY', 5, 7, {}, None, 't'), FearGreedIndex(65, 'Greed', 't'), [ChokepointStatus('Suez', 82, 'HIGH')], [])
    assert 'MACRO_SHOCK_RISK' in result.flags


def test_regime_flag_liquidity_stress():
    result = detect_regime(MarketRadarVerdict('BUY', 5, 7, {}, None, 't'), FearGreedIndex(65, 'Greed', 't'), [], [StablecoinStatus('USDT', 0.99, 1.0, -1.0, True)])
    assert 'LIQUIDITY_STRESS' in result.flags


def test_alert_iv_rank_high_warning():
    context = _context_with_chain_rank(75)
    alerts = evaluate_alerts(context)
    assert any(alert.alert_type == 'IV_RANK_HIGH' and alert.severity == 'WARNING' for alert in alerts)


def test_alert_iv_rank_high_critical():
    context = _context_with_chain_rank(90)
    alerts = evaluate_alerts(context)
    assert any(alert.alert_type == 'IV_RANK_HIGH' and alert.severity == 'CRITICAL' for alert in alerts)


def test_alert_stablecoin_depeg():
    context = _context_with_chain_rank(50)
    context.stablecoins = [StablecoinStatus('USDT', 0.994, 1.0, -0.6, True)]
    alerts = evaluate_alerts(context)
    assert any(alert.alert_type == 'STABLECOIN_DEPEG' and alert.severity == 'CRITICAL' for alert in alerts)


def test_place_order_execution_disabled(monkeypatch):
    async def scenario():
        monkeypatch.delenv('EXECUTION_ENABLED', raising=False)
        try:
            await place_order({'symbol': 'AAPL', 'side': 'BUY', 'quantity': 1, 'order_type': 'market'})
        except ExecutionDisabledError:
            assert True
        else:
            raise AssertionError('Expected ExecutionDisabledError')
    asyncio.run(scenario())


def test_format_for_hermes_shape():
    context = _context_with_chain_rank(75)
    payload = format_for_hermes(context)
    for key in ['agent', 'timestamp', 'regime', 'signals', 'alerts', 'summary']:
        assert key in payload


def test_format_for_hermes_does_not_invent_symbols():
    context = _context_with_chain_rank(75)
    payload = format_for_hermes(context)
    summary = payload['summary']
    assert set(summary['active_symbols']) == {'AAPL', 'TSLA'}
    assert summary['position_count'] == 2


def test_format_for_hermes_stablecoin_depegs_only_when_flagged():
    context = _context_with_chain_rank(75)
    # Only USDT is marked depegged here.
    context.stablecoins = [
        StablecoinStatus('USDT', 0.99, 1.0, -1.0, True),
        StablecoinStatus('USDC', 1.0, 1.0, 0.0, False),
    ]
    payload = format_for_hermes(context)
    assert payload['summary']['depegged_stablecoins'] == ['USDT']


async def _ret(value):
    return value


def _context_with_chain_rank(rank):
    account, positions, quotes, chains, macro, verdict, fear_greed, stablecoins, etf_flows, energy, chokepoints, trade_restrictions, bis_rates = make_context_fixture()
    chains['AAPL'] = OptionsChain(symbol='AAPL', expiration='2026-01-16', contracts=[], iv_metrics=IVMetrics(iv_rank=rank, implied_volatility=0.7))
    from core.schemas import FinanceContext
    context = FinanceContext(
        account=account,
        positions=positions,
        quotes=quotes,
        options_chains=chains,
        macro=macro,
        market_radar=verdict,
        fear_greed=fear_greed,
        stablecoins=stablecoins,
        etf_flows=etf_flows,
        energy=energy,
        chokepoints=chokepoints,
        trade_restrictions=trade_restrictions,
        bis_policy_rates=bis_rates,
        signals=[],
        regime='RISK_ON',
        regime_flags=[],
        timestamp='2026-01-01T00:00:00Z',
    )
    context.alerts = evaluate_alerts(context)
    return context
