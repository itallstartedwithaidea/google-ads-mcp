# googleadsagent-mcp

一个用于 Google Ads API 的 MCP（Model Context Protocol）服务器 + 独立代理 SDK。  
由 [googleadsagent.ai](https://googleadsagent.ai) 构建 · MIT 许可证

[English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh.md) | [Nederlands](README.nl.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

---

## 安装

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

## 兼容所有 MCP 客户端

| 客户端 | 传输方式 | 配置 |
|---|---|---|
| **Claude Code** | stdio | 项目根目录的 `.mcp.json`（已包含） |
| **Claude Desktop** | stdio | `claude_desktop_config.example.json` |
| **Cursor / Windsurf** | stdio | 设置 → MCP → `python -m ads_mcp.server` |
| **OpenAI Agents SDK** | stdio | `MCPServerStdio(command="python", args=["-m", "ads_mcp.server"])` |
| **LangChain** | stdio | `langchain-mcp-adapters` |
| **远程 / 云端** | HTTP SSE | `python -m ads_mcp.server --http` |

---

## 快速开始

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

将 `.mcp.json` 放置在项目根目录（已包含）：

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

Claude Code 会自动发现 `.mcp.json`。`CLAUDE.md` 是专门为 Claude Code 编写的定向文件——每次会话开始时会首先读取它。

---

## Gemini CLI

添加到项目的 `.gemini/settings.json` 中：

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

要了解包含 Google Ads 斜杠命令和代理技能的完整 Gemini CLI 设置，请参阅
[gemini-cli-googleadsagent](https://github.com/itallstartedwithaidea/gemini-cli-googleadsagent)。

**远程选项** — 如果您在 Cloudflare Workers 上部署了
[buddy-agent](https://github.com/itallstartedwithaidea/googleadsagent-site/tree/main/workers/buddy-agent)，
可以完全跳过本地凭据，通过 SSE 连接：

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

## 工具参考

### 读取工具
`list_accessible_customers` · `list_accounts` · `execute_gaql` · `get_campaign_performance`
`get_keyword_performance` · `get_search_terms` · `get_ad_performance` · `get_account_budget_summary`
`generate_keyword_ideas`

### 审计工具
`get_auction_insights` · `get_change_history` · `get_device_performance` · `get_geo_performance`
`get_recommendations` · `get_pmax_performance` · `get_impression_share`

### 写入工具（默认模拟运行 — 需要 `confirm=True`）
`update_campaign_budget` · `update_campaign_status` · `update_ad_group_status` · `update_keyword_bid`
`add_keywords` · `add_negative_keywords` · `remove_negative_keyword` · `create_campaign`
`create_ad_group` · `switch_bidding_strategy` · `generic_mutate`

### 文档工具
`get_gaql_reference` · `get_workflow_guide`

---

## 凭据

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

完整凭据设置指南：[google-ads-api-agent README → 步骤 1A](https://github.com/itallstartedwithaidea/google-ads-api-agent#1a-google-ads-api-credentials)

---

## v23 服务覆盖

Google Ads API v23 拥有 70 多项服务。当前状态：
- ✅ **已实现 29 个工具** — 核心报告、审计、写入操作、文档参考
- 🔧 **计划中 42 项服务** — 完整路线图见 [`docs/SERVICES.md`](docs/SERVICES.md)
- ⬜ **约 20 项超出范围** — 平台管理、已弃用、LSA 专属

---

## 归属声明

### Google LLC (Apache 2.0)

> **google-ads Python 客户端库** — Copyright 2023 Google LLC  
> https://github.com/googleads/google-ads-python  
> 本包中的所有 API 调用均使用 Google 发布的 `google-ads` pip 包。
> v23 服务定义、proto 类型和 gRPC 客户端均为 Google 的成果。

> **googleads/google-ads-mcp** — https://github.com/googleads/google-ads-mcp  
> 模式：MCP 单例、`search_stream` + `field_mask.paths`

> **google-marketing-solutions/google_ads_mcp** — https://github.com/google-marketing-solutions/google_ads_mcp  
> 模式：文档服务 MCP 工具、远程 OAuth、`omit_unselected_resource_names`

### 社区 (MIT)

> **cohnen/mcp-google-ads** — https://github.com/cohnen/mcp-google-ads  
> 模式：`format_value` proto 序列化辅助工具

> **gomarble-ai/google-ads-mcp-server** — https://github.com/gomarble-ai/google-ads-mcp-server  
> 模式：双传输（stdio + HTTP）、KeywordPlanIdeaService

> **itallstartedwithaidea/google-ads-api-agent** — https://github.com/itallstartedwithaidea/google-ads-api-agent  
> 模式：竞价洞察、变更历史、广告系列创建器、出价策略管理器、
> 否定关键词、地理定位、PMax 报告、Filter-First 架构

按功能的详细归属表：[`docs/SERVICES.md`](docs/SERVICES.md)

---

## 相关项目

- **[google-ads-skills](https://github.com/itallstartedwithaidea/google-ads-skills)** — 用于 Claude 的 Anthropic Agent 技能（分析、审计、写入、数学、MCP）
- **[google-ads-api-agent](https://github.com/itallstartedwithaidea/google-ads-api-agent)** — 完整的 Python 代理，包含 28 个 API 操作和 6 个子代理
- **[google-ads-gemini-extension](https://github.com/itallstartedwithaidea/google-ads-gemini-extension)** — Gemini CLI 扩展，包含 22 个 MCP 工具、技能、命令和主题
- **[googleadsagent.ai](https://googleadsagent.ai)** — 生产部署（Buddy），运行在 Cloudflare 上，具备语义记忆、计费和监控功能

---

## 许可证

MIT — 参见 [LICENSE](LICENSE)  
`google-ads` 依赖：Apache 2.0，Copyright 2023 Google LLC  
FastMCP：Apache 2.0

---

[googleadsagent.ai](https://googleadsagent.ai) · [Google Ads API 文档](https://developers.google.com/google-ads/api) · [MCP 规范](https://modelcontextprotocol.io)
