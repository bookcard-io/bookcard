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

"""Deutsche Nationalbibliothek (DNB) metadata provider.

This provider fetches book metadata from the German National Library
using the SRU (Search/Retrieve via URL) API with MARC21-XML format.
Documentation: https://www.dnb.de/EN/Professionell/Standardisierung/SRU/sru_node.html
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import quote

import httpx
from lxml import etree  # type: ignore[attr-defined]

from bookcard.metadata.base import (
    MetadataProvider,
    MetadataProviderNetworkError,
    MetadataProviderParseError,
    MetadataProviderTimeoutError,
)
from bookcard.metadata.providers.dnb._cover_validator import CoverValidator
from bookcard.metadata.providers.dnb._marc21_parser import MARC21Parser
from bookcard.metadata.providers.dnb._query_builder import SRUQueryBuilder
from bookcard.metadata.providers.dnb._text_cleaner import TextCleaner
from bookcard.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class DNBProvider(MetadataProvider):
    """Metadata provider for Deutsche Nationalbibliothek (DNB).

    This provider uses the DNB SRU API to search for books and retrieve
    metadata in MARC21-XML format. It handles German-specific text processing
    and series extraction.

    Attributes
    ----------
    SOURCE_ID : str
        Provider identifier.
    SOURCE_NAME : str
        Human-readable provider name.
    SOURCE_DESCRIPTION : str
        Provider description.
    API_BASE_URL : str
        Base URL for DNB portal.
    SRU_ENDPOINT : str
        SRU API endpoint URL.
    COVER_BASE_URL : str
        Base URL for cover images.
    REQUEST_TIMEOUT : int
        Request timeout in seconds.
    MAX_RESULTS : int
        Maximum number of results per query.
    """

    SOURCE_ID = "dnb"
    SOURCE_NAME = "Deutsche Nationalbibliothek"
    SOURCE_DESCRIPTION = "German National Library (DNB) SRU API"
    API_BASE_URL = "https://portal.dnb.de"
    SRU_ENDPOINT = "https://services.dnb.de/sru/dnb"
    COVER_BASE_URL = "https://portal.dnb.de/opac/mvb/cover"
    REQUEST_TIMEOUT = 15
    MAX_RESULTS = 10

    # SRU namespaces
    SRU_NS: ClassVar[dict[str, str]] = {
        "zs": "http://www.loc.gov/zing/srw/",
        "marc21": "http://www.loc.gov/MARC21/slim",
    }

    # HTTP headers for SRU requests
    HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "Accept": "application/xml, text/xml",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(
        self,
        enabled: bool = True,
        timeout: int = REQUEST_TIMEOUT,
        max_results: int = MAX_RESULTS,
    ) -> None:
        """Initialize DNB provider.

        Parameters
        ----------
        enabled : bool
            Whether this provider is enabled.
        timeout : int
            Request timeout in seconds.
        max_results : int
            Maximum number of results per query.
        """
        super().__init__(enabled)
        self.timeout = timeout
        self.max_results = max_results
        self._query_builder = SRUQueryBuilder()
        self._parser = MARC21Parser()
        self._text_cleaner = TextCleaner()
        self._cover_validator = CoverValidator(timeout=timeout)

    def get_source_info(self) -> MetadataSourceInfo:
        """Get information about DNB source.

        Returns
        -------
        MetadataSourceInfo
            Source information including ID, name, description, and base URL.
        """
        return MetadataSourceInfo(
            id=self.SOURCE_ID,
            name=self.SOURCE_NAME,
            description=self.SOURCE_DESCRIPTION,
            base_url=self.API_BASE_URL,
        )

    def search(
        self,
        query: str,
        locale: str = "en",  # noqa: ARG002
        max_results: int = 10,
    ) -> Sequence[MetadataRecord]:
        """Search for books using DNB SRU API.

        Parameters
        ----------
        query : str
            Search query. Can be:
            - Plain text (title/author search)
            - "dnb-idn:XXXXX" (DNB IDN identifier)
            - "isbn:XXXXXXXXXX" (ISBN identifier)
        locale : str
            Locale code (default: 'en'). Currently unused but reserved
            for future locale filtering.
        max_results : int
            Maximum number of results to return (default: 10).

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
            # Parse query for special identifiers
            query_params = self._parse_query(query)
            # Build query variations
            query_strings = self._query_builder.build_queries(**query_params)

            records = self._execute_queries_and_parse(query_strings)
            return records[:max_results]

        except httpx.TimeoutException as e:
            msg = f"DNB SRU API request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"DNB SRU API request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (etree.XMLSyntaxError, etree.ParseError) as e:
            msg = f"Failed to parse DNB SRU XML response: {e}"
            raise MetadataProviderParseError(msg) from e
        except (KeyError, ValueError, TypeError, AttributeError):
            logger.exception("DNB search failed for query '%s'", query)
            return []

    def _parse_query(self, query: str) -> dict[str, str | None]:
        """Parse query string for special identifiers.

        Parameters
        ----------
        query : str
            Raw query string.

        Returns
        -------
        dict[str, str | None]
            Dictionary with 'idn', 'isbn', and 'title' keys.
        """
        query = query.strip()
        result: dict[str, str | None] = {
            "idn": None,
            "isbn": None,
            "title": None,
        }

        if query.startswith("dnb-idn:"):
            result["idn"] = query.replace("dnb-idn:", "").strip()
        elif query.startswith("isbn:"):
            result["isbn"] = query.replace("isbn:", "").strip()
        else:
            result["title"] = query

        return result

    def _execute_sru_query(self, query: str) -> list[etree._Element]:
        """Execute SRU query and return MARC21 records.

        Parameters
        ----------
        query : str
            SRU query string.

        Returns
        -------
        list[etree._Element]
            List of MARC21 record elements.

        Raises
        ------
        MetadataProviderNetworkError
            If network request fails.
        MetadataProviderTimeoutError
            If request times out.
        MetadataProviderParseError
            If response cannot be parsed.
        """
        params = {
            "version": "1.1",
            "maximumRecords": str(self.max_results),
            "operation": "searchRetrieve",
            "recordSchema": "MARC21-xml",
            "query": query,
        }

        query_url = f"{self.SRU_ENDPOINT}?{self._build_query_string(params)}"
        logger.debug("DNB Query URL: %s", query_url)

        try:
            response = httpx.get(
                self.SRU_ENDPOINT,
                params=params,
                headers=self.HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()

            xml_data = etree.XML(response.content)
            num_records_elem = xml_data.xpath(
                "./zs:numberOfRecords",
                namespaces=self.SRU_NS,
            )
            if num_records_elem:
                num_records = int(num_records_elem[0].text.strip())
                logger.debug("DNB found %d records", num_records)
                if num_records == 0:
                    return []

            return xml_data.xpath(
                "./zs:records/zs:record/zs:recordData/marc21:record",
                namespaces=self.SRU_NS,
            )

        except httpx.TimeoutException as e:
            msg = f"DNB SRU API request timed out: {e}"
            raise MetadataProviderTimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"DNB SRU API request failed: {e}"
            raise MetadataProviderNetworkError(msg) from e
        except (etree.XMLSyntaxError, etree.ParseError, IndexError, ValueError) as e:
            msg = f"Failed to parse DNB SRU XML response: {e}"
            raise MetadataProviderParseError(msg) from e

    def _execute_queries_and_parse(
        self, query_strings: list[str]
    ) -> list[MetadataRecord]:
        """Execute SRU queries and parse results.

        Parameters
        ----------
        query_strings : list[str]
            List of SRU query strings to try.

        Returns
        -------
        list[MetadataRecord]
            List of parsed metadata records.
        """
        records = []
        for query_str in query_strings:
            try:
                marc21_records = self._execute_sru_query(query_str)
                if not marc21_records:
                    continue

                parsed_records = self._parse_marc21_records(marc21_records)
                records.extend(parsed_records)

                # Stop on first successful query
                if records:
                    break

            except (
                MetadataProviderNetworkError,
                MetadataProviderTimeoutError,
                MetadataProviderParseError,
            ):
                # Re-raise provider-specific errors
                raise
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                logger.warning("DNB search error for query '%s': %s", query_str, e)
                continue

        return records

    def _parse_marc21_records(
        self,
        marc21_records: list[etree._Element],
    ) -> list[MetadataRecord]:
        """Parse MARC21 records into metadata records.

        Parameters
        ----------
        marc21_records : list[etree._Element]
            List of MARC21 record elements.

        Returns
        -------
        list[MetadataRecord]
            List of parsed metadata records.
        """
        records = []
        for marc21_record in marc21_records:
            book_data = self._parser.parse(marc21_record)
            if book_data and self._is_valid_book(book_data):
                meta_record = self._create_metadata_record(book_data)
                if meta_record:
                    records.append(meta_record)
        return records

    def _build_query_string(self, params: dict[str, str]) -> str:
        """Build URL query string from parameters.

        Parameters
        ----------
        params : dict[str, str]
            Query parameters.

        Returns
        -------
        str
            URL-encoded query string.
        """
        return "&".join(f"{k}={quote(str(v))}" for k, v in params.items())

    def _is_valid_book(self, book_data: dict) -> bool:
        """Check if book data represents a valid book record.

        Parameters
        ----------
        book_data : dict
            Parsed book data dictionary.

        Returns
        -------
        bool
            True if record is valid, False otherwise.
        """
        # Require at least title and authors
        return bool(book_data.get("title") and book_data.get("authors"))

    def _create_metadata_record(self, book_data: dict) -> MetadataRecord | None:
        """Create MetadataRecord from parsed book data.

        Parameters
        ----------
        book_data : dict
            Parsed book data dictionary.

        Returns
        -------
        MetadataRecord | None
            Metadata record or None if creation fails.
        """
        try:
            # Clean title and authors
            title = self._text_cleaner.clean_title(book_data.get("title", ""))
            authors = [
                self._text_cleaner.clean_author_name(author)
                for author in book_data.get("authors", [])
            ]

            if not title or not authors:
                return None

            # Build record components
            identifiers = self._build_identifiers(book_data)
            publisher = self._build_publisher(book_data)
            published_date = self._format_published_date(book_data.get("pubdate"))
            cover_url = self._cover_validator.get_cover_url(book_data.get("isbn"))
            url = self._build_record_url(book_data.get("idn", ""))

            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=book_data.get("idn", ""),
                title=title,
                authors=authors,
                url=url,
                cover_url=cover_url,
                description=book_data.get("comments"),
                series=self._text_cleaner.clean_series(
                    book_data.get("series"),
                    book_data.get("publisher_name"),
                ),
                series_index=(
                    float(book_data["series_index"])
                    if book_data.get("series_index")
                    else None
                ),
                identifiers=identifiers,
                publisher=publisher,
                published_date=published_date,
                rating=None,
                languages=book_data.get("languages", []),
                tags=book_data.get("tags", []),
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("Failed to create DNB metadata record: %s", e)
            return None

    def _build_identifiers(self, book_data: dict) -> dict[str, str]:
        """Build identifiers dictionary from book data.

        Parameters
        ----------
        book_data : dict
            Parsed book data dictionary.

        Returns
        -------
        dict[str, str]
            Dictionary of identifiers.
        """
        identifiers: dict[str, str] = {}
        if book_data.get("idn"):
            identifiers["dnb-idn"] = book_data["idn"]
        if book_data.get("isbn"):
            identifiers["isbn"] = book_data["isbn"]
        if book_data.get("urn"):
            identifiers["urn"] = book_data["urn"]
        return identifiers

    def _build_publisher(self, book_data: dict) -> str | None:
        """Build publisher string from book data.

        Parameters
        ----------
        book_data : dict
            Parsed book data dictionary.

        Returns
        -------
        str | None
            Publisher string, or None if not available.
        """
        publisher_parts = []
        if book_data.get("publisher_location"):
            publisher_parts.append(book_data["publisher_location"])
        if book_data.get("publisher_name"):
            publisher_parts.append(
                self._text_cleaner.remove_sorting_characters(
                    book_data["publisher_name"],
                ),
            )
        return " ; ".join(publisher_parts) if publisher_parts else None

    def _format_published_date(
        self, pubdate: datetime.datetime | str | None
    ) -> str | None:
        """Format publication date to string.

        Parameters
        ----------
        pubdate : datetime.datetime | str | None
            Publication date.

        Returns
        -------
        str | None
            Formatted date string, or None if not available.
        """
        if not pubdate:
            return None
        if isinstance(pubdate, datetime.datetime):
            return pubdate.strftime("%Y-%m-%d")
        if isinstance(pubdate, str):
            return pubdate
        return None

    def _build_record_url(self, idn: str) -> str:
        """Build record URL from IDN.

        Parameters
        ----------
        idn : str
            DNB IDN identifier.

        Returns
        -------
        str
            Record URL.
        """
        return f"{self.API_BASE_URL}/opac.htm?method=simpleSearch&query={idn}"
