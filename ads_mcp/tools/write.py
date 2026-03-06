"""
Write/mutate tools for Google Ads MCP.

ALL mutate tools are DRY-RUN by default. Pass confirm=True to execute.
Claude should always show the preview to the user before passing confirm=True.

Never sends confirm=False — that is not a valid parameter. The user must
explicitly pass confirm=True to trigger any mutation.

Sources:
- google-ads-api-agent (R5 / own repo):
    25_campaign_creator.py         → create_campaign
    07_bid_keyword_manager.py      → update_keyword_bid, add_keywords
    08_negative_keywords_manager.py → add_negative_keywords, remove_negative_keyword
    09_campaign_adgroup_manager.py  → update_campaign_status, create_ad_group
    05_budget_manager.py           → update_campaign_budget
    27_bidding_strategy_manager.py → switch_bidding_strategy
    10_google_ads_mutate.py        → generic_mutate (power-user escape hatch)
"""

import logging
from typing import Any

from fastmcp.exceptions import ToolError

from ads_mcp.auth import get_ads_client, normalize_customer_id
from ads_mcp.coordinator import mcp

logger = logging.getLogger(__name__)

MICROS = 1_000_000


# ─── Internal helpers ─────────────────────────────────────────────────────────


def _client(login_customer_id: str | None = None):
    """Get an authenticated GoogleAdsClient."""
    c = get_ads_client()
    if login_customer_id:
        c.login_customer_id = normalize_customer_id(login_customer_id)
    return c


def _dry_run_response(action: str, preview: dict) -> dict:
    return {
        "dry_run": True,
        "action": action,
        "preview": preview,
        "next_step": "Pass confirm=True to execute this operation.",
    }


def _ads_error(exc) -> dict:
    try:
        msgs = [str(e.message) for e in exc.failure.errors]
    except Exception:
        msgs = [str(exc)]
    raise ToolError("Google Ads API error: " + " | ".join(msgs)) from exc


# ─── Budget ───────────────────────────────────────────────────────────────────


