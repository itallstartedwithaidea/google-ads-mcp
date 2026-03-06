# Google Ads API v23 — Service Coverage Map

## Attribution

This MCP server is built on top of the **Google Ads Python client library**, which is the
official, Google-maintained Python SDK for the Google Ads API.

| Resource | Details |
|---|---|
| **Library** | `google-ads` Python client library |
| **Copyright** | Copyright 2023 Google LLC |
| **License** | Apache License 2.0 |
| **Source** | https://github.com/googleads/google-ads-python |
| **v23 Services** | https://github.com/googleads/google-ads-python/tree/main/google/ads/googleads/v23/services/services |
| **API Reference** | https://developers.google.com/google-ads/api/reference/rpc/v23/overview |

This package does **not** copy or embed any Google source code. It uses the published
`google-ads` pip package as a dependency (`google-ads>=28.1.0`), which wraps the v23 API.
All tool implementations are original MCP wrappers written by It All Started With AI Idea.

---

## Service Coverage: v23 Complete Map

The Google Ads API v23 exposes 70+ gRPC services. This document maps every service to:
- ✅ **Implemented** — MCP tool exists
- 🔧 **Planned** — on the roadmap
- ⬜ **Out of scope** — platform-level operations not relevant to agent workflows

### Account & Access Management

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `CustomerService` | `list_accessible_customers`, `list_accounts` | ✅ | Full MCC tree traversal |
| `AccountLinkService` | — | ⬜ | Platform linking, not agent scope |
| `AccountBudgetProposalService` | `get_account_budget_summary` (read) | ✅ | Write proposals: 🔧 |
| `BillingSetupService` | — | ⬜ | Billing admin, not agent scope |

### Reporting (Read)

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `GoogleAdsService` | `execute_gaql` | ✅ | Full arbitrary GAQL |
| `GoogleAdsService` | `get_campaign_performance` | ✅ | |
| `GoogleAdsService` | `get_keyword_performance` | ✅ | |
| `GoogleAdsService` | `get_search_terms` | ✅ | |
| `GoogleAdsService` | `get_ad_performance` | ✅ | |
| `GoogleAdsService` | `get_auction_insights` | ✅ | via `auction_insight` resource |
| `GoogleAdsService` | `get_change_history` | ✅ | via `change_event` resource |
| `GoogleAdsService` | `get_device_performance` | ✅ | segments.device |
| `GoogleAdsService` | `get_geo_performance` | ✅ | via `geographic_view` resource |
| `GoogleAdsService` | `get_impression_share` | ✅ | search IS metrics |
| `GoogleAdsService` | `get_pmax_performance` | ✅ | campaign + asset_group level |
| `GoogleAdsService` | `get_recommendations` | ✅ (read) | via `recommendation` resource |
| `BenchmarksService` | `get_industry_benchmarks` | 🔧 | industry CTR/CPC benchmarks |

### Campaign Management

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `CampaignService` | `create_campaign` | ✅ | Search, Display, PMax |
| `CampaignService` | `update_campaign_status` | ✅ | ENABLED/PAUSED |
| `CampaignService` | `switch_bidding_strategy` | ✅ | |
| `CampaignBudgetService` | `update_campaign_budget` | ✅ | |
| `CampaignBudgetService` | `get_account_budget_summary` | ✅ | |
| `CampaignCriterionService` | `add_negative_keywords` | ✅ | campaign-level negatives |
| `CampaignCriterionService` | `remove_negative_keyword` | ✅ | |
| `CampaignLabelService` | `apply_label_to_campaign` | 🔧 | |
| `CampaignSharedSetService` | `link_shared_negative_set` | 🔧 | |
| `CampaignAssetService` | `add_asset_to_campaign` | 🔧 | sitelinks, callouts, calls |
| `CampaignAssetSetService` | — | 🔧 | |
| `CampaignBidModifierService` | `update_device_bid_modifier` | 🔧 | device bid adjustments |
| `CampaignConversionGoalService` | `set_campaign_conversion_goals` | 🔧 | |
| `CampaignCustomizerService` | — | ⬜ | Ad customizers, niche |
| `CampaignDraftService` | `create_campaign_draft` | 🔧 | A/B testing via drafts |
| `CampaignGoalConfigService` | — | 🔧 | |
| `CampaignGroupService` | — | ⬜ | Portfolio grouping, niche |
| `CampaignLifecycleGoalService` | — | ⬜ | |

