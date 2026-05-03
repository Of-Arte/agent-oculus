from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import yaml

from core.exceptions import ExecutionDisabledError
from core.public_api.client import PublicApiClient
from core.public_api.orders import PublicOrdersService
from core.schemas import OrderRequest

def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


async def place_order(order_request: dict, config_path: str | Path = 'config.yaml') -> dict:
    config = load_config(config_path)
    # Fail fast — do not construct any client if execution is globally disabled.
    enabled_in_env = os.getenv('EXECUTION_ENABLED', 'false').strip().lower() == 'true'
    enabled_in_config = bool(config.get('features', {}).get('execution_enabled', False))
    if not enabled_in_env or not enabled_in_config:
        raise ExecutionDisabledError(
            'Order execution is disabled. Set EXECUTION_ENABLED=true and '
            'features.execution_enabled: true in config.yaml.'
        )
    required = ['symbol', 'side', 'quantity', 'order_type']
    missing = [field for field in required if field not in order_request]
    if missing:
        raise ValueError(f'Missing required order fields: {", ".join(missing)}')
    client = PublicApiClient(config['public'])
    try:
        service = PublicOrdersService(client, config)
        result = await service.place_order(OrderRequest(**order_request))
        return result.to_dict()
    finally:
        await client.close()


def run(order_request: dict, config_path: str | Path = 'config.yaml') -> dict:
    return asyncio.run(place_order(order_request, config_path))
