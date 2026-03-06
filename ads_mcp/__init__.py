"""
googleadsagent-mcp
==================
An MCP (Model Context Protocol) server + standalone agent SDK for the Google Ads API.

Works as an MCP server with Claude Desktop, Claude Code, Cursor, and any MCP client.
Works as a standalone agent via the Anthropic API.
Works as a Python library — importable and pip-installable.

Install:
    pip install googleadsagent-mcp
    # or: uv add googleadsagent-mcp

Run MCP server (stdio):
    python -m ads_mcp.server

Run MCP server (HTTP):
    python -m ads_mcp.server --http

Standalone agent CLI:
    python scripts/cli.py

---
Built by: It All Started With AI Idea / googleadsagent.ai
Google Ads Python client: Copyright 2023 Google LLC (Apache 2.0)
  https://github.com/googleads/google-ads-python
"""

__version__ = "0.2.0"
__author__ = "It All Started With AI Idea"
__license__ = "MIT"

from ads_mcp.auth import get_ads_client, normalize_customer_id
from ads_mcp.coordinator import mcp

__all__ = ["mcp", "get_ads_client", "normalize_customer_id", "__version__"]
