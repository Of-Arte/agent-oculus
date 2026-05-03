"""Oculus Hermes plugin (low-bloat toolpack).

Hermes loads this plugin when enabled (via `hermes plugins enable oculus`).
This plugin registers *two* coarse tools under the `oculus` toolset.

Design goal: native tool calling without MCP and without tool-schema bloat.
"""

from __future__ import annotations

from .schemas import OCULUS_GET_CONTEXT, OCULUS_HEALTHCHECK
from .tools import oculus_get_context, oculus_healthcheck


def register(ctx) -> None:
    # Register two coarse tools. Keep schemas short.
    ctx.register_tool(
        name="oculus_healthcheck",
        toolset="oculus",
        schema=OCULUS_HEALTHCHECK,
        handler=oculus_healthcheck,
        emoji="🧪",
    )
    ctx.register_tool(
        name="oculus_get_context",
        toolset="oculus",
        schema=OCULUS_GET_CONTEXT,
        handler=oculus_get_context,
        emoji="👁️",
    )
