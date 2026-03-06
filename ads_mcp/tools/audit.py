"""
Audit tools for Google Ads MCP.

Covers tools that go beyond standard performance reporting into competitive
intelligence, account governance, and optimization signals.

Sources:
- cohnen/mcp-google-ads (R1)                 → auction_insight field awareness
- google-ads-api-agent (R5 / your own repo)  → auction_insights_reporter,
                                               change_history_auditor,
                                               device_performance_manager,
                                               geo_location_manager,
                                               pmax_enhanced_reporting,
                                               recommendations_manager
"""

import logging
from typing import Any

from fastmcp.exceptions import ToolError

from ads_mcp.auth import get_ads_client, normalize_customer_id
from ads_mcp.coordinator import mcp
from ads_mcp.utils import format_row, micros_to_currency

logger = logging.getLogger(__name__)


# ─── Internal search helper ───────────────────────────────────────────────────


def _search(
    customer_id: str,
    query: str,
    login_customer_id: str | None = None,
) -> list[dict[str, Any]]:
    from google.ads.googleads.errors import GoogleAdsException

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


# ─── Auction Insights ─────────────────────────────────────────────────────────


@mcp.tool()
def get_auction_insights(
    customer_id: str,
    days: int = 30,
    campaign_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Return competitive auction insights — impression share, overlap rate,
    position above rate, and outranking share for competing domains.

    This is the primary competitive intelligence tool. Shows where your ads
    appear relative to competitors in the same auctions.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30). Defaults to 30.
        campaign_id: Optional — filter to a single campaign.
        login_customer_id: Optional MCC ID.

    Key metrics:
        impression_share   — % of eligible impressions you won
        overlap_rate       — % of impressions where competitor also showed
        position_above_rate — % of shared auctions competitor ranked above you
        top_of_page_rate   — % of impressions at top of page
        outranking_share   — % of auctions you outranked them OR they didn't show

    Source: google-ads-api-agent/actions/sub-agents/reporting/05_auction_insights_reporter.py
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    where = f"segments.date DURING {date_range}"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            auction_insight.domain,
            auction_insight.is_you,
            auction_insight.search_impression_share,
            auction_insight.search_overlap_rate,
            auction_insight.search_position_above_rate,
            auction_insight.search_top_impression_share,
            auction_insight.search_outranking_share
        FROM auction_insight
        WHERE {where}
        ORDER BY auction_insight.search_impression_share DESC
        LIMIT 500
    """

    rows = _search(customer_id, query, login_customer_id)

    # Format as percentages — raw values are 0.0–1.0 fractions
    for r in rows:
        for pct_field in [
            "auction_insight.search_impression_share",
            "auction_insight.search_overlap_rate",
            "auction_insight.search_position_above_rate",
            "auction_insight.search_top_impression_share",
            "auction_insight.search_outranking_share",
        ]:
            raw = r.get(pct_field)
            if raw is not None:
                try:
                    r[pct_field + "_pct"] = round(float(raw) * 100, 1)
                except (TypeError, ValueError):
                    pass

    return {
        "data": rows,
        "date_range": date_range,
        "customer_id": normalize_customer_id(customer_id),
        "note": (
            "impression_share_pct fields are percentage (0–100)."
            " is_you=true rows are your own account."
        ),
    }


# ─── Change History ───────────────────────────────────────────────────────────


@mcp.tool()
def get_change_history(
    customer_id: str,
    days: int = 7,
    resource_type: str | None = None,
    limit: int = 500,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Return account change history — who changed what, when, and what it changed from/to.

    Invaluable for audits, debugging performance drops, and tracking unauthorized changes.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30). Defaults to 7. Max 90.
        resource_type: Optional filter — 'CAMPAIGN', 'AD_GROUP', 'AD', 'AD_GROUP_CRITERION',
                       'CAMPAIGN_CRITERION', 'CAMPAIGN_BUDGET', 'BIDDING_STRATEGY'
        limit: Max rows. API hard limit is 10,000.
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/sub-agents/reporting/06_change_history_auditor.py
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    date_range = valid.get(days, "LAST_7_DAYS")
    limit = min(limit, 10000)  # API hard cap

    where = f"segments.date DURING {date_range}"
    if resource_type:
        where += f" AND change_event.change_resource_type = '{resource_type}'"

    query = f"""
        SELECT
            change_event.change_date_time,
            change_event.change_resource_type,
            change_event.resource_change_operation,
            change_event.changed_fields,
            change_event.user_email,
            change_event.client_type,
            change_event.campaign,
            change_event.ad_group
        FROM change_event
        WHERE {where}
        ORDER BY change_event.change_date_time DESC
        LIMIT {limit}
    """

    rows = _search(customer_id, query, login_customer_id)
    return {
        "data": rows,
        "date_range": date_range,
        "count": len(rows),
        "note": (
            "user_email is empty for API/script changes."
            " changed_fields lists proto field paths that were modified."
        ),
    }


# ─── Device Performance ───────────────────────────────────────────────────────


@mcp.tool()
def get_device_performance(
    customer_id: str,
    days: int = 30,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Return campaign performance segmented by device — MOBILE, DESKTOP, TABLET.

    Use this to identify bid adjustment opportunities and diagnose mobile
    vs. desktop conversion rate gaps.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30, 90). Defaults to 30.
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/23_device_performance_manager.py
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS", 90: "LAST_90_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            segments.device,
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
          AND metrics.impressions > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 1000
    """

    rows = _search(customer_id, query, login_customer_id)
    for r in rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {"data": rows, "date_range": date_range}


# ─── Geographic Performance ───────────────────────────────────────────────────


