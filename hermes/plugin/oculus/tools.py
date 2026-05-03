"""Oculus plugin tool handlers.

Best-practice anti-bloat:
- expose only 2 coarse tools.
- keep schemas short.

This plugin loads the Oculus repo's async primitives from <OCULUS_WORKDIR>/tools/*
so we don't need to vendor logic into Hermes.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path


def _workdir() -> Path:
    wd = os.environ.get("OCULUS_WORKDIR", "").strip()
    return Path(wd) if wd else Path.cwd()


def _load(rel_path: str, module_name: str):
    wd = _workdir()
    module_path = wd / rel_path
    if not module_path.exists():
        raise FileNotFoundError(f"Oculus module not found: {module_path}")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load spec for: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def oculus_healthcheck(args: dict, **kwargs) -> str:
    wd = _workdir()
    return json.dumps(
        {
            "ok": True,
            "oculus_workdir": str(wd),
            "workdir_exists": wd.exists(),
            "has_tools_dir": (wd / "tools").is_dir(),
            "env": {
                "PUBLIC_ACCESS_TOKEN": bool(os.environ.get("PUBLIC_ACCESS_TOKEN")),
                "WM_BASE_URL": os.environ.get("WM_BASE_URL", ""),
                "EXECUTION_ENABLED": os.environ.get("EXECUTION_ENABLED", "false"),
            },
            "notes": [
                "Plugin is intentionally low-bloat (2 coarse tools).",
                "Execution is not provided by this plugin.",
            ],
        },
        indent=2,
    )


def oculus_get_context(args: dict, **kwargs) -> str:
    symbols = args.get("symbols")

    portfolio_mod = _load("tools/get_portfolio_snapshot.py", "oculus.get_portfolio_snapshot")
    macro_mod = _load("tools/get_macro_context.py", "oculus.get_macro_context")
    signals_mod = _load("tools/get_signals.py", "oculus.get_signals")

    async def _gather():
        out = {"portfolio_snapshot": None, "macro_context": None, "signals": None}

        async def _guard(coro):
            try:
                return await coro
            except Exception:
                return None

        if os.environ.get("PUBLIC_ACCESS_TOKEN"):
            out["portfolio_snapshot"] = await _guard(portfolio_mod.get_portfolio_snapshot())
        if os.environ.get("WM_BASE_URL"):
            out["macro_context"] = await _guard(macro_mod.get_macro_context())
        out["signals"] = await _guard(signals_mod.get_signals(symbols=symbols if symbols else None))
        return out

    try:
        result = asyncio.run(_gather())
        return json.dumps({"ok": True, "result": result}, default=str)
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
