# googleadsagent-mcp

Google Ads API를 위한 MCP (Model Context Protocol) 서버 + 독립형 에이전트 SDK.  
[googleadsagent.ai](https://googleadsagent.ai)에서 개발 · MIT 라이선스

[English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh.md) | [Nederlands](README.nl.md) | [Русский](README.ru.md) | [한국어](README.ko.md)

---

## 설치

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

## 모든 MCP 클라이언트와 호환

| 클라이언트 | 전송 방식 | 설정 |
|---|---|---|
| **Claude Code** | stdio | 프로젝트 루트의 `.mcp.json` (포함됨) |
| **Claude Desktop** | stdio | `claude_desktop_config.example.json` |
| **Cursor / Windsurf** | stdio | 설정 → MCP → `python -m ads_mcp.server` |
| **OpenAI Agents SDK** | stdio | `MCPServerStdio(command="python", args=["-m", "ads_mcp.server"])` |
| **LangChain** | stdio | `langchain-mcp-adapters` |
| **원격 / 클라우드** | HTTP SSE | `python -m ads_mcp.server --http` |

---

## 빠른 시작

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

프로젝트 루트에 `.mcp.json`을 배치하세요 (이미 포함됨):

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

Claude Code는 `.mcp.json`을 자동으로 감지합니다. `CLAUDE.md`는 Claude Code가 방향을 잡을 수 있도록 특별히 작성되었으며, 매 세션마다 가장 먼저 읽습니다.

---

## Gemini CLI

프로젝트의 `.gemini/settings.json`에 추가하세요:

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

Google Ads 슬래시 명령어와 에이전트 스킬을 포함한 전체 Gemini CLI 설정은
[gemini-cli-googleadsagent](https://github.com/itallstartedwithaidea/gemini-cli-googleadsagent)를 참조하세요.

**원격 옵션** — Cloudflare Workers에
[buddy-agent](https://github.com/itallstartedwithaidea/googleadsagent-site/tree/main/workers/buddy-agent)를
배포하면 로컬 자격 증명 없이 SSE로 직접 연결할 수 있습니다:

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

## 도구 참조

### 읽기 도구
`list_accessible_customers` · `list_accounts` · `execute_gaql` · `get_campaign_performance`
`get_keyword_performance` · `get_search_terms` · `get_ad_performance` · `get_account_budget_summary`
`generate_keyword_ideas`

### 감사 도구
`get_auction_insights` · `get_change_history` · `get_device_performance` · `get_geo_performance`
`get_recommendations` · `get_pmax_performance` · `get_impression_share`

### 쓰기 도구 (기본적으로 시뮬레이션 — `confirm=True` 필요)
`update_campaign_budget` · `update_campaign_status` · `update_ad_group_status` · `update_keyword_bid`
`add_keywords` · `add_negative_keywords` · `remove_negative_keyword` · `create_campaign`
`create_ad_group` · `switch_bidding_strategy` · `generic_mutate`

### 문서 도구
`get_gaql_reference` · `get_workflow_guide`

---

## 자격 증명

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

전체 자격 증명 설정 가이드: [google-ads-api-agent README → 1A 단계](https://github.com/itallstartedwithaidea/google-ads-api-agent#1a-google-ads-api-credentials)

---

## v23 서비스 커버리지

Google Ads API v23에는 70개 이상의 서비스가 있습니다. 현재 상태:
- ✅ **29개 도구 구현 완료** — 핵심 리포팅, 감사, 쓰기 작업, 문서 참조
- 🔧 **42개 서비스 계획 중** — 전체 로드맵은 [`docs/SERVICES.md`](docs/SERVICES.md) 참조
- ⬜ **약 20개 범위 밖** — 플랫폼 관리, 지원 중단, LSA 전용

---

## 저작자 표시

### Google LLC (Apache 2.0)

> **google-ads Python 클라이언트 라이브러리** — Copyright 2023 Google LLC  
> https://github.com/googleads/google-ads-python  
> 이 패키지의 모든 API 호출은 Google이 배포한 `google-ads` pip 패키지를 사용합니다.
> v23 서비스 정의, proto 타입 및 gRPC 클라이언트는 Google의 저작물입니다.

> **googleads/google-ads-mcp** — https://github.com/googleads/google-ads-mcp  
> 패턴: MCP 싱글톤, `search_stream` + `field_mask.paths`

> **google-marketing-solutions/google_ads_mcp** — https://github.com/google-marketing-solutions/google_ads_mcp  
> 패턴: 문서 제공 MCP 도구, 원격 OAuth, `omit_unselected_resource_names`

### 커뮤니티 (MIT)

> **cohnen/mcp-google-ads** — https://github.com/cohnen/mcp-google-ads  
> 패턴: `format_value` proto 직렬화 헬퍼

> **gomarble-ai/google-ads-mcp-server** — https://github.com/gomarble-ai/google-ads-mcp-server  
> 패턴: 이중 전송 (stdio + HTTP), KeywordPlanIdeaService

> **itallstartedwithaidea/google-ads-api-agent** — https://github.com/itallstartedwithaidea/google-ads-api-agent  
> 패턴: 경매 인사이트, 변경 이력, 캠페인 생성기, 입찰 전략 관리자,
> 제외 키워드, 지역 타겟팅, PMax 리포팅, Filter-First 아키텍처

기능별 상세 저작자 표시 테이블: [`docs/SERVICES.md`](docs/SERVICES.md)

---

## 관련 프로젝트

- **[google-ads-skills](https://github.com/itallstartedwithaidea/google-ads-skills)** — Claude용 Anthropic Agent 스킬 (분석, 감사, 쓰기, 수학, MCP)
- **[google-ads-api-agent](https://github.com/itallstartedwithaidea/google-ads-api-agent)** — 28개 API 액션과 6개 서브 에이전트를 갖춘 완전한 Python 에이전트
- **[google-ads-gemini-extension](https://github.com/itallstartedwithaidea/google-ads-gemini-extension)** — 22개 MCP 도구, 스킬, 명령어 및 테마를 갖춘 Gemini CLI 확장
- **[googleadsagent.ai](https://googleadsagent.ai)** — Cloudflare 기반 프로덕션 배포 (Buddy), 시맨틱 메모리, 빌링 및 모니터링 포함

---

## 라이선스

MIT — [LICENSE](LICENSE) 참조  
`google-ads` 의존성: Apache 2.0, Copyright 2023 Google LLC  
FastMCP: Apache 2.0

---

[googleadsagent.ai](https://googleadsagent.ai) · [Google Ads API 문서](https://developers.google.com/google-ads/api) · [MCP 사양](https://modelcontextprotocol.io)
