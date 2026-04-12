# googleadsagent-mcp

Een MCP (Model Context Protocol) server + zelfstandige agent-SDK voor de Google Ads API.  
Gebouwd door [googleadsagent.ai](https://googleadsagent.ai) · MIT-licentie

[English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh.md) | [Nederlands](README.nl.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

---

## Installatie

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

## Werkt met elke MCP-client

| Client | Transport | Configuratie |
|---|---|---|
| **Claude Code** | stdio | `.mcp.json` in de projectroot (inbegrepen) |
| **Claude Desktop** | stdio | `claude_desktop_config.example.json` |
| **Cursor / Windsurf** | stdio | Instellingen → MCP → `python -m ads_mcp.server` |
| **OpenAI Agents SDK** | stdio | `MCPServerStdio(command="python", args=["-m", "ads_mcp.server"])` |
| **LangChain** | stdio | `langchain-mcp-adapters` |
| **Extern / Cloud** | HTTP SSE | `python -m ads_mcp.server --http` |

---

## Snelstart

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

Plaats `.mcp.json` in je projectroot (al inbegrepen):

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

Claude Code detecteert `.mcp.json` automatisch. `CLAUDE.md` is specifiek geschreven zodat Claude Code
zich kan oriënteren — het leest dit als eerste bij elke sessie.

---

## Gemini CLI

Voeg toe aan het `.gemini/settings.json`-bestand van je project:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["-m", "ads_mcp.server"],
      "env": {
        "GOOGLE_ADS_CREDENTIALS": "/path/to/google-ads.yaml",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "1234567890"
      }
    }
  }
}
```

Voor de volledige Gemini CLI-configuratie met Google Ads slash-commando's en agent-vaardigheden, zie
[gemini-cli-googleadsagent](https://github.com/itallstartedwithaidea/gemini-cli-googleadsagent).

**Externe optie** — als je de
[buddy-agent](https://github.com/itallstartedwithaidea/googleadsagent-site/tree/main/workers/buddy-agent)
op Cloudflare Workers deployt, kun je lokale inloggegevens volledig overslaan en verbinden via SSE:

```json
{
  "mcpServers": {
    "buddy-google-ads": {
      "url": "https://your-buddy-agent.workers.dev/sse"
    }
  }
}
```

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

## Toolreferentie

### Leestools
`list_accessible_customers` · `list_accounts` · `execute_gaql` · `get_campaign_performance`
`get_keyword_performance` · `get_search_terms` · `get_ad_performance` · `get_account_budget_summary`
`generate_keyword_ideas`

### Audittools
`get_auction_insights` · `get_change_history` · `get_device_performance` · `get_geo_performance`
`get_recommendations` · `get_pmax_performance` · `get_impression_share`

### Schrijftools (droogloop standaard — vereist `confirm=True`)
`update_campaign_budget` · `update_campaign_status` · `update_ad_group_status` · `update_keyword_bid`
`add_keywords` · `add_negative_keywords` · `remove_negative_keyword` · `create_campaign`
`create_ad_group` · `switch_bidding_strategy` · `generic_mutate`

### Documentatietools
`get_gaql_reference` · `get_workflow_guide`

---

## Inloggegevens

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

Volledige handleiding voor het instellen van inloggegevens: [google-ads-api-agent README → Stap 1A](https://github.com/itallstartedwithaidea/google-ads-api-agent#1a-google-ads-api-credentials)

---

## v23-servicedekking

Google Ads API v23 heeft meer dan 70 services. Huidige status:
- ✅ **29 tools geïmplementeerd** — kernrapportage, audit, schrijfbewerkingen, documentatiereferenties
- 🔧 **42 services gepland** — volledige routekaart in [`docs/SERVICES.md`](docs/SERVICES.md)
- ⬜ **~20 buiten bereik** — platformbeheer, verouderd, LSA-specifiek

---

## Bronvermelding

### Google LLC (Apache 2.0)

> **google-ads Python-clientbibliotheek** — Copyright 2023 Google LLC  
> https://github.com/googleads/google-ads-python  
> Alle API-aanroepen in dit pakket gebruiken het `google-ads` pip-pakket gepubliceerd door Google.
> De v23-servicedefinities, proto-types en gRPC-clients zijn het werk van Google.

> **googleads/google-ads-mcp** — https://github.com/googleads/google-ads-mcp  
> Patronen: MCP-singleton, `search_stream` + `field_mask.paths`

> **google-marketing-solutions/google_ads_mcp** — https://github.com/google-marketing-solutions/google_ads_mcp  
> Patronen: documentatie-MCP-tools, externe OAuth, `omit_unselected_resource_names`

### Community (MIT)

> **cohnen/mcp-google-ads** — https://github.com/cohnen/mcp-google-ads  
> Patronen: `format_value` proto-serialisatiehelper

> **gomarble-ai/google-ads-mcp-server** — https://github.com/gomarble-ai/google-ads-mcp-server  
> Patronen: duaal transport (stdio + HTTP), KeywordPlanIdeaService

> **itallstartedwithaidea/google-ads-api-agent** — https://github.com/itallstartedwithaidea/google-ads-api-agent  
> Patronen: veilinginzichten, wijzigingsgeschiedenis, campagnemaker, biedstrategiebeheerder,
> uitsluitingszoekwoorden, geografische targeting, PMax-rapportage, Filter-First-architectuur

Volledige toewijzingstabel per functie: [`docs/SERVICES.md`](docs/SERVICES.md)

---

## Gerelateerd

- **[google-ads-skills](https://github.com/itallstartedwithaidea/google-ads-skills)** — Anthropic Agent-vaardigheden voor Claude (analyse, audit, schrijven, wiskunde, MCP)
- **[google-ads-api-agent](https://github.com/itallstartedwithaidea/google-ads-api-agent)** — Volledige Python-agent met 28 API-acties en 6 sub-agents
- **[google-ads-gemini-extension](https://github.com/itallstartedwithaidea/google-ads-gemini-extension)** — Gemini CLI-extensie met 22 MCP-tools, vaardigheden, commando's en thema's
- **[googleadsagent.ai](https://googleadsagent.ai)** — Productie-implementatie (Buddy) op Cloudflare met semantisch geheugen, facturering en monitoring

---

## Licentie

MIT — zie [LICENSE](LICENSE)  
`google-ads`-afhankelijkheid: Apache 2.0, Copyright 2023 Google LLC  
FastMCP: Apache 2.0

---

[googleadsagent.ai](https://googleadsagent.ai) · [Google Ads API-documentatie](https://developers.google.com/google-ads/api) · [MCP-specificatie](https://modelcontextprotocol.io)
