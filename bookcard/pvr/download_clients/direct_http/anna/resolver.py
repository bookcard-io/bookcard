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

"""Resolver for Anna's Archive URLs."""

import json
import logging
import re
import time
import urllib.parse
from collections.abc import Callable

import httpx
from bs4 import BeautifulSoup

from bookcard.pvr.base.interfaces import HttpClientProtocol
from bookcard.pvr.download_clients.direct_http.anna.client_strategy import (
    ClientSwitchingStrategy,
)
from bookcard.pvr.download_clients.direct_http.anna.config import AnnaArchiveConfig
from bookcard.pvr.download_clients.direct_http.anna.countdown import CountdownHandler
from bookcard.pvr.download_clients.direct_http.anna.extractors import LinkExtractor
from bookcard.pvr.download_clients.direct_http.anna.mirrors import MirrorRotator
from bookcard.pvr.download_clients.direct_http.libgen_resolver import LibgenResolver
from bookcard.pvr.download_clients.direct_http.protocols import (
    HtmlParser,
    StreamingHttpClient,
    TimeProvider,
)
from bookcard.pvr.download_clients.direct_http.protocols import (
    UrlResolver as UrlResolverProtocol,
)

logger = logging.getLogger(__name__)


class AnnaArchiveResolver(UrlResolverProtocol):
    """Resolver for Anna's Archive URLs."""

    _MD5_RE = re.compile(r"/md5/([0-9a-fA-F]{32})")

    def __init__(
        self,
        http_client_factory: Callable[[], HttpClientProtocol],
        html_parser: HtmlParser,
        time_provider: TimeProvider,
        config: AnnaArchiveConfig | None = None,
        flaresolverr_url: str | None = None,
        flaresolverr_path: str = "/v1",
        flaresolverr_timeout: int = 60000,
        use_seleniumbase: bool = False,
    ) -> None:
        self._parser = html_parser
        self._config = config or AnnaArchiveConfig()

        # Initialize components
        self._client_strategy = ClientSwitchingStrategy(
            http_client_factory,
            flaresolverr_url=flaresolverr_url,
            flaresolverr_path=flaresolverr_path,
            flaresolverr_timeout=flaresolverr_timeout,
            use_seleniumbase=use_seleniumbase,
        )
        self._mirrors = MirrorRotator(self._config.mirrors)
        self._countdown = CountdownHandler(
            time_provider, self._config.max_countdown_seconds
        )
        self._extractor = LinkExtractor()
        self._libgen = LibgenResolver(http_client_factory)

    def can_resolve(self, url: str) -> bool:
        """Check if URL is Anna's Archive."""
        return "annas-archive." in url and "/md5/" in url

    def resolve(self, url: str) -> str | None:
        """Resolve Anna's Archive URL."""
        try:
            return self._client_strategy.execute(
                lambda client: self._resolve_with_client(client, url)
            )
        except (httpx.HTTPError, ValueError, RuntimeError):
            logger.warning("Failed to resolve AA link", exc_info=True)
            return None

    def _resolve_with_client(self, client: StreamingHttpClient, url: str) -> str | None:
        md5 = self._extract_md5(url)

        # 1. Try AA Fast (if donator key present)
        if self._config.donator_key and (
            fast_url := self._try_fast_download(client, url, md5)
        ):
            return fast_url

        # 2. Try Libgen (Fast source)
        if md5:
            logger.debug("Checking Libgen fallback for MD5: %s", md5)
            if libgen_url := self._libgen.resolve(md5):
                logger.info("Found download on Libgen: %s", libgen_url)
                return libgen_url

        # 3. Fallback to AA Page (Slow sources)
        logger.debug("Resolving AA details page: %s", url)
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        soup = self._parser.parse(response.text)

        slow_url = self._find_slow_server_link(soup, url)
        if not slow_url:
            return self._find_direct_button_link(soup, url)

        return self._process_slow_download_page(client, slow_url)

    def _try_fast_download(
        self, client: StreamingHttpClient, url: str, md5: str | None = None
    ) -> str | None:
        if not md5:
            md5 = self._extract_md5(url)
        if not md5:
            return None

        # Prefer the current URL's base if it looks like an AA mirror.
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if "annas-archive" not in base:
            base = self._config.mirrors[0]

        api_url = f"{base}/dyn/api/fast_download.json?md5={md5}&key={self._config.donator_key}"
        try:
            response = client.get(api_url, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        try:
            data = json.loads(response.text)
        except ValueError:
            return None

        download_url = data.get("download_url")
        if isinstance(download_url, str) and download_url.startswith((
            "http://",
            "https://",
        )):
            return download_url
        return None

    def _extract_md5(self, url: str) -> str | None:
        match = self._MD5_RE.search(url)
        if not match:
            return None
        return match.group(1).lower()

    def _find_slow_server_link(self, soup: BeautifulSoup, base_url: str) -> str | None:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text().lower()
            if "/slow_download/" in href or "slow partner server" in text:
                return urllib.parse.urljoin(base_url, href)  # type: ignore[invalid-argument-type]
        return None

    def _find_direct_button_link(
        self, soup: BeautifulSoup, base_url: str
    ) -> str | None:
        for a in soup.find_all("a", href=True):
            text = a.get_text().lower()
            if "download" in text and "/md5/" not in a["href"]:
                return urllib.parse.urljoin(base_url, a["href"])  # type: ignore[invalid-argument-type]
        logger.warning("No download link found on %s", base_url)
        return None

    def _process_slow_download_page(
        self, client: StreamingHttpClient, url: str
    ) -> str | None:
        logger.debug("Processing slow download page: %s", url)

        mirrors = self._mirrors.get_mirrors(url)
        current_url = url
        last_blocking_error: httpx.HTTPError | None = None

        for attempt, mirror_base in enumerate(mirrors):
            if attempt > 0:
                current_url = self._mirrors.get_next_url(current_url, mirror_base)
                logger.info("Rotated mirror to: %s", current_url)
                time.sleep(self._config.retry_delay_seconds)

            try:
                return self._attempt_download_page(client, current_url)
            except (httpx.HTTPError, ValueError) as e:
                # Catch exceptions to continue rotation
                status_code = getattr(getattr(e, "response", None), "status_code", 0)
                if status_code in (403, 429):
                    if isinstance(e, httpx.HTTPError):
                        last_blocking_error = e
                    logger.warning(
                        "Mirror %s returned %s, rotating...",
                        mirror_base,
                        status_code,
                    )
                    continue

                logger.warning("Error processing %s: %s", current_url, e)
                continue

        # If we exhausted all mirrors and had at least one blocking error, raise it
        # so the ClientSwitchingStrategy can try the bypass client.
        if last_blocking_error:
            logger.warning(
                "All mirrors failed, raising last blocking error to trigger bypass."
            )
            raise last_blocking_error

        return None

    def _attempt_download_page(
        self, client: StreamingHttpClient, url: str
    ) -> str | None:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        html = response.text
        soup = self._parser.parse(html)

        if direct_link := self._extractor.extract_link(soup, html):
            return urllib.parse.urljoin(url, direct_link)

        # Check for countdown
        try:
            seconds = self._countdown.handle_countdown(soup, html)
            if seconds > 0:
                # Countdown finished, retry the same page
                # We recurse to re-process. Note that since we pass 'url' (which is the current working mirror),
                # 'get_mirrors' will put it first, so we effectively retry this mirror first.
                return self._process_slow_download_page(client, url)
        except TimeoutError:
            return None

        logger.warning("No link or countdown found on %s", url)
        msg = f"No link found on {url}"
        raise ValueError(msg)
