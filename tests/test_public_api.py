from __future__ import annotations

import asyncio
import httpx

from core.exceptions import ExecutionDisabledError
from core.public_api.account import PublicAccountService
from core.public_api.client import PublicApiClient
from core.public_api.options import PublicOptionsService
from core.public_api.orders import PublicOrdersService
from conftest import AsyncMockHttpClient, MockResponse, MockSdkTransport


PORTFOLIO_PAYLOAD = {
    'accountId': 'acct-1',
    'accountType': 'INDIVIDUAL',
    'buyingPower': {
        'buyingPower': '1250.00',
        'cashOnlyBuyingPower': '400.00',
        'optionsBuyingPower': '850.00',
    },
    'equity': [
        {'amount': '2000.00'}
    ],
    'positions': [
        {
            'instrument': {'symbol': 'AAPL', 'name': 'Apple Inc.', 'type': 'EQUITY'},
            'quantity': '2',
            'currentValue': '400.00',
            'lastPrice': {'lastPrice': '200.00'},
            'instrumentGain': {'gainValue': '40.00', 'gainPercentage': '11.11'},
            'costBasis': {'totalCost': '360.00', 'unitCost': '180.00', 'gainValue': '40.00', 'gainPercentage': '11.11'},
        }
    ],
    'orders': [
        {
            'orderId': 'ord-1',
            'instrument': {'symbol': 'AAPL', 'type': 'EQUITY'},
            'type': 'LIMIT',
            'side': 'BUY',
            'status': 'OPEN',
            'quantity': '2',
            'limitPrice': '195.00',
            'filledQuantity': '0',
            'averagePrice': '',
            'createdAt': '2026-01-01T00:00:00Z',
            'closedAt': None,
        }
    ],
}


def test_public_client_bootstraps_account_id_once(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]}),
        ])
        client = PublicApiClient(base_config['public'], bearer_token='token-123', sdk_transport=MockSdkTransport(portfolio={}), bootstrap_http_client=bootstrap_http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        assert await client.fetch_account_id() == 'acct-123'
        assert await client.fetch_account_id() == 'acct-123'
        assert len(bootstrap_http.calls) == 1
        assert bootstrap_http.calls[0]['headers']['Authorization'] == 'Bearer token-123'
        await client.close()
    asyncio.run(scenario())


def test_public_client_retries_bootstrap_request(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([httpx.ConnectError('boom'), MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]})])
        client = PublicApiClient(base_config['public'], bearer_token='token-123', sdk_transport=MockSdkTransport(portfolio={}), bootstrap_http_client=bootstrap_http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        assert await client.fetch_account_id() == 'acct-123'
        assert len(bootstrap_http.calls) == 2
        await client.close()
    asyncio.run(scenario())


def test_get_portfolio_uses_confirmed_url(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-1'}]}),
            MockResponse(200, payload=PORTFOLIO_PAYLOAD),
        ])
        client = PublicApiClient(base_config['public'], bearer_token='token-123', sdk_transport=None, bootstrap_http_client=bootstrap_http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        payload = await client.get_portfolio()
        assert payload['accountId'] == 'acct-1'
        assert bootstrap_http.calls[1]['url'].endswith('/userapigateway/trading/acct-1/portfolio/v2')
        await client.close()
    asyncio.run(scenario())


def test_account_service_normalizes_portfolio_response(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-1'}]}),
            MockResponse(200, payload=PORTFOLIO_PAYLOAD),
            MockResponse(200, payload=PORTFOLIO_PAYLOAD),
            MockResponse(200, payload=PORTFOLIO_PAYLOAD),
        ])
        client = PublicApiClient(base_config['public'], bearer_token='token-123', sdk_transport=None, bootstrap_http_client=bootstrap_http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        service = PublicAccountService(client)
        snapshot = await service.get_account_snapshot()
        positions = await service.list_positions()
        orders = await service.list_orders()
        assert snapshot.account_id == 'acct-1'
        assert snapshot.buying_power == 1250.0
        assert snapshot.cash == 400.0
        assert snapshot.equity == 2000.0
        assert positions[0].symbol == 'AAPL'
        assert positions[0].quantity == 2.0
        assert positions[0].market_value == 400.0
        assert positions[0].average_cost == 180.0
        assert positions[0].unrealized_pnl == 40.0
        assert orders[0].order_id == 'ord-1'
        assert orders[0].raw['quantity'] == 2.0
        assert orders[0].raw['limitPrice'] == 195.0
        assert orders[0].raw['filledQuantity'] == 0.0
        assert orders[0].raw['averagePrice'] is None
        await client.close()
    asyncio.run(scenario())


def test_place_order_is_gated(base_config, monkeypatch):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([MockResponse(200, payload={'accounts': [{'accountId': 'acct-1'}]})])
        client = PublicApiClient(base_config['public'], bearer_token='token-123', sdk_transport=MockSdkTransport(), bootstrap_http_client=bootstrap_http, sleeper=lambda _: None, jitter_fn=lambda: 0)
        service = PublicOrdersService(client, base_config)
        monkeypatch.setenv('EXECUTION_ENABLED', 'false')
        try:
            await service.place_order({'symbol': 'AAPL'})
        except ExecutionDisabledError:
            assert True
        else:
            raise AssertionError('Expected ExecutionDisabledError when execution is disabled')
        await client.close()
    asyncio.run(scenario())


def test_greeks_cast_from_string(base_config):
    service = PublicOptionsService(PublicApiClient(base_config['public'], sdk_transport=MockSdkTransport(), bootstrap_http_client=AsyncMockHttpClient([]), sleeper=lambda _: None, jitter_fn=lambda: 0))
    contracts = service.normalize_chain('AAPL', {'contracts': [{'symbol': 'AAPL250117C00190000', 'optionType': 'CALL', 'strike': '190', 'bid': '4.10', 'ask': '4.30', 'last': '4.20', 'delta': '0.45', 'gamma': '0.10', 'theta': '-0.05', 'vega': '0.12', 'rho': '0.03', 'iv': '0.22'}]})
    assert contracts[0].delta == 0.45
    assert isinstance(contracts[0].delta, float)
    assert contracts[0].strike == 190.0
    assert contracts[0].iv == 0.22
