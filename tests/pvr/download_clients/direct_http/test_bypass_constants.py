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

"""Tests for bypass constants module."""

from bookcard.pvr.download_clients.direct_http.bypass.constants import BypassConstants


class TestBypassConstants:
    """Test BypassConstants class."""

    def test_timeout_constants(self) -> None:
        """Test timeout constants."""
        assert BypassConstants.DEFAULT_PAGE_LOAD_TIMEOUT == 60
        assert BypassConstants.DEFAULT_RECONNECT_TIME == 1.0
        assert BypassConstants.DEFAULT_CHUNK_SIZE == 8192
        assert BypassConstants.FLARESOLVERR_CONNECT_TIMEOUT == 10
        assert BypassConstants.FLARESOLVERR_MAX_READ_TIMEOUT == 120
        assert BypassConstants.FLARESOLVERR_READ_TIMEOUT_BUFFER == 15

    def test_url_constants(self) -> None:
        """Test URL and path constants."""
        assert BypassConstants.DEFAULT_FLARESOLVERR_URL == "http://flaresolverr:8191"
        assert BypassConstants.DEFAULT_FLARESOLVERR_PATH == "/v1"
        assert BypassConstants.DEFAULT_FLARESOLVERR_TIMEOUT == 60000

    def test_http_status_constants(self) -> None:
        """Test HTTP status code constants."""
        assert BypassConstants.HTTP_STATUS_OK == 200
        assert BypassConstants.HTTP_STATUS_SERVICE_UNAVAILABLE == 503

    def test_content_type_constants(self) -> None:
        """Test content type constants."""
        assert BypassConstants.CONTENT_TYPE_HTML == "text/html; charset=utf-8"
