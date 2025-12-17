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

"""Douban (豆瓣) metadata provider.

This provider fetches book metadata by scraping Douban's website.
Douban is a Chinese social networking service for books, movies, and music.
"""

from __future__ import annotations

import concurrent.futures
import logging
import re
from typing import TYPE_CHECKING, ClassVar

import httpx
from bs4 import BeautifulSoup
from lxml import etree  # type: ignore[attr-defined]

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


def _sanitize_html_to_text(html: str) -> str:
    """Convert HTML to clean text using BeautifulSoup.

    Parameters
    ----------
    html : str
        HTML content to convert.

    Returns
    -------
    str
        Clean text content.
    """
    if isinstance(html, bytes):
        html = html.decode("utf-8")

    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and clean it up
    text = soup.get_text(separator=" ", strip=True)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_date(date: str) -> str:
    """Clean up the date string to be in the format YYYY-MM-DD.

    Handles various Chinese date formats:
    - '2014-7-16', '1988年4月', '1995-04', '2021-8', '2020-12-1', '1996年',
    - '1972', '2004/11/01', '1959年3月北京第1版第1印'

    Parameters
    ----------
    date : str
        Raw date string from Douban.

    Returns
    -------
    str
        Date string in YYYY-MM-DD format.
    """
    year = date[:4]
    moon = "01"
    day = "01"

    if len(date) > 5:
        digit = []
        ls = []
        for i in range(5, len(date)):
            if date[i].isdigit():
                digit.append(date[i])
            elif digit:
                ls.append("".join(digit) if len(digit) == 2 else f"0{digit[0]}")
                digit = []
        if digit:
            ls.append("".join(digit) if len(digit) == 2 else f"0{digit[0]}")

        if ls:
            moon = ls[0]
            if len(ls) > 1:
                day = ls[1]

    return f"{year}-{moon}-{day}"


