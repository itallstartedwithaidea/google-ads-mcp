"""
Authentication module for Google Ads MCP.

Design synthesis:
- cohnen/mcp-google-ads    → OAuth + service account dual-mode, token persistence,
                             customer ID normalization
- gomarble-ai/google-ads-mcp-server → Clean OAuth separation into its own module,
                             auto-refresh flow with local server fallback to console
- googleads/google-ads-mcp  → Application Default Credentials (ADC) support,
                             grpc interceptor pattern (not replicated here but noted)
- google-marketing-solutions → google-ads.yaml as primary credential source,
                             access_token injection for OAuth provider flows

This module unifies all four approaches into a single flexible auth layer that
supports three credential strategies, in priority order:
  1. Injected access token (for remote OAuth provider flows — repo3 pattern)
  2. google-ads.yaml file (repo2 / repo3 pattern)
  3. OAuth 2.0 client credentials with auto token persistence (repo1 / repo4 pattern)
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/adwords"]
GOOGLE_ADS_API_VERSION = "v19"

# ─── Environment variable resolution ──────────────────────────────────────────

DEVELOPER_TOKEN: str = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
LOGIN_CUSTOMER_ID: str = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
CREDENTIALS_YAML: str = os.environ.get(
    "GOOGLE_ADS_CREDENTIALS",
    str(Path.home() / "google-ads.yaml"),
)
OAUTH_CONFIG_PATH: str = os.environ.get("GOOGLE_ADS_OAUTH_CONFIG_PATH", "")

# ─── Customer ID utilities ─────────────────────────────────────────────────────


def normalize_customer_id(raw: str) -> str:
    """
    Normalize a Google Ads customer ID to a 10-digit string with no dashes.

    Handles all common formats: '123-456-7890', '1234567890', '"1234567890"'.
    Source: cohnen/mcp-google-ads, gomarble-ai/google-ads-mcp-server.
    """
    cid = str(raw).replace('"', "").replace("'", "")
    cid = "".join(ch for ch in cid if ch.isdigit())
    return cid.zfill(10)


# ─── GoogleAdsClient factory ───────────────────────────────────────────────────


def _client_from_yaml(access_token: Optional[str] = None) -> GoogleAdsClient:
    """
    Build a GoogleAdsClient from a google-ads.yaml file.

    If `access_token` is provided (e.g. from a remote OAuth provider), it
    overrides the refresh-token-based credentials in the YAML — this is the
    pattern used by google-marketing-solutions/google_ads_mcp for their
    GoogleProvider flow.
    """
    if not os.path.isfile(CREDENTIALS_YAML):
        raise FileNotFoundError(
            f"google-ads.yaml not found at '{CREDENTIALS_YAML}'. "
            "Set GOOGLE_ADS_CREDENTIALS env var or place the file in your home directory."
        )

    if access_token:
        import yaml

        with open(CREDENTIALS_YAML, "r", encoding="utf-8") as f:
            ads_config = yaml.safe_load(f)
        creds = Credentials(access_token)
        return GoogleAdsClient(
            credentials=creds,
            developer_token=ads_config.get("developer_token", DEVELOPER_TOKEN),
            login_customer_id=LOGIN_CUSTOMER_ID or ads_config.get("login_customer_id"),
        )

    return GoogleAdsClient.load_from_storage(CREDENTIALS_YAML)


def _client_from_oauth() -> GoogleAdsClient:
    """
    Build a GoogleAdsClient using saved / refreshed OAuth user credentials.

    Token persistence logic from cohnen/mcp-google-ads and
    gomarble-ai/google-ads-mcp-server: tokens are cached to disk next to the
    OAuth config file and auto-refreshed on expiry.
    """
    if not OAUTH_CONFIG_PATH:
        raise ValueError(
            "GOOGLE_ADS_OAUTH_CONFIG_PATH env var not set. "
            "Point it at your OAuth client secret JSON file."
        )
    if not os.path.exists(OAUTH_CONFIG_PATH):
        raise FileNotFoundError(f"OAuth config not found: {OAUTH_CONFIG_PATH}")
    if not DEVELOPER_TOKEN:
        raise ValueError("GOOGLE_ADS_DEVELOPER_TOKEN env var not set.")

    config_dir = Path(OAUTH_CONFIG_PATH).parent
    token_path = config_dir / "google_ads_token.json"

    creds: Optional[Credentials] = None

    # Load cached token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            logger.info("Loaded cached OAuth token from %s", token_path)
        except Exception as exc:
            logger.warning("Could not load cached token: %s", exc)

    # Refresh or re-authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired OAuth token …")
                creds.refresh(Request())
            except RefreshError as exc:
                logger.warning("Refresh failed (%s); will re-authorize.", exc)
                creds = None
        if not creds:
            from google_auth_oauthlib.flow import InstalledAppFlow

            with open(OAUTH_CONFIG_PATH) as f:
                client_config = json.load(f)
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            try:
                creds = flow.run_local_server(port=0)
                logger.info("OAuth complete via local server.")
            except Exception:
                creds = flow.run_console()
                logger.info("OAuth complete via console.")

        # Persist refreshed / new token
        try:
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
        except Exception as exc:
            logger.warning("Could not persist token: %s", exc)

    return GoogleAdsClient(
        credentials=creds,
        developer_token=DEVELOPER_TOKEN,
        login_customer_id=LOGIN_CUSTOMER_ID or None,
    )


# ─── Public API ───────────────────────────────────────────────────────────────

_cached_client: Optional[GoogleAdsClient] = None


def get_ads_client(access_token: Optional[str] = None) -> GoogleAdsClient:
    """
    Return a configured GoogleAdsClient using the best available strategy.

    Priority:
      1. Injected access_token (remote OAuth provider)
      2. google-ads.yaml  (standard YAML-based credentials)
      3. GOOGLE_ADS_OAUTH_CONFIG_PATH  (desktop OAuth flow)

    The client is cached after first construction (unless an access_token is
    provided, which bypasses the cache to ensure freshness).
    """
    global _cached_client

    if access_token:
        return _client_from_yaml(access_token=access_token)

    if _cached_client:
        return _cached_client

    if os.path.isfile(CREDENTIALS_YAML):
        _cached_client = _client_from_yaml()
    elif OAUTH_CONFIG_PATH:
        _cached_client = _client_from_oauth()
    else:
        raise EnvironmentError(
            "No credentials found. Provide one of:\n"
            "  • GOOGLE_ADS_CREDENTIALS pointing to a google-ads.yaml\n"
            "  • GOOGLE_ADS_OAUTH_CONFIG_PATH pointing to an OAuth client JSON"
        )

    return _cached_client
