"""Tool schemas for the Oculus plugin (keep these SHORT to avoid context bloat)."""

OCULUS_HEALTHCHECK = {
    "name": "oculus_healthcheck",
    "description": "Check Oculus plugin health (workdir + env vars + execution gate).",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

OCULUS_GET_CONTEXT = {
    "name": "oculus_get_context",
    "description": "Fetch portfolio + WorldMonitor macro context + derived signals (single coarse tool to avoid tool-schema bloat).",
    "parameters": {
        "type": "object",
        "properties": {
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of ticker symbols to focus signals on.",
            }
        },
        "required": [],
    },
}
