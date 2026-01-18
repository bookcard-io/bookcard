# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Tests for selenium cookie store module."""

import time
from unittest.mock import MagicMock

import pytest

from bookcard.pvr.download_clients.direct_http.bypass.selenium.cookie_store import (
    ThreadSafeCookieStore,
    ThreadSafeUserAgentStore,
    _get_base_domain,
    _should_extract_cookie,
)


class TestGetBaseDomain:
    """Test _get_base_domain function."""

    @pytest.mark.parametrize(
        ("domain", "expected"),
        [
            ("www.example.com", "example.com"),
            ("subdomain.example.com", "example.com"),
            ("example.com", "example.com"),
            ("test.co.uk", "co.uk"),
        ],
    )
    def test_get_base_domain(self, domain: str, expected: str) -> None:
        """Test _get_base_domain function."""
        result = _get_base_domain(domain)
        assert result == expected


class TestShouldExtractCookie:
    """Test _should_extract_cookie function."""

    def test_extract_all_true(self) -> None:
        """Test with extract_all=True."""
        assert _should_extract_cookie("any_cookie", extract_all=True) is True

    def test_extract_cf_cookie(self) -> None:
        """Test with CF cookie."""
        assert _should_extract_cookie("cf_clearance", extract_all=False) is True
        assert _should_extract_cookie("__cf_bm", extract_all=False) is True
        assert _should_extract_cookie("cf_chl_2", extract_all=False) is True

    def test_extract_ddg_cookie(self) -> None:
        """Test with DDoS-Guard cookie."""
        assert _should_extract_cookie("__ddg1_", extract_all=False) is True
        assert _should_extract_cookie("__ddg2_", extract_all=False) is True

    def test_extract_other_cookie(self) -> None:
        """Test with other cookie."""
        assert _should_extract_cookie("session_id", extract_all=False) is False


class TestThreadSafeCookieStore:
    """Test ThreadSafeCookieStore class."""

    def test_init(self) -> None:
        """Test initialization."""
        store = ThreadSafeCookieStore()
        assert store._cookies == {}
        assert store._lock is not None

    def test_get_empty(self) -> None:
        """Test get with empty store."""
        store = ThreadSafeCookieStore()
        result = store.get("example.com")
        assert result == {}

    def test_set_and_get(self) -> None:
        """Test set and get."""
        store = ThreadSafeCookieStore()
        cookies = {
            "cf_clearance": {
                "value": "test_value",
                "domain": "example.com",
                "path": "/",
            }
        }
        store.set("example.com", cookies)
        result = store.get("example.com")
        assert result == cookies
        # Should return a copy
        assert result is not cookies

    def test_get_cookie_values_for_url(self) -> None:
        """Test get_cookie_values_for_url."""
        store = ThreadSafeCookieStore()
        cookies = {
            "cf_clearance": {
                "value": "test_value",
                "domain": "example.com",
                "path": "/",
                "expiry": time.time() + 3600,
            }
        }
        store.set("example.com", cookies)
        result = store.get_cookie_values_for_url("https://example.com/page")
        assert result == {"cf_clearance": "test_value"}

    def test_get_cookie_values_for_url_expired(self) -> None:
        """Test get_cookie_values_for_url with expired cookies."""
        store = ThreadSafeCookieStore()
        cookies = {
            "cf_clearance": {
                "value": "test_value",
                "domain": "example.com",
                "path": "/",
                "expiry": time.time() - 3600,  # Expired
            }
        }
        store.set("example.com", cookies)
        result = store.get_cookie_values_for_url("https://example.com/page")
        assert result == {}

    def test_get_cookie_dicts_for_url(self) -> None:
        """Test get_cookie_dicts_for_url."""
        store = ThreadSafeCookieStore()
        cookies = {
            "cf_clearance": {
                "value": "test_value",
                "domain": "example.com",
                "path": "/",
                "expiry": time.time() + 3600,
            }
        }
        store.set("example.com", cookies)
        result = store.get_cookie_dicts_for_url("https://example.com/page")
        assert len(result) == 1
        assert result[0]["name"] == "cf_clearance"
        assert result[0]["value"] == "test_value"

    def test_extract_from_driver(self, mock_driver: MagicMock) -> None:
        """Test extract_from_driver."""
        store = ThreadSafeCookieStore()
        mock_driver.get_cookies.return_value = [
            {
                "name": "cf_clearance",
                "value": "test_value",
                "domain": "example.com",
                "path": "/",
                "expiry": time.time() + 3600,
                "secure": True,
                "httpOnly": True,
            }
        ]
        store.extract_from_driver(mock_driver, "https://example.com/page")
        result = store.get("example.com")
        assert "cf_clearance" in result

    def test_extract_from_driver_no_cookies(self, mock_driver: MagicMock) -> None:
        """Test extract_from_driver with no cookies."""
        store = ThreadSafeCookieStore()
        mock_driver.get_cookies.return_value = []
        store.extract_from_driver(mock_driver, "https://example.com/page")
        result = store.get("example.com")
        assert result == {}


class TestThreadSafeUserAgentStore:
    """Test ThreadSafeUserAgentStore class."""

    def test_init(self) -> None:
        """Test initialization."""
        store = ThreadSafeUserAgentStore()
        assert store._user_agents == {}
        assert store._lock is not None

    def test_set_and_get(self) -> None:
        """Test set and get."""
        store = ThreadSafeUserAgentStore()
        store.set("example.com", "Mozilla/5.0")
        result = store.get("example.com")
        assert result == "Mozilla/5.0"

    def test_get_nonexistent(self) -> None:
        """Test get with nonexistent domain."""
        store = ThreadSafeUserAgentStore()
        result = store.get("example.com")
        assert result is None

    def test_get_user_agent_for_url(self) -> None:
        """Test get_user_agent_for_url."""
        store = ThreadSafeUserAgentStore()
        store.set("example.com", "Mozilla/5.0")
        result = store.get_user_agent_for_url("https://example.com/page")
        assert result == "Mozilla/5.0"

    def test_extract_from_driver(self, mock_driver: MagicMock) -> None:
        """Test extract_from_driver."""
        store = ThreadSafeUserAgentStore()
        mock_driver.execute_script.return_value = "Mozilla/5.0"
        store.extract_from_driver(mock_driver, "https://example.com/page")
        result = store.get("example.com")
        assert result == "Mozilla/5.0"

    def test_extract_from_driver_no_ua(self, mock_driver: MagicMock) -> None:
        """Test extract_from_driver with no user agent."""
        store = ThreadSafeUserAgentStore()
        mock_driver.execute_script.return_value = None
        store.extract_from_driver(mock_driver, "https://example.com/page")
        result = store.get("example.com")
        assert result is None
