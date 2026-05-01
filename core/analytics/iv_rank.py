from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import yfinance as yf

from core.schemas import IVRankResult


@dataclass(slots=True)
class _VolStats:
    low: float
    high: float
    last_rank_change_10d: float


class IVRankEngine:
    """Computes IV Rank + IV Percentile using yfinance price history.

    Method:
    - Fetch daily closes
    - Compute rolling 30d realized vol (annualized) as IV proxy distribution
    - Use current_iv (from live options chain) vs distribution for rank + percentile

    Cache:
    - in-memory per process
    - per symbol
    - invalidates after 15 minutes
    """

    def __init__(self, lookback_days: int = 252):
        self.lookback_days = int(lookback_days)
        self._cache: dict[str, tuple[float, float, datetime]] = {}
        self._stats_cache: dict[str, tuple[_VolStats, datetime]] = {}
        self._cache_ttl = timedelta(minutes=15)

    async def compute(self, symbol: str, current_iv: float) -> IVRankResult:
        symbol = symbol.upper().strip()
        now = datetime.now(timezone.utc)

        cached = self._cache.get(symbol)
        if cached is not None:
            iv_rank, iv_percentile, computed_at = cached
            if (now - computed_at) < self._cache_ttl:
                stats = self._stats_cache.get(symbol)
                low = stats[0].low if stats is not None else 0.0
                high = stats[0].high if stats is not None else 0.0
                vol_regime = self._regime_from_stats(iv_rank=iv_rank, stats=stats[0] if stats else None)
                return IVRankResult(
                    symbol=symbol,
                    current_iv=float(current_iv),
                    iv_rank=float(iv_rank),
                    iv_percentile=float(iv_percentile),
                    vol_regime=vol_regime,
                    lookback_days=self.lookback_days,
                    computed_at=computed_at,
                    low_52w=float(low),
                    high_52w=float(high),
                )

        iv_rank, iv_percentile, stats = await self._compute_fresh(symbol=symbol, current_iv=float(current_iv))
        self._cache[symbol] = (iv_rank, iv_percentile, now)
        self._stats_cache[symbol] = (stats, now)

        vol_regime = self._regime_from_stats(iv_rank=iv_rank, stats=stats)
        return IVRankResult(
            symbol=symbol,
            current_iv=float(current_iv),
            iv_rank=float(iv_rank),
            iv_percentile=float(iv_percentile),
            vol_regime=vol_regime,
            lookback_days=self.lookback_days,
            computed_at=now,
            low_52w=float(stats.low),
            high_52w=float(stats.high),
        )

    def _regime_from_stats(self, *, iv_rank: float, stats: _VolStats | None) -> str:
        base = self.classify(iv_rank)
        if stats is not None and abs(stats.last_rank_change_10d) > 10:
            return 'TRANSITIONAL'
        return base

    def _annualized_vol(self, prices: pd.Series, window: int = 30) -> pd.Series:
        """Log returns, rolling std, * sqrt(252)."""
        log_returns = np.log(prices).diff()
        rolling = log_returns.rolling(window=window).std()
        return rolling * np.sqrt(252)

    def classify(self, iv_rank: float) -> str:
        """Classify IV regime per ATHENA thresholds.

        Rapid-change TRANSITIONAL is detected in compute() using 10d rank delta.
        """
        if iv_rank >= 60:
            return 'HIGH_VOLATILITY'
        if iv_rank >= 40:
            return 'MEDIUM_VOLATILITY'
        return 'LOW_VOLATILITY'

    async def _compute_fresh(self, *, symbol: str, current_iv: float) -> tuple[float, float, _VolStats]:
        loop = asyncio.get_running_loop()

        def fetch_close_series() -> pd.Series:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='2y', interval='1d')
            if not isinstance(hist, pd.DataFrame) or 'Close' not in hist.columns:
                raise ValueError('yfinance history missing Close')
            closes = hist['Close'].dropna()
            if closes.empty:
                raise ValueError('empty close series')
            return closes

        closes: pd.Series = await loop.run_in_executor(None, fetch_close_series)

        vol_series = self._annualized_vol(closes, window=30).dropna()
        if len(vol_series) < max(self.lookback_days, 60):
            dist = vol_series
        else:
            dist = vol_series.iloc[-self.lookback_days :]

        dist = dist.replace([np.inf, -np.inf], np.nan).dropna()
        if dist.empty:
            low = high = 0.0
            iv_rank = 0.0
            iv_percentile = 0.0
            delta10 = 0.0
            return iv_rank, iv_percentile, _VolStats(low=low, high=high, last_rank_change_10d=delta10)

        low = float(dist.min())
        high = float(dist.max())

        if high == low:
            iv_rank = 0.0
            iv_percentile = 0.0
        else:
            iv_rank = (float(current_iv) - low) / (high - low) * 100.0
            iv_rank = float(max(0.0, min(100.0, iv_rank)))
            iv_percentile = float((dist < float(current_iv)).mean() * 100.0)

        # Approximate rapid-change using realized-vol rank movement over last 10 business days.
        if len(dist) >= 11 and high != low:
            ranks = (dist - low) / (high - low) * 100.0
            delta10 = float(ranks.iloc[-1] - ranks.iloc[-11])
        else:
            delta10 = 0.0

        return float(iv_rank), float(iv_percentile), _VolStats(low=low, high=high, last_rank_change_10d=delta10)
