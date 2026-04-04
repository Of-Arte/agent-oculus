from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class MockResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None, text: str | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self._text = text if text is not None else ('{}' if payload is None else 'payload')
        self.request = None

    @property
    def text(self) -> str:
        return self._text

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError(
                f'HTTP {self.status_code}',
                request=self.request,
                response=self,
            )


class AsyncMockHttpClient:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def request(self, method: str, url: str, params: dict[str, Any] | None = None, json: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> MockResponse:
        self.calls.append({
            'method': method,
            'url': url,
            'params': params,
            'json': json,
            'headers': headers,
        })
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        item.request = type('Request', (), {'method': method, 'url': url})()
        return item

    async def aclose(self) -> None:
        return None


class MockSdkTransport:
    def __init__(self, *, portfolio: dict[str, Any] | None = None, quotes: dict[str, Any] | None = None, chain: dict[str, Any] | None = None, orders: dict[str, Any] | None = None) -> None:
        self.portfolio = portfolio or {}
        self.quotes = quotes or {}
        self.chain = chain or {}
        self.orders = orders or {}
        self.calls: list[tuple[str, Any]] = []

    async def get_portfolio(self) -> dict[str, Any]:
        self.calls.append(('get_portfolio', None))
        return self.portfolio

    async def get_orders(self) -> dict[str, Any]:
        self.calls.append(('get_orders', None))
        return self.orders

    async def get_quotes(self, symbols: list[str], instrument_type: str) -> dict[str, Any]:
        self.calls.append(('get_quotes', {'symbols': symbols, 'instrument_type': instrument_type}))
        return self.quotes

    async def get_option_expirations(self, underlying_symbol: str) -> dict[str, Any]:
        self.calls.append(('get_option_expirations', underlying_symbol))
        return {'expirations': []}

    async def get_option_chain(self, underlying_symbol: str, expiration: str | None = None) -> dict[str, Any]:
        self.calls.append(('get_option_chain', {'symbol': underlying_symbol, 'expiration': expiration}))
        return self.chain

    async def place_order(self, order_payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(('place_order', order_payload))
        return {'submitted': True}

    async def close(self) -> None:
        return None


@pytest.fixture
def base_config() -> dict[str, Any]:
    return {
        'version': '0.1.0',
        'public': {
            'base_url': 'https://public.invalid',
            'timeout_seconds': 1,
            'retry': {
                'max_attempts': 3,
                'base_delay_seconds': 0,
                'max_delay_seconds': 0,
                'jitter_seconds': 0,
            },
            'routes': {
                'account': '/account',
                'portfolio_v2': '/userapigateway/trading/{account_id}/portfolio/v2',
                'quotes': '/quotes/{account_id}',
                'expirations': '/expirations',
                'chain': '/chain',
            },
        },
        'worldmonitor': {
            'base_url': 'https://worldmonitor.invalid',
            'timeout_seconds': 1,
            'retry': {
                'max_attempts': 3,
                'base_delay_seconds': 0,
                'max_delay_seconds': 0,
                'jitter_seconds': 0,
            },
            'default_headers': {'Accept': 'application/json'},
            'routes': {
                'market': {
                    'fear_greed_index': '/api/market/v1/get-fear-greed-index',
                    'market_quotes': '/api/market/v1/list-market-quotes',
                    'stablecoin_markets': '/api/market/v1/list-stablecoin-markets',
                    'etf_flows': '/api/market/v1/list-etf-flows',
                },
                'economic': {
                    'macro_signals': '/api/economic/v1/get-macro-signals',
                    'bis_policy_rates': '/api/economic/v1/get-bis-policy-rates',
                    'bis_exchange_rates': '/api/economic/v1/get-bis-exchange-rates',
                    'bis_credit': '/api/economic/v1/get-bis-credit',
                    'energy_prices': '/api/economic/v1/get-energy-prices',
                    'crude_inventories': '/api/economic/v1/get-crude-inventories',
                },
                'supply_chain': {
                    'shipping_rates': '/api/supply-chain/v1/get-shipping-rates',
                    'chokepoint_status': '/api/supply-chain/v1/get-chokepoint-status',
                    'critical_minerals': '/api/supply-chain/v1/get-critical-minerals',
                    'shipping_stress': '/api/supply-chain/v1/get-shipping-stress',
                },
                'trade': {
                    'trade_restrictions': '/api/trade/v1/get-trade-restrictions',
                    'tariff_trends': '/api/trade/v1/get-tariff-trends',
                    'trade_flows': '/api/trade/v1/get-trade-flows',
                    'trade_barriers': '/api/trade/v1/get-trade-barriers',
                    'customs_revenue': '/api/trade/v1/get-customs-revenue',
                    'comtrade_flows': '/api/trade/v1/list-comtrade-flows',
                },
            },
        },
        'features': {
            'execution_enabled': False,
        },
        'thresholds': {
            'signal_score_alert': 0.7,
            'bearish_signal_alert_count': 2,
            'stablecoin_depeg_threshold': 0.01,
        },
    }