### Ad Groups

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `AdGroupService` | `create_ad_group` | ✅ | |
| `AdGroupService` | `update_ad_group_status` | ✅ | |
| `AdGroupCriterionService` | `add_keywords` | ✅ | |
| `AdGroupCriterionService` | `update_keyword_bid` | ✅ | |
| `AdGroupCriterionService` | `add_keywords_from_search_terms` | 🔧 | port from repo5 |
| `AdGroupAdService` | `create_rsa` | 🔧 | Responsive Search Ads |
| `AdGroupAdService` | `update_ad_status` | 🔧 | pause/enable ad |
| `AdGroupLabelService` | `apply_label_to_ad_group` | 🔧 | |
| `AdGroupAdLabelService` | `apply_label_to_ad` | 🔧 | |
| `AdGroupCriterionLabelService` | `apply_label_to_keyword` | 🔧 | |
| `AdGroupBidModifierService` | `update_audience_bid_modifier` | 🔧 | |
| `AdGroupAssetService` | `add_asset_to_ad_group` | 🔧 | |
| `AdGroupAssetSetService` | — | 🔧 | |
| `AdGroupCriterionCustomizerService` | — | ⬜ | Ad customizers, niche |
| `AdGroupCustomizerService` | — | ⬜ | |
| `AdParameterService` | — | ⬜ | Dynamic number insertion |

### Ads & Assets

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `AdService` | `list_ads` | 🔧 | list ads across account |
| `AssetService` | `create_asset` | 🔧 | upload images, text assets |
| `AssetService` | `list_assets` | 🔧 | |
| `AssetGroupService` | `create_asset_group` | 🔧 | PMax asset groups |
| `AssetGroupService` | `update_asset_group_status` | 🔧 | |
| `AssetGroupAssetService` | `add_asset_to_group` | 🔧 | |
| `AssetGroupSignalService` | `add_signal_to_asset_group` | 🔧 | audience signals for PMax |
| `AssetGroupListingGroupFilterService` | `set_listing_group_filters` | 🔧 | Shopping PMax product splits |
| `AssetSetService` | `create_asset_set` | 🔧 | |
| `AssetSetAssetService` | — | 🔧 | |
| `AssetGenerationService` | `generate_assets` | 🔧 | AI-generated asset suggestions |
| `AutomaticallyCreatedAssetRemovalService` | `remove_auto_assets` | 🔧 | auto-created asset cleanup |

### Labels

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `LabelService` | `create_label`, `list_labels` | 🔧 | port from repo5/01_label_manager.py |
| `CampaignLabelService` | `apply_label_to_campaign` | 🔧 | |
| `AdGroupLabelService` | `apply_label_to_ad_group` | 🔧 | |
| `AdGroupAdLabelService` | `apply_label_to_ad` | 🔧 | |
| `AdGroupCriterionLabelService` | `apply_label_to_keyword` | 🔧 | |
| `CustomerLabelService` | — | ⬜ | MCC-level labeling |

### Audiences & Targeting

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `AudienceService` | `list_audiences` | 🔧 | customer match, remarketing lists |
| `AudienceInsightsService` | `get_audience_insights` | 🔧 | demographic/interest data |
| `ContentCreatorInsightsService` | `get_creator_insights` | 🔧 | YouTube creator targeting |

### Conversions & Measurement

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `ConversionActionService` | `list_conversion_actions` | 🔧 | port from repo5/02_conversion_tracking |
| `ConversionActionService` | `create_conversion_action` | 🔧 | |
| `ConversionActionService` | `update_conversion_action` | 🔧 | |
| `ConversionAdjustmentUploadService` | `upload_conversion_adjustments` | 🔧 | offline conversion adjustments |
| `ConversionUploadService` | `upload_conversions` | 🔧 | offline conversion import |
| `ConversionCustomVariableService` | — | ⬜ | |
| `ConversionGoalCampaignConfigService` | — | 🔧 | |
| `CustomerConversionGoalService` | `list_conversion_goals` | 🔧 | |
| `OfflineUserDataJobService` | `upload_customer_match_list` | 🔧 | CRM data upload |
| `UserDataService` | — | ⬜ | |
| `UserListService` | `create_remarketing_list` | 🔧 | audience list management |
| `UserListCustomerTypeService` | — | ⬜ | |

### Bidding & Optimization

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `BiddingStrategyService` | `switch_bidding_strategy` | ✅ | |
| `BiddingStrategyService` | `list_portfolio_strategies` | 🔧 | |
| `BiddingStrategyService` | `create_portfolio_strategy` | 🔧 | port from repo5/27 |
| `BiddingDataExclusionService` | `create_data_exclusion` | 🔧 | exclude data from smart bidding |
| `BiddingSeasonalityAdjustmentService` | `create_seasonality_adjustment` | 🔧 | holiday/event adjustments |
| `RecommendationService` | `get_recommendations` | ✅ (read) | |
| `RecommendationService` | `apply_recommendation` | 🔧 | |
| `RecommendationService` | `dismiss_recommendation` | 🔧 | |
| `RecommendationSubscriptionService` | — | ⬜ | auto-apply subscriptions |

