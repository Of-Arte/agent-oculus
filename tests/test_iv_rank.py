from __future__ import annotations

import asyncio
from datetime import timedelta


def test_iv_rank_high(monkeypatch):
    async def scenario():
        from core.analytics.iv_rank import IVRankEngine

        engine = IVRankEngine(lookback_days=252)

        call_count = {'history': 0}

        class StubTicker:
            def history(self, *args, **kwargs):
                call_count['history'] += 1
                import pandas as pd
                idx = pd.date_range('2024-01-01', periods=300, freq='B')
                return pd.DataFrame({'Close': [100.0] * len(idx)}, index=idx)

        monkeypatch.setattr('yfinance.Ticker', lambda symbol: StubTicker())

        import pandas as pd

        def stub_vol(_prices: pd.Series, window: int = 30) -> pd.Series:
            # 252d distribution roughly 0.10 → 0.50
            idx = _prices.index
            values = [0.10 + (0.40 * i / (len(idx) - 1)) for i in range(len(idx))]
            return pd.Series(values, index=idx)

        monkeypatch.setattr(engine, '_annualized_vol', stub_vol)

        result = await engine.compute('SPY', current_iv=0.45)
        assert result.iv_rank > 60
        assert result.vol_regime == 'HIGH_VOLATILITY'
        assert result.iv_percentile > 60
        assert call_count['history'] == 1

    asyncio.run(scenario())


def test_iv_rank_low(monkeypatch):
    async def scenario():
        from core.analytics.iv_rank import IVRankEngine

        engine = IVRankEngine(lookback_days=252)

        class StubTicker:
            def history(self, *args, **kwargs):
                import pandas as pd
                idx = pd.date_range('2024-01-01', periods=300, freq='B')
                return pd.DataFrame({'Close': [100.0] * len(idx)}, index=idx)

        monkeypatch.setattr('yfinance.Ticker', lambda symbol: StubTicker())

        import pandas as pd

        def stub_vol(_prices: pd.Series, window: int = 30) -> pd.Series:
            idx = _prices.index
            values = [0.10 + (0.40 * i / (len(idx) - 1)) for i in range(len(idx))]
            return pd.Series(values, index=idx)

        monkeypatch.setattr(engine, '_annualized_vol', stub_vol)

        result = await engine.compute('SPY', current_iv=0.12)
        assert result.iv_rank < 40
        assert result.vol_regime == 'LOW_VOLATILITY'

    asyncio.run(scenario())


def test_strategy_selector_premium_selling():
    from core.analytics.strategy_selector import select_strategy

    rec = select_strategy(
        iv_rank=75,
        regime='RISK_OFF',
        dte_available=45,
        buying_power=5000,
        net_delta=0.0,
    )
    assert rec.blocked is False
    assert rec.strategy_type == 'iron_condor'


def test_strategy_selector_risk_on_bull_put():
    from core.analytics.strategy_selector import select_strategy

    rec = select_strategy(
        iv_rank=75,
        regime='RISK_ON',
        dte_available=45,
        buying_power=5000,
        net_delta=0.0,
    )
    assert rec.blocked is False
    assert rec.strategy_type == 'bull_put_spread'


def test_strategy_selector_medium_iv_calendar():
    from core.analytics.strategy_selector import select_strategy

    rec = select_strategy(
        iv_rank=50,
        regime='TRANSITIONAL',
        dte_available=45,
        buying_power=5000,
        net_delta=0.0,
    )
    assert rec.strategy_type == 'calendar_spread'


def test_strategy_selector_low_iv_debit():
    from core.analytics.strategy_selector import select_strategy

    rec = select_strategy(
        iv_rank=30,
        regime='RISK_ON',
        dte_available=45,
        buying_power=5000,
        net_delta=0.0,
    )
    assert rec.strategy_type == 'debit_spread'


def test_strategy_selector_blocked_dte():
    from core.analytics.strategy_selector import select_strategy

    rec = select_strategy(
        iv_rank=75,
        regime='RISK_OFF',
        dte_available=15,
        buying_power=5000,
        net_delta=0.0,
    )
    assert rec.blocked is True
    assert rec.blocked_reason


def test_strategy_selector_blocked_bp():
    from core.analytics.strategy_selector import select_strategy

    rec = select_strategy(
        iv_rank=75,
        regime='RISK_OFF',
        dte_available=45,
        buying_power=300,
        net_delta=0.0,
    )
    assert rec.blocked is True
    assert rec.blocked_reason


def test_cache_invalidation(monkeypatch):
    async def scenario():
        from core.analytics.iv_rank import IVRankEngine

        engine = IVRankEngine(lookback_days=252)

        call_count = {'history': 0}

        class StubTicker:
            def history(self, *args, **kwargs):
                call_count['history'] += 1
                import pandas as pd
                idx = pd.date_range('2024-01-01', periods=300, freq='B')
                return pd.DataFrame({'Close': [100.0] * len(idx)}, index=idx)

        monkeypatch.setattr('yfinance.Ticker', lambda symbol: StubTicker())

        import pandas as pd

        def stub_vol(_prices: pd.Series, window: int = 30) -> pd.Series:
            idx = _prices.index
            values = [0.10 + (0.40 * i / (len(idx) - 1)) for i in range(len(idx))]
            return pd.Series(values, index=idx)

        monkeypatch.setattr(engine, '_annualized_vol', stub_vol)

        await engine.compute('SPY', current_iv=0.30)
        await engine.compute('SPY', current_iv=0.31)
        assert call_count['history'] == 1, 'expected cache hit within 15 minutes'

        iv_rank, iv_pct, computed_at = engine._cache['SPY']
        engine._cache['SPY'] = (iv_rank, iv_pct, computed_at - timedelta(minutes=16))

        await engine.compute('SPY', current_iv=0.32)
        assert call_count['history'] == 2, 'expected recompute after 15 minutes'

    asyncio.run(scenario())


def test_vol_regime_classification():
    from core.analytics.iv_rank import IVRankEngine

    engine = IVRankEngine()
    assert engine.classify(60.0) == 'HIGH_VOLATILITY'
    assert engine.classify(59.9) == 'MEDIUM_VOLATILITY'
    assert engine.classify(40.0) == 'MEDIUM_VOLATILITY'
    assert engine.classify(39.9) == 'LOW_VOLATILITY'
