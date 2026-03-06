# Tool Reference

All 23+ tools available via MCP. Tools are organized into four categories.

## Read Tools (`ads_mcp/tools/core.py`)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `list_accessible_customers` | — | Fast list of directly accessible account IDs |
| `list_accounts` | — | Full account tree including MCC sub-accounts |
| `execute_gaql` | `query`, `customer_id` | Run any GAQL query directly |
| `get_campaign_performance` | `customer_id`, `days` (default 30) | Campaign metrics: clicks, impressions, cost, conversions |
| `get_keyword_performance` | `customer_id`, `days` (default 30) | Keyword metrics with quality score |
| `get_search_terms` | `customer_id`, `days` (default 30) | Search query report (SQR) |
| `get_ad_performance` | `customer_id`, `days` (default 30) | Ad-level metrics including RSA creative details |
| `get_account_budget_summary` | `customer_id` | Budget allocation vs. 30-day actual spend |
| `generate_keyword_ideas` | `customer_id`, `keywords` | Keyword Planner suggestions with volume and competition |

## Audit Tools (`ads_mcp/tools/audit.py`)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_auction_insights` | `customer_id`, `days` (default 30) | Competitor impression share and overlap rate |
| `get_change_history` | `customer_id`, `days` (default 30) | Full audit trail of account changes |
| `get_device_performance` | `customer_id`, `days` (default 30) | Mobile / desktop / tablet split |
| `get_geo_performance` | `customer_id`, `days` (default 30) | Performance by geographic location |
| `get_recommendations` | `customer_id` | Google's optimization recommendations |
| `get_pmax_performance` | `customer_id`, `days` (default 30) | Performance Max asset group reporting |
| `get_impression_share` | `customer_id`, `days` (default 30) | Impression share and lost IS metrics |

## Write Tools (`ads_mcp/tools/write.py`)

**All write tools require `confirm=True` to execute. Default is dry-run mode (preview only).**

| Tool | Parameters | Description |
|------|-----------|-------------|
| `update_campaign_budget` | `customer_id`, `campaign_id`, `new_daily_budget_dollars`, `confirm` | Change daily budget |
| `update_campaign_status` | `customer_id`, `campaign_id`, `status`, `confirm` | ENABLED / PAUSED |
| `update_ad_group_status` | `customer_id`, `ad_group_id`, `status`, `confirm` | ENABLED / PAUSED |
| `update_keyword_bid` | `customer_id`, `ad_group_id`, `criterion_id`, `cpc_bid_dollars`, `confirm` | Change keyword CPC bid |
| `add_keywords` | `customer_id`, `ad_group_id`, `keywords`, `confirm` | Add keywords to ad group |
| `add_negative_keywords` | `customer_id`, `campaign_id`, `keywords`, `match_type`, `confirm` | Add campaign-level negatives |
| `remove_negative_keyword` | `customer_id`, `resource_name`, `confirm` | Remove a specific negative keyword |
| `create_campaign` | `customer_id`, `name`, `daily_budget_dollars`, `bidding_strategy`, ..., `confirm` | Create new campaign (PAUSED by default) |
| `switch_bidding_strategy` | `customer_id`, `campaign_id`, `strategy`, `confirm` | Change bidding strategy |
| `generic_mutate` | `customer_id`, `operations`, `confirm` | Raw mutate for advanced operations |

## Doc Tools (`ads_mcp/tools/docs.py`)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_gaql_reference` | — | GAQL syntax + common field names (call before writing custom queries) |
| `get_workflow_guide` | — | Step-by-step usage guide for the agent |

## Notes

- **Micros**: All cost fields from the API are in micros (÷ 1,000,000 = dollars). Tools automatically convert and include both `.cost_micros` and `.cost` in responses.
- **Account resolution**: Tools accept either `customer_id` (digits) or `account_name` (fuzzy match against descriptive names under the MCC).
- **GAQL tips**: Use full field paths like `ad_group_criterion.keyword.text`, not `keyword.text`. Use `LIKE '%term%'` not `CONTAINS`.