### Planning & Research

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `KeywordPlanService` | `generate_keyword_ideas` | ✅ | |
| `KeywordPlanAdGroupService` | — | ⬜ | |
| `KeywordPlanAdGroupKeywordService` | — | ⬜ | |
| `KeywordPlanCampaignService` | — | ⬜ | |
| `KeywordPlanCampaignKeywordService` | — | ⬜ | |
| `KeywordPlanIdeaService` | `forecast_keyword_performance` | 🔧 | bid/volume forecasting |
| `ReachPlanService` | `get_reach_forecast` | 🔧 | YouTube/Display reach planning |
| `BrandSuggestionService` | `get_brand_suggestions` | 🔧 | brand keyword suggestions |

### Shopping & Feed

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `ProductLinkService` | `link_merchant_center` | 🔧 | connect Merchant Center |
| `ProductLinkInvitationService` | — | ⬜ | |
| `MerchantCenterLinkService` | — | ⬜ | |

### Scripts & Automation

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `BatchJobService` | `create_batch_job` | 🔧 | bulk operations (up to 10K mutations) |
| `SharedSetService` | `create_shared_negative_set` | 🔧 | shared negative keyword lists |
| `SharedCriterionService` | `add_to_shared_set` | 🔧 | port from repo5/08 |
| `ExperimentService` | `create_experiment` | 🔧 | port from repo5/13 |
| `ExperimentArmService` | — | 🔧 | |
| `CustomConversionGoalService` | — | ⬜ | |
| `CustomizerAttributeService` | — | ⬜ | Ad customizer attributes |

### Identity & Misc

| v23 Service | MCP Tool | Status | Notes |
|---|---|---|---|
| `GeoTargetConstantService` | used internally by `create_campaign` | ✅ | geo lookup helper |
| `GoogleAdsFieldService` | `get_gaql_reference` (partial) | ✅ | field metadata |
| `CustomerService` | `list_accessible_customers`, `list_accounts` | ✅ | |
| `CustomerManagerLinkService` | — | ⬜ | MCC structure management |
| `CustomerUserAccessService` | `check_user_access` | 🔧 | port from repo5/15 |
| `CustomerUserAccessInvitationService` | — | ⬜ | |
| `ThirdPartyAppAnalyticsLinkService` | — | ⬜ | |
| `TravelAssetSuggestionService` | — | ⬜ | |
| `LocalServicesLeadService` | — | ⬜ | LSA-specific |
| `LocalServicesEmployeeService` | — | ⬜ | LSA-specific |
| `SmartCampaignSettingService` | — | ⬜ | Smart campaigns deprecated |
| `SmartCampaignSuggestService` | — | ⬜ | |

---

## Status Summary

| Status | Count | Description |
|---|---|---|
| ✅ Implemented | **23** | MCP tools exist and tested |
| 🔧 Planned | **42** | On roadmap, implementation guide above |
| ⬜ Out of scope | **20** | Platform admin, deprecated, or niche |

---

## Pip Installability Confirmation

This package is structured as a valid pip-installable Python package:

```
pyproject.toml          ← build config (hatchling)
ads_mcp/__init__.py     ← package root with __version__
ads_mcp/tools/          ← sub-package with tools
```

### Install options

```bash
# From PyPI (once published)
pip install googleadsagent-mcp

# From GitHub directly (works today)
pip install git+https://github.com/itallstartedwithaidea/google-ads-mcp.git

# From source clone
git clone https://github.com/itallstartedwithaidea/google-ads-mcp.git
cd google-ads-mcp
pip install -e .

# With uv (faster)
uv add googleadsagent-mcp
# or
uv pip install git+https://github.com/itallstartedwithaidea/google-ads-mcp.git
```

### Entry points (after pip install)

```bash
gads-mcp         # MCP server (stdio by default, --http for HTTP)
gads-agent       # Standalone CLI agent
gads-validate    # Deployment health check
```

### Compatible MCP clients

