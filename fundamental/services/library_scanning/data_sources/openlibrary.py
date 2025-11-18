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
from collections.abc import Sequence
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
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
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
                author_key = doc.get("key", "").replace("/authors/", "")
                if not author_key:
                    continue

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

    def get_author(self, key: str) -> AuthorData | None:
        """Get full author details by key.

        Parameters
        ----------
        key : str
            Author key (e.g., "OL23919A").

        Returns
        -------
        AuthorData | None
            Full author data if found, None otherwise.
        """
        try:
            # Normalize key (remove /authors/ prefix if present)
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

            return AuthorData(
                key=normalized_key,
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

    def get_book(self, key: str) -> BookData | None:
        """Get full book details by key.

        Parameters
        ----------
        key : str
            Book key (e.g., "OL82563W").

        Returns
        -------
        BookData | None
            Full book data if found, None otherwise.
        """
        try:
            normalized_key = key.replace("/works/", "").replace("/books/", "")
            path = f"/works/{normalized_key}.json"
            data = self._make_request(path)

            author_names = self._extract_authors_from_book_data(data)
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
                subjects=list(data.get("subjects", [])),
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
