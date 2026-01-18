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

import re
import urllib.parse
import uuid
from contextlib import suppress
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


def _extract_filename_from_content_disposition(content_disposition: str) -> str | None:
    """Extract filename from Content-Disposition header.

    Parameters
    ----------
    content_disposition : str
        The Content-Disposition header value.

    Returns
    -------
    str | None
        Extracted filename or None if not found.
    """
    if not content_disposition:
        return None

    # Try RFC 5987 format: filename*=UTF-8''filename.ext
    rfc5987_match = re.search(
        r"filename\*=UTF-8''([^;]+)", content_disposition, re.IGNORECASE
    )
    if rfc5987_match:
        with suppress(UnicodeDecodeError):
            return urllib.parse.unquote(rfc5987_match.group(1))

    # Try standard format: filename="filename.ext" or filename=filename.ext
    standard_match = re.search(r"filename=([^;]+)", content_disposition, re.IGNORECASE)
    if standard_match:
        filename = standard_match.group(1).strip()
        # Remove quotes if present
        filename = filename.strip("\"'")
        if filename:
            return filename

    return None


class FilenameResolver:
    """Determines filenames from various sources."""

    def resolve(
        self,
        response: StreamingResponse,
        url: str,
        title: str | None,
        author: str | None = None,
        quality: str | None = None,
        guid: str | None = None,
    ) -> str:
        """Resolve filename with fallback chain.

        Checks in order:
        1. Content-Disposition header (standard HTTP way)
        2. Name from ReleaseInfo (Author - Title.Extension)
        3. Title with content-type extension (legacy fallback)
        4. URL path (if meaningful)
        5. GUID (if available)
        6. UUID (final fallback)
        """
        # 1. Content-Disposition
        if name := self._from_content_disposition(response):
            return name

        # 2. ReleaseInfo (Author - Title.ext)
        if name := self._from_release_info(title, author, quality):
            return name

        # 3. Title + content-type/quality
        if name := self._from_title_fallback(response, title, quality):
            return name

        # 4. URL path
        if name := self._from_url_path(url):
            return name

        # 5. GUID
        if name := self._from_guid(guid, quality):
            return name

        # 6. UUID
        return f"download-{uuid.uuid4()}"

    def _from_content_disposition(self, response: StreamingResponse) -> str | None:
        """Try resolving from Content-Disposition header."""
        content_disposition = response.headers.get("content-disposition", "")
        if content_disposition:
            filename = _extract_filename_from_content_disposition(content_disposition)
            if filename:
                sanitized = sanitize_filename(filename)
                if sanitized:
                    return sanitized
        return None

    def _from_release_info(
        self, title: str | None, author: str | None, quality: str | None
    ) -> str | None:
        """Try resolving from release metadata."""
        if title and quality:
            ext = quality.lower().lstrip(".")
            candidate = f"{author} - {title}.{ext}" if author else f"{title}.{ext}"
            return sanitize_filename(candidate)
        return None

    def _from_title_fallback(
        self, response: StreamingResponse, title: str | None, quality: str | None
    ) -> str | None:
        """Try resolving from title and content type."""
        if not title:
            return None

        safe_title = sanitize_filename(title)
        if not safe_title:
            return None

        ext = ".bin"
        content_type = response.headers.get("content-type", "")
        if "pdf" in content_type:
            ext = ".pdf"
        elif "epub" in content_type:
            ext = ".epub"
        elif quality:
            ext = f".{quality.lstrip('.')}"

        return f"{safe_title}{ext}"

    def _from_url_path(self, url: str) -> str | None:
        """Try resolving from URL path."""
        path = urllib.parse.urlparse(url).path
        name = Path(path).name
        if name and "." in name:
            name = sanitize_filename(name)
            if name:
                return name
        return None

    def _from_guid(self, guid: str | None, quality: str | None) -> str | None:
        """Try resolving from GUID."""
        if not guid:
            return None

        # GUID might be a URL, extract last part
        if guid.startswith(("http:", "https:")):
            guid_name = Path(urllib.parse.urlparse(guid).path).name
        else:
            guid_name = guid

        if not guid_name:
            return None

        safe_guid = sanitize_filename(guid_name)
        if not safe_guid:
            return None

        if quality:
            return f"{safe_guid}.{quality.lstrip('.')}"
        return safe_guid


__all__ = [
    "AnnaArchiveResolver",
    "DirectUrlResolver",
    "FilenameResolver",
    "UrlResolver",
]
