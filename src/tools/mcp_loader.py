import json
import os
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

CONFIG_PATH = Path(__file__).resolve().parents[2] / "mcp_config.json"


def load_mcp_server_configs() -> Dict[str, Any]:
    """Reads and validates server configurations from mcp_config.json."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file missing at {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            raise ValueError(f"{CONFIG_PATH} is empty. Add MCP server configs.")
        return json.loads(content).get("mcpServers", {})


async def get_mcp_tools(server_names: List[str]) -> list:
    """Connects to specified MCP servers and returns LangChain-ready tools.

    Args:
        server_names: List of keys defined in mcp_config.json (e.g. ['filesystem', 'git']).
    """
    all_configs = load_mcp_server_configs()
    selected_configs = {
        name: config
        for name, config in all_configs.items()
        if name in server_names
    }

    if not selected_configs:
        return []

    if "github" in selected_configs:
        token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
        if token:
            selected_configs["github"].setdefault("env", {})["GITHUB_PERSONAL_ACCESS_TOKEN"] = token

    client = MultiServerMCPClient(selected_configs)
    return await client.get_tools()