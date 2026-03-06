"""
Coordinator module — declares the singleton FastMCP instance.

All tool modules import `mcp` from here and register their tools via
@mcp.tool() decorators. This pattern (borrowed from googleads/google-ads-mcp
and google-marketing-solutions/google_ads_mcp) keeps the server entry point
clean and allows tools to be organized across multiple modules.
"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="Google Ads MCP — googleadsagent.ai",
    mask_error_details=False,  # Set True in production for security
)
