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

"""Tests for bypass config module."""

import pytest

from bookcard.pvr.download_clients.direct_http.bypass.config import (
    BypassConfig,
    FlareSolverrConfig,
    SeleniumBaseConfig,
)
from bookcard.pvr.download_clients.direct_http.bypass.constants import (
    BypassConstants,
)


class TestFlareSolverrConfig:
    """Test FlareSolverrConfig class."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        config = FlareSolverrConfig()
        assert config.url == BypassConstants.DEFAULT_FLARESOLVERR_URL
        assert config.path == BypassConstants.DEFAULT_FLARESOLVERR_PATH
        assert config.timeout == BypassConstants.DEFAULT_FLARESOLVERR_TIMEOUT

    def test_init_custom(self) -> None:
        """Test initialization with custom values."""
        config = FlareSolverrConfig(
            url="http://custom:8191",
            path="/v2",
            timeout=120000,
        )
        assert config.url == "http://custom:8191"
        assert config.path == "/v2"
        assert config.timeout == 120000

    def test_frozen(self) -> None:
        """Test that config is frozen."""
        config = FlareSolverrConfig()
        with pytest.raises(Exception):  # noqa: B017, PT011
            config.url = "new_url"  # type: ignore[misc]


class TestSeleniumBaseConfig:
    """Test SeleniumBaseConfig class."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        config = SeleniumBaseConfig()
        assert config.page_load_timeout == BypassConstants.DEFAULT_PAGE_LOAD_TIMEOUT
        assert config.reconnect_time == BypassConstants.DEFAULT_RECONNECT_TIME
        assert config.headless is False
        assert config.incognito is True
        assert config.locale == "en"
        assert config.ad_block is True

    def test_init_custom(self) -> None:
        """Test initialization with custom values."""
        config = SeleniumBaseConfig(
            page_load_timeout=120,
            reconnect_time=2.0,
            headless=True,
            incognito=False,
            locale="fr",
            ad_block=False,
        )
        assert config.page_load_timeout == 120
        assert config.reconnect_time == 2.0
        assert config.headless is True
        assert config.incognito is False
        assert config.locale == "fr"
        assert config.ad_block is False

    def test_frozen(self) -> None:
        """Test that config is frozen."""
        config = SeleniumBaseConfig()
        with pytest.raises(Exception):  # noqa: B017, PT011
            config.headless = True  # type: ignore[misc]


class TestBypassConfig:
    """Test BypassConfig class."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        config = BypassConfig()
        assert config.flaresolverr is None
        assert config.seleniumbase is None
        assert config.use_seleniumbase is False

    def test_init_with_flaresolverr(self) -> None:
        """Test initialization with FlareSolverr config."""
        flaresolverr_config = FlareSolverrConfig()
        config = BypassConfig(flaresolverr=flaresolverr_config)
        assert config.flaresolverr == flaresolverr_config
        assert config.seleniumbase is None

    def test_init_with_seleniumbase(self) -> None:
        """Test initialization with SeleniumBase config."""
        seleniumbase_config = SeleniumBaseConfig()
        config = BypassConfig(seleniumbase=seleniumbase_config, use_seleniumbase=True)
        assert config.seleniumbase == seleniumbase_config
        assert config.use_seleniumbase is True
