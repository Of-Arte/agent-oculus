from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml

from core.public_api.client import PublicApiClient
from core.public_api.options import PublicOptionsService

# TODO: HERMES REGISTRATION — wire this tool through tools/registry.py -> model_tools.py -> toolsets.py.


def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


async def get_options_chain(symbol: str, expiration: str | None = None, config_path: str | Path = 'config.yaml') -> dict:
    config = load_config(config_path)
    client = PublicApiClient(config['public'])
    try:
        chain = await PublicOptionsService(client).get_normalized_chain(symbol, expiration)
        return chain.to_dict()
    finally:
        await client.close()


def run(symbol: str, expiration: str | None = None, config_path: str | Path = 'config.yaml') -> dict:
    return asyncio.run(get_options_chain(symbol, expiration, config_path))
