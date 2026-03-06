"""
Basic tests for Google Ads MCP utilities.
Auth/API tests require real credentials and are integration tests only.
"""

from ads_mcp.auth import normalize_customer_id
from ads_mcp.utils import micros_to_currency


class TestNormalizeCustomerId:
    def test_strips_dashes(self):
        assert normalize_customer_id("123-456-7890") == "1234567890"

    def test_pads_short_id(self):
        assert normalize_customer_id("12345") == "0000012345"

    def test_strips_quotes(self):
        assert normalize_customer_id('"1234567890"') == "1234567890"

    def test_integer_input(self):
        assert normalize_customer_id(1234567890) == "1234567890"


class TestMicrosToCurrency:
    def test_one_dollar(self):
        assert micros_to_currency(1_000_000) == 1.0

    def test_fractional(self):
        assert micros_to_currency(1_500_000) == 1.5

    def test_zero(self):
        assert micros_to_currency(0) == 0.0
