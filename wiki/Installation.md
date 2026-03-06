# Installation

## Install the package

```bash
# From PyPI (once published)
pip install googleadsagent-mcp

# From GitHub
pip install git+https://github.com/itallstartedwithaidea/google-ads-mcp.git

# With uv
uv add googleadsagent-mcp

# From source
git clone https://github.com/itallstartedwithaidea/google-ads-mcp.git
cd google-ads-mcp
pip install -e .
```

Requires **Python 3.10+**.

## Configure your MCP client

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["-m", "ads_mcp.server"],
      "env": {
        "GOOGLE_ADS_CREDENTIALS": "/path/to/google-ads.yaml",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "123-456-7890"
      }
    }
  }
}
```

### Claude Code

Place `.mcp.json` in your project root (already included in the repo):

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

### Cursor / Windsurf

Settings → MCP → Add server:
- Command: `python -m ads_mcp.server`

### OpenAI Agents SDK

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
```

### HTTP / Remote

```bash
python -m ads_mcp.server --http
```

Starts an SSE server on `http://localhost:8000` for remote agent connections.

## Environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

See [[Connecting to Google Ads API]] for full credential setup.

## Validate

```bash
python scripts/validate.py
```

This checks that your credentials are valid and the API is reachable.