| Client | How to connect | Config |
|---|---|---|
| **Claude Code** | `.mcp.json` in project root | auto-discovered by `claude` CLI |
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` | `claude_desktop_config.example.json` |
| **Cursor** | MCP settings → add server | command: `python -m ads_mcp.server` |
| **Windsurf** | MCP settings | same as Cursor |
| **OpenAI Agents SDK** | `MCPServerStdio` | `command="python -m ads_mcp.server"` |
| **LangChain** | `langchain-mcp-adapters` | standard stdio MCP |
| **Any MCP client** | stdio or `--http` | standard MCP transport |

### OpenAI Agents SDK example

```python
from agents.mcp import MCPServerStdio

server = MCPServerStdio(
    command="python",
    args=["-m", "ads_mcp.server"],
    env={
        "GOOGLE_ADS_CREDENTIALS": "/path/to/google-ads.yaml",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "123-456-7890",
    }
)

# All 23+ tools automatically available
```

### HTTP mode (remote agents)

```bash
# Start HTTP server
python -m ads_mcp.server --http
# → Listening on http://127.0.0.1:8000/mcp

# Connect any MCP client via SSE
MCP_SERVER_URL=http://localhost:8000/mcp
```

---

## Attribution Table (All Sources)

| Decision / Feature | Source Repository | License | URL |
|---|---|---|---|
| Google Ads Python client (all API calls) | `googleads/google-ads-python` | Apache 2.0 | https://github.com/googleads/google-ads-python |
| API v23 service definitions | Google LLC | Apache 2.0 | https://github.com/googleads/google-ads-python/tree/main/google/ads/googleads/v23 |
| FastMCP server framework | jlowin/fastmcp | Apache 2.0 | https://github.com/jlowin/fastmcp |
| MCP protocol specification | Anthropic | MIT | https://github.com/modelcontextprotocol/specification |
| MCP singleton + import side-effects pattern | `googleads/google-ads-mcp` | Apache 2.0 | https://github.com/googleads/google-ads-mcp |
| Remote OAuth provider (GoogleProvider/GoogleTokenVerifier) | `google-marketing-solutions/google_ads_mcp` | Apache 2.0 | https://github.com/google-marketing-solutions/google_ads_mcp |
| Doc-serving tools pattern (get_gaql_reference) | `google-marketing-solutions/google_ads_mcp` | Apache 2.0 | https://github.com/google-marketing-solutions/google_ads_mcp |
| search_stream + field_mask.paths pattern | `googleads/google-ads-mcp` | Apache 2.0 | https://github.com/googleads/google-ads-mcp |
| omit_unselected_resource_names preprocessing | `google-marketing-solutions/google_ads_mcp` | Apache 2.0 | https://github.com/google-marketing-solutions/google_ads_mcp |
| Dual transport (stdio + streamable-http) | `gomarble-ai/google-ads-mcp-server` | MIT | https://github.com/gomarble-ai/google-ads-mcp-server |
| generate_keyword_ideas (KeywordPlanIdeaService) | `gomarble-ai/google-ads-mcp-server` | MIT | https://github.com/gomarble-ai/google-ads-mcp-server |
| format_value proto serialization | `cohnen/mcp-google-ads` | MIT | https://github.com/cohnen/mcp-google-ads |
| Auction insights reporter | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Change history auditor | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Campaign creator (Search, Display, PMax) | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Bidding strategy switcher + portfolio strategies | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Negative keyword management (shared sets) | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Geo targeting via SuggestGeoTargetConstants | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| PMax enhanced reporting | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Device + geo performance segmentation | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Filter-First Architecture / CEP protocol | `itallstartedwithaidea/google-ads-api-agent` | MIT | https://github.com/itallstartedwithaidea/google-ads-api-agent |
| Dry-run confirm pattern for write tools | Original (googleadsagent.ai) | MIT | — |
| Unified auth layer (3-strategy) | Original (googleadsagent.ai) | MIT | — |
| Standalone agent CLI + orchestrator | Original (googleadsagent.ai) | MIT | — |
| CLAUDE.md / Claude Code integration | Original (googleadsagent.ai) | MIT | — |

---

## Priority Roadmap (Next 3 Planned Tools)

1. **`create_rsa`** — Responsive Search Ad creation  
   Service: `AdGroupAdService`  
   Reference: `itallstartedwithaidea/google-ads-api-agent/actions/main-agent/06_rsa_ad_manager.py`

2. **`manage_labels`** — Create, apply, and list labels  
   Service: `LabelService` + `CampaignLabelService` + `AdGroupLabelService`  
   Reference: `itallstartedwithaidea/google-ads-api-agent/actions/main-agent/01_label_manager.py`

3. **`manage_conversion_actions`** — List, create, update conversion tracking  
   Service: `ConversionActionService`  
   Reference: `itallstartedwithaidea/google-ads-api-agent/actions/main-agent/02_conversion_tracking_manager.py`
