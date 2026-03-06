# googleadsagent-mcp

An MCP (Model Context Protocol) server + standalone agent SDK for the Google Ads API.

Built by [googleadsagent.ai](https://googleadsagent.ai) · MIT License

## What is this?

This package gives any MCP-compatible AI client (Claude Desktop, Claude Code, Cursor, OpenAI Agents SDK, LangChain) full read/write access to Google Ads accounts via the Google Ads API v23.

- **23 tools** covering campaign performance, keyword analysis, budget management, auction insights, and more
- **Write tools** are dry-run by default — nothing changes until you pass `confirm=True`
- **Works with every MCP client** — stdio for desktop apps, HTTP SSE for remote/cloud

## Pages

- [[Installation]] — install from PyPI or source, configure your MCP client
- [[Tool Reference]] — every tool with parameters and examples
- [[Connecting to Google Ads API]] — get your Developer Token, OAuth credentials, and Refresh Token
- [[Publishing to PyPI]] — how releases work with trusted publishing
