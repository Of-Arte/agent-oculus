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
├── .hermes/plugins/oculus/        # Hermes plugin toolpack (ships with repo)
├── hermes-skill-oculus.md         # Hermes skill (scope + intent mapping)
├── oculus.agent-pack.yaml         # Hermes /agent pack manifest
└── scripts/                       # Install helpers
```

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

You have two tiers:

### Tier 1: Hermes drives the repo via terminal
This works on any Hermes install.

```bash
cd /path/to/agent-oculus
hermes
```

Then ask Hermes to run:
- `python main.py --run-once`

### Tier 2: Best practice (native tools, low-bloat) + `/agent` launcher
This repo ships Hermes integration artifacts:
- **Skill**: scope lock + intent mapping (“check portfolio” → fetch context)
- **Plugin toolpack**: registers **two coarse tools** to avoid tool-schema bloat
  - `oculus_healthcheck`
  - `oculus_get_context`
- **Agent pack manifest**: allows launching via Hermes `/agent`

Install everything (one command):

```bash
./scripts/install_agent_pack.sh
```

What the script does:
- installs the skill into `~/.hermes/skills/oculus/`
- installs the plugin into `~/.hermes/plugins/oculus/`
- enables the plugin (if `hermes` is available)
- creates the `oculus` Hermes profile (if missing)
- sets `OCULUS_WORKDIR` in the oculus profile env to this repo path
- installs the `/agent` manifest into `~/.hermes/agent-packs/`

Then:
1) start Hermes anywhere: `hermes`
2) launch: `/agent oculus`

Note:
- If the oculus tools don’t show up, run `/tools` and enable the `oculus` toolset.

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
