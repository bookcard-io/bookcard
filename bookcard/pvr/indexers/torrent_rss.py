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

"""Torrent RSS indexer implementation.

Supports generic torrent RSS feeds that don't follow Torznab specification.
Can parse various RSS formats including MRSS.
"""

import logging
from collections.abc import Sequence
from xml.etree import ElementTree as ET  # noqa: S405

import httpx

from bookcard.pvr.base import BaseIndexer, IndexerSettings
from bookcard.pvr.base.interfaces import (
    RequestGeneratorProtocol,
    ResponseParserProtocol,
)
from bookcard.pvr.error_handlers import handle_http_error_response
from bookcard.pvr.exceptions import (
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.indexers.parsers import (
    CompositeReleaseParser,
    MetadataExtractor,
    PublishDateExtractor,
    ReleaseFieldExtractor,
    RssDownloadUrlExtractor,
    RssSeedersLeechersExtractor,
    SimpleTextExtractor,
    SizeExtractor,
    TitleExtractor,
)
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)


class TorrentRssSettings(IndexerSettings):
    """Settings for Torrent RSS indexer.

    Attributes
    ----------
    cookies : dict[str, str] | None
        Cookies to send with requests (e.g., auth cookies).
    """

    cookies: dict[str, str] | None = None


class TorrentRssRequestGenerator:
    """Generates Torrent RSS feed URLs.

    Since generic RSS feeds don't support standardized search parameters,
    this generator handles basic URL construction.
    """

    def __init__(self, settings: TorrentRssSettings) -> None:
        """Initialize request generator.

        Parameters
        ----------
        settings : TorrentRssSettings
            Torrent RSS indexer settings.
        """
        self.settings = settings

    def build_search_url(
        self,
        query: str | None = None,  # noqa: ARG002
        title: str | None = None,  # noqa: ARG002
        author: str | None = None,  # noqa: ARG002
        isbn: str | None = None,  # noqa: ARG002
        categories: list[int] | None = None,  # noqa: ARG002
        offset: int = 0,  # noqa: ARG002
        limit: int = 100,  # noqa: ARG002
    ) -> str:
        """Build search URL.

        Note: Generic RSS feeds typically don't support search.
        This implementation returns the base RSS URL and relies on
        client-side filtering, or assumes the base URL itself is a
        search result feed.

        Parameters
        ----------
        query, title, author, isbn, categories, offset, limit :
            Ignored for generic RSS (unless URL construction logic is customized).

        Returns
        -------
        str
            The configured RSS feed URL.
        """
        # Return the configured base URL as the feed URL
        # For generic RSS, the "base_url" setting is often the full feed URL
        return self.settings.base_url

    def build_rss_url(
        self,
        categories: list[int] | None = None,  # noqa: ARG002
        limit: int = 100,  # noqa: ARG002
    ) -> str:
        """Build RSS URL.

        Parameters
        ----------
        categories, limit :
            Ignored for generic RSS.

        Returns
        -------
        str
            The configured RSS feed URL.
        """
        return self.settings.base_url


class TorrentRssParser:
    """Parses generic Torrent RSS feeds.

    Handles standard RSS 2.0 and some common extensions.
    """

    def __init__(self) -> None:
        """Initialize parser with composite extractors."""
        extractors: dict[str, ReleaseFieldExtractor] = {
            "title": TitleExtractor(),
            "download_url": RssDownloadUrlExtractor(),
            "size_bytes": SizeExtractor(),
            "publish_date": PublishDateExtractor(),
            "seeders_leechers": RssSeedersLeechersExtractor(),
            "description": SimpleTextExtractor("description"),
            "category": SimpleTextExtractor("category"),
            "metadata": MetadataExtractor(),
        }

        self.composite = CompositeReleaseParser(extractors)

    def parse_response(
        self, xml_content: bytes | str, indexer_id: int | None = None
    ) -> list[ReleaseInfo]:
        """Parse RSS XML response into ReleaseInfo objects.

        Parameters
        ----------
        xml_content : bytes | str
            XML content from RSS feed.
        indexer_id : int | None
            Optional indexer ID to include in results.

        Returns
        -------
        list[ReleaseInfo]
            List of parsed release information.

        Raises
        ------
        PVRProviderParseError
            If XML parsing fails.
        """
        try:
            if isinstance(xml_content, bytes):
                root = ET.fromstring(xml_content)  # noqa: S314
            else:
                root = ET.fromstring(xml_content.encode())  # noqa: S314

            # Find all item elements
            items = root.findall(".//item")
            releases: list[ReleaseInfo] = []

            for item in items:
                try:
                    data = self.composite.parse(item)

                    if not data.get("title") or not data.get("download_url"):
                        continue

                    release = ReleaseInfo(
                        indexer_id=indexer_id,
                        title=data.get("title"),  # type: ignore
                        download_url=data.get("download_url"),  # type: ignore
                        size_bytes=data.get("size_bytes"),
                        publish_date=data.get("publish_date"),
                        seeders=data.get("seeders"),
                        leechers=data.get("leechers"),
                        quality=None,  # Hard to infer from generic RSS
                        author=None,
                        isbn=None,
                        description=data.get("description"),
                        category=data.get("category"),
                        additional_info=None,
                    )
                    releases.append(release)
                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    logger.warning("Failed to parse item: %s", e, exc_info=True)
                    continue
        except ET.ParseError as e:
            msg = f"Failed to parse XML response: {e}"
            raise PVRProviderParseError(msg) from e
        except Exception as e:
            msg = f"Unexpected error parsing response: {e}"
            raise PVRProviderParseError(msg) from e
        else:
            return releases


