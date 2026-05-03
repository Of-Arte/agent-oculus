# Agent Oculus V1 (`agent-oculus-v1`)

> [!CAUTION]
> **IMPORTANT: DISCLAIMER**
> This project is for **educational and experimental purposes only**. It is not intended for live trading or financial decision making.

A **Python finance worker** that fetches broker + macro context and exposes it as:
- a runnable script (`main.py`) for one-shot dumps or scheduled polling, and
- a set of importable “tool-shaped” functions in `tools/` (good primitives for an agent to call).

If you came here expecting a fully self-contained “AI agent”: it’s not that (yet). Today it’s closer to a **library + worker runtime** that a higher-level agent (especially Hermes Agent) can orchestrate.

Current state (honest):
- ✅ Works as a CLI/script (`python main.py --run-once` or `python main.py` scheduler)
- ✅ Code is structured into modules (`core/`, `tools/`)
- ✅ Designed to be *agent-callable* (atomic functions in `tools/`)
- ⚠️ Hermes integration is not “plug-and-play install” from this repo alone (see Roadmap)

---

## What it does

- Pulls broker context from Public.com (portfolio snapshot, etc.)
- Pulls macro context from WorldMonitor (fear/greed, market radar, energy, supply chain, trade policy, etc.)
- Produces JSON-able outputs suitable for:
  - an agent deciding a strategy
  - a monitor/alert loop
  - later execution wiring (currently gated)

Safety note:
- Any execution pathway must remain **explicitly gated** via env/config (default: no execution).

---

## Repo layout

```text
agent-oculus-v1/
├── main.py                 # Entrypoint & APScheduler runtime
├── config.yaml             # System & threshold configuration
├── core/                   # Clients + analytics + schemas
├── tools/                  # Atomic functions (good building blocks for agents)
└── tests/
```

---

## Install & run (current, standalone)

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

## Use it with Hermes Agent (current state)

You have two workable integration modes *today*:

### Mode A (zero integration): Hermes orchestrates the script via terminal
This is the fastest path for users.

1) Install Hermes Agent (if not already):
- https://hermes-agent.nousresearch.com/docs/

2) Start Hermes in this repo:
```bash
cd /path/to/agent-oculus-v1
hermes
```

3) Ask Hermes to run one-shot context:
- “Run `python main.py --run-once` and summarize the macro + portfolio context.”

This works because Hermes can use its `terminal` toolset to run commands in-repo.

### Mode B (recommended next step): expose `tools/*` as Hermes-callable tools
This repo already has “tool-shaped” functions under `tools/`.
To make them *actual Hermes tools* you need a registration layer so Hermes can discover and call them.

Status today:
- Some of these tools have been manually registered in a Hermes backend in at least one dev setup.
- This repo does not yet ship a clean, user-installable integration artifact.

---

## Roadmap: make this an easy install for agentic runtimes (especially Hermes)

Goal: a user should be able to do:
1) `pip install agent-oculus-v1` (or clone)
2) `hermes tools enable oculus` (or similar)
3) Hermes can call `get_macro_context`, `get_portfolio_snapshot`, `get_options_chain`, etc.

I’d implement it in this order:

1) **Fix “script vs library” correctness**
   - Ensure `main.py` always runs (it currently needs a couple correctness/packaging passes)
   - Add a stable CLI entrypoint (e.g. `oculus run --run-once`)

2) **Pick an integration packaging strategy (best-practice)**
   - Best practice for Hermes is either:
     - **MCP server** (clean boundary, easiest distribution, no Hermes core PR needed), or
     - **Hermes plugin/toolpack** (tighter UX, but depends on Hermes plugin loading conventions)

3) **Ship a “one command” Hermes profile launcher**
   - Provide `scripts/launch_oculus_hermes.sh` that:
     - creates/uses a dedicated Hermes profile
     - starts Hermes from repo root
     - documents required env vars

4) **Optional: upstream UX (“/agent” choice)**
   - True “/agent” selection is a Hermes feature request/PR: add a slash command + registry entry that enumerates installed agent packs.
   - This repo can provide the metadata contract Hermes would need (name, description, toolset, env requirements).

---

## If you’re building an agent on top of this

Treat this repo as a reliable “finance context substrate”. The agent layer should:
- call the primitives in `tools/`
- decide strategy
- (later) produce an OrderIntent-style output
- keep execution gated

See also: `ai_setup.md` (instructions for AI coding agents working on this repo).

