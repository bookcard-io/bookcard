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

"""Constants for bypass client."""


class BypassConstants:
    """Constants used by bypass client."""

    # Timeouts
    DEFAULT_PAGE_LOAD_TIMEOUT = 60
    DEFAULT_RECONNECT_TIME = 1.0
    DEFAULT_CHUNK_SIZE = 8192
    FLARESOLVERR_CONNECT_TIMEOUT = 10
    FLARESOLVERR_MAX_READ_TIMEOUT = 120
    FLARESOLVERR_READ_TIMEOUT_BUFFER = 15

    # Default URLs and paths
    DEFAULT_FLARESOLVERR_URL = "http://flaresolverr:8191"
    DEFAULT_FLARESOLVERR_PATH = "/v1"
    DEFAULT_FLARESOLVERR_TIMEOUT = 60000  # milliseconds

    # HTTP status codes
    HTTP_STATUS_OK = 200
    HTTP_STATUS_SERVICE_UNAVAILABLE = 503

    # Content types
    CONTENT_TYPE_HTML = "text/html; charset=utf-8"
