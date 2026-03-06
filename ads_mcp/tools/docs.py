"""
Documentation tools — expose GAQL reference and API view docs to the LLM.

Source: google-marketing-solutions/google_ads_mcp (tools/docs.py) —
this is the only repo that provides doc-serving tools as first-class MCP
tools and resources. Strongly improves LLM query accuracy by giving the
model on-demand access to field metadata.
"""

from ads_mcp.coordinator import mcp


GAQL_REFERENCE = """
# Google Ads Query Language (GAQL) Reference

## Syntax
```
SELECT field1, field2, ...
FROM resource_type
[WHERE condition [AND condition ...]]
[ORDER BY field [ASC|DESC] [, field ...]]
[LIMIT n]
[PARAMETERS omit_unselected_resource_names=true]
```

## Date Literals
- `LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS`, `LAST_90_DAYS`
- `THIS_MONTH`, `LAST_MONTH`, `THIS_YEAR`
- `BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'`

Dates in BETWEEN must use dashes: '2024-01-01' ✓   '20240101' ✗

## Operators
- `=`, `!=`, `<`, `<=`, `>`, `>=`
- `IN (...)`, `NOT IN (...)`
- `LIKE '%pattern%'`  — use LIKE, NOT CONTAINS (unsupported)
- `IS NULL`, `IS NOT NULL`
- `DURING <date_literal>`

## Common Resources and Key Fields

### campaign
| Field | Notes |
|---|---|
| campaign.id | Always select when joining to ad_group |
| campaign.name | |
| campaign.status | ENABLED, PAUSED, REMOVED |
| campaign.advertising_channel_type | SEARCH, DISPLAY, SHOPPING, VIDEO, PERFORMANCE_MAX |
| campaign_budget.amount_micros | Budget in micros (÷ 1,000,000 = currency) |
| metrics.impressions, clicks, ctr, cost_micros | Core metrics |
| metrics.conversions, conversions_value | Conversion data |

### ad_group
Requires `campaign.id` in SELECT.

### keyword_view
```sql
SELECT
  campaign.id,
  ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  metrics.impressions
FROM keyword_view
```
⚠️  WRONG: `keyword.text`   CORRECT: `ad_group_criterion.keyword.text`

### search_term_view
```sql
SELECT search_term_view.search_term, metrics.clicks FROM search_term_view
```

### ad_group_ad (RSA creatives)
```sql
SELECT
  ad_group_ad.ad.responsive_search_ad.headlines,
  ad_group_ad.ad.responsive_search_ad.descriptions,
  ad_group_ad.ad.final_urls
FROM ad_group_ad
```

### campaign_budget (queried separately from campaign)
```sql
SELECT campaign_budget.amount_micros, campaign_budget.delivery_method
FROM campaign_budget
```
⚠️  WRONG: `campaign.campaign_budget.amount_micros`
   CORRECT: query `campaign_budget` resource directly

### asset (images, videos, text)
```sql
SELECT asset.id, asset.name, asset.type, asset.image_asset.full_size.url
FROM asset
WHERE asset.type = 'IMAGE'
```

### change_event
Requires `LIMIT <= 10000`.

## Revenue Metrics
| Field | Meaning |
|---|---|
| metrics.conversions_value | Direct conversion revenue (use for ROAS) |
| metrics.all_conversions_value | Total attributed (includes view-through) |

## Cost Micros
All cost fields are in micros: `1,000,000 micros = 1 currency unit`
```python
cost_usd = cost_micros / 1_000_000
```

## GAQL Grammar Reference
https://developers.google.com/google-ads/api/docs/query/grammar

## All Fields Reference
https://developers.google.com/google-ads/api/fields/v19/overview
"""


@mcp.tool()
def get_gaql_reference() -> str:
    """
    Return the GAQL (Google Ads Query Language) reference guide.

    Call this before writing complex queries to ensure correct field names,
    operators, and resource relationships. Avoids the most common GAQL errors
    (wrong keyword field names, unsupported CONTAINS operator, cost field paths).

    Source: google-marketing-solutions/google_ads_mcp (tools/docs.py)
    """
    return GAQL_REFERENCE


@mcp.resource("resource://gaql_reference")
def gaql_reference_resource() -> str:
    """GAQL reference guide as an MCP resource."""
    return GAQL_REFERENCE


WORKFLOW_GUIDE = """
# Google Ads MCP — Recommended Workflow

## Step 1: Discover accounts
```
list_accessible_customers()   # quick list of IDs
list_accounts()               # full tree including MCC sub-accounts
```

## Step 2: Check currency before analyzing costs
```
execute_gaql(
    query="SELECT customer.currency_code FROM customer LIMIT 1",
    customer_id="<ID>"
)
```
Cost fields are always in account currency, reported as micros.

## Step 3: Pull the data you need
| Goal | Tool |
|---|---|
| Campaign performance | get_campaign_performance(customer_id, days=30) |
| Keyword analysis | get_keyword_performance(customer_id, days=30) |
| Search query report | get_search_terms(customer_id, days=30) |
| Ad creative audit | get_ad_performance(customer_id) |
| Budget pacing | get_account_budget_summary(customer_id) |
| Keyword ideas | generate_keyword_ideas(customer_id, keywords=[...]) |
| Custom query | execute_gaql(query="...", customer_id="...") |

## Step 4: For custom queries
1. Call `get_gaql_reference()` to check field names
2. Use `execute_gaql()` with your custom GAQL
3. MCC accounts: pass `login_customer_id` = MCC ID, `customer_id` = child ID

## Tips
- customer_id: digits only, no dashes ('1234567890' not '123-456-7890')
- All cost values in API responses are in micros ÷ 1,000,000 = currency unit
- Search resource field names must match exactly — use get_gaql_reference() when unsure
"""


@mcp.tool()
def get_workflow_guide() -> str:
    """
    Return the recommended workflow for using Google Ads MCP tools.

    Provides a step-by-step guide: account discovery → currency check →
    data retrieval → custom queries. Good first call when starting a new
    analysis session.
    """
    return WORKFLOW_GUIDE


@mcp.resource("resource://workflow_guide")
def workflow_guide_resource() -> str:
    """Workflow guide as an MCP resource."""
    return WORKFLOW_GUIDE
