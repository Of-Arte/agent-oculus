from __future__ import annotations

import asyncio

from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WorldMonitorClient
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from conftest import AsyncMockHttpClient, MockResponse


def test_wm_client_no_auth_header_when_key_not_set(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        monkeypatch.delenv('WORLDMONITOR_API_KEY', raising=False)
        http = AsyncMockHttpClient([MockResponse(200, payload={'ok': True})])
        client = WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        await client.request('GET', '/api/market/v1/get-fear-greed-index')
        assert 'X-WorldMonitor-Key' not in http.calls[0]['headers']
        await client.close()
    asyncio.run(scenario())


def test_wm_client_auth_header_when_key_set(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        monkeypatch.setenv('WORLDMONITOR_API_KEY', 'test-key')
        http = AsyncMockHttpClient([MockResponse(200, payload={'ok': True})])
        client = WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        await client.request('GET', '/api/market/v1/get-fear-greed-index')
        assert http.calls[0]['headers']['X-WorldMonitor-Key'] == 'test-key'
        await client.close()
    asyncio.run(scenario())


def test_retry_on_503(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        http = AsyncMockHttpClient([
            MockResponse(503, payload={'error': 'temporary'}),
            MockResponse(503, payload={'error': 'temporary'}),
            MockResponse(200, payload={'ok': True}),
        ])
        client = WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        payload = await client.request('GET', '/api/market/v1/get-fear-greed-index')
        assert payload == {'ok': True}
        assert len(http.calls) == 3
        await client.close()
    asyncio.run(scenario())


def test_stablecoin_depeg_flag(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        http = AsyncMockHttpClient([
            MockResponse(200, payload={'timestamp': '2026-01-01T00:00:00Z', 'stablecoins': [{'symbol': 'USDT', 'price': 0.994, 'deviation': -0.006, 'pegStatus': 'DEPEG'}]})
        ])
        service = WorldMonitorStablecoinService(WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0))
        items = await service.list_stablecoin_markets()
        assert items[0].is_depegged is True
    asyncio.run(scenario())


def test_stablecoin_no_depeg_flag(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        http = AsyncMockHttpClient([
            MockResponse(200, payload={'timestamp': '2026-01-01T00:00:00Z', 'stablecoins': [{'symbol': 'USDC', 'price': 0.998, 'deviation': -0.002, 'pegStatus': 'STABLE'}]})
        ])
        service = WorldMonitorStablecoinService(WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0))
        items = await service.list_stablecoin_markets()
        assert items[0].is_depegged is False
    asyncio.run(scenario())


def test_fear_greed_normalization(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        http = AsyncMockHttpClient([
            MockResponse(200, payload={'compositeScore': '62', 'compositeLabel': 'Greed', 'seededAt': '2026-01-01T00:00:00Z'})
        ])
        service = WorldMonitorMarketRadarService(WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0))
        item = await service.get_fear_greed()
        assert item.value == 62
        assert isinstance(item.value, int)
    asyncio.run(scenario())


def test_market_radar_verdict_buy(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        payload = {
            'timestamp': '2026-01-01T00:00:00Z',
            'signals': {
                'liquidity': {'status': 'BULLISH'},
                'flowStructure': {'status': 'BULLISH'},
                'macroRegime': {'status': 'BULLISH'},
                'technicalTrend': {'status': 'BULLISH', 'mayerMultiple': 1.3},
                'hashRate': {'status': 'BULLISH'},
                'priceMomentum': {'status': 'BEARISH'},
                'fearGreed': {'status': 'BEARISH'},
            },
        }
        http = AsyncMockHttpClient([MockResponse(200, payload=payload)])
        service = WorldMonitorMarketRadarService(WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0))
        verdict = await service.get_market_radar_verdict()
        assert verdict.verdict == 'BUY'
    asyncio.run(scenario())


def test_market_radar_verdict_cash(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        payload = {
            'timestamp': '2026-01-01T00:00:00Z',
            'signals': {
                'liquidity': {'status': 'BULLISH'},
                'flowStructure': {'status': 'BULLISH'},
                'macroRegime': {'status': 'BULLISH'},
                'technicalTrend': {'status': 'BEARISH'},
                'hashRate': {'status': 'BEARISH'},
                'priceMomentum': {'status': 'BEARISH'},
                'fearGreed': {'status': 'BEARISH'},
            },
        }
        http = AsyncMockHttpClient([MockResponse(200, payload=payload)])
        service = WorldMonitorMarketRadarService(WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0))
        verdict = await service.get_market_radar_verdict()
        assert verdict.verdict == 'CASH'
    asyncio.run(scenario())


def test_chokepoint_score_normalization(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        http = AsyncMockHttpClient([
            MockResponse(200, payload={'chokepoints': [{'name': 'Suez Canal', 'disruptionScore': '72.5', 'status': 'HIGH'}]})
        ])
        service = WorldMonitorSupplyChainService(WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0))
        items = await service.get_chokepoint_status()
        assert items[0].score == 72.5
        assert isinstance(items[0].score, float)
    asyncio.run(scenario())


def test_unknown_field_ignored(monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv('WM_BASE_URL', 'https://wm.invalid')
        http = AsyncMockHttpClient([
            MockResponse(200, payload={'timestamp': '2026-01-01T00:00:00Z', 'stablecoins': [{'symbol': 'USDC', 'price': 1.0, 'deviation': 0.0, 'pegStatus': 'STABLE', 'unexpected': 'ignored'}]})
        ])
        service = WorldMonitorStablecoinService(WorldMonitorClient(http_client=http, sleeper=lambda _: None, jitter_fn=lambda: 0))
        items = await service.list_stablecoin_markets()
        assert len(items) == 1
        assert items[0].symbol == 'USDC'
    asyncio.run(scenario())
