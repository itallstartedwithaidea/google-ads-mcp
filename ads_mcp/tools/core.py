"""
Core Google Ads MCP tools: account listing and GAQL query execution.

Design synthesis:
- googleads/google-ads-mcp     → list_accessible_customers via CustomerService,
                                  clean search() helper with field_mask-driven
                                  output (no manual field parsing)
- google-marketing-solutions   → execute_gaql with login_customer_id override,
                                  omit_unselected_resource_names preprocessing,
                                  structured output schema annotation
- cohnen/mcp-google-ads        → rich docstrings with workflow guidance, named
                                  convenience tools for common queries
- gomarble-ai/google-ads-mcp-server → MCC traversal in list_accounts, Context
                                  logging, keyword planner integration
"""

import logging
from typing import Any, Optional

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.auth import get_ads_client, normalize_customer_id
from ads_mcp.coordinator import mcp
from ads_mcp.utils import format_row, micros_to_currency

logger = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _preprocess_gaql(query: str) -> str:
    """
    Append omit_unselected_resource_names=true if not already present.
    Source: google-marketing-solutions/google_ads_mcp (tools/api.py).
    Reduces response noise by omitting resource name fields that weren't
    explicitly selected.
    """
    if "omit_unselected_resource_names" not in query:
        if "PARAMETERS" in query and "include_drafts" in query:
            return query + " omit_unselected_resource_names=true"
        return query + " PARAMETERS omit_unselected_resource_names=true"
    return query


