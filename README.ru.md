# googleadsagent-mcp

MCP (Model Context Protocol) сервер + автономный агентский SDK для Google Ads API.  
Создано [googleadsagent.ai](https://googleadsagent.ai) · Лицензия MIT

[English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh.md) | [Nederlands](README.nl.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

---

## Установка

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

## Работает с любым MCP-клиентом

| Клиент | Транспорт | Конфигурация |
|---|---|---|
| **Claude Code** | stdio | `.mcp.json` в корне проекта (включён) |
| **Claude Desktop** | stdio | `claude_desktop_config.example.json` |
| **Cursor / Windsurf** | stdio | Настройки → MCP → `python -m ads_mcp.server` |
| **OpenAI Agents SDK** | stdio | `MCPServerStdio(command="python", args=["-m", "ads_mcp.server"])` |
| **LangChain** | stdio | `langchain-mcp-adapters` |
| **Удалённый / Облако** | HTTP SSE | `python -m ads_mcp.server --http` |

---

## Быстрый старт

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

Поместите `.mcp.json` в корень вашего проекта (уже включён):

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

Claude Code автоматически обнаруживает `.mcp.json`. `CLAUDE.md` написан специально для ориентации Claude Code — он читает этот файл первым при каждой сессии.

---

## Gemini CLI

Добавьте в файл `.gemini/settings.json` вашего проекта:

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

Полное руководство по настройке Gemini CLI с командами Google Ads и навыками агента см. в
[gemini-cli-googleadsagent](https://github.com/itallstartedwithaidea/gemini-cli-googleadsagent).

**Удалённый вариант** — если вы развернули
[buddy-agent](https://github.com/itallstartedwithaidea/googleadsagent-site/tree/main/workers/buddy-agent)
на Cloudflare Workers, можно полностью обойтись без локальных учётных данных и подключиться через SSE:

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

## Справочник инструментов

### Инструменты чтения
`list_accessible_customers` · `list_accounts` · `execute_gaql` · `get_campaign_performance`
`get_keyword_performance` · `get_search_terms` · `get_ad_performance` · `get_account_budget_summary`
`generate_keyword_ideas`

### Инструменты аудита
`get_auction_insights` · `get_change_history` · `get_device_performance` · `get_geo_performance`
`get_recommendations` · `get_pmax_performance` · `get_impression_share`

### Инструменты записи (пробный режим по умолчанию — требуется `confirm=True`)
`update_campaign_budget` · `update_campaign_status` · `update_ad_group_status` · `update_keyword_bid`
`add_keywords` · `add_negative_keywords` · `remove_negative_keyword` · `create_campaign`
`create_ad_group` · `switch_bidding_strategy` · `generic_mutate`

### Инструменты документации
`get_gaql_reference` · `get_workflow_guide`

---

## Учётные данные

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

Полное руководство по настройке учётных данных: [google-ads-api-agent README → Шаг 1A](https://github.com/itallstartedwithaidea/google-ads-api-agent#1a-google-ads-api-credentials)

---

## Покрытие сервисов v23

Google Ads API v23 включает более 70 сервисов. Текущий статус:
- ✅ **29 инструментов реализовано** — основные отчёты, аудит, операции записи, справочные материалы
- 🔧 **42 сервиса запланировано** — полная дорожная карта в [`docs/SERVICES.md`](docs/SERVICES.md)
- ⬜ **~20 вне области охвата** — администрирование платформы, устаревшие, специфичные для LSA

---

## Атрибуция

### Google LLC (Apache 2.0)

> **Клиентская библиотека google-ads для Python** — Copyright 2023 Google LLC  
> https://github.com/googleads/google-ads-python  
> Все API-вызовы в этом пакете используют pip-пакет `google-ads`, опубликованный Google.
> Определения сервисов v23, proto-типы и gRPC-клиенты — работа Google.

> **googleads/google-ads-mcp** — https://github.com/googleads/google-ads-mcp  
> Паттерны: MCP-синглтон, `search_stream` + `field_mask.paths`

> **google-marketing-solutions/google_ads_mcp** — https://github.com/google-marketing-solutions/google_ads_mcp  
> Паттерны: MCP-инструменты документации, удалённый OAuth, `omit_unselected_resource_names`

### Сообщество (MIT)

> **cohnen/mcp-google-ads** — https://github.com/cohnen/mcp-google-ads  
> Паттерны: вспомогательная функция сериализации proto `format_value`

> **gomarble-ai/google-ads-mcp-server** — https://github.com/gomarble-ai/google-ads-mcp-server  
> Паттерны: двойной транспорт (stdio + HTTP), KeywordPlanIdeaService

> **itallstartedwithaidea/google-ads-api-agent** — https://github.com/itallstartedwithaidea/google-ads-api-agent  
> Паттерны: аналитика аукционов, история изменений, создатель кампаний, менеджер стратегий назначения ставок,
> минус-слова, географический таргетинг, отчёты PMax, архитектура Filter-First

Полная таблица атрибуции по функциям: [`docs/SERVICES.md`](docs/SERVICES.md)

---

## Связанные проекты

- **[google-ads-skills](https://github.com/itallstartedwithaidea/google-ads-skills)** — Навыки Anthropic Agent для Claude (анализ, аудит, запись, математика, MCP)
- **[google-ads-api-agent](https://github.com/itallstartedwithaidea/google-ads-api-agent)** — Полноценный Python-агент с 28 API-действиями и 6 суб-агентами
- **[google-ads-gemini-extension](https://github.com/itallstartedwithaidea/google-ads-gemini-extension)** — Расширение Gemini CLI с 22 MCP-инструментами, навыками, командами и темами
- **[googleadsagent.ai](https://googleadsagent.ai)** — Продакшн-развёртывание (Buddy) на Cloudflare с семантической памятью, биллингом и мониторингом

---

## Лицензия

MIT — см. [LICENSE](LICENSE)  
Зависимость `google-ads`: Apache 2.0, Copyright 2023 Google LLC  
FastMCP: Apache 2.0

---

[googleadsagent.ai](https://googleadsagent.ai) · [Документация Google Ads API](https://developers.google.com/google-ads/api) · [Спецификация MCP](https://modelcontextprotocol.io)
