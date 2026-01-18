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

"""Tests for Anna's Archive config module."""

from bookcard.pvr.download_clients.direct_http.anna.config import AnnaArchiveConfig


class TestAnnaArchiveConfig:
    """Test AnnaArchiveConfig class."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        config = AnnaArchiveConfig()
        assert len(config.mirrors) > 0
        assert (
            "annas-archive.li" in config.mirrors[0]
            or "annas-archive.se" in config.mirrors[0]
        )
        assert config.donator_key is None
        assert config.max_countdown_seconds == 300
        assert config.retry_delay_seconds == 1.0

    def test_init_custom(self) -> None:
        """Test initialization with custom values."""
        mirrors = ["https://custom1.com", "https://custom2.com"]
        config = AnnaArchiveConfig(
            mirrors=mirrors,
            donator_key="test-key",
            max_countdown_seconds=600,
            retry_delay_seconds=2.0,
        )
        assert config.mirrors == mirrors
        assert config.donator_key == "test-key"
        assert config.max_countdown_seconds == 600
        assert config.retry_delay_seconds == 2.0

    def test_mirrors_default(self) -> None:
        """Test default mirrors."""
        config = AnnaArchiveConfig()
        assert len(config.mirrors) == 4
        assert all("annas-archive" in mirror for mirror in config.mirrors)
