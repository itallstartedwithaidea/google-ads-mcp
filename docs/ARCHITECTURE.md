# Architecture Decision Record — Google Ads MCP Synthesis

This document explains what was taken from each of the four source repositories,
what was discarded, and why. Each section maps to a concrete area of the codebase.

---

## Source Repositories

| ID | Repo | Author | License |
|---|---|---|---|
| R1 | [cohnen/mcp-google-ads](https://github.com/cohnen/mcp-google-ads) | Ernesto Cohnen / ixigo | MIT |
| R2 | [googleads/google-ads-mcp](https://github.com/googleads/google-ads-mcp) | Google LLC | Apache 2.0 |
| R3 | [google-marketing-solutions/google_ads_mcp](https://github.com/google-marketing-solutions/google_ads_mcp) | Google LLC | Apache 2.0 |
| R4 | [gomarble-ai/google-ads-mcp-server](https://github.com/gomarble-ai/google-ads-mcp-server) | GoMarble AI | MIT |

---

## 1. Module Structure

### Decision: Singleton coordinator pattern (R2, R3)

**Adopted from R2/R3:** The `coordinator.py` module declares a single `FastMCP` instance.
All tool modules import it and register tools via `@mcp.tool()`. The server entry point
imports tool modules as side-effects to trigger registration.

**Discarded from R1/R4:** Both place all tools in a single `server.py` / `google_ads_server.py`
file. This works but doesn't scale. As the tool count grows (especially for googleadsagent.ai
where we're building a 250-point audit engine), a monolithic file becomes unmaintainable.

```
ads_mcp/
├── coordinator.py    ← FastMCP singleton (R2/R3 pattern)
├── server.py         ← entry point only, imports tools for side effects
└── tools/
    ├── core.py       ← reporting + keyword tools
    └── docs.py       ← documentation tools
```

---

## 2. Authentication

### Decision: Three-strategy layered auth (all four repos synthesized)

The most complex decision. Each repo handles auth differently:

| Repo | Auth Approach | Strength | Weakness |
|---|---|---|---|
| R1 | OAuth + service account via raw REST, token JSON persistence | Dual mode, thorough | Raw REST (not Python client library); token path logic complex |
| R2 | Application Default Credentials (ADC) via Python client library | Clean, enterprise-friendly | ADC setup is non-obvious for most users; no OAuth flow |
| R3 | google-ads.yaml primary; injected access_token for remote OAuth | Best for hosted deployments | YAML setup required; OAuth provider is heavy for local use |
| R4 | OAuth flow in separate `oauth/` module; auto-refresh | Clean separation; good UX | Raw REST again; token manager class is verbose |

**Synthesized approach in `ads_mcp/auth.py`:**

Priority order:
1. **Injected access_token** → for remote OAuth provider flows (R3 pattern). Bypasses cache.
2. **google-ads.yaml** → if `GOOGLE_ADS_CREDENTIALS` points to a valid YAML file (R2/R3 pattern). Uses Python client library.
3. **OAuth client JSON** → desktop OAuth flow with token persistence (R1/R4 pattern). Falls back to console if local server fails (R4 pattern).

**What was discarded:**
- R2's ADC-only approach (too confusing for most users who don't use `gcloud`)
- R1's raw REST for credentials (Python client library is safer and handles retries/proto serialization)
- R4's `TokenManager` class (adds abstraction without value over direct `google-auth` calls)
- Service account support from R1 (out of scope for typical MCP use cases)

---

## 3. GAQL Execution

### Decision: `search_stream` + `field_mask.paths` (R2/R3 pattern)

**Adopted from R2/R3:** The `search_stream` API returns results in batches. Each batch
includes a `field_mask` listing the exact fields that were selected. We iterate `field_mask.paths`
to build output dicts — the API tells us what fields came back rather than us hardcoding them.

```python
for batch in stream:
    for row in batch.results:
        output.append({field: format_value(get_nested_attr(row, field))
                        for field in batch.field_mask.paths})
```

**Discarded from R1/R4:** Both use the non-streaming `/googleAds:search` REST endpoint
and manually parse nested dicts from JSON. This means:
- Manual field traversal (`result.get('campaign', {}).get('name', '')`)
- Fields must be known ahead of time
- No support for `execute_gaql` returning arbitrary user-defined queries cleanly

### Decision: `omit_unselected_resource_names` preprocessing (R3)

R3 appends `PARAMETERS omit_unselected_resource_names=true` to every query.
This eliminates resource name fields (e.g. `customers/123/campaigns/456`) from
responses when they weren't explicitly selected — significantly reduces token
usage in LLM contexts. Adopted wholesale.

### Decision: `output_schema` annotation on `execute_gaql` (R3)

R3 annotates the tool with a JSON Schema for its return type. This helps MCP
clients (and LLMs) understand the structure of results before executing a call.
Adopted for `execute_gaql`.

---

## 4. Proto Serialization

### Decision: Combined R2 + R3 approach in `utils.py`

| Repo | Serialization approach |
|---|---|
| R2 | `format_output_value` — handles `proto.Enum` → `.name`, pass-through otherwise |
| R3 | `format_value` — adds `proto.Message` → JSON round-trip, `Repeated` → list |
| R1/R4 | Raw JSON from REST endpoint; no proto serialization needed |

R3's approach is more complete. The JSON round-trip for nested `proto.Message` objects
avoids edge cases with custom serializers. `Repeated` support from R3 handles list fields
correctly. Both combined into `ads_mcp/utils.py::format_value`.

---

## 5. Account Listing

### Decision: CustomerService (R2/R3) + MCC traversal (R4)

`list_accessible_customers()` from R2/R3: uses `CustomerService.list_accessible_customers()`
via the Python client library. Clean, typed, no raw REST.

MCC sub-account traversal from R4's `list_accounts()`: queries `customer_client` resource
to enumerate child accounts. Two-level deep traversal (top → manager → sub-manager → leaf).

`list_accessible_customers()` is kept as a fast lightweight tool.
`list_accounts()` is the full traversal for users with complex account hierarchies.

---

## 6. Tools Added (Not in Any Source Repo)

### `get_search_terms()` — Search Query Report

None of the four source repos expose a search terms / SQR tool despite it being
one of the highest-value reports in PPC management. Added as a core tool using
`search_term_view` resource.

### `get_account_budget_summary()` — Budget Pacing

R1 documents `campaign_budget.amount_micros` incorrectly (wrong resource). Added
a correct implementation using the `campaign_budget` resource directly.

### `micros_to_currency()` enrichment

All four repos return raw micros from cost fields. We add `.cost` in currency units
to every response row automatically so LLMs don't need to divide by 1,000,000.

---

## 7. Documentation Tools

### Decision: Doc-serving MCP tools (R3)

R3 is the only repo that provides documentation as first-class MCP tools
(`get_gaql_doc()`, `get_reporting_view_doc()`). This is the right pattern —
an LLM can call `get_gaql_reference()` before writing a complex query to
verify field names and avoid the most common GAQL errors.

Adopted and expanded: `get_gaql_reference()` covers the most common GAQL
pitfalls we've encountered across 15+ Google Ads accounts.
`get_workflow_guide()` provides a step-by-step recommended workflow.

R3's per-view YAML docs (requires a `generate_views.py` build step) were
not adopted — too much maintenance overhead for this release.

---

## 8. Transport

### Decision: Dual transport with `--http` flag (R4 pattern)

R4 checks `sys.argv` for `--http` to switch between stdio and streamable-http.
This is the simplest possible dual-transport approach and adopted here.

R3 hardcodes `streamable-http` and requires code changes to switch. R1/R2 use
stdio only.

For googleadsagent.ai's SaaS use case (serving MCP over HTTP to multiple users),
the `--http` flag + env-var host/port config covers both Claude Desktop (stdio)
and remote API access (HTTP) without separate codebases.

Remote OAuth wiring (GoogleProvider / GoogleTokenVerifier) from R3 is supported
via env vars but not enabled by default.

---

## 9. What Was Discarded

| Feature | Source | Reason not adopted |
|---|---|---|
| `get_image_assets()` / `download_image_asset()` | R1 | Asset download is a niche use case; adds binary I/O complexity |
| `analyze_image_assets()` | R1 | Campaign asset metrics available via `execute_gaql` |
| `list_resources()` (google_ads_field query) | R1 | Slow, returns huge payloads; `get_gaql_reference()` is better for LLM use |
| `MCPHeaderInterceptor` (grpc telemetry) | R2 | Google-specific instrumentation; not needed for this project |
| `generate_views.py` build step | R3 | Too much overhead for initial release |
| Raw REST for all API calls | R1/R4 | Python client library handles auth, retries, proto, and streaming better |
| Service account auth | R1 | Uncommon for MCP use cases; adds env var complexity |
| Application Default Credentials only | R2 | Too confusing for typical setup without gcloud |

---

## Licenses

- R1 (cohnen/mcp-google-ads): MIT — permissive, no restrictions on use or modification
- R2 (googleads/google-ads-mcp): Apache 2.0 — permissive with patent grant; attribution required
- R3 (google-marketing-solutions/google_ads_mcp): Apache 2.0 — same as R2
- R4 (gomarble-ai/google-ads-mcp-server): MIT — permissive

This project is MIT licensed. Apache 2.0 repos (R2, R3) are compatible with MIT
when used as inspiration/reference rather than as copied code. No source code
from R2 or R3 was copied verbatim into this project — all implementations are
original rewrites informed by those repos' architectural decisions.
