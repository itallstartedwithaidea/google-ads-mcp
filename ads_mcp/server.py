"""
Google Ads MCP Server — entry point.

Transport options:
  stdio (default)           — Claude Desktop, Cursor
  streamable-http           — Remote/cloud deployments
  --http flag               — Force HTTP on localhost:8000

Source notes:
- Dual transport (stdio + streamable-http) from gomarble-ai/google-ads-mcp-server
- GoogleProvider / GoogleTokenVerifier auth hooks from google-marketing-solutions
  (disabled by default; enable via env vars for remote deployments)
- Tool registration via import side-effects pattern from googleads/google-ads-mcp
"""

import logging
import os
import sys

from ads_mcp.coordinator import mcp

# Import tool modules to trigger @mcp.tool() registration
from ads_mcp.tools import audit, core, docs, write  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _configure_remote_auth() -> None:
    """
    Optionally wire in Google OAuth provider for remote deployments.
    Source: google-marketing-solutions/google_ads_mcp (server.py).

    Set USE_GOOGLE_OAUTH_ACCESS_TOKEN=1 for token verification mode.
    Set FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID + _SECRET for full OAuth provider.
    """
    if os.getenv("USE_GOOGLE_OAUTH_ACCESS_TOKEN"):
        try:
            from fastmcp.server.auth.providers.google import GoogleTokenVerifier

            mcp.auth = GoogleTokenVerifier()
            logger.info("Remote auth: GoogleTokenVerifier enabled.")
        except ImportError:
            logger.warning("fastmcp GoogleTokenVerifier not available.")

    client_id = os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID")
    client_secret = os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        try:
            from fastmcp.server.auth.providers.google import GoogleProvider

            base_url = os.getenv("FASTMCP_SERVER_BASE_URL", "http://localhost:8000")
            mcp.auth = GoogleProvider(
                base_url=base_url,
                required_scopes=["https://www.googleapis.com/auth/adwords"],
            )
            logger.info("Remote auth: GoogleProvider enabled at %s", base_url)
        except ImportError:
            logger.warning("fastmcp GoogleProvider not available.")


def run() -> None:
    _configure_remote_auth()

    use_http = "--http" in sys.argv
    transport = "streamable-http" if use_http else "stdio"

    if use_http:
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        path = os.getenv("MCP_PATH", "/mcp")
        logger.info("Starting HTTP transport on http://%s:%s%s", host, port, path)
        mcp.run(transport=transport, host=host, port=port, path=path)
    else:
        logger.info("Starting stdio transport (Claude Desktop / Cursor mode)")
        mcp.run(transport=transport)


if __name__ == "__main__":
    run()
