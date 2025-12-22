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

"""Generic Torrent RSS feed indexer implementation.

This indexer parses standard RSS feeds containing torrent links.
It supports both magnet links and .torrent file URLs.
"""

import logging
import re
from collections.abc import Sequence
from contextlib import suppress
from datetime import datetime
from xml.etree import ElementTree as ET  # noqa: S405
from xml.etree.ElementTree import Element  # noqa: S405

import httpx

from bookcard.pvr.base import (
    BaseIndexer,
    IndexerSettings,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
    handle_http_error_response,
)
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)


class TorrentRssSettings(IndexerSettings):
    """Settings for Torrent RSS indexer.

    Extends IndexerSettings with RSS feed URL.

    Attributes
    ----------
    feed_url : str
        RSS feed URL to parse.
    """

    feed_url: str


class TorrentRssParser:
    """Parses generic RSS feeds for torrent links.

    Extracts release information from standard RSS feeds, looking for
    torrent links in enclosure elements, links, or descriptions.
    """

    def __init__(self) -> None:
        """Initialize parser."""

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
                    release = self._parse_item(item, indexer_id)
                    if release:
                        releases.append(release)
                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    logger.warning("Failed to parse item: %s", e, exc_info=True)
                    continue
        except Exception as e:
            if isinstance(e, PVRProviderError):
                raise
            msg = f"Failed to parse RSS feed: {e}"
            raise PVRProviderParseError(msg) from e
        else:
            return releases

    def _parse_item(self, item: Element, indexer_id: int | None) -> ReleaseInfo | None:
        """Parse a single item element into ReleaseInfo.

        Parameters
        ----------
        item : Element
            XML item element.
        indexer_id : int | None
            Optional indexer ID.

        Returns
        -------
        ReleaseInfo | None
            Parsed release info, or None if invalid.
        """
        # Extract title
        title_elem = item.find("title")
        if title_elem is None or title_elem.text is None:
            return None
        title = title_elem.text.strip()

        # Extract download URL (enclosure, link, or from description)
        download_url = self._get_download_url(item)
        if not download_url:
            return None

        # Extract size
        size_bytes = self._get_size(item)

        # Extract publish date
        publish_date = self._extract_publish_date(item)

        # Extract description
        desc_elem = item.find("description")
        description = desc_elem.text if desc_elem is not None else None

        # Extract category
        category_elem = item.find("category")
        category = category_elem.text if category_elem is not None else None

        # Try to infer quality/format from title
        quality = self._infer_quality_from_title(title)

        # Try to extract seeders/leechers from description if available
        seeders, leechers = self._extract_seeders_leechers(description)

        return ReleaseInfo(
            indexer_id=indexer_id,
            title=title,
            download_url=download_url,
            size_bytes=size_bytes,
            publish_date=publish_date,
            seeders=seeders,
            leechers=leechers,
            quality=quality,
            author=None,
            isbn=None,
            description=description,
            category=category,
            additional_info=None,
        )

    def _extract_publish_date(self, item: Element) -> datetime | None:
        """Extract publish date from item.

        Parameters
        ----------
        item : Element
            XML item element.

        Returns
        -------
        datetime | None
            Parsed publish date or None if not found/invalid.
        """
        pub_date_elem = item.find("pubDate")
        if pub_date_elem is not None and pub_date_elem.text:
            try:
                from email.utils import parsedate_to_datetime

                return parsedate_to_datetime(pub_date_elem.text)
            except (ValueError, TypeError):
                pass
        return None

    def _infer_quality_from_title(self, title: str) -> str | None:
        """Infer quality/format from title.

        Parameters
        ----------
        title : str
            Item title.

        Returns
        -------
        str | None
            Inferred quality or None.
        """
        title_lower = title.lower()
        if "epub" in title_lower:
            return "epub"
        if "pdf" in title_lower:
            return "pdf"
        if "mobi" in title_lower:
            return "mobi"
        if "azw" in title_lower or "kindle" in title_lower:
            return "azw"
        return None

    def _extract_seeders_leechers(
        self, description: str | None
    ) -> tuple[int | None, int | None]:
        """Extract seeders and leechers from description.

        Parameters
        ----------
        description : str | None
            Item description text.

        Returns
        -------
        tuple[int | None, int | None]
            Tuple of (seeders, leechers).
        """
        seeders: int | None = None
        leechers: int | None = None

        if description:
            # Look for common patterns like "Seeders: 5" or "S:5 L:2"
            seeders_match = re.search(
                r"(?:seeders?|seeds?|s)[\s:]+(\d+)", description, re.IGNORECASE
            )
            if seeders_match:
                with suppress(ValueError, TypeError):
                    seeders = int(seeders_match.group(1))

            leechers_match = re.search(
                r"(?:leechers?|leech|peers?|l)[\s:]+(\d+)", description, re.IGNORECASE
            )
            if leechers_match:
                with suppress(ValueError, TypeError):
                    leechers = int(leechers_match.group(1))

        return (seeders, leechers)

    def _get_download_url(self, item: Element) -> str | None:
        """Extract download URL from item.

        Looks for torrent links in:
        1. Enclosure element (type="application/x-bittorrent")
        2. Link element (if it's a magnet or .torrent)
        3. Description (magnet links)

        Parameters
        ----------
        item : Element
            XML item element.

        Returns
        -------
        str | None
            Download URL or None if not found.
        """
        # Try enclosure element
        enclosure = item.find("enclosure")
        if enclosure is not None:
            url_attr = enclosure.get("url")
            type_attr = enclosure.get("type", "").lower()
            if url_attr and (
                type_attr == "application/x-bittorrent"
                or url_attr.startswith("magnet:")
                or url_attr.endswith(".torrent")
            ):
                return url_attr

        # Try link element
        link_elem = item.find("link")
        if link_elem is not None and link_elem.text:
            link = link_elem.text.strip()
            if link.startswith("magnet:") or link.endswith(".torrent"):
                return link

        # Try to find magnet link in description
        desc_elem = item.find("description")
        if desc_elem is not None and desc_elem.text:
            # Look for magnet links
            magnet_match = re.search(
                r"magnet:\?[^\s<>\"']+", desc_elem.text, re.IGNORECASE
            )
            if magnet_match:
                return magnet_match.group(0)

            # Look for .torrent URLs
            torrent_match = re.search(
                r"https?://[^\s<>\"']+\.torrent", desc_elem.text, re.IGNORECASE
            )
            if torrent_match:
                return torrent_match.group(0)

        return None

    def _get_size(self, item: Element) -> int | None:
        """Extract size from item.

        Parameters
        ----------
        item : Element
            XML item element.

        Returns
        -------
        int | None
            Size in bytes or None if not found.
        """
        # Try enclosure length
        enclosure = item.find("enclosure")
        if enclosure is not None:
            length_attr = enclosure.get("length")
            if length_attr:
                try:
                    return int(length_attr)
                except (ValueError, TypeError):
                    pass

        return None


