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

"""Amazon Books metadata provider.

This provider fetches book metadata by scraping Amazon's website.
It searches for digital books and extracts metadata from product pages.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import TYPE_CHECKING, ClassVar

import httpx
from bs4 import BeautifulSoup

from bookcard.metadata.base import (
    MetadataProvider,
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from bookcard.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


def _normalize_href(href: object) -> str:
    """Normalize a BeautifulSoup href value to a string.

    Parameters
    ----------
    href : object
        Value returned by BeautifulSoup for an attribute.

    Returns
    -------
    str
        A string href if one can be extracted, otherwise an empty string.
    """
    if isinstance(href, str):
        return href
    if isinstance(href, list):
        for value in href:
            if isinstance(value, str):
                return value
    return ""


class AmazonProvider(MetadataProvider):
    """Metadata provider for Amazon Books.

    This provider scrapes Amazon's website to search for books and
    retrieve metadata. It uses HTML parsing to extract book information
    from product pages.
    """

    BASE_URL = "https://www.amazon.com"
    SEARCH_URL = f"{BASE_URL}/s"
    SOURCE_ID = "amazon"
    SOURCE_NAME = "Amazon"
    SOURCE_DESCRIPTION = "Amazon Books"
    REQUEST_TIMEOUT = 15  # seconds
    MAX_WORKERS = 5  # concurrent requests for detail pages

    # Headers to mimic a browser request
    HEADERS: ClassVar[dict[str, str]] = {
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "alt-used": "www.amazon.com",
        "priority": "u=0, i",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
    }

    def __init__(self, enabled: bool = True, timeout: int = REQUEST_TIMEOUT) -> None:
        """Initialize Amazon provider.

        Parameters
        ----------
        enabled : bool
            Whether this provider is enabled.
        timeout : int
            Request timeout in seconds.
        """
        super().__init__(enabled)
        self.timeout = timeout

    def get_source_info(self) -> MetadataSourceInfo:
        """Get information about Amazon source.

        Returns
        -------
        MetadataSourceInfo
            Source information.
        """
        return MetadataSourceInfo(
            id=self.SOURCE_ID,
            name=self.SOURCE_NAME,
            description=self.SOURCE_DESCRIPTION,
            base_url=self.BASE_URL,
        )

    def search(
        self,
        query: str,
        locale: str = "en",  # noqa: ARG002
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for books on Amazon.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code (default: 'en', currently only 'en' supported).
        max_results : int
            Maximum number of results (default: 10).

        Returns
        -------
        Sequence[MetadataRecord]
            Sequence of metadata records.

        Raises
        ------
        MetadataProviderNetworkError
            If network request fails.
        MetadataProviderTimeoutError
            If request times out.
        MetadataProviderParseError
            If response cannot be parsed.
        """
        if not self.is_enabled():
            return []

        if not query or not query.strip():
            return []

        try:
            # Build search URL for digital books
            search_query = query.strip().replace(" ", "+")
            search_params = {
                "k": search_query,
                "i": "digital-text",
                "sprefix": f"{search_query}%2Cdigital-text",
                "ref": "nb_sb_noss",
            }

            # Fetch search results page and detail pages using same client
            with httpx.Client(
                headers=self.HEADERS, timeout=self.timeout, follow_redirects=True
            ) as client:
                response = client.get(self.SEARCH_URL, params=search_params)
                response.raise_for_status()

                # Parse search results
                soup = BeautifulSoup(response.text, "html.parser")
                links_list = self._extract_search_result_links(soup)

                if not links_list:
                    return []

                # Limit to max_results
                links_list = links_list[:max_results]

                # Fetch detail pages concurrently
                records = self._fetch_book_details(links_list, client)

                # Sort by original order for relevance
                records.sort(key=lambda x: x[1])
                result = [record[0] for record in records]
        except httpx.TimeoutException as e:
            msg = f"Amazon search request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except (
            httpx.HTTPStatusError,
            httpx.HTTPError,
            httpx.RequestError,
        ) as e:
            msg = f"Amazon search request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (ValueError, TypeError, AttributeError) as e:
            msg = f"Failed to parse Amazon search results: {e}"
            raise MetadataProviderParseError(msg) from e
        else:
            return result

    def _extract_search_result_links(self, soup: BeautifulSoup) -> list[str]:
        """Extract book detail page links from search results.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML of search results page.

        Returns
        -------
        list[str]
            List of relative URLs to book detail pages.
        """
        links = []
        search_results = soup.find_all(
            "div", attrs={"data-component-type": "s-search-result"}
        )

        for result in search_results:
            links_elem = result.find_all("a")
            for link_elem in links_elem:
                href = _normalize_href(link_elem.get("href"))
                if "digital-text" in href:
                    links.append(href)
                    break

        return links

    def _fetch_book_details(
        self, links: list[str], client: httpx.Client
    ) -> list[tuple[MetadataRecord, int]]:
        """Fetch book details from multiple detail pages concurrently.

        Parameters
        ----------
        links : list[str]
            List of relative URLs to book detail pages.
        client : httpx.Client
            HTTP client for making requests.

        Returns
        -------
        list[tuple[MetadataRecord, int]]
            List of (metadata record, original index) tuples.
        """
        results: list[tuple[MetadataRecord, int]] = []

        # Fetch details concurrently
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS
        ) as executor:
            futures = {
                executor.submit(self._fetch_single_book_detail, link, index, client)
                for index, link in enumerate(links)
            }

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except (
                    httpx.HTTPStatusError,
                    httpx.HTTPError,
                    httpx.RequestError,
                    AttributeError,
                    ValueError,
                    TypeError,
                    concurrent.futures.CancelledError,
                ) as e:
                    # Safety net: catch exceptions that might have escaped
                    # the inner try-except block (shouldn't happen, but defensive)
                    logger.warning(
                        "Unexpected error in Amazon detail fetch future: %s",
                        e,
                        exc_info=True,
                    )

        return results

    def _fetch_single_book_detail(
        self, link: str, index: int, client: httpx.Client
    ) -> tuple[MetadataRecord, int] | None:
        """Fetch and parse a single book detail page.

        Parameters
        ----------
        link : str
            Relative URL to book detail page.
        index : int
            Original index in search results.
        client : httpx.Client
            HTTP client for making requests.

        Returns
        -------
        tuple[MetadataRecord, int] | None
            Parsed metadata record with index, or None if parsing fails.
        """
        try:
            url = f"{self.BASE_URL}{link}"
            response = client.get(url, headers=self.HEADERS)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            detail_section = self._find_detail_section(soup)

            # Extract description first - if missing, it's likely not a book
            description = self._extract_description(detail_section)
            if description is None:
                return None
            record = self._create_metadata_record(
                link, url, detail_section, description
            )

        except (
            httpx.HTTPStatusError,
            httpx.HTTPError,
            httpx.RequestError,
            AttributeError,
            ValueError,
            TypeError,
        ) as e:
            self._log_http_error(e)
            return None
        else:
            return (record, index)

    def _find_detail_section(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Find the detail section in Amazon's HTML structure.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML of the book detail page.

        Returns
        -------
        BeautifulSoup
            The detail section element, or the whole soup as fallback.
        """
        detail_section = soup.find(
            "div",
            attrs={"cel_widget_id": "dpx-ppd_csm_instrumentation_wrapper"},
        )
        if detail_section is not None:
            return detail_section

        detail_section = soup.find("div", attrs={"id": "dp-container"})
        if detail_section is not None:
            return detail_section

        return soup

    def _create_metadata_record(
        self, link: str, url: str, detail_section: BeautifulSoup, description: str
    ) -> MetadataRecord:
        """Create a metadata record from extracted data.

        Parameters
        ----------
        link : str
            Relative URL to book detail page.
        url : str
            Full URL to book detail page.
        detail_section : BeautifulSoup
            Parsed HTML section containing book details.
        description : str
            Book description.

        Returns
        -------
        MetadataRecord
            Metadata record for the book.
        """
        title = self._extract_title(detail_section)
        authors = self._extract_authors(detail_section)
        rating = self._extract_rating(detail_section)
        cover_url = self._extract_cover_url(detail_section)
        external_id = self._extract_asin(link)

        return MetadataRecord(
            source_id=self.SOURCE_ID,
            external_id=external_id,
            title=title,
            authors=authors,
            url=url,
            cover_url=cover_url,
            description=description,
            rating=rating,
            # Amazon doesn't reliably provide these fields
            series=None,
            series_index=None,
            identifiers={},
            publisher=None,
            published_date=None,
            languages=[],
            tags=[],
        )

    def _log_http_error(self, error: Exception) -> None:
        """Log HTTP errors for debugging.

        Parameters
        ----------
        error : Exception
            The HTTP error that occurred.
        """
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code if error.response else "unknown"
            logger.debug(
                "Failed to fetch Amazon book detail page: %s (status: %s)",
                error,
                status_code,
            )
        elif isinstance(error, httpx.HTTPError):
            logger.debug("Failed to fetch Amazon book detail page: %s", error)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract book title from detail page.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML section containing book details.

        Returns
        -------
        str
            Book title, or empty string if not found.
        """
        try:
            title_elem = soup.find("span", attrs={"id": "productTitle"})
            if title_elem:
                return title_elem.get_text(strip=True)
        except (AttributeError, TypeError):
            pass
        return ""

    def _extract_authors(self, soup: BeautifulSoup) -> list[str]:
        """Extract authors from detail page.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML section containing book details.

        Returns
        -------
        list[str]
            List of author names.
        """
        authors = []
        try:
            author_elems = soup.find_all("span", attrs={"class": "author"})
            for author_elem in author_elems:
                # Filter out empty strings, newlines, and JSON-like strings
                author_texts = author_elem.find_all(string=True)
                for text in author_texts:
                    text = text.strip()
                    if text and text != "\n" and not text.startswith("{"):
                        authors.append(text)
                        break
        except (AttributeError, TypeError, StopIteration):
            pass
        return authors

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        """Extract book description from detail page.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML section containing book details.

        Returns
        -------
        str | None
            Book description, or None if not found (indicates not a book).
        """
        try:
            desc_elem = soup.find("div", attrs={"data-feature-name": "bookDescription"})
            if desc_elem:
                # Join all text content and clean it
                description = "\n".join(desc_elem.stripped_strings)
                # Remove trailing "Show more" text and clean whitespace
                description = description.replace("\xa0", " ").strip().strip("\n")
                # Remove trailing "Show more" if present
                if description.endswith("Show more"):
                    description = description[:-9].strip()
                return description if description else None
        except (AttributeError, TypeError):
            pass
        return None

    def _extract_rating(self, soup: BeautifulSoup) -> float | None:
        """Extract book rating from detail page.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML section containing book details.

        Returns
        -------
        float | None
            Rating value (0-5), or None if not found.
        """
        try:
            rating_elem = soup.find("span", class_="a-icon-alt")
            if rating_elem:
                rating_text = rating_elem.get_text()
                # Extract first number from string like "4.5 out of 5 stars"
                rating_str = rating_text.split(" ")[0].split(".")[0]
                rating = int(rating_str)
                return float(rating) if 0 <= rating <= 5 else None
        except (AttributeError, ValueError, IndexError):
            pass
        return None

    def _extract_cover_url(self, soup: BeautifulSoup) -> str | None:
        """Extract cover image URL from detail page.

        Parameters
        ----------
        soup : BeautifulSoup
            Parsed HTML section containing book details.

        Returns
        -------
        str | None
            Cover image URL, or None if not found.
        """
        try:
            cover_elem = soup.find("img", attrs={"class": "a-dynamic-image"})
            if cover_elem:
                cover_url = cover_elem.get("src")
                if cover_url:
                    return cover_url
        except (AttributeError, TypeError):
            pass
        return None

    def _extract_asin(self, link: str) -> str:
        """Extract ASIN (Amazon Standard Identification Number) from URL.

        Parameters
        ----------
        link : str
            Relative URL to book detail page.

        Returns
        -------
        str
            ASIN identifier.
        """
        # ASIN is typically in the URL like /dp/B00ABC123 or /gp/product/B00ABC123
        # Extract the alphanumeric code after /dp/ or /gp/product/
        parts = link.split("/")
        for i, part in enumerate(parts):
            if part in ("dp", "gp") and i + 1 < len(parts):
                asin = parts[i + 1].split("?")[0].split("/")[0]
                if asin:
                    return asin
        # Fallback: use the link itself as external_id
        return link.split("/")[-1].split("?")[0] if link else "unknown"
