# Agent Oculus V1 (`agent-oculus-v1`)

> [!CAUTION]
> **IMPORTANT: DISCLAIMER**
> This project is for **educational and experimental purposes only**. It is not intended for live trading or financial decision making.

A **Python finance worker** that fetches broker + macro context and exposes it as:
- a runnable script (`main.py`) for one-shot dumps or scheduled polling, and
- a set of importable primitives in `tools/` (good building blocks for an agent to call).

This is not a fully self-contained "AI agent" by itself. The intended use is: **Hermes (or any agent runtime) orchestrates these primitives**.

Current state (honest):
- ✅ Works as a CLI/script (`python main.py --run-once` or scheduler mode)
- ✅ Modules are cleanly separated (`core/`, `tools/`)
- ✅ Can be used by an agent today (via Hermes skill + native low-bloat toolset)
- ⚠️ Live execution is intentionally gated (default: disabled)

---

## What it does

- Pulls broker context from Public.com (portfolio snapshot, buying power, positions)
- Pulls macro context from WorldMonitor (fear/greed, market radar verdict, stablecoins, ETF flows, energy, chokepoints, trade policy, BIS rates)
- Produces JSON-able outputs suitable for:
  - an agent deciding a strategy
  - a monitor/alert loop
  - later execution wiring (still gated)

Safety note:
- Any execution pathway must remain **explicitly gated** via env/config.

---

## Repo layout

```text
agent-oculus-v1/
├── main.py                 # Entrypoint & APScheduler runtime
├── config.yaml             # System & threshold configuration
├── core/                   # Clients + analytics + schemas
├── tools/                  # Atomic async primitives
└── tests/
```

---

## Install & run (standalone)

### Prerequisites
- Python 3.11+
- Git

### Setup
```bash
git clone <repository-url>
cd agent-oculus-v1
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .[dev]
cp .env.example .env
```

### WorldMonitor dependency
This repo expects a WorldMonitor instance for macro signals.

Local dev server:
```bash
git clone https://github.com/koala73/worldmonitor.git ../worldmonitor
cd ../worldmonitor
npm install
npm run dev:finance
```

Then set in `.env` (back in this repo):
- `WM_BASE_URL=http://localhost:8000` (or whatever your WM uses)

### Environment variables
Edit `.env`:
- `PUBLIC_ACCESS_TOKEN` (required for broker data)
- `WM_BASE_URL` (required for macro signals)
- Optional: `FINNHUB_API_KEY`, `EIA_API_KEY`
- `EXECUTION_ENABLED=false` (keep false unless you *really* mean it)

### Run
```bash
# One-shot (prints JSON)
python main.py --run-once

# Long-running scheduler worker
python main.py

# Tests
pytest -v
```

---

## Use it with Hermes Agent (recommended)

There are two integration tiers:

### Tier 1 (works everywhere): Hermes runs the script via terminal
1) Start Hermes in this repo:
```bash
cd /path/to/agent-oculus-v1
hermes
```

2) Ask:
- "Run `python main.py --run-once` and summarize the portfolio + macro context."

### Tier 2 (best practice, low-bloat): native Hermes tools + /agent launcher
This repo ships:
- a Hermes skill that scope-locks the agent and maps intents like "check portfolio"
- an agent-pack manifest so you can launch it via Hermes `/agent`

Install:
```bash
# from repo root
./scripts/install_oculus_skill.sh
./scripts/install_agent_pack.sh

# one-time (gives Oculus its own memory/config boundary)
hermes profile create oculus
```

Usage:
1) Open Hermes anywhere
2) Run:
- `/agent oculus`

What happens:
- Hermes relaunches into this repo + profile and preloads the `oculus` skill.

Native tools (low-bloat):
- `oculus_healthcheck` (workdir + env sanity)
- `oculus_get_context` (portfolio + macro + derived signals)

Note:
- The native toolset lives in Hermes core (not in this repo). If you are not on the patched Hermes build, Tier 2 won’t be available.

### Config: OCULUS_WORKDIR
If your repo path differs from what Hermes expects, set:
- `OCULUS_WORKDIR=/absolute/path/to/agent-oculus-v1`

Best place to set it:
- in the `oculus` Hermes profile env file (`hermes config env-path` while using profile `oculus`).

---

## If you’re building an agent on top of this

Treat this repo as a reliable “finance context substrate”. The agent layer should:
- call the primitives (or `oculus_get_context`)
- decide strategy
- (later) produce an OrderIntent-style output
- keep execution gated

See also: `ai_setup.md`.
