# Agent Oculus (agent-oculus)

Agent Oculus is an open-source **finance context worker**: it collects broker + macro context (Public.com + WorldMonitor) and returns structured outputs that an agent runtime (especially **Hermes Agent**) can use to make decisions.

This repository is intentionally **execution-safe by default**. It is designed for education/experimentation and for building agentic pipelines where *analysis and intent* are separated from *trade execution*.

---

## Disclaimer

This project is for **educational and experimental purposes only**. It is **not** financial advice and is not intended for live trading. Any execution pathway must remain explicitly gated.

---

## What you get

Core capabilities:
- Portfolio snapshot ingestion from **Public.com**
- Macro/regime context ingestion from **WorldMonitor**
- Normalized “signals” / context objects suitable for downstream strategy logic
- A standalone runtime (one-shot or scheduled polling)
- Hermes integration artifacts (skill + plugin toolpack + /agent launcher manifest)

Design goals:
- **Composable primitives**: functions under `tools/` are useful building blocks
- **Low tool-schema bloat**: Hermes integration exposes *two coarse tools* instead of dozens
- **Safety gates**: execution is disabled unless you explicitly enable it

---

## Repository layout

```
agent-oculus/
├── main.py                       # Entrypoint (one-shot + scheduler)
├── config.yaml                   # Thresholds/schedule config
├── core/                         # Clients + analytics + schemas
├── tools/                        # Atomic async primitives
- hermes/plugin/oculus/          # Hermes plugin toolpack (ships with repo)
- hermes/skills/oculus/SKILL.md   # Hermes skill (scope + intent mapping)
- hermes/agent-packs/oculus.yaml  # Hermes /agent pack manifest
- scripts/                        # Install helpers

---

## Quickstart (standalone)

### Prerequisites
- Python 3.11+
- Git
- WorldMonitor instance (local or hosted)

### Install

```bash
git clone https://github.com/Of-Arte/agent-oculus.git
cd agent-oculus
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .[dev]
cp .env.example .env
```

### Run WorldMonitor (local)

```bash
git clone https://github.com/koala73/worldmonitor.git ../worldmonitor
cd ../worldmonitor
npm install
npm run dev:finance
```

Then set in your `.env` (back in `agent-oculus/`):
- `WM_BASE_URL=http://localhost:8000` (adjust if needed)

### Configure environment

Edit `.env`:
- `PUBLIC_ACCESS_TOKEN` (required for broker data)
- `WM_BASE_URL` (required for macro)
- Optional: `FINNHUB_API_KEY`, `EIA_API_KEY`
- `EXECUTION_ENABLED=false` (keep false unless you explicitly intend otherwise)

### Run

```bash
# One-shot JSON dump
python main.py --run-once

# Long-running scheduler worker
python main.py

# Tests
pytest -v
```

---

## Hermes Agent integration (recommended)

Hermes is the intended UX: Oculus behaves like a selectable “agent pack” with a dedicated profile, a scope-locking skill, and a tiny (low-bloat) tool surface.

### Fast path: one command install

```bash
./scripts/install_agent_pack.sh
```

This installs, configures, and (when possible) auto-enables:
- Skill → `~/.hermes/skills/oculus/`
- Plugin → `~/.hermes/plugins/oculus/`
- Skin → `~/.hermes/skins/oculus.yaml` (optional UI polish)
- Agent pack manifest → `~/.hermes/agent-packs/oculus.yaml`
- Profile → creates `oculus` profile if missing
- Profile env → sets `OCULUS_WORKDIR` automatically

### Run
1) Start Hermes:
   - `hermes`
2) In-session:
   - `/agent oculus`

If you don’t see the tools, enable them in-session:
- `/tools` → enable toolset `oculus`

### What Oculus adds to Hermes (low-bloat by design)
Tools (2 total):
- `oculus_healthcheck` — verify env/workdir/safety gate
- `oculus_get_context` — fetch portfolio + WorldMonitor macro context + derived signals

Skill:
- Scope lock + intent mapping (e.g. “check portfolio” → fetch context)

Skin:
- Optional “Oculus” skin to match Hermes’ vibe:
  - `hermes config set display.skin oculus`

### Fallback (Tier 1): Hermes drives the repo via terminal
Works everywhere, no plugin required:
- Run `python main.py --run-once` via Hermes terminal tool and summarize output.

---

## Safety model

- `EXECUTION_ENABLED` is expected to remain `false` by default.
- This repo is optimized for **context generation** and **agent decision support**, not unattended execution.

---

## Contributing

PRs welcome. Please:
- keep tool surfaces minimal (avoid adding many small tools unless necessary)
- keep schemas short (tool schema text is prompt context)
- don’t weaken execution safety gates
- add tests for any data-shape contracts you introduce

---

## License

MIT (see `LICENSE` if present in this repository). If missing, treat as all-rights-reserved until added.
