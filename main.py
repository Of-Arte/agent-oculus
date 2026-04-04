from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from core.public_api.client import PublicApiClient
from core.worldmonitor.client import WorldMonitorClient
from tools.get_macro_context import get_macro_context
from tools.get_portfolio_snapshot import get_portfolio_snapshot


def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


def mask_secret(value: str | None) -> str:
    if not value:
        return '<missing>'
    if len(value) <= 8:
        return '***'
    return value[:4] + '...' + value[-4:]


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    summary = {
        'public_base_url': config.get('public', {}).get('base_url', ''),
        'wm_base_url': os.getenv('WM_BASE_URL', ''),
        'execution_enabled': os.getenv('EXECUTION_ENABLED', 'false').strip().lower() == 'true',
        'public_token': mask_secret(os.getenv('PUBLIC_ACCESS_TOKEN')),
        'wm_key': mask_secret(os.getenv('WORLDMONITOR_API_KEY')),
    }
    return summary


def build_scheduler(config: dict[str, Any]) -> BackgroundScheduler:
    schedule = config.get('schedule', {})
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run(get_portfolio_snapshot()), 'interval', minutes=int(schedule.get('portfolio_snapshot_interval_minutes', 5)), id='portfolio_snapshot')
    scheduler.add_job(lambda: asyncio.run(get_macro_context()), 'interval', minutes=int(schedule.get('macro_context_interval_minutes', 15)), id='macro_context')
    scheduler.add_job(lambda: asyncio.run(get_macro_context()), 'interval', minutes=int(schedule.get('etf_flows_interval_minutes', 15)), id='etf_flows')
    scheduler.add_job(lambda: asyncio.run(get_macro_context()), 'interval', minutes=int(schedule.get('supply_chain_interval_minutes', 5)), id='supply_chain')
    scheduler.add_job(lambda: asyncio.run(get_portfolio_snapshot()), 'interval', minutes=int(schedule.get('options_refresh_interval_minutes', 15)), id='options_refresh')
    return scheduler


async def run_once() -> dict[str, Any]:
    portfolio = await get_portfolio_snapshot()
    macro = await get_macro_context()
    print('PORTFOLIO_SNAPSHOT:')
    print(json.dumps(portfolio if portfolio is not None else None, indent=2, default=str))
    print('MACRO_CONTEXT:')
    print(json.dumps(macro if macro is not None else None, indent=2, default=str))
    result = {'portfolio_snapshot': portfolio, 'macro_context': macro}
    print('RUN_ONCE_RESULT:')
    print(json.dumps(result, indent=2, default=str))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description='agent-finance runtime')
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--run-once', action='store_true')
    args = parser.parse_args()

    load_dotenv()

    config = load_config(args.config)
    summary = validate_config(config)
    print(json.dumps({'config_summary': summary}, indent=2))

    public_client = PublicApiClient(config.get('public', {}))
    wm_client = WorldMonitorClient()

    execution_state = 'execution ENABLED' if summary['execution_enabled'] else 'execution disabled'
    print(f'agent-finance ready | regime detection active | {execution_state}')

    if args.run_once:
        try:
            asyncio.run(run_once())
        finally:
            asyncio.run(public_client.close())
            asyncio.run(wm_client.close())
        return

    scheduler = build_scheduler(config)
    scheduler.start()
    if args.dry_run:
        scheduler.shutdown(wait=False)
        asyncio.run(public_client.close())
        asyncio.run(wm_client.close())
        return

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.shutdown(wait=False)
        asyncio.run(public_client.close())
        asyncio.run(wm_client.close())


if __name__ == '__main__':
    main()
