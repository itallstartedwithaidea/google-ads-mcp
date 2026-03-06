# googleadsagent-mcp

An MCP (Model Context Protocol) server + standalone agent SDK for the Google Ads API.  
Built by [googleadsagent.ai](https://googleadsagent.ai) · MIT License

---

## Install

```bash
# From PyPI (once published)
pip install googleadsagent-mcp

# From GitHub right now
pip install git+https://github.com/itallstartedwithaidea/google-ads-mcp.git

# With uv
uv add googleadsagent-mcp

# From source
git clone https://github.com/itallstartedwithaidea/google-ads-mcp.git && cd google-ads-mcp && pip install -e .
```

---

## Works with every MCP client

| Client | Transport | Config |
|---|---|---|
| **Claude Code** | stdio | `.mcp.json` in project root (included) |
| **Claude Desktop** | stdio | `claude_desktop_config.example.json` |
| **Cursor / Windsurf** | stdio | Settings → MCP → `python -m ads_mcp.server` |
| **OpenAI Agents SDK** | stdio | `MCPServerStdio(command="python", args=["-m", "ads_mcp.server"])` |
| **LangChain** | stdio | `langchain-mcp-adapters` |
| **Remote / Cloud** | HTTP SSE | `python -m ads_mcp.server --http` |

---

## Quick Start

```bash
# 1. Copy and fill credentials
cp .env.example .env

# 2. Validate environment
python scripts/validate.py

# 3a. Run as MCP server (stdio — Claude Desktop/Cursor/Claude Code)
python -m ads_mcp.server

# 3b. Run as MCP server (HTTP — remote agents)
python -m ads_mcp.server --http

# 3c. Run as standalone agent CLI
python scripts/cli.py
python scripts/cli.py --single "Show campaign performance for account 1234567890"
```

---

## Claude Code

Place `.mcp.json` in your project root (already included):

```json
{
  "mcpServers": {
    "google-ads": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ads_mcp.server"],
      "env": {
        "GOOGLE_ADS_CREDENTIALS": "${GOOGLE_ADS_CREDENTIALS}",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "${GOOGLE_ADS_LOGIN_CUSTOMER_ID}"
      }
    }
  }
}
```

Claude Code auto-discovers `.mcp.json`. `CLAUDE.md` is written specifically for Claude Code
to orient itself — it reads this first on every session.

---

## OpenAI Agents SDK

```python
from agents.mcp import MCPServerStdio
import os

server = MCPServerStdio(
    command="python",
    args=["-m", "ads_mcp.server"],
    env={
        "GOOGLE_ADS_CREDENTIALS": os.environ["GOOGLE_ADS_CREDENTIALS"],
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""),
    }
)
# All 29 Google Ads tools automatically available
```

---

## Tool Reference

### Read Tools
`list_accessible_customers` · `list_accounts` · `execute_gaql` · `get_campaign_performance`
`get_keyword_performance` · `get_search_terms` · `get_ad_performance` · `get_account_budget_summary`
`generate_keyword_ideas`

### Audit Tools
`get_auction_insights` · `get_change_history` · `get_device_performance` · `get_geo_performance`
`get_recommendations` · `get_pmax_performance` · `get_impression_share`

### Write Tools (dry-run by default — requires `confirm=True`)
`update_campaign_budget` · `update_campaign_status` · `update_ad_group_status` · `update_keyword_bid`
`add_keywords` · `add_negative_keywords` · `remove_negative_keyword` · `create_campaign`
`create_ad_group` · `switch_bidding_strategy` · `generic_mutate`

### Doc Tools
`get_gaql_reference` · `get_workflow_guide`

---

## Credentials

```env
# Option 1: google-ads.yaml path (recommended)
GOOGLE_ADS_CREDENTIALS=/path/to/google-ads.yaml
GOOGLE_ADS_LOGIN_CUSTOMER_ID=123-456-7890

# Option 2: individual env vars
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=123-456-7890
```

Full credential setup guide: [google-ads-api-agent README → Step 1A](https://github.com/itallstartedwithaidea/google-ads-api-agent#1a-google-ads-api-credentials)

---

## v23 Service Coverage

Google Ads API v23 has 70+ services. Current status:
- ✅ **29 tools implemented** — core reporting, audit, write operations, doc references
- 🔧 **42 services planned** — full roadmap in [`docs/SERVICES.md`](docs/SERVICES.md)
- ⬜ **~20 out of scope** — platform admin, deprecated, LSA-specific

---

## Attribution

### Google LLC (Apache 2.0)

> **google-ads Python client library** — Copyright 2023 Google LLC  
> https://github.com/googleads/google-ads-python  
> All API calls in this package use the `google-ads` pip package published by Google.
> The v23 service definitions, proto types, and gRPC clients are Google's work.

> **googleads/google-ads-mcp** — https://github.com/googleads/google-ads-mcp  
> Patterns: MCP singleton, `search_stream` + `field_mask.paths`

> **google-marketing-solutions/google_ads_mcp** — https://github.com/google-marketing-solutions/google_ads_mcp  
> Patterns: doc-serving MCP tools, remote OAuth, `omit_unselected_resource_names`

### Community (MIT)

> **cohnen/mcp-google-ads** — https://github.com/cohnen/mcp-google-ads  
> Patterns: `format_value` proto serialization helper

> **gomarble-ai/google-ads-mcp-server** — https://github.com/gomarble-ai/google-ads-mcp-server  
> Patterns: dual transport (stdio + HTTP), KeywordPlanIdeaService

> **itallstartedwithaidea/google-ads-api-agent** — https://github.com/itallstartedwithaidea/google-ads-api-agent  
> Patterns: auction insights, change history, campaign creator, bidding strategy manager,
> negative keywords, geo targeting, PMax reporting, Filter-First Architecture

Full per-feature attribution table: [`docs/SERVICES.md`](docs/SERVICES.md)

---

## Related

- **[google-ads-api-agent](https://github.com/itallstartedwithaidea/google-ads-api-agent)** — Full Python agent with 28 API actions and 6 sub-agents
- **[google-ads-gemini-extension](https://github.com/itallstartedwithaidea/google-ads-gemini-extension)** — Gemini CLI extension with 22 MCP tools, skills, commands, and themes
- **[googleadsagent.ai](https://googleadsagent.ai)** — Production deployment (Buddy) on Cloudflare with semantic memory, billing, and monitoring

---

## License

MIT — see [LICENSE](LICENSE)  
`google-ads` dependency: Apache 2.0, Copyright 2023 Google LLC  
FastMCP: Apache 2.0

---

[googleadsagent.ai](https://googleadsagent.ai) · [Google Ads API Docs](https://developers.google.com/google-ads/api) · [MCP Spec](https://modelcontextprotocol.io)
