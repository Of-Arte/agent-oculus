from __future__ import annotations

import os
from typing import Any

from core.exceptions import ExecutionDisabledError
from core.public_api.client import PublicApiClient
from core.schemas import OrderRequest, OrderResult


class PublicOrdersService:
    def __init__(self, client: PublicApiClient, config: dict[str, Any]) -> None:
        self.client = client
        self.config = config

    async def list_orders(self) -> dict[str, Any]:
        return await self.client.get_orders()

    async def place_order(self, order_payload: dict[str, Any] | OrderRequest) -> OrderResult:
        enabled_in_env = os.getenv('EXECUTION_ENABLED', 'false').strip().lower() == 'true'
        enabled_in_config = bool(self.config.get('features', {}).get('execution_enabled', False))
        if not enabled_in_env or not enabled_in_config:
            raise ExecutionDisabledError('Order execution is disabled. Set EXECUTION_ENABLED=true and enable features.execution_enabled.')
        payload = order_payload.to_dict() if isinstance(order_payload, OrderRequest) else dict(order_payload)
        raw = await self.client.place_order(payload)
        return OrderResult(
            ok=True,
            order_id=str(raw.get('orderId') or raw.get('id') or '' ) or None,
            status=str(raw.get('status') or 'submitted'),
            raw=raw,
        )
