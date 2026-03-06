#!/usr/bin/env python3
"""
Google Ads MCP — Standalone Agent CLI
Runs the full agent loop via the Anthropic API without any MCP server.
Useful for Claude Code workflows, automation, and testing.

Usage:
    python scripts/cli.py
    python scripts/cli.py --single "Show me campaign performance for account 1234567890"
    python scripts/cli.py --model claude-sonnet-4-6
    python scripts/cli.py --verbose

Source: google-ads-api-agent/scripts/cli.py (adapted for MCP tool layer)
"""

import os
import sys
import argparse
import logging
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import anthropic

from ads_mcp.tools.core import (
    list_accessible_customers, list_accounts, execute_gaql,
    get_campaign_performance, get_keyword_performance,
    get_search_terms, get_ad_performance,
    get_account_budget_summary, generate_keyword_ideas,
)
from ads_mcp.tools.audit import (
    get_auction_insights, get_change_history,
    get_device_performance, get_geo_performance,
    get_recommendations, get_pmax_performance, get_impression_share,
)
from ads_mcp.tools.write import (
    update_campaign_budget, update_campaign_status, update_ad_group_status,
    update_keyword_bid, add_keywords, add_negative_keywords,
    remove_negative_keyword, create_campaign, create_ad_group,
    switch_bidding_strategy, generic_mutate,
)
from ads_mcp.tools.docs import get_gaql_reference, get_workflow_guide


# ─── Tool registry: name → callable ───────────────────────────────────────────

TOOLS: dict = {
    # Read
    "list_accessible_customers": list_accessible_customers,
    "list_accounts": list_accounts,
    "execute_gaql": execute_gaql,
    "get_campaign_performance": get_campaign_performance,
    "get_keyword_performance": get_keyword_performance,
    "get_search_terms": get_search_terms,
    "get_ad_performance": get_ad_performance,
    "get_account_budget_summary": get_account_budget_summary,
    "generate_keyword_ideas": generate_keyword_ideas,
    # Audit
    "get_auction_insights": get_auction_insights,
    "get_change_history": get_change_history,
    "get_device_performance": get_device_performance,
    "get_geo_performance": get_geo_performance,
    "get_recommendations": get_recommendations,
    "get_pmax_performance": get_pmax_performance,
    "get_impression_share": get_impression_share,
    # Write (dry-run by default)
    "update_campaign_budget": update_campaign_budget,
    "update_campaign_status": update_campaign_status,
    "update_ad_group_status": update_ad_group_status,
    "update_keyword_bid": update_keyword_bid,
    "add_keywords": add_keywords,
    "add_negative_keywords": add_negative_keywords,
    "remove_negative_keyword": remove_negative_keyword,
    "create_campaign": create_campaign,
    "create_ad_group": create_ad_group,
    "switch_bidding_strategy": switch_bidding_strategy,
    "generic_mutate": generic_mutate,
    # Docs
    "get_gaql_reference": get_gaql_reference,
    "get_workflow_guide": get_workflow_guide,
}

SYSTEM_PROMPT = """You are an expert Google Ads strategist with 15+ years of experience.
You have LIVE API access to read, analyze, AND modify data in Google Ads accounts via tools.

## Core principles

1. CONTEXT FIRST — Before making any API calls, gather context through questions.
   Ask: Which account? Which campaign? What date range? Enabled only or include paused?

2. FILTER AGGRESSIVELY — Always use cost/status filters to reduce result sets.
   Never pull unbounded data dumps.

3. DOLLARS NOT MICROS — All monetary inputs and outputs use dollars. The API
   returns micros; the tools convert automatically.

4. WRITE OPS ARE DRY-RUN BY DEFAULT — All mutate tools show a preview first.
   Always show the preview to the user before confirming execution.
   Never pass confirm=True without the user explicitly approving.

5. EXPLAIN WHAT YOU SEE — Don't just return data. Interpret it. Flag anomalies,
   highlight what matters, and suggest next actions.

## Tool quick reference

Read: list_accounts, execute_gaql, get_campaign_performance, get_keyword_performance,
      get_search_terms, get_ad_performance, get_account_budget_summary, generate_keyword_ideas

Audit: get_auction_insights, get_change_history, get_device_performance,
       get_geo_performance, get_recommendations, get_pmax_performance, get_impression_share

Write (dry-run by default): update_campaign_budget, update_campaign_status,
       update_keyword_bid, add_keywords, add_negative_keywords, create_campaign,
       create_ad_group, switch_bidding_strategy

Docs: get_gaql_reference (call before writing custom GAQL), get_workflow_guide

## GAQL reminders
- Field names: ad_group_criterion.keyword.text (NOT keyword.text)
- Budgets: query campaign_budget resource directly
- String matching: LIKE '%term%' (NOT CONTAINS)
- Dates: 'YYYY-MM-DD' format with dashes
"""


