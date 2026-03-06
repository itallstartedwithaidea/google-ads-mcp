#!/usr/bin/env python3
"""
Google Ads MCP — Deployment Validator
Checks environment, credentials, imports, tool count, and optionally live API.

Usage:
    python scripts/validate.py
    python scripts/validate.py --skip-api    # skip live Google Ads API call
    python scripts/validate.py --skip-claude # skip live Anthropic API call

Source: google-ads-api-agent/scripts/validate.py (adapted for MCP tool layer)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def ok(label: str, detail: str = "") -> bool:
    msg = f"  ✅  {label}"
    if detail:
        msg += f"  — {detail}"
    print(msg)
    return True


def fail(label: str, detail: str = "") -> bool:
    msg = f"  ❌  {label}"
    if detail:
        msg += f"  — {detail}"
    print(msg)
    return False


def warn(label: str, detail: str = ""):
    msg = f"  ⚠️  {label}"
    if detail:
        msg += f"  — {detail}"
    print(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-api", action="store_true", help="Skip live Google Ads API call")
    parser.add_argument("--skip-claude", action="store_true", help="Skip live Anthropic API call")
    args = parser.parse_args()

    results: list[bool] = []
    print()
    print("=" * 60)
    print("  GOOGLE ADS MCP — DEPLOYMENT VALIDATOR")
    print("=" * 60)

    # ── Phase 1: File Structure ────────────────────────────────────────
    print("\n📁  Phase 1: Repository Structure")
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent

    def file_check(path: str) -> bool:
        p = root / path
        if p.exists():
            return ok(path)
        return fail(path, "NOT FOUND")

    results.append(file_check("ads_mcp/auth.py"))
    results.append(file_check("ads_mcp/coordinator.py"))
    results.append(file_check("ads_mcp/server.py"))
    results.append(file_check("ads_mcp/utils.py"))
    results.append(file_check("ads_mcp/tools/core.py"))
    results.append(file_check("ads_mcp/tools/audit.py"))
    results.append(file_check("ads_mcp/tools/write.py"))
    results.append(file_check("ads_mcp/tools/docs.py"))
    results.append(file_check("scripts/cli.py"))
    results.append(file_check("CLAUDE.md"))
    results.append(file_check(".env.example"))

    # ── Phase 2: Package Imports ───────────────────────────────────────
    print("\n📦  Phase 2: Package Imports")

    try:
        import anthropic

        results.append(ok("anthropic SDK", f"v{anthropic.__version__}"))
    except ImportError:
        results.append(fail("anthropic SDK", "pip install anthropic"))

    try:
        import google.ads.googleads

        results.append(ok("google-ads SDK", f"v{google.ads.googleads.__version__}"))
    except ImportError:
        results.append(fail("google-ads SDK", "pip install google-ads"))

    try:
        import fastmcp

        results.append(ok("fastmcp", f"v{fastmcp.__version__}"))
    except ImportError:
        results.append(fail("fastmcp", "pip install fastmcp"))

    try:
        import yaml  # noqa: F401

        results.append(ok("pyyaml"))
    except ImportError:
        warn("pyyaml not installed — YAML credential file won't work", "pip install pyyaml")

    # ── Phase 3: Tool Registration ─────────────────────────────────────
    print("\n🔧  Phase 3: Tool Registration")
    try:
        from ads_mcp.coordinator import mcp
        from ads_mcp.tools import audit, core, docs, write  # noqa: F401

        tool_list = list(mcp._tool_manager._tools.keys()) if hasattr(mcp, "_tool_manager") else []
        if not tool_list:
            # fallback count from scripts/cli.py
            from scripts.cli import TOOLS

            tool_list = list(TOOLS.keys())
        n = len(tool_list)
        if n >= 20:
            results.append(ok("Tool registration", f"{n} tools registered"))
        else:
            results.append(fail("Tool registration", f"Only {n} tools — expected 20+"))
    except Exception as exc:
        results.append(fail("Tool registration", str(exc)))

    # ── Phase 4: Environment Variables ────────────────────────────────
    print("\n🔑  Phase 4: Environment Variables")

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key.startswith("sk-ant-"):
        results.append(ok("ANTHROPIC_API_KEY", "set"))
    elif anthropic_key:
        results.append(warn("ANTHROPIC_API_KEY", "set but unexpected format") or True)
    else:
        results.append(fail("ANTHROPIC_API_KEY", "NOT SET — required for standalone CLI"))

    # Google Ads credentials — one of these paths must work
    yaml_path = os.environ.get("GOOGLE_ADS_CREDENTIALS")
    oauth_path = os.environ.get("GOOGLE_ADS_OAUTH_CONFIG_PATH")
    dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")

    if yaml_path and Path(yaml_path).exists():
        results.append(ok("GOOGLE_ADS_CREDENTIALS", f"YAML file exists at {yaml_path}"))
    elif yaml_path:
        results.append(fail("GOOGLE_ADS_CREDENTIALS", f"File not found: {yaml_path}"))
    elif oauth_path and Path(oauth_path).exists():
        results.append(ok("GOOGLE_ADS_OAUTH_CONFIG_PATH", "OAuth JSON file exists"))
    elif dev_token:
        # Check for full env-var credential set
        needed = ["GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN"]
        missing = [k for k in needed if not os.environ.get(k)]
        if not missing:
            results.append(ok("Google Ads env vars", "Full credential set present"))
        else:
            results.append(fail("Google Ads env vars", f"Missing: {', '.join(missing)}"))
    else:
        results.append(
            fail(
                "Google Ads credentials",
                "No credentials found. Set GOOGLE_ADS_CREDENTIALS (path to google-ads.yaml), "
                "OR set GOOGLE_ADS_DEVELOPER_TOKEN + CLIENT_ID + CLIENT_SECRET + REFRESH_TOKEN",
            )
        )

    login_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if login_id:
        results.append(ok("GOOGLE_ADS_LOGIN_CUSTOMER_ID", login_id))
    else:
        warn("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "not set — required for MCC accounts")

    # ── Phase 5: Live API Calls ────────────────────────────────────────
    if not args.skip_api:
        print("\n🌐  Phase 5: Live Google Ads API")
        try:
            from ads_mcp.auth import get_ads_client

            client = get_ads_client()
            customer_service = client.get_service("CustomerService")
            result = customer_service.list_accessible_customers()
            count = len(result.resource_names)
            results.append(ok("Google Ads API connection", f"{count} accessible account(s)"))
        except Exception as exc:
            results.append(fail("Google Ads API connection", str(exc)))
    else:
        print("\n🌐  Phase 5: Live Google Ads API — SKIPPED (--skip-api)")

    if not args.skip_claude:
        print("\n🤖  Phase 6: Live Anthropic API")
        try:
            import anthropic as anth

            c = anth.Anthropic()
            resp = c.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=20,
                messages=[{"role": "user", "content": "Say 'OK'"}],
            )
            results.append(ok("Anthropic API", f"Response: {resp.content[0].text.strip()}"))
        except Exception as exc:
            results.append(fail("Anthropic API", str(exc)))
    else:
        print("\n🤖  Phase 6: Anthropic API — SKIPPED (--skip-claude)")

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    if passed == total:
        print(f"  🎉  All {total} checks passed — ready to go!")
    else:
        print(f"  ⚠️   {passed}/{total} checks passed — fix issues above before proceeding")
    print("=" * 60)
    print()

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