class DoubanProvider(MetadataProvider):
    """Metadata provider for Douban (豆瓣).

    This provider scrapes Douban's website to search for books and
    retrieve metadata. It uses XPath queries to extract information
    from HTML pages.
    """

    BASE_URL = "https://book.douban.com/"
    SEARCH_URL = "https://www.douban.com/search"
    SOURCE_ID = "douban"
    SOURCE_NAME = "豆瓣"
    SOURCE_DESCRIPTION = "豆瓣 - Chinese book database"
    REQUEST_TIMEOUT = 15  # seconds
    MAX_WORKERS = 5  # concurrent requests for detail pages

    # Regex patterns for parsing
    ID_PATTERN = re.compile(r"sid: (?P<id>\d+),")
    AUTHORS_PATTERN = re.compile(r"作者|译者")
    PUBLISHER_PATTERN = re.compile(r"出版社")
    SUBTITLE_PATTERN = re.compile(r"副标题")
    PUBLISHED_DATE_PATTERN = re.compile(r"出版年")
    SERIES_PATTERN = re.compile(r"丛书")
    IDENTIFIERS_PATTERN = re.compile(r"ISBN|统一书号")
    CRITERIA_PATTERN = re.compile(r"criteria = '(.+)'")

    # XPath expressions for parsing
    TITLE_XPATH = "//span[@property='v:itemreviewed']"
    COVER_XPATH = "//a[@class='nbg']"
    INFO_XPATH = "//*[@id='info']//span[@class='pl']"
    TAGS_XPATH = "//a[contains(@class, 'tag')]"
    DESCRIPTION_XPATH = "//div[@id='link-report']//div[@class='intro']"
    RATING_XPATH = "//div[@class='rating_self clearfix']/strong"

    # Headers to mimic a browser request
    HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    }

    def __init__(self, enabled: bool = True, timeout: int = REQUEST_TIMEOUT) -> None:
        """Initialize Douban provider.

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
        """Get information about Douban source.

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
        """Search for books on Douban.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code (default: 'en', not used by Douban).
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
            # Prepare search query
            search_query = self._prepare_query(query)
            if not search_query:
                return []

            # Get book IDs from search results
            book_ids = self._get_book_id_list_from_html(search_query)

            if not book_ids:
                return []

            # Limit to max_results
            book_ids = book_ids[:max_results]

            # Fetch detail pages concurrently
            with httpx.Client(
                headers=self.HEADERS, timeout=self.timeout, follow_redirects=True
            ) as client:
                records = self._fetch_book_details(book_ids, client)

        except httpx.TimeoutException as e:
            msg = f"Douban search request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except (
            httpx.HTTPStatusError,
            httpx.HTTPError,
            httpx.RequestError,
        ) as e:
            msg = f"Douban search request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (ValueError, TypeError, AttributeError) as e:
            msg = f"Failed to parse Douban search results: {e}"
            raise MetadataProviderParseError(msg) from e
        else:
            return records

    def _prepare_query(self, query: str) -> str:
        """Prepare search query by tokenizing.

        Parameters
        ----------
        query : str
            Raw search query.

        Returns
        -------
        str
            Prepared query string with tokens joined by '+'.
        """
        # Simple tokenization - split on whitespace and filter short tokens
        title_tokens = [t for t in query.split() if len(t) > 1]

        if not title_tokens:
            return ""

        return "+".join(title_tokens)

    def _get_book_id_list_from_html(self, query: str) -> list[str]:
        """Extract book IDs from HTML search results.

        Parameters
        ----------
        query : str
            Search query string.

        Returns
        -------
        list[str]
            List of book IDs.
        """
        try:
            with httpx.Client(
                headers=self.HEADERS, timeout=self.timeout, follow_redirects=True
            ) as client:
                response = client.get(self.SEARCH_URL, params={"cat": 1001, "q": query})
                response.raise_for_status()

                html = etree.HTML(response.content.decode("utf8"))
                result_list = html.xpath(self.COVER_XPATH)

                book_ids = []
                for item in result_list[:10]:
                    onclick = item.get("onclick", "")
                    if match := self.ID_PATTERN.search(onclick):
                        book_ids.append(match.group("id"))

                return book_ids

        except (
            httpx.HTTPStatusError,
            httpx.HTTPError,
            httpx.RequestError,
            httpx.TimeoutException,
            UnicodeDecodeError,
            AttributeError,
            ValueError,
            TypeError,
        ) as e:
            logger.warning("Failed to get book IDs from Douban search: %s", e)
            return []

    def _fetch_book_details(
        self, book_ids: list[str], client: httpx.Client
    ) -> list[MetadataRecord]:
        """Fetch book details from multiple detail pages concurrently.

        Parameters
        ----------
        book_ids : list[str]
            List of book IDs.
        client : httpx.Client
            HTTP client for making requests.

        Returns
        -------
        list[MetadataRecord]
            List of metadata records.
        """
        records: list[MetadataRecord] = []

        # Fetch details concurrently
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS
        ) as executor:
            futures = {
                executor.submit(self._parse_single_book, book_id, client)
                for book_id in book_ids
            }

            for future in concurrent.futures.as_completed(futures):
                try:
                    record = future.result()
                    if record is not None:
                        records.append(record)
                except (
                    httpx.HTTPStatusError,
                    httpx.HTTPError,
                    httpx.RequestError,
                    AttributeError,
                    ValueError,
                    TypeError,
                    concurrent.futures.CancelledError,
                ) as e:
                    logger.warning(
                        "Unexpected error in Douban detail fetch future: %s",
                        e,
                        exc_info=True,
                    )

        return records

    def _parse_single_book(
        self, book_id: str, client: httpx.Client
    ) -> MetadataRecord | None:
        """Fetch and parse a single book detail page.

        Parameters
        ----------
        book_id : str
            Book ID from Douban.
        client : httpx.Client
            HTTP client for making requests.

        Returns
        -------
        MetadataRecord | None
            Parsed metadata record, or None if parsing fails.
        """
        url = f"{self.BASE_URL}subject/{book_id}/"
        logger.debug("Parsing Douban book: %s", url)

        try:
            response = client.get(url, headers=self.HEADERS)
            response.raise_for_status()

            decode_content = response.content.decode("utf8")
            html = etree.HTML(decode_content)

            # Extract title
            title_elements = html.xpath(self.TITLE_XPATH)
            if not title_elements:
                return None

            title = title_elements[0].text or ""

            # Extract cover
            cover_elements = html.xpath(self.COVER_XPATH)
            cover_url = cover_elements[0].attrib.get("href") if cover_elements else None

            # Extract rating
            rating = self._extract_rating(html)

            # Extract tags
            tags = self._extract_tags(html, decode_content)

            # Extract description
            description = self._extract_description(html)

            # Extract metadata from info section
            authors, publisher, subtitle, published_date, series, identifiers = (
                self._extract_info_metadata(html)
            )

            # Add subtitle to title if present
            if subtitle:
                title = f"{title}:{subtitle}"

            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=book_id,
                title=title,
                authors=authors,
                url=url,
                cover_url=cover_url,
                description=description,
                series=series,
                series_index=None,
                identifiers=identifiers,
                publisher=publisher,
                published_date=published_date,
                rating=rating,
                languages=[],
                tags=tags,
            )

        except (
            httpx.HTTPStatusError,
            httpx.HTTPError,
            httpx.RequestError,
            AttributeError,
            ValueError,
            TypeError,
            IndexError,
        ) as e:
            logger.debug("Failed to fetch Douban book detail page: %s", e)
            return None

    def _extract_rating(self, html: etree._Element) -> float | None:
        """Extract book rating.

        Parameters
        ----------
        html : etree._Element
            Parsed HTML element.

        Returns
        -------
        float | None
            Rating value (0-5), or None if not found.
        """
        try:
            rating_elements = html.xpath(self.RATING_XPATH)
            if rating_elements:
                rating_text = rating_elements[0].text
                if rating_text:
                    rating_num = float(rating_text.strip())
                    # Convert from 0-10 scale to 0-5 scale
                    return float(int(-1 * rating_num // 2 * -1)) if rating_num else 0.0
        except (ValueError, AttributeError, IndexError):
            pass
        return None

    def _extract_tags(self, html: etree._Element, content: str) -> list[str]:
        """Extract tags/categories.

        Parameters
        ----------
        html : etree._Element
            Parsed HTML element.
        content : str
            Raw HTML content as string.

        Returns
        -------
        list[str]
            List of tags.
        """
        tag_elements = html.xpath(self.TAGS_XPATH)
        if tag_elements:
            return [
                tag_element.text for tag_element in tag_elements if tag_element.text
            ]

        # Fallback: extract from criteria pattern
        if match := self.CRITERIA_PATTERN.search(content):
            return [
                item.replace("7:", "")
                for item in match.group().split("|")
                if item.startswith("7:")
            ]

        return []

    def _extract_description(self, html: etree._Element) -> str | None:
        """Extract book description.

        Parameters
        ----------
        html : etree._Element
            Parsed HTML element.

        Returns
        -------
        str | None
            Description text, or None if not found.
        """
        description_elements = html.xpath(self.DESCRIPTION_XPATH)
        if description_elements:
            try:
                description_html = etree.tostring(description_elements[-1]).decode(
                    "utf8"
                )
                return _sanitize_html_to_text(description_html)
            except (AttributeError, ValueError, TypeError):
                pass
        return None

    def _extract_info_metadata(
        self, html: etree._Element
    ) -> tuple[
        list[str], str | None, str | None, str | None, str | None, dict[str, str]
    ]:
        """Extract metadata from info section.

        Parameters
        ----------
        html : etree._Element
            Parsed HTML element.

        Returns
        -------
        tuple[list[str], str | None, str | None, str | None, str | None, dict[str, str]]
            Tuple of (authors, publisher, subtitle, published_date, series, identifiers).
        """
        authors: list[str] = []
        publisher: str | None = None
        subtitle: str | None = None
        published_date: str | None = None
        series: str | None = None
        identifiers: dict[str, str] = {}

        info_elements = html.xpath(self.INFO_XPATH)

        for element in info_elements:
            text = element.text
            if not text:
                continue

            if self.AUTHORS_PATTERN.search(text):
                authors.extend(self._extract_authors_from_element(element))
            elif self.PUBLISHER_PATTERN.search(text):
                publisher = self._extract_publisher_from_element(element)
            elif self.SUBTITLE_PATTERN.search(text):
                subtitle = self._extract_subtitle_from_element(element)
            elif self.PUBLISHED_DATE_PATTERN.search(text):
                published_date = self._extract_published_date_from_element(element)
            elif self.SERIES_PATTERN.search(text):
                series = self._extract_series_from_element(element)
            elif match := self.IDENTIFIERS_PATTERN.search(text):
                self._extract_identifier_from_element(element, match, identifiers)

        return authors, publisher, subtitle, published_date, series, identifiers

    def _extract_authors_from_element(self, element: etree._Element) -> list[str]:
        """Extract authors from element.

        Parameters
        ----------
        element : etree._Element
            Element containing author information.

        Returns
        -------
        list[str]
            List of author names.
        """
        authors = []
        next_element = element.getnext()
        while next_element is not None and next_element.tag != "br":
            if next_element.text:
                authors.append(next_element.text)
            next_element = next_element.getnext()
        return authors

    def _extract_publisher_from_element(self, element: etree._Element) -> str | None:
        """Extract publisher from element.

        Parameters
        ----------
        element : etree._Element
            Element containing publisher information.

        Returns
        -------
        str | None
            Publisher name, or None if not found.
        """
        publisher_text = element.tail.strip() if element.tail else ""
        if not publisher_text:
            next_element = element.getnext()
            if next_element is not None and next_element.text:
                publisher_text = next_element.text
        return publisher_text if publisher_text else None

    def _extract_subtitle_from_element(self, element: etree._Element) -> str | None:
        """Extract subtitle from element.

        Parameters
        ----------
        element : etree._Element
            Element containing subtitle information.

        Returns
        -------
        str | None
            Subtitle, or None if not found.
        """
        subtitle_text = element.tail.strip() if element.tail else ""
        return subtitle_text if subtitle_text else None

    def _extract_published_date_from_element(
        self, element: etree._Element
    ) -> str | None:
        """Extract published date from element.

        Parameters
        ----------
        element : etree._Element
            Element containing published date information.

        Returns
        -------
        str | None
            Published date string, or None if not found.
        """
        date_text = element.tail.strip() if element.tail else ""
        return _clean_date(date_text) if date_text else None

    def _extract_series_from_element(self, element: etree._Element) -> str | None:
        """Extract series from element.

        Parameters
        ----------
        element : etree._Element
            Element containing series information.

        Returns
        -------
        str | None
            Series name, or None if not found.
        """
        next_element = element.getnext()
        if next_element is not None and next_element.text:
            return next_element.text
        return None

    def _extract_identifier_from_element(
        self,
        element: etree._Element,
        match: re.Match[str],
        identifiers: dict[str, str],
    ) -> None:
        """Extract identifier from element and add to identifiers dict.

        Parameters
        ----------
        element : etree._Element
            Element containing identifier information.
        match : re.Match[str]
            Regex match object for identifier pattern.
        identifiers : dict[str, str]
            Dictionary to add identifier to.
        """
        id_type = match.group()
        id_value = element.tail.strip() if element.tail else ""
        if id_value:
            # Normalize identifier types
            if "ISBN" in id_type:
                identifiers["isbn"] = id_value
            else:
                identifiers[id_type] = id_value