@mcp.tool()
def get_geo_performance(
    customer_id: str,
    days: int = 30,
    geo_level: str = "country",
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Return performance segmented by geographic location.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30, 90). Defaults to 30.
        geo_level: 'country', 'region', or 'city'. Defaults to 'country'.
        login_customer_id: Optional MCC ID.

    Use to identify top-performing cities/regions, find areas to exclude,
    and discover geo expansion opportunities.

    Source: google-ads-api-agent/actions/main-agent/22_geo_location_manager.py
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS", 90: "LAST_90_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    level_map = {
        "country": "geographic_view.country_criterion_id",
        "region": "geographic_view.resource_name",
        "city": "geographic_view.resource_name",
    }
    _geo_field = level_map.get(geo_level, "geographic_view.country_criterion_id")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            geographic_view.country_criterion_id,
            geographic_view.location_type,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM geographic_view
        WHERE segments.date DURING {date_range}
          AND metrics.impressions > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 1000
    """

    rows = _search(customer_id, query, login_customer_id)
    for r in rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {
        "data": rows,
        "date_range": date_range,
        "note": (
            "country_criterion_id maps to geo target constants."
            " Use execute_gaql on geo_target_constant to resolve names."
        ),
    }


# ─── Recommendations ─────────────────────────────────────────────────────────


@mcp.tool()
def get_recommendations(
    customer_id: str,
    recommendation_type: str | None = None,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Return Google's optimization recommendations for the account.

    Args:
        customer_id: Google Ads account ID.
        recommendation_type: Optional filter — e.g. 'KEYWORD', 'BID', 'TARGET_CPA_OPT_IN',
                             'ENHANCED_CPC_OPT_IN', 'MOVE_UNUSED_BUDGET', 'SITELINK_ASSET',
                             'CALL_ASSET', 'CALLOUT_ASSET'. Leave None for all types.
        login_customer_id: Optional MCC ID.

    Returns recommendations with type, impact score, and recommended action.
    Use `apply_recommendation()` (write tool) to act on specific recommendations.

    Source: google-ads-api-agent/actions/main-agent/20_recommendations_manager.py
    """
    where = "recommendation.dismissed = FALSE"
    if recommendation_type:
        where += f" AND recommendation.type = '{recommendation_type}'"

    query = f"""
        SELECT
            recommendation.resource_name,
            recommendation.type,
            recommendation.impact.base_metrics.impressions,
            recommendation.impact.base_metrics.clicks,
            recommendation.impact.base_metrics.cost_micros,
            recommendation.impact.potential_metrics.impressions,
            recommendation.impact.potential_metrics.clicks,
            recommendation.impact.potential_metrics.cost_micros,
            campaign.id,
            campaign.name
        FROM recommendation
        WHERE {where}
        LIMIT 500
    """

    rows = _search(customer_id, query, login_customer_id)
    return {
        "data": rows,
        "count": len(rows),
        "note": "resource_name is needed to apply or dismiss a recommendation via the write tools.",
    }


# ─── PMax Enhanced Reporting ──────────────────────────────────────────────────


@mcp.tool()
def get_pmax_performance(
    customer_id: str,
    days: int = 30,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Return Performance Max campaign and asset group performance.

    PMax requires separate queries for campaign-level and asset-group-level data
    since asset groups can't be joined to standard metrics in a single query.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30, 90). Defaults to 30.
        login_customer_id: Optional MCC ID.

    Returns both campaign-level aggregates and per-asset-group breakdowns.

    Source: google-ads-api-agent/actions/sub-agents/reporting/07_pmax_enhanced_reporting.py
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS", 90: "LAST_90_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    # Campaign-level PMax metrics
    campaign_query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.ctr
        FROM campaign
        WHERE segments.date DURING {date_range}
          AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """

    # Asset group level
    asset_group_query = f"""
        SELECT
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group.status,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM asset_group
        WHERE segments.date DURING {date_range}
          AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'
          AND asset_group.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 200
    """

    campaign_rows = _search(customer_id, campaign_query, login_customer_id)
    asset_rows = _search(customer_id, asset_group_query, login_customer_id)

    for r in campaign_rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))
    for r in asset_rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {
        "campaigns": campaign_rows,
        "asset_groups": asset_rows,
        "date_range": date_range,
    }


# ─── Impression Share ─────────────────────────────────────────────────────────


@mcp.tool()
def get_impression_share(
    customer_id: str,
    days: int = 30,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Return search impression share and lost IS reasons by campaign.

    Shows what % of eligible impressions you're winning and whether you're
    losing to budget constraints or ad rank. Critical for scaling decisions.

    Args:
        customer_id: Google Ads account ID.
        days: Look-back window (7, 14, 30). Defaults to 30.
        login_customer_id: Optional MCC ID.
    """
    valid = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    date_range = valid.get(days, "LAST_30_DAYS")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            metrics.search_impression_share,
            metrics.search_rank_lost_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_top_impression_share,
            metrics.search_absolute_top_impression_share,
            metrics.cost_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions
        FROM campaign
        WHERE segments.date DURING {date_range}
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status = 'ENABLED'
          AND metrics.impressions > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 200
    """

    rows = _search(customer_id, query, login_customer_id)
    for r in rows:
        cost_micros = r.get("metrics.cost_micros", 0) or 0
        r["metrics.cost"] = micros_to_currency(int(cost_micros))

    return {
        "data": rows,
        "date_range": date_range,
        "note": (
            "search_rank_lost_impression_share = lost to ad rank (quality/bid)."
            " search_budget_lost_impression_share = lost to budget."
        ),
    }
