# Google Ads MCP — googleadsagent.ai

An MCP server + agent SDK for the Google Ads API. Clean Python, full read/write access, works with Claude Desktop, Claude Code, and Cursor.

## Quick orientation

```
ads_mcp/
├── auth.py          ← credential layer (YAML / OAuth / injected token)
├── coordinator.py   ← FastMCP singleton — import this to register tools
├── server.py        ← entry point (stdio or --http)
├── utils.py         ← proto serialization, micros conversion
└── tools/
    ├── core.py      ← read tools: campaigns, keywords, ads, budgets, search terms
    ├── audit.py     ← auction insights, change history, device/geo performance
    ├── write.py     ← mutate tools: budgets, bids, pause/enable, negatives, campaigns
    └── docs.py      ← GAQL reference + workflow guide (LLM-callable)

deploy/
├── orchestrator.py  ← standalone agentic loop (Anthropic API)
├── tool_executor.py ← maps tool names → tool functions
└── server.py        ← FastAPI REST API with session management

scripts/
├── cli.py           ← interactive terminal agent
└── validate.py      ← deployment health check
```

## Commands

```bash
# Install
pip install -e .          # or: uv pip install -e .

# Run MCP server (stdio — Claude Desktop/Cursor)
python -m ads_mcp.server

# Run MCP server (HTTP — remote/cloud)
python -m ads_mcp.server --http

# Run standalone agent (CLI)
python scripts/cli.py
python scripts/cli.py --single "Show me campaign performance for account 1234567890"
python scripts/cli.py --model claude-sonnet-4-6

# Validate deployment
python scripts/validate.py

# Run tests
pytest tests/
```

## Environment setup

```bash
cp .env.example .env
# Edit .env — minimum required:
# GOOGLE_ADS_DEVELOPER_TOKEN=...
# GOOGLE_ADS_CREDENTIALS=/path/to/google-ads.yaml
```

## Credentials

Three strategies, tried in order:

1. `GOOGLE_ADS_CREDENTIALS` → path to `google-ads.yaml` (recommended)
2. `GOOGLE_ADS_OAUTH_CONFIG_PATH` → OAuth client JSON (desktop flow with auto-refresh)
3. Injected `access_token` → for remote OAuth provider flows

MCC accounts: also set `GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_mcc_id`

## Tool inventory

### Read tools (`ads_mcp/tools/core.py`)
- `list_accessible_customers()` — fast list of directly accessible IDs
- `list_accounts()` — full tree including MCC sub-accounts
- `execute_gaql(query, customer_id)` — run any GAQL query
- `get_campaign_performance(customer_id, days)` — campaign metrics + spend
- `get_keyword_performance(customer_id, days)` — keyword metrics + quality score
- `get_search_terms(customer_id, days)` — search query report (SQR)
- `get_ad_performance(customer_id, days)` — ad-level metrics + RSA creative
- `get_account_budget_summary(customer_id)` — budgets vs. 30-day spend
- `generate_keyword_ideas(customer_id, keywords)` — Keyword Planner

### Audit tools (`ads_mcp/tools/audit.py`)
- `get_auction_insights(customer_id, days)` — competitor impression share, overlap rate
- `get_change_history(customer_id, days)` — full audit trail of account changes
- `get_device_performance(customer_id, days)` — mobile/desktop/tablet split
- `get_geo_performance(customer_id, days)` — performance by location
- `get_recommendations(customer_id)` — Google's optimization recommendations
- `get_pmax_performance(customer_id, days)` — Performance Max asset group reporting

### Write tools (`ads_mcp/tools/write.py`)
**All write tools require explicit `confirm=True` to execute. Default is dry-run mode.**

- `update_campaign_budget(customer_id, campaign_id, new_daily_budget_dollars)` — budget change
- `update_campaign_status(customer_id, campaign_id, status)` — ENABLED/PAUSED
- `update_keyword_bid(customer_id, ad_group_id, criterion_id, cpc_bid_dollars)` — keyword CPC
- `add_negative_keywords(customer_id, campaign_id, keywords, match_type)` — campaign negatives
- `remove_negative_keyword(customer_id, resource_name)` — remove a negative
- `add_keywords(customer_id, ad_group_id, keywords)` — add keywords to ad group
- `create_campaign(customer_id, name, daily_budget_dollars, bidding_strategy, ...)` — new campaign (PAUSED by default)
- `resolve_account_name(customer_id, search)` — find account ID by name

### Doc tools (`ads_mcp/tools/docs.py`)
- `get_gaql_reference()` — GAQL syntax + common field names (call before writing custom queries)
- `get_workflow_guide()` — step-by-step usage guide

## Key patterns

**GAQL field names** — always use the full path:
- ✓ `ad_group_criterion.keyword.text` not `keyword.text`
- ✓ `campaign_budget.amount_micros` queried from `campaign_budget` resource
- ✓ LIKE '%term%' not CONTAINS (unsupported)

**Micros** — all cost fields from the API are in micros (÷ 1,000,000 = currency unit). The `micros_to_currency()` helper is applied automatically so responses include both `.cost_micros` and `.cost`.

**Write safety** — all mutate tools show a preview and require `confirm=True`. Never passes `confirm=False` as default. Claude should show the preview to the user before passing `confirm=True`.

**account resolution** — tools accept either `customer_id` (digits) or `account_name` (fuzzy match against `customer_client.descriptive_name` under the MCC).

## Adding new tools

1. Create or add to a module in `ads_mcp/tools/`
2. Import `mcp` from `ads_mcp.coordinator`
3. Decorate with `@mcp.tool()`
4. Import the module in `ads_mcp/server.py` (side-effect registration)

```python
from ads_mcp.coordinator import mcp

@mcp.tool()
def my_new_tool(customer_id: str) -> dict:
    """Tool description shown to the LLM."""
    ...
```

## Claude Code workflow

When working in this repo with Claude Code:
1. Read `CLAUDE.md` (this file) first
2. Check `docs/ARCHITECTURE.md` for synthesis decisions
3. Use `scripts/validate.py` to verify environment before testing
4. Write tools go in `ads_mcp/tools/write.py` — always include the `confirm` guard
5. Read tools go in `ads_mcp/tools/core.py` or `ads_mcp/tools/audit.py`

## Known gaps / TODOs

- Elsa (Optimization) and Aladdin (Shopping/PMax) sub-agents have no action files yet — see `docs/ARCHITECTURE.md`
- RSA ad creation tool not yet implemented (see `actions/main-agent/06_rsa_ad_manager.py` for reference)
- Conversion tracking manager not yet implemented
- Label manager not yet implemented
- Ad schedule manager not yet implemented
- Experiments manager not yet implemented
- Shared negative keyword set management (add to shared set) — partial
