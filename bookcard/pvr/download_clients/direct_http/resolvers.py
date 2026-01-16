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

"""URL and filename resolvers for Direct HTTP download client."""

import urllib.parse
import uuid
from pathlib import Path

from bookcard.common.filesystem import sanitize_filename
from bookcard.pvr.download_clients.direct_http.anna import AnnaArchiveResolver
from bookcard.pvr.download_clients.direct_http.protocols import (
    StreamingResponse,
    UrlResolver,
)


class DirectUrlResolver(UrlResolver):
    """Resolver for direct download URLs."""

    def can_resolve(self, url: str) -> bool:
        """Check if URL is direct."""
        return not ("annas-archive." in url and "/md5/" in url)

    def resolve(self, url: str) -> str | None:
        """Resolve direct URL."""
        return url


class FilenameResolver:
    """Determines filenames from various sources."""

    def resolve(self, response: StreamingResponse, url: str, title: str | None) -> str:
        """Resolve filename with fallback chain."""
        if title:
            safe_title = sanitize_filename(title)
            if safe_title:
                ext = ".bin"
                content_type = response.headers.get("content-type", "")
                if "pdf" in content_type:
                    ext = ".pdf"
                elif "epub" in content_type:
                    ext = ".epub"
                return f"{safe_title}{ext}"

        path = urllib.parse.urlparse(url).path
        name = Path(path).name
        if name:
            name = sanitize_filename(name)
        return name or f"download-{uuid.uuid4()}"


__all__ = [
    "AnnaArchiveResolver",
    "DirectUrlResolver",
    "FilenameResolver",
    "UrlResolver",
]
