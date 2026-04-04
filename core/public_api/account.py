from __future__ import annotations

from typing import Any

from core.public_api.client import PublicApiClient
from core.schemas import AccountSnapshot, OrderResult, PortfolioSnapshot, PositionSnapshot, parse_float, utc_now_iso


class PublicAccountService:
    def __init__(self, client: PublicApiClient) -> None:
        self.client = client

    async def get_account(self) -> dict[str, Any]:
        return await self.client.get_account()

    async def get_portfolio(self) -> dict[str, Any]:
        return await self.client.get_portfolio()

    def _normalize_position(self, item: dict[str, Any]) -> PositionSnapshot:
        instrument = item.get('instrument', {}) or {}
        last_price = item.get('lastPrice', {}) or {}
        gain = item.get('instrumentGain', {}) or {}
        cost_basis = item.get('costBasis', {}) or {}
        metadata = dict(item)
        metadata['lastPrice'] = last_price
        metadata['instrumentGain'] = gain
        metadata['costBasis'] = cost_basis
        return PositionSnapshot(
            symbol=str(instrument.get('symbol', 'UNKNOWN')),
            asset_type=str(instrument.get('type', 'UNKNOWN')),
            quantity=parse_float(item.get('quantity')),
            market_value=parse_float(item.get('currentValue')),
            average_cost=parse_float(cost_basis.get('unitCost')) if cost_basis.get('unitCost') not in (None, '') else None,
            unrealized_pnl=parse_float(gain.get('gainValue')) if gain.get('gainValue') not in (None, '') else None,
            currency='USD',
            metadata=metadata,
        )

    def _normalize_order(self, item: dict[str, Any]) -> OrderResult:
        instrument = item.get('instrument', {}) or {}
        raw = dict(item)
        raw['instrument'] = instrument
        raw['quantity'] = parse_float(item.get('quantity'))
        raw['limitPrice'] = parse_float(item.get('limitPrice')) if item.get('limitPrice') not in (None, '') else None
        raw['filledQuantity'] = parse_float(item.get('filledQuantity')) if item.get('filledQuantity') not in (None, '') else None
        raw['averagePrice'] = parse_float(item.get('averagePrice')) if item.get('averagePrice') not in (None, '') else None
        return OrderResult(
            ok=True,
            order_id=str(item.get('orderId', '')) or None,
            status=str(item.get('status', '')) or None,
            raw=raw,
        )

    async def get_account_snapshot(self) -> AccountSnapshot:
        portfolio = await self.get_portfolio()
        buying_power = portfolio.get('buyingPower', {}) or {}
        return AccountSnapshot(
            account_id=str(portfolio.get('accountId', '')),
            buying_power=parse_float(buying_power.get('buyingPower')) if buying_power.get('buyingPower') not in (None, '') else None,
            cash=parse_float(buying_power.get('cashOnlyBuyingPower')) if buying_power.get('cashOnlyBuyingPower') not in (None, '') else None,
            equity=parse_float((portfolio.get('equity') or [{}])[0].get('amount')) if isinstance(portfolio.get('equity'), list) and portfolio.get('equity') else None,
            raw=portfolio,
        )

    async def list_positions(self) -> list[PositionSnapshot]:
        portfolio = await self.get_portfolio()
        return [self._normalize_position(item) for item in portfolio.get('positions', []) if isinstance(item, dict)]

    async def list_orders(self) -> list[OrderResult]:
        portfolio = await self.get_portfolio()
        return [self._normalize_order(item) for item in portfolio.get('orders', []) if isinstance(item, dict)]

    async def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        portfolio = await self.get_portfolio()
        buying_power = portfolio.get('buyingPower', {}) or {}
        positions = [self._normalize_position(item) for item in portfolio.get('positions', []) if isinstance(item, dict)]
        return PortfolioSnapshot(
            account_id=str(portfolio.get('accountId', '')),
            generated_at=utc_now_iso(),
            buying_power=parse_float(buying_power.get('buyingPower')) if buying_power.get('buyingPower') not in (None, '') else None,
            cash=parse_float(buying_power.get('cashOnlyBuyingPower')) if buying_power.get('cashOnlyBuyingPower') not in (None, '') else None,
            equity=parse_float((portfolio.get('equity') or [{}])[0].get('amount')) if isinstance(portfolio.get('equity'), list) and portfolio.get('equity') else None,
            positions=positions,
            raw=portfolio,
        )
