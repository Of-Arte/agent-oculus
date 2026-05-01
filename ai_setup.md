# AI Setup Guide: Agent Oculus V1

**Target Audience:** AI Coding Agents (e.g., Cursor, Cascade, Antigravity)

Hello fellow agent! This document is designed to give you the exact context and steps needed to install and configure the `agent-oculus-v1` project for the user. 

## Project Context
You are working on `agent-oculus-v1` (formerly `agent-finance`). It's a read-first finance worker that relies on `Public.com` for broker data and `WorldMonitor` for macro signals.

## Your Task: Install the Project for the User
When the user asks you to "set up the project" or "install dependencies", execute the following steps in sequence. 

### Step 1: Python Environment Setup
Check if a virtual environment exists. If not, create one:
```bash
python -m venv venv
```
Instruct the user to source the environment, or do it for them if your terminal tool supports state persistence.

### Step 2: Install Python Dependencies
Run the following command to install the project and its development dependencies:
```bash
pip install -e .[dev]
```

### Step 3: WorldMonitor Local Server (Dependency)
This project requires WorldMonitor to run locally for macro signals. Ask the user if they want you to set it up. If yes:
1. Clone it into a parallel directory (e.g., one level up from the current repo):
```bash
git clone https://github.com/koala73/worldmonitor.git ../worldmonitor
```
2. Navigate to it and install NPM dependencies:
```bash
cd ../worldmonitor
npm install
```
3. Advise the user to open a separate terminal and run `npm run dev:finance` to keep the server alive.

### Step 4: Environment Variables
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Instruct the user to manually populate `PUBLIC_ACCESS_TOKEN`. Ensure `EXECUTION_ENABLED` remains `false` for safety unless explicitly told otherwise.

## Development Rules for Agents
- **Safety First**: Do not modify `tools/place_order.py` to bypass the `EXECUTION_ENABLED` flag. This is a critical safety gate.
- **Concurrency**: This project relies heavily on `asyncio`. Use `asyncio.gather` for parallel I/O instead of sequential awaits.
- **Architecture**: Do not add synchronous blocking calls inside async functions. Use `run_in_executor` for heavy mathematical tasks (like IV calculations using pandas/numpy).