def _run_search(
    customer_id: str,
    query: str,
    login_customer_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Execute a GAQL query and return a list of plain dicts.

    Uses search_stream (repo2 / repo3) for efficiency on large result sets.
    Field names are driven by field_mask.paths so callers never need to
    know the proto structure in advance.
    """
    client = get_ads_client()
    if login_customer_id:
        client.login_customer_id = login_customer_id

    ga_service = client.get_service("GoogleAdsService")
    try:
        stream = ga_service.search_stream(
            customer_id=normalize_customer_id(customer_id),
            query=query,
        )
        rows: list[dict[str, Any]] = []
        for batch in stream:
            for row in batch.results:
                rows.append(format_row(row, batch.field_mask.paths))
        return rows
    except GoogleAdsException as exc:
        raise ToolError("\n".join(str(e) for e in exc.failure.errors)) from exc


# ─── Account tools ────────────────────────────────────────────────────────────


@mcp.tool()
def list_accessible_customers() -> list[str]:
    """
    Return customer IDs directly accessible by the authenticated user.

    These IDs can be used as the `customer_id` parameter in all other tools.
    For MCC (manager) accounts, use list_accounts() to also see child accounts.

    Source: googleads/google-ads-mcp (tools/core.py) —
    uses CustomerService.list_accessible_customers() via the Python client
    library (cleaner than raw REST used in repo1/repo4).
    """
    client = get_ads_client()
    svc = client.get_service("CustomerService")
    resp = svc.list_accessible_customers()
    return [rn.removeprefix("customers/") for rn in resp.resource_names]


@mcp.tool()
def list_accounts() -> dict[str, Any]:
    """
    List all accessible Google Ads accounts including MCC sub-accounts.

    Returns a structured dict with account metadata (id, name, is_manager,
    level, parent_id). For manager (MCC) accounts, sub-accounts are fetched
    and included up to two levels deep.

    Source: gomarble-ai/google-ads-mcp-server (server.py) — MCC traversal
    logic; combined with repo2 CustomerService pattern for cleaner API calls.

    Recommended first step: run this to discover available customer IDs before
    calling any reporting tools.
    """
    top_level_ids = list_accessible_customers()
    accounts: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _account_meta(cid: str, level: int = 0, parent_id: Optional[str] = None) -> dict:
        rows = _run_search(cid, "SELECT customer.id, customer.descriptive_name, customer.manager FROM customer LIMIT 1")
        if not rows:
            return {"id": cid, "name": f"Account {cid}", "is_manager": False, "level": level, "parent_id": parent_id}
        r = rows[0]
        return {
            "id": normalize_customer_id(str(r.get("customer.id", cid))),
            "name": r.get("customer.descriptive_name", f"Account {cid}"),
            "is_manager": bool(r.get("customer.manager", False)),
            "level": level,
            "parent_id": parent_id,
        }

    def _sub_accounts(manager_id: str, level: int) -> list[dict]:
        query = (
            "SELECT customer_client.id, customer_client.descriptive_name, "
            "customer_client.level, customer_client.manager "
            "FROM customer_client WHERE customer_client.level > 0"
        )
        try:
            rows = _run_search(manager_id, query)
        except Exception:
            return []
        subs = []
        for r in rows:
            cid = normalize_customer_id(str(r.get("customer_client.id", "")))
            subs.append({
                "id": cid,
                "name": r.get("customer_client.descriptive_name", f"Account {cid}"),
                "is_manager": bool(r.get("customer_client.manager", False)),
                "level": level,
                "parent_id": manager_id,
            })
        return subs

    for top_id in top_level_ids:
        fid = normalize_customer_id(top_id)
        if fid in seen:
            continue
        meta = _account_meta(fid, level=0)
        accounts.append(meta)
        seen.add(fid)

        if meta["is_manager"]:
            for sub in _sub_accounts(fid, level=1):
                if sub["id"] not in seen:
                    accounts.append(sub)
                    seen.add(sub["id"])
                    if sub["is_manager"]:
                        for nested in _sub_accounts(sub["id"], level=2):
                            if nested["id"] not in seen:
                                accounts.append(nested)
                                seen.add(nested["id"])

    return {"accounts": accounts, "total": len(accounts)}


# ─── GAQL execution tools ─────────────────────────────────────────────────────


@mcp.tool(
    output_schema={
        "type": "object",
        "properties": {"data": {"type": "array", "items": {"type": "object"}}},
        "required": ["data"],
    }
)
def execute_gaql(
    query: str,
    customer_id: str,
    login_customer_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Execute any Google Ads Query Language (GAQL) query.

    Args:
        query: A valid GAQL SELECT statement.
        customer_id: The Google Ads account ID to query (digits only, no dashes).
        login_customer_id: Optional MCC ID if querying a child account.

    Returns:
        {"data": [{"field.name": value, ...}, ...]}

    Output schema annotation source: google-marketing-solutions/google_ads_mcp.
    login_customer_id override pattern source: same repo.
    omit_unselected_resource_names preprocessing source: same repo.

    GAQL reference:
        https://developers.google.com/google-ads/api/docs/query/grammar

    Common resources: campaign, ad_group, ad_group_ad, keyword_view,
    campaign_budget, asset, customer, customer_client, change_event

    Date range literals: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS,
    LAST_90_DAYS, THIS_MONTH, LAST_MONTH, or BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'

    Cost fields are in micros (1,000,000 micros = 1 currency unit).
    Always include campaign.id when querying ad_group or keyword_view resources.
    Use LIKE '%term%' not CONTAINS (unsupported in GAQL).
    """
    processed = _preprocess_gaql(query)
    rows = _run_search(customer_id, processed, login_customer_id)
    return {"data": rows}


# ─── Convenience reporting tools ──────────────────────────────────────────────


@mcp.tool()
def get_campaign_performance(
    customer_id: str,
    days: int = 30,
    login_customer_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Return campaign performance metrics for the last N days.

    Args:
        customer_id: Google Ads account ID (digits only).
        days: Look-back window — 7, 14, 30, or 90. Defaults to 30.
        login_customer_id: Optional MCC ID.

    Returns cost in both micros and currency units for convenience.
    Results sorted by spend descending.

    Source: cohnen/mcp-google-ads (get_campaign_performance) — the named
    convenience tool pattern; metric set expanded with conversions_value.
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS", 90: "LAST_90_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date DURING {date_range}
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    rows = _run_search(customer_id, query, login_customer_id)

    # Enrich with human-readable cost
    for r in rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {"data": rows, "date_range": date_range, "customer_id": normalize_customer_id(customer_id)}


@mcp.tool()
def get_keyword_performance(
    customer_id: str,
    days: int = 30,
    min_impressions: int = 0,
    login_customer_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Return keyword performance metrics.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30, or 90). Defaults to 30.
        min_impressions: Filter out keywords below this impression threshold.
        login_customer_id: Optional MCC ID.

    Source: cohnen/mcp-google-ads — keyword field names corrected
    (ad_group_criterion.keyword.text vs the invalid keyword.text that repo1
    documents in its GAQL reference as a known error to avoid).
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS", 90: "LAST_90_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.quality_score
        FROM keyword_view
        WHERE segments.date DURING {date_range}
          AND metrics.impressions >= {min_impressions}
          AND ad_group_criterion.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 500
    """
    rows = _run_search(customer_id, query, login_customer_id)
    for r in rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {"data": rows, "date_range": date_range}


@mcp.tool()
def get_search_terms(
    customer_id: str,
    days: int = 30,
    min_clicks: int = 1,
    login_customer_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Return search term performance — actual queries that triggered your ads.

    Essential for SQR (Search Query Reports), finding negative keyword
    opportunities, and identifying new keyword candidates.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30, or 90).
        min_clicks: Minimum clicks threshold to reduce noise. Defaults to 1.
        login_customer_id: Optional MCC ID.
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS", 90: "LAST_90_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    query = f"""
        SELECT
            search_term_view.search_term,
            search_term_view.status,
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM search_term_view
        WHERE segments.date DURING {date_range}
          AND metrics.clicks >= {min_clicks}
        ORDER BY metrics.cost_micros DESC
        LIMIT 1000
    """
    rows = _run_search(customer_id, query, login_customer_id)
    for r in rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {"data": rows, "date_range": date_range}


@mcp.tool()
def get_ad_performance(
    customer_id: str,
    days: int = 30,
    login_customer_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Return ad-level performance including RSA headlines and descriptions.

    Useful for creative audits, A/B analysis, and identifying low-performing
    ad copy that should be refreshed.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30, or 90). Defaults to 30.
        login_customer_id: Optional MCC ID.

    Source: cohnen/mcp-google-ads — get_ad_creatives and get_ad_performance
    combined into a single richer tool.
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS", 90: "LAST_90_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_ad.ad.id,
            ad_group_ad.ad.name,
            ad_group_ad.ad.type,
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.status,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM ad_group_ad
        WHERE segments.date DURING {date_range}
          AND ad_group_ad.status != 'REMOVED'
        ORDER BY metrics.impressions DESC
        LIMIT 200
    """
    rows = _run_search(customer_id, query, login_customer_id)
    for r in rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {"data": rows, "date_range": date_range}


@mcp.tool()
def get_account_budget_summary(
    customer_id: str,
    login_customer_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Return campaign budgets and current spend for budget pacing analysis.

    Returns daily budget amounts alongside 30-day cost to help identify
    budget-constrained campaigns or overspending.

    Args:
        customer_id: Google Ads account ID.
        login_customer_id: Optional MCC ID.
    """
    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign_budget.amount_micros,
            campaign_budget.delivery_method,
            campaign_budget.explicitly_shared,
            metrics.cost_micros
        FROM campaign
        WHERE campaign.status = 'ENABLED'
          AND segments.date DURING LAST_30_DAYS
        ORDER BY campaign_budget.amount_micros DESC
        LIMIT 100
    """
    rows = _run_search(customer_id, query, login_customer_id)
    for r in rows:
        budget_micros = r.get("campaign_budget.amount_micros", 0) or 0
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["campaign_budget.amount"] = micros_to_currency(int(budget_micros))
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {"data": rows}


@mcp.tool()
def generate_keyword_ideas(
    customer_id: str,
    keywords: list[str],
    page_url: Optional[str] = None,
    language_id: str = "1000",
    geo_target_id: str = "2840",
    login_customer_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Generate keyword ideas using the Google Ads Keyword Planner.

    Args:
        customer_id: Google Ads account ID.
        keywords: Seed keywords to expand on. At least one required if no page_url.
        page_url: Optional landing page URL to generate keyword ideas from.
        language_id: Language constant ID (default: 1000 = English).
        geo_target_id: Geo target constant ID (default: 2840 = United States).
        login_customer_id: Optional MCC ID.

    Returns keyword ideas with avg monthly searches, competition level, and
    estimated CPC ranges.

    Source: gomarble-ai/google-ads-mcp-server (run_keyword_planner) — the only
    one of the four repos to implement Keyword Planner; adapted to use the
    Python client library instead of raw REST.
    """
    if not keywords and not page_url:
        raise ToolError("At least one of 'keywords' or 'page_url' must be provided.")

    client = get_ads_client()
    if login_customer_id:
        client.login_customer_id = login_customer_id

    kp_service = client.get_service("KeywordPlanIdeaService")
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = normalize_customer_id(customer_id)
    request.language = f"languageConstants/{language_id}"
    request.geo_target_constants.append(f"geoTargetConstants/{geo_target_id}")
    request.keyword_plan_network = (
        client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
    )

    if keywords and page_url:
        request.keyword_and_url_seed.url = page_url
        request.keyword_and_url_seed.keywords.extend(keywords)
    elif keywords:
        request.keyword_seed.keywords.extend(keywords)
    else:
        request.url_seed.url = page_url

    try:
        response = kp_service.generate_keyword_ideas(request=request)
    except GoogleAdsException as exc:
        raise ToolError("\n".join(str(e) for e in exc.failure.errors)) from exc

    ideas = []
    for idea in response.results:
        m = idea.keyword_idea_metrics
        ideas.append({
            "keyword": idea.text,
            "avg_monthly_searches": m.avg_monthly_searches,
            "competition": m.competition.name,
            "competition_index": m.competition_index,
            "low_top_of_page_bid": micros_to_currency(m.low_top_of_page_bid_micros),
            "high_top_of_page_bid": micros_to_currency(m.high_top_of_page_bid_micros),
        })

    return {
        "keyword_ideas": ideas,
        "total": len(ideas),
        "seed_keywords": keywords,
        "seed_url": page_url,
    }