class TorrentRssIndexer(BaseIndexer):
    """Torrent RSS indexer implementation.

    Reads generic RSS feeds to find torrent releases.
    """

    def __init__(
        self,
        settings: TorrentRssSettings | IndexerSettings,
        request_generator: RequestGeneratorProtocol,
        parser: ResponseParserProtocol,
    ) -> None:
        """Initialize Torrent RSS indexer.

        Parameters
        ----------
        settings : TorrentRssSettings | IndexerSettings
            Indexer settings. If IndexerSettings, converts to TorrentRssSettings.
        request_generator : RequestGeneratorProtocol
            Request generator service.
        parser : ResponseParserProtocol
            Response parser service.
        """
        # Convert IndexerSettings to TorrentRssSettings if needed
        if isinstance(settings, IndexerSettings) and not isinstance(
            settings, TorrentRssSettings
        ):
            rss_settings = TorrentRssSettings(
                base_url=settings.base_url,
                api_key=settings.api_key,
                timeout_seconds=settings.timeout_seconds,
                retry_count=settings.retry_count,
                categories=settings.categories,
                cookies=None,
            )
            settings = rss_settings

        super().__init__(settings)
        self.settings: TorrentRssSettings = settings  # type: ignore[assignment]
        self.request_generator = request_generator
        self.parser = parser

    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
    ) -> Sequence[ReleaseInfo]:
        """Search for releases matching the query.

        For generic RSS feeds, this typically fetches the feed and filters
        results in memory, as the feed URL is static.

        Parameters
        ----------
        query : str
            General search query.
        title, author, isbn : str | None
            Specific search terms.
        max_results : int
            Maximum number of results to return.

        Returns
        -------
        Sequence[ReleaseInfo]
            Sequence of matching release information.

        Raises
        ------
        PVRProviderError
            If fetching or parsing fails.
        """
        # Build URL (likely just the feed URL)
        url = self.request_generator.build_search_url()

        try:
            response = self._make_request(url)
            releases = self.parser.parse_response(
                response.content,
                indexer_id=None,
            )

            # Filter in memory since generic RSS often doesn't support search params
            filtered_releases = []
            search_terms = []
            if title:
                search_terms.append(title.lower())
            if author:
                search_terms.append(author.lower())
            if isbn:
                search_terms.append(isbn.replace("-", ""))
            if query:
                search_terms.append(query.lower())

            if not search_terms:
                return releases[:max_results]

            for release in releases:
                release_title = release.title.lower()
                # Simple check: if any search term is in the title
                # Ideally this would be smarter (all terms must match, etc.)
                if any(term in release_title for term in search_terms):
                    filtered_releases.append(release)

            return filtered_releases[:max_results]

        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Unexpected error during search: {e}"
            raise PVRProviderError(msg) from e

    def test_connection(self) -> bool:
        """Test connectivity to the feed.

        Fetches the feed and attempts to parse it.

        Returns
        -------
        bool
            True if connection test succeeds.

        Raises
        ------
        PVRProviderError
            If connection or parsing fails.
        """
        url = self.request_generator.build_search_url()

        try:
            response = self._make_request(url)
            # Try to parse to ensure it's valid XML
            ET.fromstring(response.content)  # noqa: S314
        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Connection test failed: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True

    def _make_request(self, url: str) -> httpx.Response:
        """Make HTTP request to RSS feed.

        Parameters
        ----------
        url : str
            Request URL.

        Returns
        -------
        httpx.Response
            HTTP response.

        Raises
        ------
        PVRProviderNetworkError, PVRProviderTimeoutError, PVRProviderError
        """
        timeout = self.settings.timeout_seconds
        cookies = self.settings.cookies

        try:
            with httpx.Client(
                timeout=timeout, follow_redirects=True, cookies=cookies
            ) as client:
                response = client.get(url)
                handle_http_error_response(response.status_code, response.text)
                return response

        except httpx.TimeoutException as e:
            msg = f"Request timeout after {timeout}s"
            raise PVRProviderTimeoutError(msg) from e
        except httpx.HTTPStatusError as e:
            msg = f"HTTP error: {e}"
            raise PVRProviderNetworkError(msg) from e
        except httpx.RequestError as e:
            msg = f"Request failed: {e}"
            raise PVRProviderNetworkError(msg) from e
        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Unexpected error making request: {e}"
            raise PVRProviderError(msg) from e
