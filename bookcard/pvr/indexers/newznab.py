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

"""Newznab indexer implementation.

Newznab is a standardized API for Usenet indexers. This implementation
supports searching by title/author and fetching RSS feeds from Newznab-compatible
indexers.

Documentation: https://newznab.readthedocs.io/
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from urllib.parse import urlencode, urljoin
from xml.etree import ElementTree as ET  # noqa: S405

import httpx

from bookcard.pvr.base import (
    BaseIndexer,
    IndexerSettings,
    PVRProviderAuthenticationError,
    PVRProviderError,
    PVRProviderNetworkError,
    PVRProviderParseError,
    PVRProviderTimeoutError,
    handle_api_error_response,
    handle_http_error_response,
)
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)

# Newznab XML namespace
NEWZNAB_NS = "{http://www.newznab.com/DTD/2010/feeds/attributes/}"

# Default book categories for Newznab (ebooks)
DEFAULT_BOOK_CATEGORIES = [7000, 7020]  # Books: 7000, E-Books: 7020


class NewznabSettings(IndexerSettings):
    """Settings for Newznab indexer.

    Extends IndexerSettings with Newznab-specific configuration.

    Attributes
    ----------
    api_path : str
        API path (default: "/api").
    """

    api_path: str = "/api"


class NewznabRequestGenerator:
    """Generates Newznab API request URLs.

    Builds properly formatted Newznab API requests with query parameters,
    categories, and pagination support.
    """

    def __init__(self, settings: NewznabSettings) -> None:
        """Initialize request generator.

        Parameters
        ----------
        settings : NewznabSettings
            Newznab indexer settings.
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
            Complete Newznab API URL.
        """
        # Build base URL
        base_url = self.settings.base_url.rstrip("/")
        api_path = self.settings.api_path.rstrip("/")
        url = urljoin(base_url, api_path)

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
            Complete Newznab RSS URL.
        """
        # Build base URL
        base_url = self.settings.base_url.rstrip("/")
        api_path = self.settings.api_path.rstrip("/")
        url = urljoin(base_url, api_path)

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


