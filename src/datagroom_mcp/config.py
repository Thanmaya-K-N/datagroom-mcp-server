"""Configuration management for Datagroom MCP server."""

import json
import os
from pathlib import Path
from typing import Any, Optional

# PAT and gateway URL are read from mcp.json (~/.cursor/mcp.json), not from .env

# Default MCP config path (Cursor): ~/.cursor/mcp.json
_MCP_JSON_PATH = Path(os.path.expanduser("~")) / ".cursor" / "mcp.json"
_MCP_SERVER_KEY = "datagroom"  # key under mcpServers in mcp.json


def _load_env_from_mcp_json() -> dict[str, Any]:
    """
    Read DATAGROOM_* env from Cursor's mcp.json.
    Expects: mcpServers["datagroom"]["env"] with DATAGROOM_PAT_TOKEN, DATAGROOM_GATEWAY_URL.
    """
    if not _MCP_JSON_PATH.exists():
        return {}
    try:
        text = _MCP_JSON_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        servers = data.get("mcpServers") or {}
        server = servers.get(_MCP_SERVER_KEY)
        if not server or not isinstance(server, dict):
            return {}
        env = server.get("env")
        if not env or not isinstance(env, dict):
            return {}
        return env
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


class Config:
    """Configuration: env vars override; otherwise read from ~/.cursor/mcp.json."""

    _validated = False

    @classmethod
    def _reload(cls) -> None:
        """Load config: env vars first, then mcp.json (mcpServers.datagroom.env)."""
        cls.GATEWAY_URL = os.getenv("DATAGROOM_GATEWAY_URL") or "http://localhost:8887"
        cls.PAT_TOKEN = os.getenv("DATAGROOM_PAT_TOKEN")

        # If PAT not in environment, read from mcp.json (primary source for MCP)
        if not cls.PAT_TOKEN:
            mcp_env = _load_env_from_mcp_json()
            cls.PAT_TOKEN = mcp_env.get("DATAGROOM_PAT_TOKEN") or None
            if mcp_env.get("DATAGROOM_GATEWAY_URL"):
                cls.GATEWAY_URL = mcp_env["DATAGROOM_GATEWAY_URL"]
        elif not os.getenv("DATAGROOM_GATEWAY_URL"):
            # PAT from env; gateway URL can still come from mcp.json
            mcp_env = _load_env_from_mcp_json()
            if mcp_env.get("DATAGROOM_GATEWAY_URL"):
                cls.GATEWAY_URL = mcp_env["DATAGROOM_GATEWAY_URL"]

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if cls._validated:
            return

        cls._reload()

        if not cls.PAT_TOKEN:
            raise ValueError(
                "DATAGROOM_PAT_TOKEN is required. "
                "Set it in Cursor's mcp.json under mcpServers.datagroom.env (e.g. "
                '"env": {"DATAGROOM_PAT_TOKEN": "dgpat_...", "DATAGROOM_GATEWAY_URL": "http://localhost:8887"}). '
                "Generate a token in Datagroom Settings > Personal Access Tokens"
            )

        cls._validated = True

    @classmethod
    def get_gateway_url(cls, endpoint: str) -> str:
        """Construct full Gateway URL for an endpoint."""
        if not cls._validated:
            cls.validate()
        return f"{cls.GATEWAY_URL}{endpoint}"


# Initialize config values (will be reloaded on validate())
Config._reload()
