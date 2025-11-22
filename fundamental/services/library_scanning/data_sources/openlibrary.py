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

"""OpenLibrary data source implementation."""

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNetworkError,
    DataSourceNotFoundError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
    IdentifierDict,
)

logger = logging.getLogger(__name__)

# OpenLibrary API base URL
OPENLIBRARY_API_BASE = "https://openlibrary.org"
OPENLIBRARY_COVERS_BASE = "https://covers.openlibrary.org"

# Error messages
_RATE_LIMIT_MSG = "OpenLibrary rate limit exceeded"
_RESOURCE_NOT_FOUND_MSG = "Resource not found: {path}"
_SEARCH_AUTHORS_ERROR_MSG = "Error searching authors: {error}"
_FETCH_AUTHOR_ERROR_MSG = "Error fetching author: {error}"
_SEARCH_BOOKS_ERROR_MSG = "Error searching books: {error}"
_FETCH_BOOK_ERROR_MSG = "Error fetching book: {error}"
_FETCH_AUTHOR_WORKS_ERROR_MSG = "Error fetching author works: {error}"

# Constants
OPENLIBRARY_MAX_PAGE_SIZE = 100


# ============================================================================
# Pagination and Request Building Classes
# ============================================================================


@dataclass
class PaginationState:
    """State tracking for pagination operations.

    Attributes
    ----------
    offset : int
        Current offset in pagination.
    collected_count : int
        Number of items collected so far.
    page_size : int
        Size of each page.
    """

    offset: int = 0
    collected_count: int = 0
    page_size: int = OPENLIBRARY_MAX_PAGE_SIZE


class PaginationStrategy:
    """Strategy for handling pagination logic.

    Determines when to stop pagination and calculates request limits.
    """

    def __init__(self, total_limit: int | None = None) -> None:
        """Initialize pagination strategy.

        Parameters
        ----------
        total_limit : int | None
            Maximum total items to collect (None = no limit).
        """
        self.total_limit = total_limit

    def calculate_request_limit(self, state: PaginationState, page_size: int) -> int:
        """Calculate the limit for the next request.

        Parameters
        ----------
        state : PaginationState
            Current pagination state.
        page_size : int
            Maximum page size.

        Returns
        -------
        int
            Request limit for next page.
        """
        if self.total_limit is None:
            return page_size

        remaining = self.total_limit - state.collected_count
        return min(page_size, max(0, remaining))

    def should_continue(
        self,
        state: PaginationState,
        docs_count: int,
        total_found: int,
    ) -> bool:
        """Determine if pagination should continue.

        Parameters
        ----------
        state : PaginationState
            Current pagination state.
        docs_count : int
            Number of documents in current page.
        total_found : int
            Total number of items found (from API).

        Returns
        -------
        bool
            True if pagination should continue, False otherwise.
        """
        # Stop if no documents in current page
        if docs_count == 0:
            return False

        # Stop if we've reached the total limit
        if self.total_limit is not None and state.collected_count >= self.total_limit:
            return False

        # Stop if we've reached the end of all results
        return state.offset + docs_count < total_found

    def update_state(
        self,
        state: PaginationState,
        docs_count: int,
    ) -> None:
        """Update pagination state after processing a page.

        Parameters
        ----------
        state : PaginationState
            Current pagination state.
        docs_count : int
            Number of documents processed.
        """
        state.collected_count += docs_count
        state.offset += docs_count


class WorkKeyExtractor:
    """Extracts work keys from OpenLibrary API response documents."""

    @staticmethod
    def extract(docs: list[dict[str, Any]]) -> list[str]:
        """Extract work keys from API response documents.

        OpenLibrary returns keys like "/works/OL123456W" or "/books/OL123456M".

        Parameters
        ----------
        docs : list[dict[str, Any]]
            List of document dictionaries from API response.

        Returns
        -------
        list[str]
            List of extracted work keys.
        """
        work_keys: list[str] = []
        for doc in docs:
            key = doc.get("key", "")
            if key:
                # Remove "/works/" or "/books/" prefix
                normalized_key = key.replace("/works/", "").replace("/books/", "")
                if normalized_key:
                    work_keys.append(normalized_key)
        return work_keys


