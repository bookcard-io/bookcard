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

"""Hardcover data source implementation."""

import logging
import os
from collections.abc import Sequence
from typing import Any

import httpx

from fundamental.metadata.base import (
    MetadataProviderNetworkError,
    MetadataProviderParseError,
)
from fundamental.metadata.providers._hardcover.client import (
    HardcoverGraphQLClient,
    HttpClient,
)
from fundamental.metadata.providers._hardcover.enrichment import HardcoverEnrichment
from fundamental.metadata.providers._hardcover.extractors import (
    AuthorsExtractor,
    CoverExtractor,
    IdentifiersExtractor,
    PublishedDateExtractor,
    PublisherExtractor,
    TagsExtractor,
)
from fundamental.metadata.providers._hardcover.parser import (
    HardcoverResponseParser,
)
from fundamental.metadata.providers._hardcover.queries import (
    AUTHOR_BY_ID_OPERATION_NAME,
    AUTHOR_BY_ID_QUERY,
    AUTHOR_SEARCH_OPERATION_NAME,
    AUTHOR_SEARCH_QUERY,
    EDITION_OPERATION_NAME,
    EDITION_QUERY,
    SEARCH_OPERATION_NAME,
    SEARCH_QUERY,
)
from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNetworkError,
)
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
    IdentifierDict,
)

logger = logging.getLogger(__name__)

# Hardcover API base URL
HARDCOVER_API_BASE = "https://api.hardcover.app/v1"
HARDCOVER_GRAPHQL_ENDPOINT = f"{HARDCOVER_API_BASE}/graphql"

# Error messages
_SEARCH_AUTHORS_ERROR_MSG = "Error searching authors: {error}"
_FETCH_AUTHOR_ERROR_MSG = "Error fetching author: {error}"
_SEARCH_BOOKS_ERROR_MSG = "Error searching books: {error}"
_FETCH_BOOK_ERROR_MSG = "Error fetching book: {error}"