class TorrentRssIndexer(BaseIndexer):
    """Generic Torrent RSS feed indexer.

    Parses standard RSS feeds to find torrent links. Supports both
    magnet links and .torrent file URLs.
    """

    def __init__(
        self, settings: TorrentRssSettings | IndexerSettings, enabled: bool = True
    ) -> None:
        """Initialize Torrent RSS indexer.

        Parameters
        ----------
        settings : TorrentRssSettings | IndexerSettings
            Indexer settings. Must include feed_url.
        enabled : bool
            Whether this indexer is enabled.
        """
        # Convert IndexerSettings to TorrentRssSettings if needed
        if isinstance(settings, IndexerSettings) and not isinstance(
            settings, TorrentRssSettings
        ):
            # Try to get feed_url from additional_settings or use base_url
            feed_url = getattr(settings, "feed_url", None)
            if not feed_url and hasattr(settings, "base_url"):
                feed_url = settings.base_url

            if not feed_url:
                msg = "TorrentRssSettings requires feed_url"
                raise ValueError(msg)

            torrent_rss_settings = TorrentRssSettings(
                base_url=settings.base_url,
                api_key=settings.api_key,
                timeout_seconds=settings.timeout_seconds,
                retry_count=settings.retry_count,
                categories=settings.categories,
                feed_url=str(feed_url),
            )
            settings = torrent_rss_settings

        super().__init__(settings, enabled)
        self.settings: TorrentRssSettings = settings  # type: ignore[assignment]
        self.parser = TorrentRssParser()

    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
    ) -> Sequence[ReleaseInfo]:
        """Search for releases matching the query.

        For RSS feeds, this fetches the feed and filters results by
        the search query (title/author).

        Parameters
        ----------
        query : str
            General search query (title, author, etc.).
        title : str | None
            Optional specific title to search for.
        author : str | None
            Optional specific author to search for.
        isbn : str | None
            Optional ISBN to search for.
        max_results : int
            Maximum number of results to return (default: 100).

        Returns
        -------
        Sequence[ReleaseInfo]
            Sequence of release information matching the query.
            Returns empty sequence if no results or if indexer is disabled.

        Raises
        ------
        PVRProviderError
            If the search fails due to network, parsing, or other errors.
        """
        if not self.is_enabled():
            return []

        # Fetch RSS feed
        try:
            response = self._make_request(self.settings.feed_url)
            releases = self.parser.parse_response(
                response.content,
                indexer_id=None,  # TODO: Get from definition
            )

            # Filter by search query
            search_terms = self._build_search_terms(query, title, author, isbn)
            if search_terms:
                releases = self._filter_releases_by_terms(releases, search_terms)

            return releases[:max_results]

        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Unexpected error during search: {e}"
            raise PVRProviderError(msg) from e

    def _build_search_terms(
        self,
        query: str,
        title: str | None,
        author: str | None,
        isbn: str | None,
    ) -> list[str]:
        """Build list of search terms from query parameters.

        Parameters
        ----------
        query : str
            General search query.
        title : str | None
            Optional title.
        author : str | None
            Optional author.
        isbn : str | None
            Optional ISBN.

        Returns
        -------
        list[str]
            List of lowercase search terms.
        """
        search_terms: list[str] = []
        if title:
            search_terms.append(title.lower())
        if author:
            search_terms.append(author.lower())
        if isbn:
            search_terms.append(isbn.lower())
        if query:
            search_terms.append(query.lower())
        return search_terms

    def _filter_releases_by_terms(
        self, releases: list[ReleaseInfo], search_terms: list[str]
    ) -> list[ReleaseInfo]:
        """Filter releases by search terms.

        Parameters
        ----------
        releases : list[ReleaseInfo]
            List of releases to filter.
        search_terms : list[str]
            List of search terms to match.

        Returns
        -------
        list[ReleaseInfo]
            Filtered list of releases.
        """
        filtered_releases: list[ReleaseInfo] = []
        for release in releases:
            title_lower = release.title.lower()
            desc_lower = (release.description or "").lower()

            # Check if any search term matches
            if any(term in title_lower or term in desc_lower for term in search_terms):
                filtered_releases.append(release)

        return filtered_releases

    def test_connection(self) -> bool:
        """Test connectivity to the RSS feed.

        Fetches the RSS feed to verify it's accessible and valid.

        Returns
        -------
        bool
            True if connection test succeeds, False otherwise.

        Raises
        ------
        PVRProviderError
            If the connection test fails with a specific error.
        """
        try:
            response = self._make_request(self.settings.feed_url)
            # Try to parse as XML to verify it's valid
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
        PVRProviderNetworkError
            If network request fails.
        PVRProviderTimeoutError
            If request times out.
        PVRProviderError
            For other errors.
        """
        timeout = self.settings.timeout_seconds

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url)

                # Check for HTTP errors
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
