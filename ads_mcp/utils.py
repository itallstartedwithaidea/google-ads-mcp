"""
Shared utilities for Google Ads MCP.

format_value / format_row adapted from googleads/google-ads-mcp (utils.py)
and google-marketing-solutions/google_ads_mcp (tools/api.py).
Both repos solve the proto → Python dict serialization problem; this
implementation consolidates them with support for Repeated fields (repo3).
"""

import json
import logging
from typing import Any

import proto
from google.ads.googleads.util import get_nested_attr

logger = logging.getLogger(__name__)


def format_value(value: Any) -> Any:
    """
    Recursively serialize a proto value to a plain Python type.

    Handles:
    - proto.Enum → name string (repo2 pattern)
    - proto.Message → dict via JSON round-trip (repo3 pattern, avoids
      serialization edge-cases with nested messages)
    - proto.marshal.collections.repeated.Repeated → list (repo3 addition)
    - Everything else → pass-through
    """
    if isinstance(value, proto.marshal.collections.repeated.Repeated):
        return [format_value(i) for i in value]
    if isinstance(value, proto.Message):
        return json.loads(proto.Message.to_json(value, use_integers_for_enums=False))
    if isinstance(value, proto.Enum):
        return value.name
    return value


def format_row(row: proto.Message, fields: list[str]) -> dict[str, Any]:
    """Build a plain dict from a search result row given a list of field paths."""
    return {field: format_value(get_nested_attr(row, field)) for field in fields}


def micros_to_currency(micros: int, decimals: int = 2) -> float:
    """Convert Google Ads micros to currency units (1_000_000 micros = 1 unit)."""
    return round(micros / 1_000_000, decimals)
