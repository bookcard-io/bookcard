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

"""Torznab indexer implementation.

Torznab is a standardized API for torrent indexers, extending the Newznab API.
This implementation supports searching by title/author and fetching RSS feeds.

Documentation: https://torznab.github.io/spec-1.3-draft/torznab/
"""

import logging
from collections.abc import Sequence
from urllib.parse import urlencode
from xml.etree import ElementTree as ET  # noqa: S405

import httpx

from bookcard.pvr.base import BaseIndexer, IndexerSettings
from bookcard.pvr.base.interfaces import (
    RequestGeneratorProtocol,
    ResponseParserProtocol,
)
from bookcard.pvr.error_handlers import (
    handle_api_error_response,
    handle_http_error_response,
)
from bookcard.pvr.exceptions import (
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
)
from bookcard.pvr.indexers.parsers import (
    AdditionalInfoExtractor,
    AttributeExtractor,
    CompositeReleaseParser,
    DownloadUrlExtractor,
    GuidExtractor,
    MetadataExtractor,
    PublishDateExtractor,
    ReleaseFieldExtractor,
    SimpleTextExtractor,
    SizeExtractor,
    TitleExtractor,
)
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)

# Torznab XML namespace
TORZNAB_NS = "{http://torznab.com/schemas/2015/feed}"

# Default book categories for Torznab (ebooks)
DEFAULT_BOOK_CATEGORIES = [7000, 7020]  # Books: 7000, E-Books: 7020


def _build_api_url(base_url: str, api_path: str) -> str:
    """Build API URL handling paths correctly.

    Ensures that api_path is appended to base_url correctly, avoiding
    duplication if base_url already contains the path, and handling
    slashes properly.
    """
    base_url = base_url.rstrip("/")
    api_path = api_path.strip("/")

    if base_url.endswith(f"/{api_path}"):
        return base_url

    return f"{base_url}/{api_path}"


class TorznabSettings(IndexerSettings):
    """Settings for Torznab indexer.

    Extends IndexerSettings with Torznab-specific configuration.

    Attributes
    ----------
    api_path : str
        API path (default: "/api").
    """

    api_path: str = "/api"


