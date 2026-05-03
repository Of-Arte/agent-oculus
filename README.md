# Agent Oculus (agent-oculus)

Agent Oculus is an open-source **finance context worker**.
It pulls **portfolio + options data (Public.com)** and **macro/regime context (WorldMonitor)** and returns structured outputs that an agent runtime (especially **Hermes Agent**) can use for decisions.

This repo is intentionally **execution-safe by default**: it focuses on **context + signals**, not unattended trading.

---

## Quick setup (recommended: Hermes)

If you’re using Hermes Agent, Oculus is meant to feel like an “agent pack”: one command install, then `/agent oculus`.

### Install (one command)

```bash
git clone https://github.com/Of-Arte/agent-oculus.git
cd agent-oculus
./scripts/install_agent_pack.sh
```

That installer will (when Hermes is installed) set everything up for you:
- Skill → `~/.hermes/skills/oculus/`
- Plugin → `~/.hermes/plugins/oculus/`
- Agent pack manifest → `~/.hermes/agent-packs/oculus.yaml`
- Profile → creates `oculus` profile if missing
- Profile env → sets `OCULUS_WORKDIR` automatically
- Optional UI polish → installs `~/.hermes/skins/oculus.yaml`

### Run

1) Start Hermes:
   - `hermes`
2) In-session:
   - `/agent oculus`

If you don’t see the tools:
- `/tools` → enable toolset `oculus`

Optional UI polish:
- `hermes config set display.skin oculus`

### What Oculus adds to Hermes (low-bloat by design)

Tools (2 total):
- `oculus_healthcheck` — verify env/workdir/safety gate
- `oculus_get_context` — fetch portfolio + macro context + derived signals

Skill:
- Scope lock + intent mapping (so Hermes stays on-task and uses the right tools)

---

## Quick setup (standalone Python)

### Prereqs
- Python 3.11+
- A WorldMonitor instance (local or hosted)
- A Public.com access token

### Install

```bash
git clone https://github.com/Of-Arte/agent-oculus.git
cd agent-oculus
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .[dev]
cp .env.example .env
```

### Configure

Edit `.env`:
- `PUBLIC_ACCESS_TOKEN` (required for broker data)
- `WM_BASE_URL` (required for macro)
- `EXECUTION_ENABLED=false` (keep false unless you explicitly intend otherwise)

Optional:
- `WORLDMONITOR_API_KEY`
- `FINNHUB_API_KEY`, `EIA_API_KEY`

### Run (one-shot)

```bash
python main.py --run-once
```

This prints `PORTFOLIO_SNAPSHOT`, `MACRO_CONTEXT`, and `RUN_ONCE_RESULT` as JSON.

---

## Scheduled worker (polling mode)

Oculus can also run as a **long-running scheduled worker**.
This is useful when you want a continuously refreshed “context cache” in memory for repeated calls (e.g. interactive Hermes sessions, dashboards, or your own downstream pipeline).

### Run the worker

```bash
# Starts an APScheduler loop and refreshes data on an interval
python main.py
```

What it does (today):
- Runs periodic jobs (portfolio snapshot / macro context / option refresh)
- Prints a startup config summary + “ready” banner
- Keeps refreshed results in-process (in-memory cache inside the worker)

What it does NOT do (yet):
- It does not publish to Redis, write to disk, or push to webhooks by default.
  If you want that, we can add a clean “sink” interface (file/redis/webhook) without turning this into a bloated agent framework.

### Configure the schedule

Intervals live in `config.yaml` under `schedule:`

```yaml
schedule:
  portfolio_snapshot_interval_minutes: 5
  macro_context_interval_minutes: 15
  options_refresh_interval_minutes: 15
```

Tip: you can sanity-check config/env without running the loop:

```bash
python main.py --dry-run
```

### Production-ish ways to run it

Pick one:
- `systemd` service
- `pm2` (works fine for python processes)
- Docker (simple container + restart policy)

---

## Repository layout

```
agent-oculus/
├── main.py                       # Entrypoint (one-shot + scheduled worker)
├── config.yaml                   # Thresholds + schedule config
├── core/                         # Clients + analytics + schemas
├── tools/                        # Atomic async primitives
├── hermes/
│   ├── plugin/oculus/            # Hermes plugin toolpack (ships with repo)
│   ├── skills/oculus/SKILL.md    # Hermes skill (scope + intent mapping)
│   ├── skins/oculus.yaml         # Optional Hermes skin
│   └── agent-packs/oculus.yaml   # Hermes /agent pack manifest
└── scripts/                      # Install helpers
```

---

## Safety model

- `EXECUTION_ENABLED` is expected to remain `false` by default.
- This repo is optimized for **context generation** and **agent decision support**, not unattended execution.

---

## Disclaimer

This project is for **educational and experimental purposes only**. It is **not** financial advice and is not intended for live trading. Any execution pathway must remain explicitly gated.

---

## Contributing

PRs welcome. Please:
- keep tool surfaces minimal (tool schema text is prompt context)
- don’t weaken execution safety gates
- add tests for any data-shape contracts you introduce

---

## License

MIT (see `LICENSE` if present in this repository). If missing, treat as all-rights-reserved until added.