def _build_tool_schemas() -> list[dict]:
    """Build Anthropic tool schema list from Python functions."""
    import inspect

    schemas = []
    for name, fn in TOOLS.items():
        doc = inspect.getdoc(fn) or ""
        sig = inspect.signature(fn)
        props = {}
        required = []

        for param_name, param in sig.parameters.items():
            ptype = "string"
            annotation = param.annotation
            if annotation != inspect.Parameter.empty:
                origin = getattr(annotation, "__origin__", None)
                if annotation in (int,):
                    ptype = "integer"
                elif annotation in (float,):
                    ptype = "number"
                elif annotation in (bool,):
                    ptype = "boolean"
                elif origin is list:
                    ptype = "array"

            prop: dict = {"type": ptype, "description": f"See tool docstring: {param_name}"}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
            elif param.default is not None:
                prop["default"] = param.default

            props[param_name] = prop

        schemas.append({
            "name": name,
            "description": doc[:1000],
            "input_schema": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        })

    return schemas


class GoogleAdsAgent:
    """Standalone agentic loop using the Anthropic API + ads_mcp tools."""

    DEFAULT_MODEL = "claude-sonnet-4-6"
    MAX_TOKENS = 8192
    MAX_ROUNDS = 25

    def __init__(self, api_key: str = None, model: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model or self.DEFAULT_MODEL
        self.tool_schemas = _build_tool_schemas()
        self.history: list[dict] = []

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        return self._loop()

    def _loop(self) -> str:
        for _round in range(self.MAX_ROUNDS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=self.tool_schemas,
                messages=self.history,
            )

            self.history.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content if hasattr(b, "text"))

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                fn = TOOLS.get(block.name)
                if fn is None:
                    result = {"error": f"Unknown tool: {block.name}"}
                else:
                    try:
                        result = fn(**block.input)
                    except Exception as exc:
                        result = {"error": str(exc)}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

            self.history.append({"role": "user", "content": tool_results})

        return "[Agent hit maximum tool rounds — try a more specific request]"

    def reset(self):
        self.history = []


def main():
    parser = argparse.ArgumentParser(description="Google Ads MCP — Agent CLI")
    parser.add_argument("--model", default=None, help="Claude model (default: claude-sonnet-4-6)")
    parser.add_argument("--single", default=None, help="Single message (non-interactive mode)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(name)s | %(message)s",
    )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print("  → Get one at https://console.anthropic.com/settings/keys")
        print("  → Add it to your .env file or run: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    agent = GoogleAdsAgent(model=args.model)

    print("╔══════════════════════════════════════════╗")
    print("║   Google Ads MCP — Agent CLI             ║")
    print("║   Type 'quit' to exit, 'reset' to clear  ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Model : {agent.model}")
    print(f"  Tools : {len(TOOLS)} loaded")
    print()

    if args.single:
        response = agent.chat(args.single)
        print(response)
        return

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("  [Conversation cleared]\n")
            continue

        print("  [thinking…]")
        try:
            response = agent.chat(user_input)
            print(f"\nAgent: {response}\n")
        except Exception as exc:
            print(f"\n  ERROR: {exc}\n")


if __name__ == "__main__":
    main()
