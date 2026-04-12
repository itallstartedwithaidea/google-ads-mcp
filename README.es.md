# googleadsagent-mcp

Un servidor MCP (Model Context Protocol) + SDK de agente autónomo para la API de Google Ads.  
Creado por [googleadsagent.ai](https://googleadsagent.ai) · Licencia MIT

[English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh.md) | [Nederlands](README.nl.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

---

## Instalación

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

## Compatible con todos los clientes MCP

| Cliente | Transporte | Configuración |
|---|---|---|
| **Claude Code** | stdio | `.mcp.json` en la raíz del proyecto (incluido) |
| **Claude Desktop** | stdio | `claude_desktop_config.example.json` |
| **Cursor / Windsurf** | stdio | Ajustes → MCP → `python -m ads_mcp.server` |
| **OpenAI Agents SDK** | stdio | `MCPServerStdio(command="python", args=["-m", "ads_mcp.server"])` |
| **LangChain** | stdio | `langchain-mcp-adapters` |
| **Remoto / Cloud** | HTTP SSE | `python -m ads_mcp.server --http` |

---

## Inicio rápido

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

Coloca `.mcp.json` en la raíz de tu proyecto (ya incluido):

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

Claude Code detecta automáticamente `.mcp.json`. `CLAUDE.md` está escrito específicamente para que Claude Code
se oriente — lo lee primero en cada sesión.

---

## Gemini CLI

Añade a tu archivo `.gemini/settings.json` del proyecto:

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

Para la configuración completa de Gemini CLI con comandos slash de Google Ads y habilidades de agente, consulta
[gemini-cli-googleadsagent](https://github.com/itallstartedwithaidea/gemini-cli-googleadsagent).

**Opción remota** — si despliegas el
[buddy-agent](https://github.com/itallstartedwithaidea/googleadsagent-site/tree/main/workers/buddy-agent)
en Cloudflare Workers, puedes omitir las credenciales locales y conectarte vía SSE:

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

## Referencia de herramientas

### Herramientas de lectura
`list_accessible_customers` · `list_accounts` · `execute_gaql` · `get_campaign_performance`
`get_keyword_performance` · `get_search_terms` · `get_ad_performance` · `get_account_budget_summary`
`generate_keyword_ideas`

### Herramientas de auditoría
`get_auction_insights` · `get_change_history` · `get_device_performance` · `get_geo_performance`
`get_recommendations` · `get_pmax_performance` · `get_impression_share`

### Herramientas de escritura (simulación por defecto — requiere `confirm=True`)
`update_campaign_budget` · `update_campaign_status` · `update_ad_group_status` · `update_keyword_bid`
`add_keywords` · `add_negative_keywords` · `remove_negative_keyword` · `create_campaign`
`create_ad_group` · `switch_bidding_strategy` · `generic_mutate`

### Herramientas de documentación
`get_gaql_reference` · `get_workflow_guide`

---

## Credenciales

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

Guía completa de configuración de credenciales: [google-ads-api-agent README → Paso 1A](https://github.com/itallstartedwithaidea/google-ads-api-agent#1a-google-ads-api-credentials)

---

## Cobertura de servicios v23

La API de Google Ads v23 tiene más de 70 servicios. Estado actual:
- ✅ **29 herramientas implementadas** — informes principales, auditoría, operaciones de escritura, referencias documentales
- 🔧 **42 servicios planificados** — hoja de ruta completa en [`docs/SERVICES.md`](docs/SERVICES.md)
- ⬜ **~20 fuera de alcance** — administración de plataforma, obsoletos, específicos de LSA

---

## Atribución

### Google LLC (Apache 2.0)

> **Biblioteca cliente Python google-ads** — Copyright 2023 Google LLC  
> https://github.com/googleads/google-ads-python  
> Todas las llamadas API en este paquete utilizan el paquete pip `google-ads` publicado por Google.
> Las definiciones de servicios v23, tipos proto y clientes gRPC son obra de Google.

> **googleads/google-ads-mcp** — https://github.com/googleads/google-ads-mcp  
> Patrones: singleton MCP, `search_stream` + `field_mask.paths`

> **google-marketing-solutions/google_ads_mcp** — https://github.com/google-marketing-solutions/google_ads_mcp  
> Patrones: herramientas MCP de documentación, OAuth remoto, `omit_unselected_resource_names`

### Comunidad (MIT)

> **cohnen/mcp-google-ads** — https://github.com/cohnen/mcp-google-ads  
> Patrones: asistente de serialización proto `format_value`

> **gomarble-ai/google-ads-mcp-server** — https://github.com/gomarble-ai/google-ads-mcp-server  
> Patrones: transporte dual (stdio + HTTP), KeywordPlanIdeaService

> **itallstartedwithaidea/google-ads-api-agent** — https://github.com/itallstartedwithaidea/google-ads-api-agent  
> Patrones: información de subastas, historial de cambios, creador de campañas, gestor de estrategias de puja,
> palabras clave negativas, segmentación geográfica, informes PMax, Arquitectura Filter-First

Tabla de atribución detallada por funcionalidad: [`docs/SERVICES.md`](docs/SERVICES.md)

---

## Relacionados

- **[google-ads-skills](https://github.com/itallstartedwithaidea/google-ads-skills)** — Habilidades Anthropic Agent para Claude (análisis, auditoría, escritura, matemáticas, MCP)
- **[google-ads-api-agent](https://github.com/itallstartedwithaidea/google-ads-api-agent)** — Agente Python completo con 28 acciones API y 6 sub-agentes
- **[google-ads-gemini-extension](https://github.com/itallstartedwithaidea/google-ads-gemini-extension)** — Extensión Gemini CLI con 22 herramientas MCP, habilidades, comandos y temas
- **[googleadsagent.ai](https://googleadsagent.ai)** — Despliegue en producción (Buddy) en Cloudflare con memoria semántica, facturación y monitorización

---

## Licencia

MIT — ver [LICENSE](LICENSE)  
Dependencia `google-ads`: Apache 2.0, Copyright 2023 Google LLC  
FastMCP: Apache 2.0

---

[googleadsagent.ai](https://googleadsagent.ai) · [Documentación API de Google Ads](https://developers.google.com/google-ads/api) · [Especificación MCP](https://modelcontextprotocol.io)