@mcp.tool()
def update_campaign_budget(
    customer_id: str,
    campaign_id: str,
    new_daily_budget_dollars: float,
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Update a campaign's daily budget.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        campaign_id: Campaign ID (numeric string).
        new_daily_budget_dollars: New daily budget in dollars (e.g. 150.00 = $150/day).
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/05_budget_manager.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "campaign_id": campaign_id,
        "new_daily_budget": f"${new_daily_budget_dollars:.2f}",
    }

    if not confirm:
        return _dry_run_response("update_campaign_budget", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    ga_service = client.get_service("GoogleAdsService")

    # Look up the budget resource name via campaign
    q = f"""
        SELECT campaign.id, campaign.campaign_budget
        FROM campaign
        WHERE campaign.id = {campaign_id}
        LIMIT 1
    """
    try:
        rows = list(ga_service.search(customer_id=cid, query=q))
    except GoogleAdsException as e:
        return _ads_error(e)

    if not rows:
        raise ToolError(f"Campaign {campaign_id} not found in account {cid}")

    budget_resource = rows[0].campaign.campaign_budget
    op = client.get_type("CampaignBudgetOperation")
    budget = op.update
    budget.resource_name = budget_resource
    budget.amount_micros = int(new_daily_budget_dollars * MICROS)
    op.update_mask.paths.append("amount_micros")

    try:
        result = client.get_service("CampaignBudgetService").mutate_campaign_budgets(
            customer_id=cid, operations=[op]
        )
        return {
            "status": "success",
            "resource_name": result.results[0].resource_name,
            "new_daily_budget": f"${new_daily_budget_dollars:.2f}",
            "campaign_id": campaign_id,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


# ─── Campaign Status ──────────────────────────────────────────────────────────


@mcp.tool()
def update_campaign_status(
    customer_id: str,
    campaign_id: str,
    status: str,
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Pause or enable a campaign.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        campaign_id: Campaign ID (numeric string).
        status: 'ENABLED' or 'PAUSED'.
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/09_campaign_adgroup_manager.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    status = status.upper()
    if status not in ("ENABLED", "PAUSED"):
        raise ToolError("status must be 'ENABLED' or 'PAUSED'")

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "campaign_id": campaign_id,
        "new_status": status,
    }

    if not confirm:
        return _dry_run_response("update_campaign_status", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    op = client.get_type("CampaignOperation")
    c = op.update
    c.resource_name = f"customers/{cid}/campaigns/{campaign_id}"
    c.status = client.enums.CampaignStatusEnum[status]
    op.update_mask.paths.append("status")

    try:
        result = client.get_service("CampaignService").mutate_campaigns(
            customer_id=cid, operations=[op]
        )
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "new_status": status,
            "resource_name": result.results[0].resource_name,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


# ─── Ad Group Status ──────────────────────────────────────────────────────────


@mcp.tool()
def update_ad_group_status(
    customer_id: str,
    ad_group_id: str,
    status: str,
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Pause or enable an ad group.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        ad_group_id: Ad group ID (numeric string).
        status: 'ENABLED' or 'PAUSED'.
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.
    """
    from google.ads.googleads.errors import GoogleAdsException

    status = status.upper()
    if status not in ("ENABLED", "PAUSED"):
        raise ToolError("status must be 'ENABLED' or 'PAUSED'")

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "ad_group_id": ad_group_id,
        "new_status": status,
    }

    if not confirm:
        return _dry_run_response("update_ad_group_status", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    op = client.get_type("AdGroupOperation")
    ag = op.update
    ag.resource_name = f"customers/{cid}/adGroups/{ad_group_id}"
    ag.status = client.enums.AdGroupStatusEnum[status]
    op.update_mask.paths.append("status")

    try:
        svc = client.get_service("AdGroupService")
        result = svc.mutate_ad_groups(customer_id=cid, operations=[op])
        return {
            "status": "success",
            "ad_group_id": ad_group_id,
            "new_status": status,
            "resource_name": result.results[0].resource_name,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


# ─── Keyword Bid ──────────────────────────────────────────────────────────────


@mcp.tool()
def update_keyword_bid(
    customer_id: str,
    ad_group_id: str,
    criterion_id: str,
    cpc_bid_dollars: float,
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Update the CPC bid for a specific keyword.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        ad_group_id: Ad group containing the keyword.
        criterion_id: Keyword criterion ID (from get_keyword_performance).
        cpc_bid_dollars: New CPC bid in dollars (e.g. 2.50 = $2.50 max CPC).
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/07_bid_keyword_manager.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "ad_group_id": ad_group_id,
        "criterion_id": criterion_id,
        "new_cpc_bid": f"${cpc_bid_dollars:.2f}",
    }

    if not confirm:
        return _dry_run_response("update_keyword_bid", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    op = client.get_type("AdGroupCriterionOperation")
    criterion = op.update
    criterion.resource_name = f"customers/{cid}/adGroupCriteria/{ad_group_id}~{criterion_id}"
    criterion.cpc_bid_micros = int(cpc_bid_dollars * MICROS)
    op.update_mask.paths.append("cpc_bid_micros")

    try:
        result = client.get_service("AdGroupCriterionService").mutate_ad_group_criteria(
            customer_id=cid, operations=[op]
        )
        return {
            "status": "success",
            "criterion_id": criterion_id,
            "new_cpc_bid": f"${cpc_bid_dollars:.2f}",
            "resource_name": result.results[0].resource_name,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


# ─── Add Keywords ─────────────────────────────────────────────────────────────


@mcp.tool()
def add_keywords(
    customer_id: str,
    ad_group_id: str,
    keywords: list[dict],
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Add keywords to an ad group.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        ad_group_id: Ad group ID to add keywords to.
        keywords: List of keyword dicts. Each dict:
            {
              "keyword": "running shoes",
              "match_type": "EXACT",  // EXACT, PHRASE, or BROAD
              "cpc_bid": 2.50         // optional, dollars
            }
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/07_bid_keyword_manager.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    if not keywords:
        raise ToolError("keywords list is required and cannot be empty")

    # Validate keywords
    valid = []
    for kw in keywords:
        if not kw.get("keyword"):
            continue
        mt = kw.get("match_type", "BROAD").upper()
        if mt not in ("EXACT", "PHRASE", "BROAD"):
            mt = "BROAD"
        valid.append({"keyword": kw["keyword"], "match_type": mt, "cpc_bid": kw.get("cpc_bid")})

    if not valid:
        raise ToolError("No valid keywords provided (each needs a 'keyword' field)")

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "ad_group_id": ad_group_id,
        "keywords_to_add": valid,
        "count": len(valid),
    }

    if not confirm:
        return _dry_run_response("add_keywords", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    agc_service = client.get_service("AdGroupCriterionService")
    ag_service = client.get_service("AdGroupService")

    operations = []
    for kw in valid:
        op = client.get_type("AdGroupCriterionOperation")
        crit = op.create
        crit.ad_group = ag_service.ad_group_path(cid, ad_group_id)
        crit.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        crit.keyword.text = kw["keyword"]
        crit.keyword.match_type = client.enums.KeywordMatchTypeEnum[kw["match_type"]]
        if kw.get("cpc_bid"):
            crit.cpc_bid_micros = int(float(kw["cpc_bid"]) * MICROS)
        operations.append(op)

    try:
        result = agc_service.mutate_ad_group_criteria(customer_id=cid, operations=operations)
        added = [r.resource_name for r in result.results]
        return {
            "status": "success",
            "added_count": len(added),
            "resource_names": added,
            "keywords": valid,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


# ─── Negative Keywords ────────────────────────────────────────────────────────


@mcp.tool()
def add_negative_keywords(
    customer_id: str,
    campaign_id: str,
    keywords: list[str],
    match_type: str = "BROAD",
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Add negative keywords to a campaign.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        campaign_id: Campaign to add negatives to.
        keywords: List of keyword strings (no brackets/quotes needed — just the text).
        match_type: 'BROAD', 'PHRASE', or 'EXACT'. Defaults to 'BROAD'.
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/08_negative_keywords_manager.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    match_type = match_type.upper()
    if match_type not in ("BROAD", "PHRASE", "EXACT"):
        raise ToolError("match_type must be BROAD, PHRASE, or EXACT")

    if not keywords:
        raise ToolError("keywords list cannot be empty")

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "campaign_id": campaign_id,
        "negatives_to_add": keywords,
        "match_type": match_type,
        "count": len(keywords),
    }

    if not confirm:
        return _dry_run_response("add_negative_keywords", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    cc_service = client.get_service("CampaignCriterionService")
    campaign_service = client.get_service("CampaignService")

    operations = []
    for kw_text in keywords:
        op = client.get_type("CampaignCriterionOperation")
        criterion = op.create
        criterion.campaign = campaign_service.campaign_path(cid, campaign_id)
        criterion.negative = True
        criterion.keyword.text = kw_text
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type]
        operations.append(op)

    try:
        result = cc_service.mutate_campaign_criteria(customer_id=cid, operations=operations)
        return {
            "status": "success",
            "added_count": len(result.results),
            "resource_names": [r.resource_name for r in result.results],
            "keywords": keywords,
            "match_type": match_type,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


@mcp.tool()
def remove_negative_keyword(
    customer_id: str,
    resource_name: str,
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Remove a negative keyword by resource name.

    Get the resource_name from get_search_terms or execute_gaql on campaign_criterion.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        resource_name: Full resource name, e.g.
            'customers/1234567890/campaignCriteria/111111~222222'
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/08_negative_keywords_manager.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "resource_name_to_remove": resource_name,
    }

    if not confirm:
        return _dry_run_response("remove_negative_keyword", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)

    if "campaignCriteria" in resource_name or "campaign_criteria" in resource_name:
        service = client.get_service("CampaignCriterionService")
        op = client.get_type("CampaignCriterionOperation")
        op.remove = resource_name
        try:
            service.mutate_campaign_criteria(customer_id=cid, operations=[op])
        except GoogleAdsException as e:
            return _ads_error(e)
    elif "sharedCriteria" in resource_name or "shared_criteria" in resource_name:
        service = client.get_service("SharedCriterionService")
        op = client.get_type("SharedCriterionOperation")
        op.remove = resource_name
        try:
            service.mutate_shared_criteria(customer_id=cid, operations=[op])
        except GoogleAdsException as e:
            return _ads_error(e)
    else:
        raise ToolError(
            f"Cannot determine resource type from: {resource_name}. "
            "Expected campaignCriteria or sharedCriteria."
        )

    return {"status": "success", "removed": resource_name}


# ─── Campaign Creator ─────────────────────────────────────────────────────────


@mcp.tool()
def create_campaign(
    customer_id: str,
    name: str,
    campaign_type: str,
    daily_budget_dollars: float,
    bidding_strategy: str = "MAXIMIZE_CONVERSIONS",
    target_cpa: float | None = None,
    target_roas: float | None = None,
    geo_targets: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str = "PAUSED",
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a new campaign.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.
    New campaigns are always created PAUSED unless you explicitly set status='ENABLED'.

    Args:
        customer_id: Google Ads account ID.
        name: Campaign name.
        campaign_type: 'SEARCH', 'DISPLAY', or 'PERFORMANCE_MAX'.
        daily_budget_dollars: Daily budget in dollars (e.g. 100.00 = $100/day).
        bidding_strategy: One of MAXIMIZE_CONVERSIONS, TARGET_CPA, TARGET_ROAS,
                          MAXIMIZE_CLICKS, MAXIMIZE_CONVERSION_VALUE, MANUAL_CPC.
        target_cpa: Required if bidding_strategy=TARGET_CPA. Dollars.
        target_roas: Required if bidding_strategy=TARGET_ROAS. Decimal (e.g. 4.0 = 400%).
        geo_targets: List of location names or criterion IDs.
                     e.g. ['United States', 'New York'] or ['1023191'].
        start_date: YYYY-MM-DD. Defaults to today.
        end_date: YYYY-MM-DD. Optional.
        status: 'PAUSED' (default) or 'ENABLED'. Always confirm before ENABLED.
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/25_campaign_creator.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    campaign_type = campaign_type.upper()
    if campaign_type not in ("SEARCH", "DISPLAY", "PERFORMANCE_MAX"):
        raise ToolError("campaign_type must be SEARCH, DISPLAY, or PERFORMANCE_MAX")

    status = status.upper()
    if status not in ("PAUSED", "ENABLED"):
        status = "PAUSED"

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "name": name,
        "type": campaign_type,
        "daily_budget": f"${daily_budget_dollars:.2f}",
        "bidding_strategy": bidding_strategy,
        "target_cpa": f"${target_cpa:.2f}" if target_cpa else None,
        "target_roas": target_roas,
        "geo_targets": geo_targets,
        "start_date": start_date,
        "end_date": end_date,
        "initial_status": status,
        "warning": (
            "Campaign will be PAUSED after creation. Enable manually when ready."
            if status == "PAUSED"
            else None
        ),
    }

    if not confirm:
        return _dry_run_response("create_campaign", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)

    # Create budget
    budget_op = client.get_type("CampaignBudgetOperation")
    b = budget_op.create
    b.name = f"{name} Budget"
    b.amount_micros = int(daily_budget_dollars * MICROS)
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

    try:
        budget_result = client.get_service("CampaignBudgetService").mutate_campaign_budgets(
            customer_id=cid, operations=[budget_op]
        )
        budget_resource = budget_result.results[0].resource_name
    except GoogleAdsException as e:
        return _ads_error(e)

    # Build campaign
    op = client.get_type("CampaignOperation")
    c = op.create
    c.name = name
    c.campaign_budget = budget_resource
    c.status = client.enums.CampaignStatusEnum[status]

    channel_map = {
        "SEARCH": client.enums.AdvertisingChannelTypeEnum.SEARCH,
        "DISPLAY": client.enums.AdvertisingChannelTypeEnum.DISPLAY,
        "PERFORMANCE_MAX": client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX,
    }
    c.advertising_channel_type = channel_map[campaign_type]

    # Bidding strategy
    bs = bidding_strategy.upper()
    if bs == "MAXIMIZE_CONVERSIONS":
        c.maximize_conversions.target_cpa_micros = int(target_cpa * MICROS) if target_cpa else 0
    elif bs == "TARGET_CPA":
        if not target_cpa:
            raise ToolError("target_cpa is required for TARGET_CPA bidding")
        c.target_cpa.target_cpa_micros = int(target_cpa * MICROS)
    elif bs == "TARGET_ROAS":
        if not target_roas:
            raise ToolError("target_roas is required for TARGET_ROAS bidding")
        c.target_roas.target_roas = target_roas
    elif bs == "MAXIMIZE_CLICKS":
        c.maximize_clicks.cpc_bid_ceiling_micros = 0
    elif bs == "MAXIMIZE_CONVERSION_VALUE":
        c.maximize_conversion_value.target_roas = target_roas or 0
    elif bs == "MANUAL_CPC":
        c.manual_cpc.enhanced_cpc_enabled = True
    else:
        c.maximize_conversions.target_cpa_micros = 0

    if campaign_type == "SEARCH":
        c.network_settings.target_google_search = True
        c.network_settings.target_search_network = True
        c.network_settings.target_content_network = False
    elif campaign_type == "DISPLAY":
        c.network_settings.target_content_network = True

    if start_date:
        c.start_date = start_date.replace("-", "")
    if end_date:
        c.end_date = end_date.replace("-", "")

    try:
        result = client.get_service("CampaignService").mutate_campaigns(
            customer_id=cid, operations=[op]
        )
        campaign_id = result.results[0].resource_name.split("/")[-1]

        geo_result = None
        if geo_targets:
            geo_result = _add_geo_targets(client, cid, campaign_id, geo_targets)

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "resource_name": result.results[0].resource_name,
            "name": name,
            "type": campaign_type,
            "daily_budget": f"${daily_budget_dollars:.2f}",
            "initial_status": status,
            "geo_targeting": geo_result,
            "next_steps": [
                "1. Create an ad group (create_ad_group)",
                "2. Add keywords (add_keywords)",
                "3. Create RSA ads",
                "4. Enable when ready (update_campaign_status)",
            ],
        }
    except GoogleAdsException as e:
        return _ads_error(e)


def _add_geo_targets(client, cid: str, campaign_id: str, geo_targets: list) -> dict:
    """Helper: add geographic targets to a campaign."""
    from google.ads.googleads.errors import GoogleAdsException

    cc_svc = client.get_service("CampaignCriterionService")
    gtc_svc = client.get_service("GeoTargetConstantService")
    ops = []
    results = []

    for t in geo_targets:
        if str(t).isdigit():
            geo_id = t
        else:
            req = client.get_type("SuggestGeoTargetConstantsRequest")
            req.locale = "en"
            req.location_names.names.append(str(t))
            try:
                resp = gtc_svc.suggest_geo_target_constants(request=req)
                if resp.geo_target_constant_suggestions:
                    geo_id = resp.geo_target_constant_suggestions[0].geo_target_constant.id
                else:
                    results.append({"target": t, "status": "not_found"})
                    continue
            except Exception:
                results.append({"target": t, "status": "lookup_error"})
                continue

        op = client.get_type("CampaignCriterionOperation")
        crit = op.create
        crit.campaign = f"customers/{cid}/campaigns/{campaign_id}"
        crit.location.geo_target_constant = f"geoTargetConstants/{geo_id}"
        ops.append(op)
        results.append({"target": t, "geo_id": str(geo_id), "status": "queued"})

    if ops:
        try:
            cc_svc.mutate_campaign_criteria(customer_id=cid, operations=ops)
            for r in results:
                if r["status"] == "queued":
                    r["status"] = "added"
        except GoogleAdsException as e:
            return {"status": "error", "message": str(e.failure.errors[0].message)}

    return {"status": "success", "locations": results}


# ─── Ad Group Creator ─────────────────────────────────────────────────────────


@mcp.tool()
def create_ad_group(
    customer_id: str,
    campaign_id: str,
    name: str,
    cpc_bid_dollars: float | None = None,
    status: str = "ENABLED",
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a new ad group within a campaign.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        campaign_id: Parent campaign ID.
        name: Ad group name.
        cpc_bid_dollars: Default CPC bid in dollars for the ad group.
        status: 'ENABLED' (default) or 'PAUSED'.
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.
    """
    from google.ads.googleads.errors import GoogleAdsException

    status = status.upper()

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "campaign_id": campaign_id,
        "name": name,
        "default_cpc_bid": (
            f"${cpc_bid_dollars:.2f}" if cpc_bid_dollars else "inherits campaign default"
        ),
        "status": status,
    }

    if not confirm:
        return _dry_run_response("create_ad_group", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    op = client.get_type("AdGroupOperation")
    ag = op.create
    ag.name = name
    ag.campaign = f"customers/{cid}/campaigns/{campaign_id}"
    ag.status = client.enums.AdGroupStatusEnum[status]
    if cpc_bid_dollars:
        ag.cpc_bid_micros = int(cpc_bid_dollars * MICROS)

    try:
        svc = client.get_service("AdGroupService")
        result = svc.mutate_ad_groups(customer_id=cid, operations=[op])
        ad_group_id = result.results[0].resource_name.split("/")[-1]
        return {
            "status": "success",
            "ad_group_id": ad_group_id,
            "resource_name": result.results[0].resource_name,
            "name": name,
            "campaign_id": campaign_id,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


# ─── Switch Bidding Strategy ──────────────────────────────────────────────────


@mcp.tool()
def switch_bidding_strategy(
    customer_id: str,
    campaign_id: str,
    new_strategy: str,
    target_cpa: float | None = None,
    target_roas: float | None = None,
    max_cpc_limit: float | None = None,
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Change a campaign's bidding strategy.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        campaign_id: Campaign to update.
        new_strategy: One of: MAXIMIZE_CONVERSIONS, TARGET_CPA, MAXIMIZE_CONVERSION_VALUE,
                      TARGET_ROAS, MAXIMIZE_CLICKS, MANUAL_CPC.
        target_cpa: Required for TARGET_CPA. In dollars.
        target_roas: Required for TARGET_ROAS. Decimal (4.0 = 400% ROAS).
        max_cpc_limit: Optional CPC ceiling in dollars for MAXIMIZE_CLICKS.
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/27_bidding_strategy_manager.py
    """
    from google.ads.googleads.errors import GoogleAdsException

    new_strategy = new_strategy.upper()
    valid_strategies = {
        "MAXIMIZE_CONVERSIONS",
        "TARGET_CPA",
        "MAXIMIZE_CONVERSION_VALUE",
        "TARGET_ROAS",
        "MAXIMIZE_CLICKS",
        "MANUAL_CPC",
    }
    if new_strategy not in valid_strategies:
        raise ToolError(f"new_strategy must be one of: {', '.join(sorted(valid_strategies))}")

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "campaign_id": campaign_id,
        "new_strategy": new_strategy,
        "target_cpa": f"${target_cpa:.2f}" if target_cpa else None,
        "target_roas": target_roas,
        "max_cpc_limit": f"${max_cpc_limit:.2f}" if max_cpc_limit else None,
    }

    if not confirm:
        return _dry_run_response("switch_bidding_strategy", preview)

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    svc = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")
    c = op.update
    c.resource_name = f"customers/{cid}/campaigns/{campaign_id}"
    field_masks = []

    if new_strategy == "MAXIMIZE_CONVERSIONS":
        c.maximize_conversions.target_cpa_micros = int(target_cpa * MICROS) if target_cpa else 0
        field_masks.append("maximize_conversions")
    elif new_strategy == "TARGET_CPA":
        if not target_cpa:
            raise ToolError("target_cpa is required for TARGET_CPA")
        c.target_cpa.target_cpa_micros = int(target_cpa * MICROS)
        if max_cpc_limit:
            c.target_cpa.cpc_bid_ceiling_micros = int(max_cpc_limit * MICROS)
        field_masks.append("target_cpa")
    elif new_strategy == "MAXIMIZE_CONVERSION_VALUE":
        c.maximize_conversion_value.target_roas = target_roas or 0
        field_masks.append("maximize_conversion_value")
    elif new_strategy == "TARGET_ROAS":
        if not target_roas:
            raise ToolError("target_roas is required for TARGET_ROAS")
        c.target_roas.target_roas = target_roas
        if max_cpc_limit:
            c.target_roas.cpc_bid_ceiling_micros = int(max_cpc_limit * MICROS)
        field_masks.append("target_roas")
    elif new_strategy == "MAXIMIZE_CLICKS":
        ceiling = int(max_cpc_limit * MICROS) if max_cpc_limit else 0
        c.maximize_clicks.cpc_bid_ceiling_micros = ceiling
        field_masks.append("maximize_clicks")
    elif new_strategy == "MANUAL_CPC":
        c.manual_cpc.enhanced_cpc_enabled = True
        field_masks.append("manual_cpc")

    op.update_mask.paths.extend(field_masks)

    try:
        result = svc.mutate_campaigns(customer_id=cid, operations=[op])
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "new_strategy": new_strategy,
            "target_cpa": f"${target_cpa:.2f}" if target_cpa else None,
            "target_roas": target_roas,
            "resource_name": result.results[0].resource_name,
        }
    except GoogleAdsException as e:
        return _ads_error(e)


# ─── Generic Mutate (power-user escape hatch) ─────────────────────────────────


@mcp.tool()
def generic_mutate(
    customer_id: str,
    resource_type: str,
    operation_type: str,
    resource_data: dict,
    update_fields: list[str] | None = None,
    confirm: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Generic mutate operation for advanced use cases not covered by specific tools.

    Use this when you need to modify a resource type that doesn't have a dedicated
    write tool. Requires understanding the Google Ads API proto structure.

    Default is DRY RUN — shows preview. Pass confirm=True to execute.

    Args:
        customer_id: Google Ads account ID.
        resource_type: API resource type, e.g. 'campaign', 'ad_group', 'ad_group_criterion',
                       'ad_group_ad', 'campaign_budget', 'campaign_criterion'.
        operation_type: 'create', 'update', or 'remove'.
        resource_data: Dict of fields to set on the resource. For 'remove', just
                       pass {"resource_name": "customers/.../..."}
        update_fields: For 'update' only — list of field paths to update
                       (e.g. ['status', 'cpc_bid_micros']). Required for updates.
        confirm: Set True to execute. Default False (dry run).
        login_customer_id: Optional MCC ID.

    Source: google-ads-api-agent/actions/main-agent/10_google_ads_mutate.py
    """
    SERVICE_MAP = {
        "campaign": ("CampaignService", "mutate_campaigns", "CampaignOperation"),
        "ad_group": ("AdGroupService", "mutate_ad_groups", "AdGroupOperation"),
        "ad_group_criterion": (
            "AdGroupCriterionService",
            "mutate_ad_group_criteria",
            "AdGroupCriterionOperation",
        ),
        "ad_group_ad": ("AdGroupAdService", "mutate_ad_group_ads", "AdGroupAdOperation"),
        "campaign_budget": (
            "CampaignBudgetService",
            "mutate_campaign_budgets",
            "CampaignBudgetOperation",
        ),
        "campaign_criterion": (
            "CampaignCriterionService",
            "mutate_campaign_criteria",
            "CampaignCriterionOperation",
        ),
    }

    rt = resource_type.lower()
    if rt not in SERVICE_MAP:
        raise ToolError(
            f"Unsupported resource_type '{resource_type}'. Supported: {list(SERVICE_MAP.keys())}"
        )

    op_type = operation_type.lower()
    if op_type not in ("create", "update", "remove"):
        raise ToolError("operation_type must be 'create', 'update', or 'remove'")

    preview = {
        "customer_id": normalize_customer_id(customer_id),
        "resource_type": resource_type,
        "operation_type": op_type,
        "resource_data": resource_data,
        "update_fields": update_fields,
    }

    if not confirm:
        return _dry_run_response("generic_mutate", preview)

    from google.ads.googleads.errors import GoogleAdsException

    client = _client(login_customer_id)
    cid = normalize_customer_id(customer_id)
    service_name, mutate_method, op_type_name = SERVICE_MAP[rt]

    op = client.get_type(op_type_name)

    if op_type == "remove":
        op.remove = resource_data["resource_name"]
    else:
        target = op.create if op_type == "create" else op.update
        for key, val in resource_data.items():
            try:
                setattr(target, key, val)
            except Exception as err:
                raise ToolError(f"Cannot set field '{key}': {err}") from err

        if op_type == "update" and update_fields:
            op.update_mask.paths.extend(update_fields)

    svc = client.get_service(service_name)
    mutate_fn = getattr(svc, mutate_method)

    try:
        result = mutate_fn(customer_id=cid, operations=[op])
        return {
            "status": "success",
            "resource_name": result.results[0].resource_name if result.results else "removed",
        }
    except GoogleAdsException as e:
        return _ads_error(e)
