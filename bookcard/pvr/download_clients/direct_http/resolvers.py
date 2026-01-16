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

import logging
import re
import urllib.parse
import uuid
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Protocol, cast

import httpx
from bs4 import BeautifulSoup

from bookcard.pvr.base.interfaces import HttpClientProtocol
from bookcard.pvr.download_clients.direct_http.protocols import (
    HtmlParser,
    StreamingHttpClient,
    StreamingResponse,
    TimeProvider,
)
from bookcard.pvr.download_clients.direct_http.settings import DownloadConstants

logger = logging.getLogger(__name__)


class UrlResolver(Protocol):
    """Protocol for URL resolution strategies."""

    def can_resolve(self, url: str) -> bool:
        """Check if this resolver can handle the URL."""
        ...

    def resolve(self, url: str) -> str | None:
        """Resolve URL to actual download link."""
        ...


class DirectUrlResolver(UrlResolver):
    """Resolver for direct download URLs."""

    def can_resolve(self, url: str) -> bool:
        """Check if URL is direct."""
        return not any(pattern in url for pattern in ["annas-archive.org/md5/"])

    def resolve(self, url: str) -> str | None:
        """Resolve direct URL."""
        return url


class AnnaArchiveResolver(UrlResolver):
    """Resolver for Anna's Archive URLs."""

    def __init__(
        self,
        http_client_factory: Callable[[], HttpClientProtocol],
        html_parser: HtmlParser,
        time_provider: TimeProvider,
    ) -> None:
        self._factory = http_client_factory
        self._parser = html_parser
        self._time = time_provider

    def can_resolve(self, url: str) -> bool:
        """Check if URL is Anna's Archive."""
        return "annas-archive.org/md5/" in url

    def resolve(self, url: str) -> str | None:
        """Resolve Anna's Archive URL."""
        try:
            # Cast to StreamingHttpClient because we know our factory produces httpx clients
            # that satisfy the interface, even if typed as generic HttpClientProtocol
            with cast("Callable[[], StreamingHttpClient]", self._factory)() as client:
                logger.debug("Resolving AA details page: %s", url)
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()
                soup = self._parser.parse(response.text)

                # Find slow partner server link
                slow_url = self._find_slow_server_link(soup, url)
                if not slow_url:
                    return self._find_direct_button_link(soup, url)

                return self._process_slow_download_page(client, slow_url)

        except (httpx.HTTPError, ValueError):
            logger.warning("Failed to resolve AA link", exc_info=True)
            return None

    def _find_slow_server_link(self, soup: BeautifulSoup, base_url: str) -> str | None:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text().lower()
            if "/slow_download/" in href or "slow partner server" in text:
                return urllib.parse.urljoin(base_url, href)
        return None

    def _find_direct_button_link(
        self, soup: BeautifulSoup, base_url: str
    ) -> str | None:
        for a in soup.find_all("a", href=True):
            text = a.get_text().lower()
            if "download" in text and "/md5/" not in a["href"]:
                return urllib.parse.urljoin(base_url, a["href"])
        logger.warning("No download link found on %s", base_url)
        return None

    def _process_slow_download_page(
        self, client: StreamingHttpClient, url: str
    ) -> str | None:
        logger.debug("Processing slow download page: %s", url)
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        html = response.text
        soup = self._parser.parse(html)

        direct_link = self._extract_direct_link(soup, html)
        if direct_link:
            return urllib.parse.urljoin(url, direct_link)

        countdown = self._extract_countdown_seconds(soup, html)
        if countdown > 0:
            logger.info("AA countdown detected: %ds", countdown)
            if countdown > DownloadConstants.MAX_COUNTDOWN_SECONDS:
                logger.warning("Countdown too long (%ds), aborting", countdown)
                return None

            self._time.sleep(countdown + 1)
            return self._process_slow_download_page(client, url)

        return None

    def _extract_direct_link(self, soup: BeautifulSoup, html_str: str) -> str | None:
        return (
            self._extract_from_clipboard(html_str)
            or self._extract_from_download_button(soup)
            or self._extract_from_window_location(html_str)
            or self._extract_from_other_links(soup)
        )

    def _extract_from_clipboard(self, html_str: str) -> str | None:
        match = re.search(
            r"navigator\.clipboard\.writeText\(['\"]([^'\"]+)['\"]\)", html_str
        )
        if match:
            link = match.group(1)
            if link.startswith("http") and "/slow_download/" not in link:
                return link
        return None

    def _extract_from_download_button(self, soup: BeautifulSoup) -> str | None:
        links = soup.find_all("a", href=True)
        for link in links:
            if link.string == "📚 Download now":
                return link["href"]
        for link in links:
            if link.string and "Download now" in link.string:
                return link["href"]
        return None

    def _extract_from_window_location(self, html_str: str) -> str | None:
        match = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", html_str)
        if match:
            link = match.group(1)
            if link.startswith("http") and "/slow_download/" not in link:
                return link
        return None

    def _extract_from_other_links(self, soup: BeautifulSoup) -> str | None:
        for a_tag in soup.find_all("a", href=True):
            if a_tag.has_attr("download"):
                href = a_tag["href"]
                if href.startswith("http") and "/slow_download/" not in href:
                    return href
        return None

    def _extract_countdown_seconds(self, soup: BeautifulSoup, html_str: str) -> int:
        elem = soup.find("span", class_="js-partner-countdown")
        if elem:
            with suppress(ValueError):
                return int(elem.get_text(strip=True))

        js_var = re.search(r"(?:var|let|const)\s+countdown\s*=\s*(\d+)", html_str)
        if js_var:
            return int(js_var.group(1))
        return 0


class FilenameResolver:
    """Determines filenames from various sources."""

    def resolve(self, response: StreamingResponse, url: str, title: str | None) -> str:
        """Resolve filename with fallback chain."""
        if title:
            safe_title = self._sanitize_filename(title)
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
        return name or f"download-{uuid.uuid4()}"

    def _sanitize_filename(self, title: str, max_length: int = 200) -> str:
        """Sanitize title for use as filename."""
        sanitized = re.sub(r"[^\w\s._-]", "", title)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized[:max_length]
