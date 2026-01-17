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

"""Tests for Anna's Archive mirrors module."""

from bookcard.pvr.download_clients.direct_http.anna.mirrors import MirrorRotator


class TestMirrorRotator:
    """Test MirrorRotator class."""

    def test_init(self) -> None:
        """Test initialization."""
        mirrors = ["https://mirror1.com", "https://mirror2.com"]
        rotator = MirrorRotator(mirrors)
        assert rotator._mirrors == mirrors

    def test_get_mirrors_current_first(self) -> None:
        """Test get_mirrors with current URL in mirrors."""
        mirrors = ["https://mirror1.com", "https://mirror2.com"]
        rotator = MirrorRotator(mirrors)
        result = rotator.get_mirrors("https://mirror2.com/page")
        assert result[0] == "https://mirror2.com"
        assert "https://mirror1.com" in result

    def test_get_mirrors_current_not_in_list(self) -> None:
        """Test get_mirrors with current URL not in mirrors."""
        mirrors = ["https://mirror1.com", "https://mirror2.com"]
        rotator = MirrorRotator(mirrors)
        result = rotator.get_mirrors("https://other.com/page")
        assert result[0] == "https://other.com"
        assert len(result) == 3

    def test_get_next_url(self) -> None:
        """Test get_next_url."""
        mirrors = ["https://mirror1.com", "https://mirror2.com"]
        rotator = MirrorRotator(mirrors)
        result = rotator.get_next_url(
            "https://mirror1.com/page1", "https://mirror2.com"
        )
        assert result == "https://mirror2.com/page1"

    def test_get_next_url_preserves_path(self) -> None:
        """Test get_next_url preserves path."""
        mirrors = ["https://mirror1.com", "https://mirror2.com"]
        rotator = MirrorRotator(mirrors)
        result = rotator.get_next_url(
            "https://mirror1.com/path/to/page", "https://mirror2.com"
        )
        assert result == "https://mirror2.com/path/to/page"
