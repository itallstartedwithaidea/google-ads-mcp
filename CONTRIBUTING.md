# Contributing

Thanks for your interest in improving this project.

## Priorities

The highest-value contributions right now are implementing planned tools from [`docs/SERVICES.md`](docs/SERVICES.md).

**Top 3 wanted:**
1. `create_rsa` — Responsive Search Ad creation (`AdGroupAdService`)
2. `manage_labels` — Create, apply, list labels (`LabelService` + related)
3. `manage_conversion_actions` — Conversion tracking CRUD (`ConversionActionService`)

Reference implementations exist in [`itallstartedwithaidea/google-ads-api-agent`](https://github.com/itallstartedwithaidea/google-ads-api-agent).

## Adding a Tool

1. Add to the appropriate module in `ads_mcp/tools/`
2. Decorate with `@mcp.tool()`
3. For write tools: always include the `confirm: bool = False` dry-run guard
4. Import the module in `ads_mcp/server.py` (side-effect registration)
5. Add to `scripts/cli.py` TOOLS dict
6. Update `docs/SERVICES.md` status from 🔧 to ✅
7. Add a test in `tests/`

## Read tool template

```python
from ads_mcp.coordinator import mcp
from ads_mcp.auth import get_ads_client, normalize_customer_id
from ads_mcp.utils import format_row, micros_to_currency

@mcp.tool()
def my_new_tool(customer_id: str, days: int = 30) -> dict:
    """
    One-sentence description shown to the LLM.
    
    Args:
        customer_id: Google Ads account ID.
        days: Look-back window.
    """
    client = get_ads_client()
    cid = normalize_customer_id(customer_id)
    # ... query and return
```

## Write tool template

```python
@mcp.tool()
def my_write_tool(customer_id: str, ..., confirm: bool = False) -> dict:
    """Description. Default is DRY RUN — pass confirm=True to execute."""
    preview = {"what_would_change": "..."}
    if not confirm:
        return {"dry_run": True, "preview": preview, "next_step": "Pass confirm=True to execute."}
    # actual mutation
```

## PR Checklist

- [ ] Tool has a clear docstring explaining what it does and all parameters
- [ ] Write tools have the `confirm=False` dry-run guard
- [ ] `docs/SERVICES.md` updated
- [ ] `scripts/cli.py` TOOLS dict updated
- [ ] No credentials hardcoded
- [ ] Runs without error against a test account
