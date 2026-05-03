# Agent Oculus

> [!CAUTION]
> **IMPORTANT**
> This project is for **educational and experimental purposes only**. It is not intended for live trading or financial decision making. 

**Agentic Finance Worker**

`Agent Oculus` merges real-time brokerage data (Public.com) with global macro signals (WorldMonitor) to drive the ATHENA options strategy framework.

**Current State: Core capabilities established, MVP live.**

---

## Core Capabilities

- **Smart Market Data Fetching**: Pulls live trading data directly from Public.com, with Finnhub integration for extended market data. If the main connection fails, it automatically switches to backup methods (like Yahoo Finance) so the agent never goes blind.
- **Volatility Analysis (IV Engine)**: Looks at the past year of market data to figure out if options are currently cheap or expensive. This helps the agent decide whether it should be buying or selling premium.
- **Market Mood Detection**: Scans various global indicators—like fear/greed indexes, supply chain issues, general market momentum, and EIA energy data—to decide if it's safe to take risks (`RISK_ON`), if we should be careful (`RISK_OFF`), or if things are changing (`TRANSITIONAL`).
- **Safety First**: Built-in safeguards ensure the agent cannot accidentally place real trades. Live trading requires you to explicitly unlock multiple "safety gates" in the settings.
- **High-Speed Processing**: Uses parallel processing to fetch and analyze massive amounts of market data simultaneously, ensuring the agent gets its insights instantly.

---

## System Architecture

```text
agent-oculus-v1/
├── main.py                 # Entrypoint & APScheduler runtime
├── config.yaml             # System & threshold configuration
├── core/
│   ├── analytics/          # Quant logic (IV Rank, Strategy Selector)
│   ├── synthesis/          # Regime detection & Alert engine
│   ├── public_api/         # Public.com SDK/REST transport
│   └── worldmonitor/       # Macro signal orchestration
├── tools/                  # Hermes-ready atomic toolset
└── tests/                  # Comprehensive suite (IV, Regime, Concurrency)
```

---

## Setup & Execution

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Project Setup
Clone the repository and set up your Python environment:
```bash
git clone <repository-url>
cd agent-oculus-v1
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -e .[dev]
```

### 3. WorldMonitor Local Server Setup
Agent Oculus relies on WorldMonitor for macro signals and regime detection. If you are not using a hosted WorldMonitor instance, you must run it locally:
```bash
git clone https://github.com/koala73/worldmonitor.git
cd worldmonitor
npm install

# Start the WorldMonitor finance server
npm run dev:finance
```
Ensure the server is running and update `WM_BASE_URL` in your `.env` to match its address.

### 4. Environment Configuration
Copy the template and configure your environment variables:
```bash
cp .env.example .env
```
Edit `.env` with your specific credentials:
- `PUBLIC_ACCESS_TOKEN`: Your Public.com bearer token (Required for broker data).
- `WM_BASE_URL`: The URL of your WorldMonitor instance (e.g., `http://localhost:8000`).
- `FINNHUB_API_KEY`: Your Finnhub API key for extended stock and market data (Optional/Recommended).
- `EIA_API_KEY`: Your EIA API key for pulling global energy supply data (Optional/Recommended).
- `EXECUTION_ENABLED`: Keep as `false` unless you explicitly want to enable live trading capabilities.

### 5. Running the Agent
Once configured, you can interact with the agent in several ways:

```bash
# One-shot market context dump (runs analytics once and exits)
python main.py --run-once

# Start background worker (APScheduler for continuous monitoring)
python main.py

# Run the comprehensive test suite
pytest -v
```

---