class NewznabParser:
    """Parses Newznab XML responses.

    Extracts release information from Newznab XML RSS feeds, including
    standard RSS elements and Newznab-specific attributes.
    """

    def __init__(self) -> None:
        """Initialize parser."""
        self.ns = NEWZNAB_NS

    def parse_response(
        self, xml_content: bytes | str, indexer_id: int | None = None
    ) -> list[ReleaseInfo]:
        """Parse Newznab XML response into ReleaseInfo objects.

        Parameters
        ----------
        xml_content : bytes | str
            XML content from Newznab API.
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
                handle_api_error_response(code, description, "Newznab")

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

    def _parse_item(
        self, item: ET.Element, indexer_id: int | None
    ) -> ReleaseInfo | None:
        """Parse a single item element into ReleaseInfo.

        Parameters
        ----------
        item : ET.Element
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

        # Extract download URL (enclosure or link)
        download_url = self._get_download_url(item)
        if not download_url:
            return None

        # Extract size
        size_bytes = self._get_size(item)

        # Extract publish date
        publish_date = self._extract_publish_date(item)

        # Usenet doesn't have seeders/leechers
        seeders: int | None = None
        leechers: int | None = None

        # Extract description
        desc_elem = item.find("description")
        description = desc_elem.text if desc_elem is not None else None

        # Extract category
        category_elem = item.find("category")
        category = category_elem.text if category_elem is not None else None

        # Extract metadata (author, isbn, quality)
        author, isbn, quality = self._extract_metadata(item, title)

        return ReleaseInfo(
            indexer_id=indexer_id,
            title=title,
            download_url=download_url,
            size_bytes=size_bytes,
            publish_date=publish_date,
            seeders=seeders,
            leechers=leechers,
            quality=quality,
            author=author,
            isbn=isbn,
            description=description,
            category=category,
            additional_info=None,
        )

    def _extract_publish_date(self, item: ET.Element) -> datetime | None:
        """Extract publish date from item.

        Parameters
        ----------
        item : ET.Element
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

    def _extract_metadata(
        self, item: ET.Element, title: str
    ) -> tuple[str | None, str | None, str | None]:
        """Extract metadata (author, isbn, quality) from item.

        Parameters
        ----------
        item : ET.Element
            XML item element.
        title : str
            Item title for quality inference.

        Returns
        -------
        tuple[str | None, str | None, str | None]
            Tuple of (author, isbn, quality).
        """
        # Try to extract from Newznab attributes
        author = self._get_newznab_attribute(item, "author") or None
        isbn = self._get_newznab_attribute(item, "isbn") or None

        # Extract quality/format
        quality_attr = self._get_newznab_attribute(item, "format")
        quality = quality_attr or self._infer_quality_from_title(title)

        return (author, isbn, quality)

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

    def _get_download_url(self, item: ET.Element) -> str | None:
        """Extract download URL from item.

        Parameters
        ----------
        item : ET.Element
            XML item element.

        Returns
        -------
        str | None
            Download URL or None if not found.
        """
        # Try enclosure URL (NZB file)
        enclosure = item.find("enclosure")
        if enclosure is not None:
            url_attr = enclosure.get("url")
            if url_attr:
                return url_attr

        # Try link element
        link_elem = item.find("link")
        if link_elem is not None and link_elem.text:
            return link_elem.text.strip()

        return None

    def _get_size(self, item: ET.Element) -> int | None:
        """Extract size from item.

        Parameters
        ----------
        item : ET.Element
            XML item element.

        Returns
        -------
        int | None
            Size in bytes or None if not found.
        """
        # Try Newznab size attribute
        size_str = self._get_newznab_attribute(item, "size")
        if size_str:
            try:
                return int(size_str)
            except (ValueError, TypeError):
                pass

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

    def _get_newznab_attribute(
        self, item: ET.Element, name: str, default: str = ""
    ) -> str:
        """Get a Newznab attribute value.

        Parameters
        ----------
        item : ET.Element
            XML item element.
        name : str
            Attribute name.
        default : str
            Default value if not found.

        Returns
        -------
        str
            Attribute value or default.
        """
        attr_elem = item.find(f".//{self.ns}attr[@name='{name}']")
        if attr_elem is not None:
            value_attr = attr_elem.get("value")
            if value_attr:
                return value_attr
        return default


class NewznabIndexer(BaseIndexer):
    """Newznab indexer implementation.

    Supports searching for books by title/author and fetching RSS feeds
    from Newznab-compatible Usenet indexers.
    """

    def __init__(
        self, settings: NewznabSettings | IndexerSettings, enabled: bool = True
    ) -> None:
        """Initialize Newznab indexer.

        Parameters
        ----------
        settings : NewznabSettings | IndexerSettings
            Indexer settings. If IndexerSettings, converts to NewznabSettings.
        enabled : bool
            Whether this indexer is enabled.
        """
        # Convert IndexerSettings to NewznabSettings if needed
        if isinstance(settings, IndexerSettings) and not isinstance(
            settings, NewznabSettings
        ):
            newznab_settings = NewznabSettings(
                base_url=settings.base_url,
                api_key=settings.api_key,
                timeout_seconds=settings.timeout_seconds,
                retry_count=settings.retry_count,
                categories=settings.categories,
                api_path="/api",  # Default
            )
            settings = newznab_settings

        super().__init__(settings, enabled)
        self.settings: NewznabSettings = settings  # type: ignore[assignment]
        self.request_generator = NewznabRequestGenerator(self.settings)
        self.parser = NewznabParser()

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
            Returns empty sequence if no results or if indexer is disabled.

        Raises
        ------
        PVRProviderError
            If the search fails due to network, parsing, or other errors.
        """
        if not self.is_enabled():
            return []

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
        base_url = self.settings.base_url.rstrip("/")
        api_path = self.settings.api_path.rstrip("/")
        url = urljoin(base_url, api_path)

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
                handle_api_error_response(code, description, "Newznab")
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
        """Make HTTP request to Newznab API.

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
