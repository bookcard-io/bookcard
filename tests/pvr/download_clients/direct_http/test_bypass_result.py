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

"""Tests for bypass result module."""

import pytest

from bookcard.pvr.download_clients.direct_http.bypass.result import BypassResult


class TestBypassResult:
    """Test BypassResult dataclass."""

    def test_init_success(self) -> None:
        """Test initialization with success."""
        result = BypassResult(html="<html>test</html>")
        assert result.html == "<html>test</html>"
        assert result.error is None
        assert result.success is True

    def test_init_failure(self) -> None:
        """Test initialization with failure."""
        result = BypassResult(html=None, error="Failed to fetch")
        assert result.html is None
        assert result.error == "Failed to fetch"
        assert result.success is False

    def test_success_property_with_html(self) -> None:
        """Test success property when HTML is present."""
        result = BypassResult(html="<html>test</html>")
        assert result.success is True

    def test_success_property_without_html(self) -> None:
        """Test success property when HTML is None."""
        result = BypassResult(html=None)
        assert result.success is False

    def test_success_property_empty_html(self) -> None:
        """Test success property with empty HTML."""
        result = BypassResult(html="")
        # Empty string is not None, so success will be True
        # This is the actual behavior - only None means failure
        assert result.success is True

    def test_frozen(self) -> None:
        """Test that result is frozen."""
        result = BypassResult(html="<html>test</html>")
        with pytest.raises(Exception):  # noqa: B017, PT011
            result.html = "new"  # type: ignore[misc]
