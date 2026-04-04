# agent-finance

Read-first finance service scaffold for Hermes.

What it does
- pulls brokerage/account context from Public.com
- pulls macro and market context from WorldMonitor
- normalizes both into a shared signal schema
- prepares Hermes event-bus and ATHENA-ready output

Public transport
- prefers the official Public Python SDK: `publicdotcom-py`
- bootstraps `accountId` on first use from `GET /userapigateway/trading/account`
- caches the discovered account ID on the client instance

What it does not do by default
- no live order execution
- `place_order` exists but returns a disabled runtime error unless `EXECUTION_ENABLED=true`

Run
```bash
python main.py --mode describe-schedule
python main.py --mode run-once
```

Environment variables
- `PUBLIC_ACCESS_TOKEN` — Public.com bearer token / API secret used for bootstrap and SDK auth
- `EXECUTION_ENABLED` — set to `true` to unlock write paths
- `WORLDMONITOR_API_KEY` — optional header value if your WorldMonitor deployment is gated

Test
```bash
python -m pytest
```