class SearchRequestBuilder:
    """Builds search request parameters for OpenLibrary API."""

    def __init__(
        self,
        author_key: str,
        lang: str = "eng",
        fields: str = "key",
    ) -> None:
        """Initialize request builder.

        Parameters
        ----------
        author_key : str
            Author key to search for.
        lang : str
            Language code to filter works (default: "eng").
        fields : str
            Fields to request from API (default: "key").
        """
        self.author_key = author_key
        self.lang = lang
        self.fields = fields

    def build_params(
        self,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """Build request parameters.

        Parameters
        ----------
        limit : int
            Maximum number of results to return.
        offset : int
            Offset for pagination.

        Returns
        -------
        dict[str, Any]
            Request parameters dictionary.
        """
        return {
            "author": self.author_key,
            "lang": self.lang,
            "fields": self.fields,
            "limit": limit,
            "offset": offset,
        }


class AuthorWorksPaginator:
    """Handles pagination for fetching author works.

    Coordinates pagination strategy, request building, and response parsing.
    """

    def __init__(
        self,
        request_builder: SearchRequestBuilder,
        pagination_strategy: PaginationStrategy,
        work_extractor: WorkKeyExtractor,
        make_request: Callable[[str, dict[str, Any] | None], dict[str, Any]],
        rate_limit: Callable[[], None],
    ) -> None:
        """Initialize paginator.

        Parameters
        ----------
        request_builder : SearchRequestBuilder
            Builder for API request parameters.
        pagination_strategy : PaginationStrategy
            Strategy for pagination logic.
        work_extractor : WorkKeyExtractor
            Extractor for work keys from responses.
        make_request : callable
            Function to make API requests.
        rate_limit : callable
            Function to enforce rate limiting.
        """
        self.request_builder = request_builder
        self.pagination_strategy = pagination_strategy
        self.work_extractor = work_extractor
        self.make_request = make_request
        self.rate_limit = rate_limit

    def fetch_all(self) -> list[str]:
        """Fetch all work keys using pagination.

        Returns
        -------
        list[str]
            List of all work keys.
        """
        all_work_keys: list[str] = []
        state = PaginationState()

        while True:
            # Calculate request limit
            request_limit = self.pagination_strategy.calculate_request_limit(
                state, OPENLIBRARY_MAX_PAGE_SIZE
            )

            if request_limit <= 0:
                break

            # Build and make request
            params = self.request_builder.build_params(request_limit, state.offset)
            data = self.make_request("/search.json", params)
            docs = data.get("docs", [])

            # Check if we should continue
            total_found = data.get("numFound", 0)
            if not self.pagination_strategy.should_continue(
                state, len(docs), total_found
            ):
                # Extract remaining keys before breaking
                if docs:
                    work_keys = self.work_extractor.extract(docs)
                    all_work_keys.extend(work_keys)
                break

            # Extract work keys from this page
            work_keys = self.work_extractor.extract(docs)
            all_work_keys.extend(work_keys)

            # Update pagination state
            self.pagination_strategy.update_state(state, len(docs))

            # Enforce rate limiting
            self.rate_limit()

        # Apply final limit if specified
        if self.pagination_strategy.total_limit is not None:
            return all_work_keys[: self.pagination_strategy.total_limit]

        return all_work_keys


class OpenLibraryDataSource(BaseDataSource):
    """OpenLibrary data source implementation.

    Fetches author and book metadata from the OpenLibrary API.
    Handles rate limiting and maps responses to normalized data structures.
    """

    def __init__(
        self,
        base_url: str = OPENLIBRARY_API_BASE,
        timeout: float = 30.0,
        rate_limit_delay: float = 0.5,
    ) -> None:
        """Initialize OpenLibrary data source.

        Parameters
        ----------
        base_url : str
            Base URL for OpenLibrary API (default: production API).
        timeout : float
            Request timeout in seconds (default: 30.0).
        rate_limit_delay : float
            Delay between requests in seconds to respect rate limits (default: 0.5).
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

    @property
    def name(self) -> str:
        """Get the name of this data source.

        Returns
        -------
        str
            Data source name.
        """
        return "OpenLibrary"

    def _rate_limit(self) -> None:
        """Enforce rate limiting by delaying requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self._last_request_time = time.time()

    def _make_request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to OpenLibrary API.

        Parameters
        ----------
        path : str
            API path (e.g., "/authors/OL23919A.json").
        params : dict[str, Any] | None
            Query parameters.

        Returns
        -------
        dict[str, Any]
            JSON response data.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded (429 status).
        DataSourceNotFoundError
            If resource is not found (404 status).
        """
        self._rate_limit()

        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, params=params)
                # Check if we were redirected to a different resource type
                # (e.g., /authors/ redirecting to /works/ means wrong ID type)
                if response.history:
                    final_url = str(response.url)
                    # If we requested /authors/ but got redirected to /works/, that's an error
                    if "/authors/" in path and "/works/" in final_url:
                        error_msg = f"OLID {path} is a work ID, not an author ID (redirected to {final_url})"
                        raise DataSourceNotFoundError(error_msg)
                response.raise_for_status()

                if response.status_code == 429:
                    raise DataSourceRateLimitError(_RATE_LIMIT_MSG)

                if response.status_code == 404:
                    error_msg = _RESOURCE_NOT_FOUND_MSG.format(path=path)
                    raise DataSourceNotFoundError(error_msg)

                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                error_msg = _RESOURCE_NOT_FOUND_MSG.format(path=path)
                raise DataSourceNotFoundError(error_msg) from e
            if e.response.status_code == 429:
                raise DataSourceRateLimitError(_RATE_LIMIT_MSG) from e
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            raise DataSourceNetworkError(error_msg) from e
        except httpx.RequestError as e:
            error_msg = f"Network error: {e}"
            raise DataSourceNetworkError(error_msg) from e

    def _extract_identifiers(self, data: dict[str, Any]) -> IdentifierDict:
        """Extract identifiers from OpenLibrary response.

        Parameters
        ----------
        data : dict[str, Any]
            OpenLibrary author data.

        Returns
        -------
        IdentifierDict
            Extracted identifiers.
        """
        remote_ids = data.get("remote_ids", {})
        return IdentifierDict(
            viaf=remote_ids.get("viaf"),
            goodreads=remote_ids.get("goodreads"),
            wikidata=remote_ids.get("wikidata"),
            isni=remote_ids.get("isni"),
            librarything=remote_ids.get("librarything"),
            amazon=remote_ids.get("amazon"),
            imdb=remote_ids.get("imdb"),
            musicbrainz=remote_ids.get("musicbrainz"),
            lc_naf=remote_ids.get("lc_naf"),
            opac_sbn=remote_ids.get("opac_sbn"),
            storygraph=remote_ids.get("storygraph"),
        )

    def _extract_bio(self, data: dict[str, Any]) -> str | None:
        """Extract biography text from OpenLibrary response.

        Parameters
        ----------
        data : dict[str, Any]
            OpenLibrary author data.

        Returns
        -------
        str | None
            Biography text, or None if not available.
        """
        bio = data.get("bio")
        if isinstance(bio, dict):
            return bio.get("value")
        if isinstance(bio, str):
            return bio
        return None

    def _get_photo_url(self, photo_id: int) -> str:
        """Generate photo URL from OpenLibrary photo ID.

        Parameters
        ----------
        photo_id : int
            OpenLibrary photo ID.

        Returns
        -------
        str
            Photo URL.
        """
        return f"{OPENLIBRARY_COVERS_BASE}/a/id/{photo_id}-L.jpg"

    def search_author(
        self,
        name: str,
        identifiers: IdentifierDict | None = None,
    ) -> Sequence[AuthorData]:
        """Search for authors by name and optional identifiers.

        Parameters
        ----------
        name : str
            Author name to search for.
        identifiers : IdentifierDict | None
            Optional external identifiers.

        Returns
        -------
        Sequence[AuthorData]
            Sequence of matching author data.
        """
        # If we have identifiers, try to find exact match first
        if identifiers:
            # Try VIAF, Goodreads, Wikidata in order
            # OpenLibrary doesn't have direct identifier search,
            # so we'll fall through to name search
            for _id_type, id_value in (
                ("viaf", identifiers.viaf),
                ("goodreads", identifiers.goodreads),
                ("wikidata", identifiers.wikidata),
            ):
                if id_value:
                    # OpenLibrary doesn't have direct identifier search,
                    # so we'll fall through to name search
                    pass

        # Search by name
        try:
            params = {"q": name}
            data = self._make_request("/search/authors.json", params=params)

            docs = data.get("docs", [])
            results: list[AuthorData] = []

            for doc in docs:
                raw_key = doc.get("key", "")
                if not raw_key:
                    continue

                # Normalize key: ensure it has /authors/ prefix (OpenLibrary convention)
                if not raw_key.startswith("/authors/"):
                    author_key = f"/authors/{raw_key.replace('authors/', '')}"
                else:
                    author_key = raw_key

                # Extract photo IDs
                photos = doc.get("photos", [])
                photo_ids = [p for p in photos if isinstance(p, int) and p > 0]

                # Extract subjects
                subjects = doc.get("top_subjects", [])

                author_data = AuthorData(
                    key=author_key,
                    name=doc.get("name", ""),
                    personal_name=doc.get("personal_name"),
                    birth_date=doc.get("birth_date"),
                    death_date=doc.get("death_date"),
                    entity_type=doc.get("type"),
                    work_count=doc.get("work_count"),
                    ratings_average=doc.get("ratings_average"),
                    ratings_count=doc.get("ratings_count"),
                    top_work=doc.get("top_work"),
                    photo_ids=photo_ids,
                    subjects=subjects,
                )

                results.append(author_data)
        except (DataSourceNetworkError, DataSourceRateLimitError):
            raise
        except Exception as e:
            logger.exception("Error searching authors in OpenLibrary")
            error_msg = _SEARCH_AUTHORS_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        else:
            return results

    def get_author_works(
        self,
        author_key: str,
        limit: int | None = None,
        lang: str = "eng",
    ) -> Sequence[str]:
        """Get work keys for an author.

        Fetches all works by default, or up to limit if specified.
        Uses pagination to fetch all results when limit is None.

        Parameters
        ----------
        author_key : str
            Author key (e.g., "OL23919A").
        limit : int | None
            Maximum number of work keys to return (None = fetch all).
        lang : str
            Language code to filter works (default: "eng").

        Returns
        -------
        Sequence[str]
            Sequence of work keys.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        """
        try:
            # Build components using dependency injection
            request_builder = SearchRequestBuilder(author_key, lang=lang)
            pagination_strategy = PaginationStrategy(total_limit=limit)
            work_extractor = WorkKeyExtractor()

            # Create paginator with injected dependencies
            paginator = AuthorWorksPaginator(
                request_builder=request_builder,
                pagination_strategy=pagination_strategy,
                work_extractor=work_extractor,
                make_request=self._make_request,
                rate_limit=self._rate_limit,
            )

            return paginator.fetch_all()
        except (DataSourceNetworkError, DataSourceRateLimitError):
            raise
        except Exception as e:
            logger.exception("Error fetching author works from OpenLibrary")
            error_msg = _FETCH_AUTHOR_WORKS_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e

    def get_author(self, key: str) -> AuthorData | None:
        """Get full author details by key.

        Parameters
        ----------
        key : str
            Author key (e.g., "OL23919A" or "/authors/OL23919A").

        Returns
        -------
        AuthorData | None
            Full author data if found, None otherwise.
        """
        try:
            # Normalize key for API request (remove /authors/ prefix if present)
            normalized_key = key.replace("/authors/", "").replace("authors/", "")
            path = f"/authors/{normalized_key}.json"

            data = self._make_request(path)

            # Extract photo IDs
            photos = data.get("photos", [])
            photo_ids = [p for p in photos if isinstance(p, int) and p > 0]

            # Extract alternate names
            alternate_names = data.get("alternate_names", [])

            # Extract links
            links = [
                {
                    "title": link.get("title", ""),
                    "url": link.get("url", ""),
                    "type": link.get("type", {}).get("key", ""),
                }
                for link in data.get("links", [])
                if isinstance(link, dict)
            ]

            # Extract subjects from top_subjects or subjects
            subjects = data.get("top_subjects", []) or data.get("subjects", [])

            identifiers = self._extract_identifiers(data)
            bio = self._extract_bio(data)

            # Store key with /authors/ prefix (OpenLibrary convention)
            return AuthorData(
                key=f"/authors/{normalized_key}",
                name=data.get("name", ""),
                personal_name=data.get("personal_name"),
                fuller_name=data.get("fuller_name"),
                title=data.get("title"),
                birth_date=data.get("birth_date"),
                death_date=data.get("death_date"),
                entity_type=data.get("entity_type"),
                biography=bio,
                photo_ids=photo_ids,
                alternate_names=alternate_names,
                links=links,
                identifiers=identifiers,
                work_count=data.get("work_count"),
                ratings_average=data.get("ratings_average"),
                ratings_count=data.get("ratings_count"),
                top_work=data.get("top_work"),
                subjects=subjects,
            )
        except DataSourceNotFoundError:
            return None
        except (DataSourceNetworkError, DataSourceRateLimitError):
            raise
        except Exception as e:
            logger.exception("Error fetching author from OpenLibrary")
            error_msg = _FETCH_AUTHOR_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e

    def _extract_book_from_doc(self, doc: dict[str, Any]) -> BookData | None:
        """Extract BookData from a search result document.

        Parameters
        ----------
        doc : dict[str, Any]
            Document from search results.

        Returns
        -------
        BookData | None
            Extracted book data, or None if key is missing.
        """
        book_key = doc.get("key", "").replace("/works/", "").replace("/books/", "")
        if not book_key:
            return None

        # Extract authors
        author_names = [
            author for author in doc.get("author_name", []) if isinstance(author, str)
        ]

        # Extract ISBNs
        isbns = doc.get("isbn", [])
        isbn_10 = isbns[0] if isbns else None
        isbn_13 = isbns[1] if len(isbns) > 1 else None

        # Extract cover
        cover_id = doc.get("cover_i")
        cover_url = None
        if cover_id:
            cover_url = f"{OPENLIBRARY_COVERS_BASE}/b/id/{cover_id}-L.jpg"

        return BookData(
            key=book_key,
            title=doc.get("title", ""),
            authors=author_names,
            isbn=isbn_10,
            isbn13=isbn_13,
            publish_date=doc.get("first_publish_year"),
            publishers=doc.get("publisher", []),
            subjects=doc.get("subject", []),
            cover_url=cover_url,
        )

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
        """
        try:
            params: dict[str, Any] = {}

            if isbn:
                params["isbn"] = isbn
            elif title:
                params["title"] = title
            elif authors:
                params["author"] = authors[0] if authors else ""

            if not params:
                return []

            data = self._make_request("/search/books.json", params=params)
            docs = data.get("docs", [])
            results: list[BookData] = []

            for doc in docs:
                book_data = self._extract_book_from_doc(doc)
                if book_data:
                    results.append(book_data)
        except (DataSourceNetworkError, DataSourceRateLimitError):
            raise
        except Exception as e:
            logger.exception("Error searching books in OpenLibrary")
            error_msg = _SEARCH_BOOKS_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
        else:
            return results

    def _extract_authors_from_book_data(self, data: dict[str, Any]) -> list[str]:
        """Extract author names from book data.

        Parameters
        ----------
        data : dict[str, Any]
            Book data from API.

        Returns
        -------
        list[str]
            List of author names.
        """
        author_names = []
        for author in data.get("authors", []):
            if isinstance(author, dict):
                author_key = author.get("author", {}).get("key", "")
                if author_key:
                    author_path = f"{author_key}.json"
                    try:
                        author_data = self._make_request(author_path)
                        author_names.append(author_data.get("name", ""))
                    except (
                        DataSourceNetworkError,
                        DataSourceRateLimitError,
                        DataSourceNotFoundError,
                    ):
                        logger.debug("Could not fetch author data for %s", author_key)
        return author_names

    def _extract_isbns_from_book_data(
        self, data: dict[str, Any]
    ) -> tuple[str | None, str | None]:
        """Extract ISBNs from book data.

        Parameters
        ----------
        data : dict[str, Any]
            Book data from API.

        Returns
        -------
        tuple[str | None, str | None]
            Tuple of (isbn_10, isbn_13).
        """
        identifiers = data.get("identifiers", {})
        isbn_10 = None
        isbn_13 = None
        for identifier in identifiers.get("isbn_10", []):
            isbn_10 = identifier
            break
        for identifier in identifiers.get("isbn_13", []):
            isbn_13 = identifier
            break
        return (isbn_10, isbn_13)

    def _extract_cover_from_book_data(self, data: dict[str, Any]) -> str | None:
        """Extract cover URL from book data.

        Parameters
        ----------
        data : dict[str, Any]
            Book data from API.

        Returns
        -------
        str | None
            Cover URL if available.
        """
        covers = data.get("covers", [])
        cover_id = covers[0] if covers else None
        if cover_id:
            return f"{OPENLIBRARY_COVERS_BASE}/b/id/{cover_id}-L.jpg"
        return None

    def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:
        """Get full book details by key.

        Parameters
        ----------
        key : str
            Book key (e.g., "OL82563W").
        skip_authors : bool
            If True, skip fetching author data (faster, useful when only subjects are needed).

        Returns
        -------
        BookData | None
            Full book data if found, None otherwise.
        """
        try:
            normalized_key = key.replace("/works/", "").replace("/books/", "")
            path = f"/works/{normalized_key}.json"
            data = self._make_request(path)

            author_names = (
                [] if skip_authors else self._extract_authors_from_book_data(data)
            )
            isbn_10, isbn_13 = self._extract_isbns_from_book_data(data)
            cover_url = self._extract_cover_from_book_data(data)

            description = data.get("description")
            if isinstance(description, dict):
                description = description.get("value")

            return BookData(
                key=normalized_key,
                title=data.get("title", ""),
                authors=author_names,
                isbn=isbn_10,
                isbn13=isbn_13,
                publish_date=data.get("first_publish_date"),
                publishers=[p.get("name", "") for p in data.get("publishers", [])],
                subjects=[
                    s
                    if isinstance(s, str)
                    else s.get("name", "")
                    if isinstance(s, dict)
                    else str(s)
                    for s in data.get("subjects", [])
                    if s
                ],
                description=description,
                cover_url=cover_url,
            )
        except DataSourceNotFoundError:
            return None
        except (DataSourceNetworkError, DataSourceRateLimitError):
            raise
        except Exception as e:
            logger.exception("Error fetching book from OpenLibrary")
            error_msg = _FETCH_BOOK_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e

    def get_work_raw(self, key: str) -> dict[str, Any] | None:
        """Get raw work JSON data by key.

        Parameters
        ----------
        key : str
            Work key (e.g., "OL82563W").

        Returns
        -------
        dict[str, Any] | None
            Raw work JSON data if found, None otherwise.
        """
        try:
            normalized_key = key.replace("/works/", "").replace("/books/", "")
            path = f"/works/{normalized_key}.json"
            return self._make_request(path)
        except DataSourceNotFoundError:
            return None
        except (DataSourceNetworkError, DataSourceRateLimitError):
            raise
        except Exception as e:
            logger.exception("Error fetching raw work data from OpenLibrary")
            error_msg = _FETCH_BOOK_ERROR_MSG.format(error=e)
            raise DataSourceNetworkError(error_msg) from e
