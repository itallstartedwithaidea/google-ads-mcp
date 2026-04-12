# googleadsagent-mcp

Un serveur MCP (Model Context Protocol) + SDK agent autonome pour l'API Google Ads.  
Créé par [googleadsagent.ai](https://googleadsagent.ai) · Licence MIT

[English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh.md) | [Nederlands](README.nl.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

---

## Installation

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

## Compatible avec tous les clients MCP

| Client | Transport | Configuration |
|---|---|---|
| **Claude Code** | stdio | `.mcp.json` à la racine du projet (inclus) |
| **Claude Desktop** | stdio | `claude_desktop_config.example.json` |
| **Cursor / Windsurf** | stdio | Paramètres → MCP → `python -m ads_mcp.server` |
| **OpenAI Agents SDK** | stdio | `MCPServerStdio(command="python", args=["-m", "ads_mcp.server"])` |
| **LangChain** | stdio | `langchain-mcp-adapters` |
| **Distant / Cloud** | HTTP SSE | `python -m ads_mcp.server --http` |

---

## Démarrage rapide

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

Placez `.mcp.json` à la racine de votre projet (déjà inclus) :

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

Claude Code détecte automatiquement `.mcp.json`. `CLAUDE.md` est rédigé spécifiquement pour que Claude Code
s'oriente — il le lit en premier à chaque session.

---

## Gemini CLI

Ajoutez à votre fichier `.gemini/settings.json` du projet :

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

Pour la configuration complète de Gemini CLI avec les commandes slash Google Ads et les compétences agent, voir
[gemini-cli-googleadsagent](https://github.com/itallstartedwithaidea/gemini-cli-googleadsagent).

**Option distante** — si vous déployez le
[buddy-agent](https://github.com/itallstartedwithaidea/googleadsagent-site/tree/main/workers/buddy-agent)
sur Cloudflare Workers, vous pouvez ignorer les identifiants locaux et vous connecter via SSE :

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

## Référence des outils

### Outils de lecture
`list_accessible_customers` · `list_accounts` · `execute_gaql` · `get_campaign_performance`
`get_keyword_performance` · `get_search_terms` · `get_ad_performance` · `get_account_budget_summary`
`generate_keyword_ideas`

### Outils d'audit
`get_auction_insights` · `get_change_history` · `get_device_performance` · `get_geo_performance`
`get_recommendations` · `get_pmax_performance` · `get_impression_share`

### Outils d'écriture (simulation par défaut — nécessite `confirm=True`)
`update_campaign_budget` · `update_campaign_status` · `update_ad_group_status` · `update_keyword_bid`
`add_keywords` · `add_negative_keywords` · `remove_negative_keyword` · `create_campaign`
`create_ad_group` · `switch_bidding_strategy` · `generic_mutate`

### Outils de documentation
`get_gaql_reference` · `get_workflow_guide`

---

## Identifiants

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

Guide complet de configuration des identifiants : [google-ads-api-agent README → Étape 1A](https://github.com/itallstartedwithaidea/google-ads-api-agent#1a-google-ads-api-credentials)

---

## Couverture des services v23

L'API Google Ads v23 comprend plus de 70 services. État actuel :
- ✅ **29 outils implémentés** — rapports essentiels, audit, opérations d'écriture, références documentaires
- 🔧 **42 services prévus** — feuille de route complète dans [`docs/SERVICES.md`](docs/SERVICES.md)
- ⬜ **~20 hors périmètre** — administration de plateforme, obsolètes, spécifiques LSA

---

## Attribution

### Google LLC (Apache 2.0)

> **Bibliothèque cliente Python google-ads** — Copyright 2023 Google LLC  
> https://github.com/googleads/google-ads-python  
> Tous les appels API de ce package utilisent le package pip `google-ads` publié par Google.
> Les définitions de services v23, les types proto et les clients gRPC sont l'œuvre de Google.

> **googleads/google-ads-mcp** — https://github.com/googleads/google-ads-mcp  
> Modèles : singleton MCP, `search_stream` + `field_mask.paths`

> **google-marketing-solutions/google_ads_mcp** — https://github.com/google-marketing-solutions/google_ads_mcp  
> Modèles : outils MCP de documentation, OAuth distant, `omit_unselected_resource_names`

### Communauté (MIT)

> **cohnen/mcp-google-ads** — https://github.com/cohnen/mcp-google-ads  
> Modèles : assistant de sérialisation proto `format_value`

> **gomarble-ai/google-ads-mcp-server** — https://github.com/gomarble-ai/google-ads-mcp-server  
> Modèles : double transport (stdio + HTTP), KeywordPlanIdeaService

> **itallstartedwithaidea/google-ads-api-agent** — https://github.com/itallstartedwithaidea/google-ads-api-agent  
> Modèles : aperçus d'enchères, historique des modifications, créateur de campagnes, gestionnaire de stratégies d'enchères,
> mots-clés négatifs, ciblage géographique, rapports PMax, Architecture Filter-First

Tableau d'attribution détaillé par fonctionnalité : [`docs/SERVICES.md`](docs/SERVICES.md)

---

## Liens connexes

- **[google-ads-skills](https://github.com/itallstartedwithaidea/google-ads-skills)** — Compétences Anthropic Agent pour Claude (analyse, audit, écriture, mathématiques, MCP)
- **[google-ads-api-agent](https://github.com/itallstartedwithaidea/google-ads-api-agent)** — Agent Python complet avec 28 actions API et 6 sous-agents
- **[google-ads-gemini-extension](https://github.com/itallstartedwithaidea/google-ads-gemini-extension)** — Extension Gemini CLI avec 22 outils MCP, compétences, commandes et thèmes
- **[googleadsagent.ai](https://googleadsagent.ai)** — Déploiement en production (Buddy) sur Cloudflare avec mémoire sémantique, facturation et surveillance

---

## Licence

MIT — voir [LICENSE](LICENSE)  
Dépendance `google-ads` : Apache 2.0, Copyright 2023 Google LLC  
FastMCP : Apache 2.0

---

[googleadsagent.ai](https://googleadsagent.ai) · [Documentation API Google Ads](https://developers.google.com/google-ads/api) · [Spécification MCP](https://modelcontextprotocol.io)
