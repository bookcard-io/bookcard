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

"""LubimyCzytac.pl metadata provider.

This provider fetches book metadata by scraping LubimyCzytac.pl website.
LubimyCzytac.pl is a Polish book database and social reading platform.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import re
from contextlib import suppress
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from lxml.html import HtmlElement, fromstring, tostring

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

# Polish character translation map for accent stripping
SYMBOLS_TO_TRANSLATE = (
    "öÖüÜóÓőŐúÚéÉáÁűŰíÍąĄćĆęĘłŁńŃóÓśŚźŹżŻ",
    "oOuUoOoOuUeEaAuUiIaAcCeElLnNoOsSzZzZ",
)
SYMBOL_TRANSLATION_MAP = {
    ord(a): ord(b) for (a, b) in zip(*SYMBOLS_TO_TRANSLATE, strict=True)
}


def _get_int_or_float(value: str) -> int | float:
    """Convert string to int or float.

    Parameters
    ----------
    value : str
        String representation of a number.

    Returns
    -------
    int | float
        Integer if value is whole number, float otherwise.
    """
    number_as_float = float(value)
    number_as_int = int(number_as_float)
    return number_as_int if number_as_float == number_as_int else number_as_float


def _strip_accents(text: str | None) -> str | None:
    """Strip Polish accents from text.

    Parameters
    ----------
    text : str | None
        Text to process.

    Returns
    -------
    str | None
        Text with accents stripped, or None if input was None.
    """
    return text.translate(SYMBOL_TRANSLATION_MAP) if text is not None else text


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

    # Replace <u> tags with <span> to avoid emphasis issues
    html = re.sub(
        r"<\s*(?P<solidus>/?)\s*[uU]\b(?P<rest>[^>]*)>",
        r"<\g<solidus>span\g<rest>>",
        html,
    )

    # Use BeautifulSoup to extract text
    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and clean it up
    text = soup.get_text(separator=" ", strip=True)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _get_language_name(locale: str, lang_code: str) -> str:
    """Get language name for a given locale and language code.

    Parameters
    ----------
    locale : str
        Locale code (e.g., 'en', 'pl').
    lang_code : str
        ISO 639-3 language code (e.g., 'pol', 'eng').

    Returns
    -------
    str
        Language name in the specified locale.
    """
    # Simple mapping for common languages
    # In a full implementation, this would use a proper language database
    language_map = {
        "pol": {"en": "Polish", "pl": "Polski"},
        "eng": {"en": "English", "pl": "Angielski"},
    }

    lang_info = language_map.get(lang_code, {})
    return lang_info.get(locale, lang_info.get("en", lang_code))


class LubimyCzytacProvider(MetadataProvider):
    """Metadata provider for LubimyCzytac.pl.

    This provider scrapes LubimyCzytac.pl to search for books and
    retrieve metadata. It uses XPath queries to extract information
    from HTML pages.
    """

    BASE_URL = "https://lubimyczytac.pl"
    SOURCE_ID = "lubimyczytac"
    SOURCE_NAME = "LubimyCzytac.pl"
    SOURCE_DESCRIPTION = "LubimyCzytac.pl - Polish book database"
    REQUEST_TIMEOUT = 15  # seconds
    MAX_WORKERS = 10  # concurrent requests for detail pages

    # XPath expressions for parsing
    BOOK_SEARCH_RESULT_XPATH = (
        "*//div[@class='listSearch']//div[@class='authorAllBooks__single']"
    )
    SINGLE_BOOK_RESULT_XPATH = ".//div[contains(@class,'authorAllBooks__singleText')]"
    TITLE_PATH = "/div/a[contains(@class,'authorAllBooks__singleTextTitle')]"
    TITLE_TEXT_PATH = f"{TITLE_PATH}//text()"
    URL_PATH = f"{TITLE_PATH}/@href"
    AUTHORS_PATH = "/div/a[contains(@href,'autor')]//text()"

    SIBLINGS = "/following-sibling::dd"

    CONTAINER = "//section[@class='container book']"
    PUBLISHER = f"{CONTAINER}//dt[contains(text(),'Wydawnictwo:')]{SIBLINGS}/a/text()"
    LANGUAGES = f"{CONTAINER}//dt[contains(text(),'Język:')]{SIBLINGS}/text()"
    DESCRIPTION = f"{CONTAINER}//div[@class='collapse-content']"
    SERIES = f"{CONTAINER}//span/a[contains(@href,'/cykl/')]/text()"
    TRANSLATOR = f"{CONTAINER}//dt[contains(text(),'Tłumacz:')]{SIBLINGS}/a/text()"

    DETAILS = "//div[@id='book-details']"
    PUBLISH_DATE = "//dt[contains(@title,'Data pierwszego wydania"
    FIRST_PUBLISH_DATE = f"{DETAILS}{PUBLISH_DATE} oryginalnego')]{SIBLINGS}[1]/text()"
    FIRST_PUBLISH_DATE_PL = f"{DETAILS}{PUBLISH_DATE} polskiego')]{SIBLINGS}[1]/text()"
    TAGS = "//a[contains(@href,'/ksiazki/t/')]/text()"

    RATING = "//meta[@property='books:rating:value']/@content"
    COVER = "//meta[@property='og:image']/@content"
    ISBN = "//meta[@property='books:isbn']/@content"
    META_TITLE = "//meta[@property='og:description']/@content"

    SUMMARY = "//script[@type='application/ld+json']//text()"

    # Headers to mimic a browser request
    HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pl,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }

    def __init__(self, enabled: bool = True, timeout: int = REQUEST_TIMEOUT) -> None:
        """Initialize LubimyCzytac provider.

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
        """Get information about LubimyCzytac source.

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
        locale: str = "en",
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for books on LubimyCzytac.pl.

        Parameters
        ----------
        query : str
            Search query (title, author, ISBN, etc.).
        locale : str
            Locale code (default: 'en').
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
            search_url = self._prepare_query(query)
            if not search_url:
                return []

            # Fetch search results page
            with httpx.Client(
                headers=self.HEADERS, timeout=self.timeout, follow_redirects=True
            ) as client:
                response = client.get(search_url)
                response.raise_for_status()

                # Parse search results
                root = fromstring(response.text)
                search_results = self._parse_search_results(root)

                if not search_results:
                    return []

                # Limit to max_results
                search_results = search_results[:max_results]

                # Fetch detail pages concurrently
                records = self._fetch_book_details(search_results, client, locale)

        except httpx.TimeoutException as e:
            msg = f"LubimyCzytac search request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except (
            httpx.HTTPStatusError,
            httpx.HTTPError,
            httpx.RequestError,
        ) as e:
            msg = f"LubimyCzytac search request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (ValueError, TypeError, AttributeError) as e:
            msg = f"Failed to parse LubimyCzytac search results: {e}"
            raise MetadataProviderParseError(msg) from e
        else:
            return records

    def _prepare_query(self, title: str) -> str:
        """Prepare search query URL.

        Parameters
        ----------
        title : str
            Book title or search query.

        Returns
        -------
        str
            Search URL, or empty string if query is invalid.
        """
        query = ""
        characters_to_remove = r"\?()\/"
        pattern = "[" + characters_to_remove + "]"
        title = re.sub(pattern, "", title)
        title = title.replace("_", " ")

        if '"' in title or ",," in title:
            title = title.split('"')[0].split(",,")[0]

        if "/" in title:
            title_tokens = [
                token for token in title.lower().split(" ") if len(token) > 1
            ]
        else:
            # Simple tokenization - split on whitespace
            title_tokens = [t for t in title.split() if len(t) > 1]

        if title_tokens:
            tokens = [quote(t.encode("utf-8")) for t in title_tokens]
            query = "%20".join(tokens)

        if not query:
            return ""

        return f"{self.BASE_URL}/szukaj/ksiazki?phrase={query}"

    def _parse_search_results(self, root: HtmlElement) -> list[dict[str, str]]:
        """Parse search results from HTML.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        list[dict[str, str]]
            List of search result dictionaries with title, url, authors, and id.
        """
        results = []
        book_elements = root.xpath(self.BOOK_SEARCH_RESULT_XPATH)

        for book_elem in book_elements:
            title = self._parse_xpath_node(
                root=book_elem,
                xpath=f"{self.SINGLE_BOOK_RESULT_XPATH}{self.TITLE_TEXT_PATH}",
            )

            book_url = self._parse_xpath_node(
                root=book_elem,
                xpath=f"{self.SINGLE_BOOK_RESULT_XPATH}{self.URL_PATH}",
            )

            authors = self._parse_xpath_node(
                root=book_elem,
                xpath=f"{self.SINGLE_BOOK_RESULT_XPATH}{self.AUTHORS_PATH}",
                take_first=False,
            )

            if not all([title, book_url, authors]):
                continue

            # Ensure book_url is a string
            if not isinstance(book_url, str):
                continue

            # Extract book ID from URL
            book_id = book_url.replace("/ksiazka/", "").split("/")[0]

            results.append({
                "id": book_id,
                "title": title,
                "url": self.BASE_URL + book_url,
                "authors": authors,
            })

        return results

    def _fetch_book_details(
        self,
        search_results: list[dict[str, str]],
        client: httpx.Client,
        locale: str,
    ) -> list[MetadataRecord]:
        """Fetch book details from multiple detail pages concurrently.

        Parameters
        ----------
        search_results : list[dict[str, str]]
            List of search result dictionaries.
        client : httpx.Client
            HTTP client for making requests.
        locale : str
            Locale code for language names.

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
                executor.submit(self._fetch_single_book_detail, result, client, locale)
                for result in search_results
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
                        "Unexpected error in LubimyCzytac detail fetch future: %s",
                        e,
                        exc_info=True,
                    )

        return records

    def _fetch_single_book_detail(
        self,
        search_result: dict[str, str],
        client: httpx.Client,
        locale: str,
    ) -> MetadataRecord | None:
        """Fetch and parse a single book detail page.

        Parameters
        ----------
        search_result : dict[str, str]
            Search result dictionary with id, title, url, and authors.
        client : httpx.Client
            HTTP client for making requests.
        locale : str
            Locale code for language names.

        Returns
        -------
        MetadataRecord | None
            Parsed metadata record, or None if parsing fails.
        """
        try:
            response = client.get(search_result["url"], headers=self.HEADERS)
            response.raise_for_status()

            root = fromstring(response.text)

            # Parse all metadata fields
            cover_url = self._parse_cover(root)
            description = self._parse_description(root)
            languages = self._parse_languages(root, locale)
            publisher = self._parse_publisher(root)
            published_date = self._parse_published_date(root)
            rating = self._parse_rating(root)
            series, series_index = self._parse_series(root)
            tags = self._parse_tags(root)
            isbn = self._parse_isbn(root)

            identifiers: dict[str, str] = {}
            if isbn:
                identifiers["isbn"] = isbn
            identifiers["lubimyczytac"] = search_result["id"]

            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=search_result["id"],
                title=search_result["title"],
                authors=[
                    _strip_accents(author) or author
                    for author in search_result["authors"]
                ],
                url=search_result["url"],
                cover_url=cover_url,
                description=description,
                series=series,
                series_index=series_index,
                identifiers=identifiers,
                publisher=publisher,
                published_date=published_date,
                rating=rating,
                languages=languages,
                tags=tags,
            )

        except (
            httpx.HTTPStatusError,
            httpx.HTTPError,
            httpx.RequestError,
            AttributeError,
            ValueError,
            TypeError,
        ) as e:
            logger.debug(
                "Failed to fetch LubimyCzytac book detail page: %s",
                e,
            )
            return None

    def _parse_xpath_node(
        self,
        xpath: str,
        root: HtmlElement | None = None,
        take_first: bool = True,
        strip_element: bool = True,
    ) -> str | list[str] | None:
        """Parse XPath node and extract text.

        Parameters
        ----------
        xpath : str
            XPath expression.
        root : HtmlElement | None
            Root element to search from. If None, uses self.root.
        take_first : bool
            If True, return first match as string. If False, return all matches as list.
        strip_element : bool
            Whether to strip whitespace from results.

        Returns
        -------
        str | list[str] | None
            Extracted text or list of texts, or None if not found.
        """
        if root is None:
            return None

        nodes = root.xpath(xpath)
        if not nodes:
            return None

        if take_first:
            result = nodes[0]
            if isinstance(result, str):
                return result.strip() if strip_element else result
            # If it's an element, get its text
            if hasattr(result, "text") and result.text:
                return result.text.strip() if strip_element else result.text
            # If it's an attribute value, it should already be a string
            return str(result).strip() if strip_element else str(result)

        # Return all matches
        results = []
        for node in nodes:
            if isinstance(node, str):
                results.append(node.strip() if strip_element else node)
            elif hasattr(node, "text") and node.text:
                results.append(node.text.strip() if strip_element else node.text)
            else:
                results.append(str(node).strip() if strip_element else str(node))

        return results

    def _parse_cover(self, root: HtmlElement) -> str | None:
        """Extract cover image URL.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str | None
            Cover image URL, or None if not found.
        """
        result = self._parse_xpath_node(xpath=self.COVER, root=root, take_first=True)
        return result if isinstance(result, str) else None

    def _parse_publisher(self, root: HtmlElement) -> str | None:
        """Extract publisher name.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str | None
            Publisher name, or None if not found.
        """
        result = self._parse_xpath_node(
            xpath=self.PUBLISHER, root=root, take_first=True
        )
        return result if isinstance(result, str) else None

    def _parse_languages(self, root: HtmlElement, locale: str) -> list[str]:
        """Extract language information.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.
        locale : str
            Locale code for language names.

        Returns
        -------
        list[str]
            List of language names.
        """
        languages = []
        lang_text = self._parse_xpath_node(
            xpath=self.LANGUAGES, root=root, take_first=True
        )

        if lang_text and isinstance(lang_text, str):
            if "polski" in lang_text.lower():
                languages.append("pol")
            if "angielski" in lang_text.lower():
                languages.append("eng")

        return [_get_language_name(locale, lang) for lang in languages]

    def _parse_series(self, root: HtmlElement) -> tuple[str | None, float | None]:
        """Extract series information.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        tuple[str | None, float | None]
            Tuple of (series name, series index).
        """
        series_text = self._parse_xpath_node(
            xpath=self.SERIES, root=root, take_first=True
        )

        if (
            series_text
            and isinstance(series_text, str)
            and "tom " in series_text.lower()
        ):
            parts = series_text.split(" (tom ", 1)
            if len(parts) == 2:
                series_name = parts[0]
                series_info = parts[1].replace(" ", "").replace(")", "")

                # Check if book is not a bundle (e.g., "1-3")
                if "-" in series_info:
                    series_info = series_info.split("-", 1)[0]

                if series_info.replace(".", "").isdigit():
                    series_index = _get_int_or_float(series_info)
                    return series_name, float(series_index)

        return None, None

    def _parse_tags(self, root: HtmlElement) -> list[str]:
        """Extract tags/categories.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        list[str]
            List of tags.
        """
        tags = self._parse_xpath_node(xpath=self.TAGS, root=root, take_first=False)

        if tags and isinstance(tags, list):
            return [
                _strip_accents(tag.replace(", itd.", " itd.")) or tag
                for tag in tags
                if isinstance(tag, str)
            ]

        return []

    def _parse_published_date(self, root: HtmlElement) -> str | None:
        """Extract published date from JSON-LD summary.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str | None
            Published date string, or None if not found.
        """
        return self._parse_from_summary(root, "datePublished")

    def _parse_from_summary(self, root: HtmlElement, attribute_name: str) -> str | None:
        """Extract value from JSON-LD summary script.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.
        attribute_name : str
            Attribute name to extract from JSON-LD.

        Returns
        -------
        str | None
            Extracted value, or None if not found.
        """
        summary_text = self._parse_xpath_node(
            xpath=self.SUMMARY, root=root, take_first=True
        )

        if summary_text and isinstance(summary_text, str):
            with suppress(json.JSONDecodeError, KeyError, AttributeError):
                data = json.loads(summary_text)
                value = data.get(attribute_name)
                if value is not None:
                    return str(value).strip()

        return None

    def _parse_rating(self, root: HtmlElement) -> float | None:
        """Extract book rating.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        float | None
            Rating value (0-5), or None if not found.
        """
        rating_text = self._parse_xpath_node(
            xpath=self.RATING, root=root, take_first=True
        )

        if rating_text and isinstance(rating_text, str):
            with suppress(ValueError):
                # Rating is on 0-10 scale, convert to 0-5
                rating = float(rating_text.replace(",", "."))
                return round(rating / 2)

        return None

    def _parse_isbn(self, root: HtmlElement) -> str | None:
        """Extract ISBN.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str | None
            ISBN, or None if not found.
        """
        result = self._parse_xpath_node(xpath=self.ISBN, root=root, take_first=True)
        return result if isinstance(result, str) else None

    def _parse_description(self, root: HtmlElement) -> str:
        """Extract and format book description.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str
            Formatted description with additional metadata.
        """
        description = ""

        # Try to get description from collapse-content div
        description_node = self._parse_xpath_node(
            xpath=self.DESCRIPTION, root=root, take_first=True, strip_element=False
        )

        if description_node is not None:
            # If it's an element, convert to HTML string
            if hasattr(description_node, "tag"):
                # Remove source attribution paragraphs
                for source_elem in root.xpath('//p[@class="source"]'):
                    parent = source_elem.getparent()
                    if parent is not None:
                        parent.remove(source_elem)

                description_html = tostring(
                    description_node, method="html", encoding="unicode"
                )
                description = _sanitize_html_to_text(description_html)
            elif isinstance(description_node, str):
                description = _sanitize_html_to_text(description_node)
        else:
            # Fallback to meta description
            meta_description = self._parse_xpath_node(
                xpath=self.META_TITLE, root=root, take_first=True
            )
            if meta_description and isinstance(meta_description, str):
                description = _sanitize_html_to_text(meta_description)

        # Add extra information to description
        return self._add_extra_info_to_description(root, description)

    def _add_extra_info_to_description(
        self, root: HtmlElement, description: str
    ) -> str:
        """Add extra metadata to description (pages, dates, translator).

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.
        description : str
            Base description text.

        Returns
        -------
        str
            Description with additional metadata appended.
        """
        # Add pages information
        pages = self._parse_from_summary(root, "numberOfPages")
        if pages:
            description += f"\n\nKsiążka ma {pages} stron(y)."

        # Add first publish date
        first_publish_date = self._parse_first_publish_date(root)
        if first_publish_date:
            description += f"\n\nData pierwszego wydania: {first_publish_date}"

        # Add first publish date in Poland
        first_publish_date_pl = self._parse_first_publish_date_pl(root)
        if first_publish_date_pl:
            description += (
                f"\n\nData pierwszego wydania w Polsce: {first_publish_date_pl}"
            )

        # Add translator
        translator = self._parse_translator(root)
        if translator:
            description += f"\n\nTłumacz: {translator}"

        return description

    def _parse_first_publish_date(self, root: HtmlElement) -> str | None:
        """Extract first publish date.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str | None
            First publish date string, or None if not found.
        """
        result = self._parse_xpath_node(
            xpath=self.FIRST_PUBLISH_DATE, root=root, take_first=True
        )
        return result if isinstance(result, str) else None

    def _parse_first_publish_date_pl(self, root: HtmlElement) -> str | None:
        """Extract first publish date in Poland.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str | None
            First publish date in Poland string, or None if not found.
        """
        result = self._parse_xpath_node(
            xpath=self.FIRST_PUBLISH_DATE_PL, root=root, take_first=True
        )
        return result if isinstance(result, str) else None

    def _parse_translator(self, root: HtmlElement) -> str | None:
        """Extract translator name.

        Parameters
        ----------
        root : HtmlElement
            Parsed HTML root element.

        Returns
        -------
        str | None
            Translator name, or None if not found.
        """
        result = self._parse_xpath_node(
            xpath=self.TRANSLATOR, root=root, take_first=True
        )
        return result if isinstance(result, str) else None