class TorznabRequestGenerator:
    """Generates Torznab API request URLs.

    Builds properly formatted Torznab API requests with query parameters,
    categories, and pagination support.
    """

    def __init__(self, settings: TorznabSettings) -> None:
        """Initialize request generator.

        Parameters
        ----------
        settings : TorznabSettings
            Torznab indexer settings.
        """
        self.settings = settings

    def build_search_url(
        self,
        query: str | None = None,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        categories: list[int] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> str:
        """Build a search request URL.

        Parameters
        ----------
        query : str | None
            General search query.
        title : str | None
            Specific title to search for.
        author : str | None
            Specific author to search for.
        isbn : str | None
            ISBN to search for.
        categories : list[int] | None
            Category IDs to filter by (None = use settings categories).
        offset : int
            Result offset for pagination (default: 0).
        limit : int
            Maximum results per page (default: 100).

        Returns
        -------
        str
            Complete Torznab API URL.
        """
        # Build base URL
        url = _build_api_url(self.settings.base_url, self.settings.api_path)

        # Build query parameters
        params: dict[str, str | int] = {
            "t": "search",  # Search type
            "extended": "1",  # Request extended attributes
        }

        # Add API key if provided
        if self.settings.api_key:
            params["apikey"] = self.settings.api_key

        # Add search query
        if query:
            params["q"] = query
        elif title:
            # Prefer title parameter if available, otherwise use q
            params["q"] = title
        elif author:
            params["q"] = author
        elif isbn:
            params["q"] = isbn

        # Add categories
        if categories is None:
            categories = self.settings.categories or DEFAULT_BOOK_CATEGORIES

        if categories:
            params["cat"] = ",".join(str(cat) for cat in categories)

        # Add pagination
        if limit > 0:
            params["offset"] = offset
            params["limit"] = limit

        # Build final URL
        query_string = urlencode(params, doseq=False)
        return f"{url}?{query_string}"

    def build_rss_url(
        self,
        categories: list[int] | None = None,
        limit: int = 100,
    ) -> str:
        """Build an RSS feed request URL.

        Parameters
        ----------
        categories : list[int] | None
            Category IDs to filter by (None = use settings categories).
        limit : int
            Maximum results to return (default: 100).

        Returns
        -------
        str
            Complete Torznab RSS URL.
        """
        # Build base URL
        url = _build_api_url(self.settings.base_url, self.settings.api_path)

        # Build query parameters
        params: dict[str, str | int] = {
            "t": "rss",  # RSS feed type
            "extended": "1",  # Request extended attributes
        }

        # Add API key if provided
        if self.settings.api_key:
            params["apikey"] = self.settings.api_key

        # Add categories
        if categories is None:
            categories = self.settings.categories or DEFAULT_BOOK_CATEGORIES

        if categories:
            params["cat"] = ",".join(str(cat) for cat in categories)

        # Add limit
        if limit > 0:
            params["limit"] = limit

        # Build final URL
        query_string = urlencode(params, doseq=False)
        return f"{url}?{query_string}"


class TorznabParser:
    """Parses Torznab XML responses.

    Extracts release information from Torznab XML RSS feeds using CompositeReleaseParser.
    """

    def __init__(self) -> None:
        """Initialize parser with composite extractors."""
        self.ns = TORZNAB_NS

        extractors: dict[str, ReleaseFieldExtractor] = {
            "title": TitleExtractor(),
            "guid": GuidExtractor(),
            "download_url": DownloadUrlExtractor(namespace=self.ns),
            "size_bytes": SizeExtractor(namespace=self.ns),
            "publish_date": PublishDateExtractor(),
            "seeders": AttributeExtractor("seeders", as_int=True, namespace=self.ns),
            "leechers": AttributeExtractor("leechers", as_int=True, namespace=self.ns),
            "description": SimpleTextExtractor("description"),
            "category": SimpleTextExtractor("category"),
            "metadata": MetadataExtractor(namespace=self.ns),
            "additional_info": AdditionalInfoExtractor(namespace=self.ns),
        }

        self.composite = CompositeReleaseParser(extractors)

    def parse_response(
        self, xml_content: bytes | str, indexer_id: int | None = None
    ) -> list[ReleaseInfo]:
        """Parse Torznab XML response into ReleaseInfo objects.

        Parameters
        ----------
        xml_content : bytes | str
            XML content from Torznab API.
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

            # Check for error elements
            error_elem = root.find(".//error")
            if error_elem is not None:
                code = int(error_elem.get("code", "0"))
                description = error_elem.get("description", "Unknown error")
                handle_api_error_response(code, description, "Torznab")

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
                        guid=data.get("guid"),
                        download_url=data.get("download_url"),  # type: ignore
                        size_bytes=data.get("size_bytes"),
                        publish_date=data.get("publish_date"),
                        seeders=data.get("seeders"),
                        leechers=data.get("leechers"),
                        quality=data.get("quality"),
                        author=data.get("author"),
                        isbn=data.get("isbn"),
                        description=data.get("description"),
                        category=data.get("category"),
                        additional_info=data.get("additional_info"),
                    )
                    releases.append(release)
                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    logger.warning("Failed to parse item: %s", e, exc_info=True)
                    continue
        except ET.ParseError as e:
            msg = f"Failed to parse XML response: {e}"
            raise PVRProviderParseError(msg) from e
        except Exception as e:
            if isinstance(e, PVRProviderError):
                raise
            msg = f"Unexpected error parsing response: {e}"
            raise PVRProviderParseError(msg) from e
        else:
            return releases


class TorznabIndexer(BaseIndexer):
    """Torznab indexer implementation.

    Supports searching for books by title/author and fetching RSS feeds
    from Torznab-compatible indexers.
    """

    def __init__(
        self,
        settings: TorznabSettings | IndexerSettings,
        request_generator: RequestGeneratorProtocol,
        parser: ResponseParserProtocol,
    ) -> None:
        """Initialize Torznab indexer.

        Parameters
        ----------
        settings : TorznabSettings | IndexerSettings
            Indexer settings. If IndexerSettings, converts to TorznabSettings.
        request_generator : RequestGeneratorProtocol
            Request generator service.
        parser : ResponseParserProtocol
            Response parser service.
        """
        # Convert IndexerSettings to TorznabSettings if needed
        if isinstance(settings, IndexerSettings) and not isinstance(
            settings, TorznabSettings
        ):
            torznab_settings = TorznabSettings(
                base_url=settings.base_url,
                api_key=settings.api_key,
                timeout_seconds=settings.timeout_seconds,
                retry_count=settings.retry_count,
                categories=settings.categories,
                api_path="/api",  # Default
            )
            settings = torznab_settings

        super().__init__(settings)
        self.settings: TorznabSettings = settings  # type: ignore[assignment]
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

        Raises
        ------
        PVRProviderError
            If the search fails due to network, parsing, or other errors.
        """
        # Build search query - prefer specific parameters over general query
        search_query: str | None = None
        if title:
            search_query = title
        elif author:
            search_query = author
        elif isbn:
            search_query = isbn
        elif query:
            search_query = query
        else:
            return []

        # Build URL
        url = self.request_generator.build_search_url(
            query=search_query,
            title=title,
            author=author,
            isbn=isbn,
            limit=max_results,
        )

        # Make request
        try:
            response = self._make_request(url)
            releases = self.parser.parse_response(
                response.content,
                indexer_id=None,  # TODO: Get from definition
            )
            return releases[:max_results]
        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Unexpected error during search: {e}"
            raise PVRProviderError(msg) from e

    def test_connection(self) -> bool:
        """Test connectivity to the indexer.

        Performs a simple capabilities request to verify the indexer is
        accessible and the API key is valid.

        Returns
        -------
        bool
            True if connection test succeeds, False otherwise.

        Raises
        ------
        PVRProviderError
            If the connection test fails with a specific error.
        """
        # Build capabilities URL
        url = _build_api_url(self.settings.base_url, self.settings.api_path)

        params: dict[str, str] = {"t": "caps"}
        if self.settings.api_key:
            params["apikey"] = self.settings.api_key

        query_string = urlencode(params)
        capabilities_url = f"{url}?{query_string}"

        try:
            response = self._make_request(capabilities_url)
            # Check if response is valid XML
            root = ET.fromstring(response.content)  # noqa: S314

            # Check for error
            error_elem = root.find(".//error")
            if error_elem is not None:
                code = int(error_elem.get("code", "0"))
                description = error_elem.get("description", "Unknown error")
                handle_api_error_response(code, description, "Torznab")
        except PVRProviderAuthenticationError:
            raise
        except PVRProviderError:
            raise
        except Exception as e:
            msg = f"Connection test failed: {e}"
            raise PVRProviderError(msg) from e
        else:
            # If we got valid XML without error, connection is good
            return True

    def _make_request(self, url: str) -> httpx.Response:
        """Make HTTP request to Torznab API.

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