class HardcoverDataSource(BaseDataSource):
    """Hardcover data source implementation.

    Fetches author and book metadata from the Hardcover GraphQL API.
    """

    def __init__(
        self,
        base_url: str = HARDCOVER_GRAPHQL_ENDPOINT,
        timeout: float = 10.0,
        bearer_token: str | None = None,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize Hardcover data source.

        Parameters
        ----------
        base_url : str
            GraphQL endpoint URL (default: production API).
        timeout : float
            Request timeout in seconds (default: 10.0).
        bearer_token : str | None
            API bearer token. If None, uses token from
            HARDCOVER_API_TOKEN environment variable.
        http_client : HttpClient | None
            HTTP client to use. If None, uses httpx directly.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.bearer_token = bearer_token or os.getenv("HARDCOVER_API_TOKEN", "").strip()

        if not self.bearer_token:
            logger.warning(
                "Hardcover data source initialized without bearer token. "
                "Set HARDCOVER_API_TOKEN environment variable."
            )

        # Initialize components
        self._client = HardcoverGraphQLClient(
            endpoint=self.base_url,
            bearer_token=self.bearer_token,
            timeout=int(self.timeout),
            http_client=http_client,
        )
        self._parser = HardcoverResponseParser()
        self._enrichment = HardcoverEnrichment()

        # Initialize extractors
        self._authors_extractor = AuthorsExtractor()
        self._cover_extractor = CoverExtractor()
        self._identifiers_extractor = IdentifiersExtractor()
        self._published_date_extractor = PublishedDateExtractor()
        self._publisher_extractor = PublisherExtractor()
        self._tags_extractor = TagsExtractor()

    @property
    def name(self) -> str:
        """Get the name of this data source.

        Returns
        -------
        str
            Data source name.
        """
        return "Hardcover"

    def search_author(
        self,
        name: str,
        identifiers: IdentifierDict | None = None,  # noqa: ARG002
    ) -> Sequence[AuthorData]:
        """Search for authors by name and optional identifiers.

        Parameters
        ----------
        name : str
            Author name to search for.
        identifiers : IdentifierDict | None
            Optional external identifiers (currently unused).

        Returns
        -------
        Sequence[AuthorData]
            Sequence of matching author data.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        """
        if not self.bearer_token:
            logger.warning("Hardcover API bearer token not set, cannot search authors")
            return []

        if not name or not name.strip():
            return []

        try:
            # Search authors using search endpoint (same format as book search)
            search_query = name.strip()
            data = self._client.execute_query(
                query=AUTHOR_SEARCH_QUERY,
                variables={"query": search_query},
                operation_name=AUTHOR_SEARCH_OPERATION_NAME,
            )

            # Parse search results (same format as book search)
            results_data = self._parser.extract_search_data(data)
            authors_data = self._parser.parse_search_results(results_data)

            if not authors_data:
                return []

            # Map to AuthorData objects
            results: list[AuthorData] = []
            for author_data in authors_data:
                author_obj = self._map_to_author_data(author_data)
                if author_obj:
                    results.append(author_obj)
        except MetadataProviderNetworkError as e:
            msg = f"Hardcover API request failed: {e}"
            raise DataSourceNetworkError(msg) from e
        except MetadataProviderParseError as e:
            error_msg = _SEARCH_AUTHORS_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        except (KeyError, ValueError, TypeError) as e:
            logger.exception("Error parsing Hardcover API response")
            error_msg = _SEARCH_AUTHORS_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        else:
            return results

    def get_author(self, key: str) -> AuthorData | None:
        """Get full author details by key.

        Parameters
        ----------
        key : str
            Author key/identifier (Hardcover author ID).

        Returns
        -------
        AuthorData | None
            Full author data if found, None otherwise.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        """
        if not self.bearer_token:
            logger.warning("Hardcover API bearer token not set, cannot fetch author")
            return None

        try:
            # Convert key to integer (Hardcover uses integer IDs)
            try:
                author_id = int(key)
            except ValueError:
                logger.warning("Invalid Hardcover author ID: %s", key)
                return None

            # Fetch author details
            data = self._client.execute_query(
                query=AUTHOR_BY_ID_QUERY,
                variables={"authorId": author_id},
                operation_name=AUTHOR_BY_ID_OPERATION_NAME,
            )

            # Extract author from response
            authors_data = data.get("data", {}).get("authors", [])
            if not isinstance(authors_data, list) or not authors_data:
                return None

            author_data = authors_data[0]
            return self._map_to_author_data(author_data)

        except MetadataProviderNetworkError as e:
            msg = f"Hardcover API request failed: {e}"
            raise DataSourceNetworkError(msg) from e
        except MetadataProviderParseError as e:
            error_msg = _FETCH_AUTHOR_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        except (KeyError, ValueError, TypeError) as e:
            logger.exception("Error parsing Hardcover API response")
            error_msg = _FETCH_AUTHOR_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e

    def search_book(
        self,
        title: str | None = None,
        isbn: str | None = None,
        authors: Sequence[str] | None = None,
    ) -> Sequence[BookData]:
        """Search for books by title, ISBN, or authors.

        Parameters
        ----------
        title : str | None
            Book title to search for.
        isbn : str | None
            ISBN identifier.
        authors : Sequence[str] | None
            Author names.

        Returns
        -------
        Sequence[BookData]
            Sequence of matching book data.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        """
        if not self.bearer_token:
            logger.warning("Hardcover API bearer token not set, cannot search books")
            return []

        # Build search query
        query_parts = []
        if title:
            query_parts.append(title)
        if isbn:
            query_parts.append(isbn)
        if authors:
            query_parts.extend(authors)

        if not query_parts:
            return []

        search_query = " ".join(query_parts)

        try:
            # Execute search query
            data = self._client.execute_query(
                query=SEARCH_QUERY,
                variables={"query": search_query},
                operation_name=SEARCH_OPERATION_NAME,
            )

            # Parse search results
            results_data = self._parser.extract_search_data(data)
            books_data = self._parser.parse_search_results(results_data)

            if not books_data:
                return []

            # Enrich with edition details
            enriched_books_data = self._enrich_books_with_editions(books_data)

            # Map to BookData objects
            return self._map_books_to_book_data(enriched_books_data)

        except MetadataProviderNetworkError as e:
            # Convert metadata provider network errors to data source errors
            msg = f"Hardcover API request failed: {e}"
            raise DataSourceNetworkError(msg) from e
        except MetadataProviderParseError as e:
            # Convert metadata provider parse errors to data source errors
            error_msg = _SEARCH_BOOKS_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        except (KeyError, ValueError, TypeError) as e:
            logger.exception("Error parsing Hardcover API response")
            error_msg = _SEARCH_BOOKS_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e

    def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:  # noqa: ARG002
        """Get full book details by key.

        Parameters
        ----------
        key : str
            Book key/identifier (Hardcover book ID).
        skip_authors : bool
            If True, skip fetching author data (unused, authors are always included).

        Returns
        -------
        BookData | None
            Full book data if found, None otherwise.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        DataSourceNotFoundError
            If book is not found.
        """
        if not self.bearer_token:
            logger.warning("Hardcover API bearer token not set, cannot fetch book")
            return None

        try:
            # Convert key to integer (Hardcover uses integer IDs)
            try:
                book_id = int(key)
            except ValueError:
                logger.warning("Invalid Hardcover book ID: %s", key)
                return None

            # Fetch edition details
            data = self._client.execute_query(
                query=EDITION_QUERY,
                variables={"bookId": book_id},
                operation_name=EDITION_OPERATION_NAME,
            )

            # Debug: Check if books array is empty
            books = data.get("data", {}).get("books", [])
            if not books:
                logger.debug(
                    "No books found for book ID %s. API response: %s",
                    book_id,
                    data.get("data", {}),
                )
                return None

            edition_data = self._parser.extract_edition_data(data)
            if edition_data:
                # Map to BookData
                return self._map_to_book_data(edition_data)
        except MetadataProviderNetworkError as e:
            # Convert metadata provider network errors to data source errors
            # Note: The client doesn't preserve status codes, so we can't distinguish
            # rate limits or not found errors. All network errors are treated as
            # DataSourceNetworkError.
            msg = f"Hardcover API request failed: {e}"
            raise DataSourceNetworkError(msg) from e
        except MetadataProviderParseError as e:
            # Convert metadata provider parse errors to data source errors
            error_msg = _FETCH_BOOK_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        except (KeyError, ValueError, TypeError) as e:
            logger.exception("Error parsing Hardcover API response")
            error_msg = _FETCH_BOOK_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        else:
            return None

    def _enrich_books_with_editions(
        self, books_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Enrich book data with detailed edition information.

        Parameters
        ----------
        books_data : list[dict[str, Any]]
            List of book data from search results.

        Returns
        -------
        list[dict[str, Any]]
            List of enriched book data.
        """
        enriched_books_data = []
        for book_data in books_data:
            book_id = book_data.get("id")
            if book_id:
                edition_data = self._fetch_edition_details(book_id)
                if edition_data:
                    enriched_book = self._enrichment.merge_book_with_editions(
                        book_data, edition_data
                    )
                    enriched_books_data.append(enriched_book)
                else:
                    enriched_books_data.append(book_data)
            else:
                enriched_books_data.append(book_data)
        return enriched_books_data

    def _fetch_edition_details(self, book_id: int | str) -> dict[str, Any] | None:
        """Fetch detailed edition information for a book.

        Parameters
        ----------
        book_id : int | str
            Hardcover book ID.

        Returns
        -------
        dict[str, Any] | None
            Book data with edition details, or None if fetch fails.
        """
        try:
            book_id_int = int(book_id)
            data = self._client.execute_query(
                query=EDITION_QUERY,
                variables={"bookId": book_id_int},
                operation_name=EDITION_OPERATION_NAME,
            )
            return self._parser.extract_edition_data(data)
        except (
            ValueError,
            TypeError,
            KeyError,
            httpx.RequestError,
            httpx.TimeoutException,
        ) as e:
            logger.debug(
                "Failed to fetch edition details for book ID %s: %s", book_id, e
            )
        return None

    def _map_books_to_book_data(
        self, books_data: list[dict[str, Any]]
    ) -> list[BookData]:
        """Map list of book data to BookData objects.

        Parameters
        ----------
        books_data : list[dict[str, Any]]
            List of book data dictionaries.

        Returns
        -------
        list[BookData]
            List of mapped book data objects.
        """
        results: list[BookData] = []
        for book_data in books_data:
            book_data_obj = self._map_to_book_data(book_data)
            if book_data_obj:
                results.append(book_data_obj)
        return results

    def _map_to_book_data(self, book_data: dict[str, Any]) -> BookData | None:
        """Map Hardcover book data to BookData.

        Parameters
        ----------
        book_data : dict[str, Any]
            Book data from API response.

        Returns
        -------
        BookData | None
            Mapped book data, or None if mapping fails.
        """
        try:
            book_id = book_data.get("id")
            if not book_id:
                return None

            # Title might be at book level or in first edition
            title = book_data.get("title", "")
            if not title:
                # Try to get title from first edition
                editions = book_data.get("editions", [])
                if editions and isinstance(editions, list) and editions[0]:
                    title = editions[0].get("title", "")

            if not title:
                # If still no title, try using slug as fallback or log more details
                slug = book_data.get("slug", "")
                if slug:
                    # Use slug as title fallback (better than returning None)
                    title = slug.replace("-", " ").title()
                    logger.debug(
                        "No title found for book ID %s, using slug as fallback: %s",
                        book_id,
                        title,
                    )
                else:
                    logger.warning(
                        "No title or slug found in book data for book ID %s. "
                        "Editions: %s",
                        book_id,
                        len(editions) if isinstance(editions, list) else 0,
                    )
                    return None

            # Extract authors
            authors_result = self._authors_extractor.extract(book_data)
            authors = authors_result if isinstance(authors_result, list) else []

            # Extract identifiers
            identifiers_result = self._identifiers_extractor.extract(book_data)
            identifiers = (
                identifiers_result if isinstance(identifiers_result, dict) else {}
            )

            # Extract ISBNs
            isbn_10 = identifiers.get("isbn")
            isbn_13 = identifiers.get("isbn13")

            # Extract cover URL
            cover_result = self._cover_extractor.extract(book_data)
            cover_url = cover_result if isinstance(cover_result, str) else None

            # Extract published date
            published_date_result = self._published_date_extractor.extract(book_data)
            publish_date = (
                published_date_result
                if isinstance(published_date_result, str)
                else None
            )

            # Extract publisher
            publisher_result = self._publisher_extractor.extract(book_data)
            publisher = publisher_result if isinstance(publisher_result, str) else None
            publishers = [publisher] if publisher else []

            # Extract subjects/tags
            tags_result = self._tags_extractor.extract(book_data)
            subjects = tags_result if isinstance(tags_result, list) else []

            # Extract description
            description = book_data.get("description")

            return BookData(
                key=str(book_id),
                title=title,
                authors=authors,
                isbn=isbn_10,
                isbn13=isbn_13,
                publish_date=publish_date,
                publishers=publishers,
                subjects=subjects,
                description=description,
                cover_url=cover_url,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("Error mapping Hardcover book data: %s", e)
            return None

    def _map_to_author_data(self, author_data: dict[str, Any]) -> AuthorData | None:
        """Map Hardcover author data to AuthorData.

        Handles both search document format and full author query format.

        Parameters
        ----------
        author_data : dict[str, Any]
            Author data from API response (search document or full author data).

        Returns
        -------
        AuthorData | None
            Mapped author data, or None if mapping fails.
        """
        try:
            author_id = author_data.get("id")
            if not author_id:
                return None

            name = author_data.get("name", "")
            if not name:
                return None

            # Extract dates (only available in full author query, not search results)
            birth_date = author_data.get("born_date")
            birth_year = author_data.get("born_year")
            if not birth_date and birth_year:
                birth_date = str(birth_year)

            death_date = author_data.get("death_date")
            death_year = author_data.get("death_year")
            if not death_date and death_year:
                death_date = str(death_year)

            # Extract alternate names
            alternate_names = author_data.get("alternate_names", [])
            if not isinstance(alternate_names, list):
                alternate_names = []

            # Extract biography (only available in full author query)
            biography = author_data.get("bio")

            # Extract identifiers (only available in full author query)
            identifiers = self._extract_author_identifiers(author_data)

            # Extract work count
            work_count = author_data.get("books_count")

            # Extract subjects (not available in author schema, leave empty)
            subjects: list[str] = []

            return AuthorData(
                key=str(author_id),
                name=name,
                birth_date=birth_date,
                death_date=death_date,
                biography=biography,
                alternate_names=alternate_names,
                identifiers=identifiers,
                work_count=work_count,
                subjects=subjects,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("Error mapping Hardcover author data: %s", e)
            return None

    def get_author_works(
        self,
        author_key: str,
        limit: int | None = None,
        lang: str = "eng",  # noqa: ARG002
    ) -> Sequence[str]:
        """Get work keys for an author.

        Extracts book IDs from the author's contributions.

        Parameters
        ----------
        author_key : str
            Author key/identifier (Hardcover author ID).
        limit : int | None
            Maximum number of work keys to return (None = fetch all).
        lang : str
            Language code (unused, kept for API compatibility).

        Returns
        -------
        Sequence[str]
            Sequence of work keys (book IDs as strings).

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        """
        if not self.bearer_token:
            logger.warning(
                "Hardcover API bearer token not set, cannot fetch author works"
            )
            return []

        try:
            # Convert key to integer (Hardcover uses integer IDs)
            try:
                author_id = int(author_key)
            except ValueError:
                logger.warning("Invalid Hardcover author ID: %s", author_key)
                return []

            # Fetch author details with contributions
            data = self._client.execute_query(
                query=AUTHOR_BY_ID_QUERY,
                variables={"authorId": author_id},
                operation_name=AUTHOR_BY_ID_OPERATION_NAME,
            )

            # Extract contributions and convert to work keys
            return self._extract_work_keys_from_contributions(data, limit)

        except MetadataProviderNetworkError as e:
            msg = f"Hardcover API request failed: {e}"
            raise DataSourceNetworkError(msg) from e
        except MetadataProviderParseError as e:
            error_msg = f"Error parsing author works: {e}"
            raise DataSourceNetworkError(error_msg) from e
        except (KeyError, ValueError, TypeError) as e:
            logger.exception("Error parsing Hardcover API response")
            error_msg = f"Error extracting author works: {e}"
            raise DataSourceNetworkError(error_msg) from e

    def _extract_work_keys_from_contributions(
        self, data: dict[str, Any], limit: int | None = None
    ) -> list[str]:
        """Extract work keys from author contributions data.

        Parameters
        ----------
        data : dict[str, Any]
            GraphQL response data.
        limit : int | None
            Maximum number of work keys to return.

        Returns
        -------
        list[str]
            List of work keys (book IDs as strings).
        """
        authors_data = data.get("data", {}).get("authors", [])
        if not isinstance(authors_data, list) or not authors_data:
            return []

        author_data = authors_data[0]
        contributions = author_data.get("contributions", [])

        if not isinstance(contributions, list):
            return []

        # Extract book IDs from contributions
        work_keys: list[str] = []
        for contribution in contributions:
            if not isinstance(contribution, dict):
                continue

            # Only get contributions to books (not editions)
            contributable_type = contribution.get("contributable_type")
            if contributable_type != "Book":
                continue

            # Extract book ID
            book = contribution.get("book")
            if isinstance(book, dict):
                book_id = book.get("id")
                if book_id:
                    work_keys.append(str(book_id))

            # Apply limit if specified
            if limit and len(work_keys) >= limit:
                break

        return work_keys

    def _extract_author_identifiers(
        self, author_data: dict[str, Any]
    ) -> IdentifierDict | None:
        """Extract identifiers from author data.

        Parameters
        ----------
        author_data : dict[str, Any]
            Author data from API response.

        Returns
        -------
        IdentifierDict | None
            Extracted identifiers, or None if none found.
        """
        identifiers_data = author_data.get("identifiers", [])
        if not isinstance(identifiers_data, list) or not identifiers_data:
            return None

        # Mapping from Hardcover identifier types to IdentifierDict attributes
        id_type_mapping = {
            "goodreads": "goodreads",
            "wikidata": "wikidata",
            "viaf": "viaf",
            "isni": "isni",
            "librarything": "librarything",
            "amazon": "amazon",
            "imdb": "imdb",
            "musicbrainz": "musicbrainz",
            "lc_naf": "lc_naf",
            "opac_sbn": "opac_sbn",
            "storygraph": "storygraph",
        }

        identifiers = IdentifierDict()
        for identifier_obj in identifiers_data:
            if not isinstance(identifier_obj, dict):
                continue

            # Hardcover identifiers format: {"type": "goodreads", "value": "12345"}
            id_type = identifier_obj.get("type", "").lower()
            id_value = identifier_obj.get("value") or identifier_obj.get("id")

            if not id_value or id_type not in id_type_mapping:
                continue

            # Set the identifier using the mapping
            attr_name = id_type_mapping[id_type]
            setattr(identifiers, attr_name, str(id_value))

        # Return None if no identifiers were found
        if not any([
            identifiers.viaf,
            identifiers.goodreads,
            identifiers.wikidata,
            identifiers.isni,
            identifiers.librarything,
            identifiers.amazon,
            identifiers.imdb,
            identifiers.musicbrainz,
            identifiers.lc_naf,
            identifiers.opac_sbn,
            identifiers.storygraph,
        ]):
            return None

        return identifiers
