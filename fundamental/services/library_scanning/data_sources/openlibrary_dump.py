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

"""OpenLibrary local dump data source implementation."""

import logging
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Engine, Text, func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, select

from fundamental.database import create_db_engine, get_session
from fundamental.models.openlibrary import (
    OpenLibraryAuthor,
    OpenLibraryAuthorWork,
    OpenLibraryEdition,
    OpenLibraryEditionIsbn,
    OpenLibraryWork,
)
from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
    IdentifierDict,
)

logger = logging.getLogger(__name__)

OPENLIBRARY_COVERS_BASE = "https://covers.openlibrary.org"

# Minimum similarity threshold for trigram search (0.0 to 1.0)
# Lower values return more results but may include false positives
MIN_TRIGRAM_SIMILARITY = 0.6


class OpenLibraryDumpDataSource(BaseDataSource):
    """Data source using local OpenLibrary dump PostgreSQL database.

    Queries a locally ingested PostgreSQL database instead of the live API.
    Uses GIN indexes for efficient text search and JSONB queries.
    Suitable for high-volume scanning.
    """

    def __init__(
        self,
        engine: Engine | None = None,
        data_directory: str = "/data",  # noqa: ARG002
    ) -> None:
        """Initialize dump data source.

        Parameters
        ----------
        engine : Engine | None
            SQLAlchemy engine for database connection. If None, creates one
            from application configuration.
        data_directory : str
            Deprecated parameter kept for backward compatibility. Ignored.
        """
        self._engine = engine or create_db_engine()

    @property
    def name(self) -> str:
        """Get data source name."""
        return "OpenLibraryDump"

    def _extract_identifiers(self, data: dict[str, Any]) -> IdentifierDict:
        """Extract identifiers from author data.

        Parameters
        ----------
        data : dict[str, Any]
            Author data dictionary.

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
        """Extract biography text.

        Parameters
        ----------
        data : dict[str, Any]
            Author data dictionary.

        Returns
        -------
        str | None
            Biography text or None if not available.
        """
        bio = data.get("bio")
        if isinstance(bio, dict):
            return bio.get("value")
        if isinstance(bio, str):
            return bio
        return None

    def search_author(
        self,
        name: str,
        identifiers: IdentifierDict | None = None,  # noqa: ARG002
    ) -> Sequence[AuthorData]:
        """Search for authors by exact name match.

        Uses simple JSONB operator for fast exact matching on the name field.
        Case-insensitive matching for better results.

        Parameters
        ----------
        name : str
            Author name to search for.
        identifiers : IdentifierDict | None
            Optional identifiers (not currently used in dump search).

        Returns
        -------
        Sequence[AuthorData]
            List of matching authors.
        """
        if not name or not name.strip():
            return []

        results: list[AuthorData] = []

        try:
            with get_session(self._engine) as session:
                # Normalize search name
                search_name = name.strip()

                # Simple exact match using JSONB operator (fast, uses GIN JSONB index)
                # Case-sensitive matching for optimal performance (no function calls on indexed column)
                # Use raw SQL text to avoid parameter binding issues with JSONB operators
                stmt = select(OpenLibraryAuthor.key, OpenLibraryAuthor.data).where(
                    sql_text(
                        "openlibrary_authors.data->>'name' = :search_name"
                    ).bindparams(search_name=search_name)
                )

                rows = session.exec(stmt).all()

                for row in rows:
                    work_key, work_data = row
                    if not work_data:
                        continue

                    try:
                        author = self._parse_author_data(work_key, work_data)
                        results.append(author)
                    except (KeyError, TypeError):
                        logger.debug("Error parsing author data for key %s", work_key)
                        continue

        except OperationalError:
            logger.exception("Database error searching authors")
            return []
        except Exception:
            logger.exception("Unexpected error searching authors")
            return []

        return results

    def _parse_author_data(self, key: str, data: dict[str, Any]) -> AuthorData:
        """Parse raw JSON data into AuthorData.

        Parameters
        ----------
        key : str
            Author key identifier (from DB, already has /authors/ prefix).
        data : dict[str, Any]
            Raw author data dictionary.

        Returns
        -------
        AuthorData
            Parsed author data.
        """
        # Ensure key has /authors/ prefix (OpenLibrary convention)
        if not key.startswith("/authors/"):
            normalized_key = f"/authors/{key.replace('authors/', '')}"
        else:
            normalized_key = key

        photos = data.get("photos", [])
        photo_ids = [p for p in photos if isinstance(p, int) and p > 0]

        links = [
            {
                "title": link.get("title", ""),
                "url": link.get("url", ""),
                "type": link.get("type", {}).get("key", ""),
            }
            for link in data.get("links", [])
            if isinstance(link, dict)
        ]

        subjects = data.get("subjects", [])

        return AuthorData(
            key=normalized_key,
            name=data.get("name", ""),
            personal_name=data.get("personal_name"),
            fuller_name=data.get("fuller_name"),
            title=data.get("title"),
            birth_date=data.get("birth_date"),
            death_date=data.get("death_date"),
            entity_type=data.get("entity_type"),
            biography=self._extract_bio(data),
            photo_ids=photo_ids,
            alternate_names=data.get("alternate_names", []),
            links=links,
            identifiers=self._extract_identifiers(data),
            work_count=None,  # Often not in author dump
            ratings_average=None,
            ratings_count=None,
            top_work=None,
            subjects=subjects,
        )

    def get_author(self, key: str) -> AuthorData | None:
        """Get author by key.

        Database stores keys with /authors/ prefix (e.g., '/authors/OL19981A').

        Parameters
        ----------
        key : str
            Author key identifier (with or without /authors/ prefix).

        Returns
        -------
        AuthorData | None
            Author data if found, None otherwise.
        """
        try:
            with get_session(self._engine) as session:
                # Ensure key has /authors/ prefix (database stores with prefix)
                if not key.startswith("/authors/"):
                    normalized_key = f"/authors/{key.replace('authors/', '')}"
                else:
                    normalized_key = key

                stmt = select(OpenLibraryAuthor).where(
                    OpenLibraryAuthor.key == normalized_key
                )
                author = session.exec(stmt).first()

                if not author or not author.data:
                    return None

                return self._parse_author_data(author.key, author.data)

        except OperationalError:
            logger.exception("Database error getting author %s", key)
            return None
        except Exception:
            logger.exception("Unexpected error getting author %s", key)
            return None

    def get_author_works(
        self,
        author_key: str,
        limit: int | None = None,
        lang: str = "eng",  # noqa: ARG002
    ) -> Sequence[str]:
        """Get work keys for an author from the database.

        Fetches work keys from openlibrary_author_works table.

        Parameters
        ----------
        author_key : str
            Author key (e.g., '/authors/OL19981A' or 'OL19981A').
        limit : int | None
            Maximum number of work keys to return (None = fetch all).
        lang : str
            Language code (not used for dump source, kept for API compatibility).

        Returns
        -------
        Sequence[str]
            Sequence of work keys.
        """
        try:
            with get_session(self._engine) as session:
                # Ensure author_key has /authors/ prefix
                if not author_key.startswith("/authors/"):
                    normalized_author_key = (
                        f"/authors/{author_key.replace('authors/', '')}"
                    )
                else:
                    normalized_author_key = author_key

                # Query openlibrary_author_works table
                # When selecting a single column, SQLModel returns the value directly, not a row object
                stmt = select(OpenLibraryAuthorWork.work_key).where(
                    OpenLibraryAuthorWork.author_key == normalized_author_key
                )

                if limit:
                    stmt = stmt.limit(limit)

                # Return work keys (they should already have /works/ prefix from DB)
                # session.exec() returns the column values directly when selecting a single column
                return list(session.exec(stmt).all())

        except OperationalError:
            logger.exception("Database error getting author works for %s", author_key)
            return []
        except Exception:
            logger.exception("Unexpected error getting author works for %s", author_key)
            return []

    def _search_by_isbn(self, session: Session, isbn: str) -> list[BookData]:  # type: ignore[type-arg]
        """Search for books by ISBN.

        Parameters
        ----------
        session : Session
            Database session.
        isbn : str
            ISBN identifier.

        Returns
        -------
        list[BookData]
            List of matching books.
        """
        results: list[BookData] = []
        # Normalize ISBN (remove hyphens, spaces)
        normalized_isbn = isbn.replace("-", "").replace(" ", "")

        # Search in edition_isbns table (uses index on isbn column)
        stmt = select(OpenLibraryEditionIsbn.edition_key).where(
            OpenLibraryEditionIsbn.isbn == normalized_isbn
        )
        edition_keys = [row.edition_key for row in session.exec(stmt).all()]

        if not edition_keys:
            return results

        # Get editions and their works
        stmt = select(OpenLibraryEdition).where(
            OpenLibraryEdition.key.in_(edition_keys)  # type: ignore[attr-defined]
        )
        editions = session.exec(stmt).all()

        # Get work keys from editions
        work_keys = [edition.work_key for edition in editions if edition.work_key]

        if work_keys:
            # Get works (uses primary key index)
            stmt = select(OpenLibraryWork).where(
                OpenLibraryWork.key.in_(work_keys)  # type: ignore[attr-defined]
            )
            works = session.exec(stmt).all()

            for work in works:
                if work.data:
                    try:
                        book = self._parse_book_data(work.key, work.data)
                        results.append(book)
                    except (KeyError, TypeError):
                        logger.debug("Error parsing book data for key %s", work.key)
                        continue

        # Also include editions directly if they have title
        for edition in editions:
            if edition.data and edition.data.get("title"):
                try:
                    book = self._parse_book_data(edition.key, edition.data)
                    results.append(book)
                except (KeyError, TypeError):
                    logger.debug("Error parsing edition data for key %s", edition.key)
                    continue

        return results[:20]

    def _search_by_title(self, session: Session, title: str) -> list[BookData]:  # type: ignore[type-arg]
        """Search for books by title using trigram similarity.

        Parameters
        ----------
        session : Session
            Database session.
        title : str
            Book title to search for.

        Returns
        -------
        list[BookData]
            List of matching books.
        """
        results: list[BookData] = []
        search_title = title.strip()

        # Access JSONB title field using -> operator with proper casting
        work_data_col = func.cast(OpenLibraryWork.data, JSONB)  # type: ignore[arg-type]
        title_field = func.cast(
            work_data_col.op("->>")("title"),
            Text(),  # type: ignore[attr-defined]
        )

        stmt = (
            select(
                OpenLibraryWork.key,
                OpenLibraryWork.data,
                func.similarity(
                    title_field,
                    search_title,
                ).label("title_similarity"),
            )
            .where(
                func.similarity(
                    title_field,
                    search_title,
                )
                >= MIN_TRIGRAM_SIMILARITY
            )
            .order_by(
                func.similarity(
                    title_field,
                    search_title,
                ).desc()
            )
            .limit(20)
        )

        rows = session.exec(stmt).all()

        for row in rows:
            work_key, work_data, _ = row
            if not work_data:
                continue

            try:
                book = self._parse_book_data(work_key, work_data)
                results.append(book)
            except (KeyError, TypeError):
                logger.debug("Error parsing book data for key %s", work_key)
                continue

        return results

    def search_book(
        self,
        title: str | None = None,
        isbn: str | None = None,
        authors: Sequence[str] | None = None,  # noqa: ARG002
    ) -> Sequence[BookData]:
        """Search for books by title or ISBN.

        Uses GIN trigram index on title field for efficient fuzzy text search.
        Uses B-tree index on ISBN for exact ISBN lookups.

        Parameters
        ----------
        title : str | None
            Book title to search for.
        isbn : str | None
            ISBN identifier for exact lookup.
        authors : Sequence[str] | None
            Author names (not currently used in dump search).

        Returns
        -------
        Sequence[BookData]
            List of matching books.

        Notes
        -----
        - Title search uses PostgreSQL trigram similarity with GIN trigram index.
        - ISBN search uses the indexed ISBN table for fast lookups.
        - If both title and ISBN are provided, ISBN takes precedence.
        """
        try:
            with get_session(self._engine) as session:
                # ISBN search takes precedence (uses indexed ISBN table)
                if isbn:
                    results = self._search_by_isbn(session, isbn)
                    if results:
                        return results

                # Title search (uses GIN trigram index on title field)
                if title:
                    return self._search_by_title(session, title)

        except OperationalError:
            logger.exception("Database error searching books")
            return []
        except Exception:
            logger.exception("Unexpected error searching books")
            return []

        return []

    def _parse_book_data(self, key: str, data: dict[str, Any]) -> BookData:
        """Parse raw JSON data into BookData.

        Parameters
        ----------
        key : str
            Book/work key identifier.
        data : dict[str, Any]
            Raw book/work data dictionary.

        Returns
        -------
        BookData
            Parsed book data.
        """
        # Authors in works dump are usually references: {"key": "/authors/OL..."}
        # We can't easily resolve names here without extra lookups,
        # so we might just return empty list or keys.
        # The BaseDataSource expects names.
        # Resolving them would require N queries.
        # For now, we skip resolving to keep it fast.
        author_names: list[str] = []

        covers = data.get("covers", [])
        cover_url = None
        if covers:
            cover_url = f"{OPENLIBRARY_COVERS_BASE}/b/id/{covers[0]}-L.jpg"

        description = data.get("description")
        if isinstance(description, dict):
            description = description.get("value")

        subjects = [
            s
            if isinstance(s, str)
            else s.get("name", "")
            if isinstance(s, dict)
            else str(s)
            for s in data.get("subjects", [])
            if s
        ]

        # Extract ISBN from edition data if available
        isbn = None
        isbn13 = None
        isbn_list = data.get("isbn_13") or data.get("isbn_10") or data.get("isbn")
        if isbn_list and isinstance(isbn_list, list) and len(isbn_list) > 0:
            # Take first ISBN
            first_isbn = str(isbn_list[0])
            if len(first_isbn) == 13:
                isbn13 = first_isbn
            else:
                isbn = first_isbn

        return BookData(
            key=key,
            title=data.get("title", ""),
            authors=author_names,
            isbn=isbn,
            isbn13=isbn13,
            publish_date=data.get("first_publish_date"),
            publishers=[],  # Works don't usually have publishers
            subjects=subjects,
            description=description,
            cover_url=cover_url,
        )

    def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:  # noqa: ARG002
        """Get book by key.

        Database stores keys with /works/ prefix (e.g., '/works/OL10301079W').

        Parameters
        ----------
        key : str
            Book/work key identifier (with or without /works/ prefix).
        skip_authors : bool
            If True, skip fetching author data (not currently used).

        Returns
        -------
        BookData | None
            Book data if found, None otherwise.
        """
        try:
            with get_session(self._engine) as session:
                # Ensure key has /works/ prefix (database stores with prefix)
                if not key.startswith("/works/") and not key.startswith("/books/"):
                    normalized_key = (
                        f"/works/{key.replace('works/', '').replace('books/', '')}"
                    )
                elif key.startswith("/books/"):
                    normalized_key = key.replace("/books/", "/works/")
                else:
                    normalized_key = key

                stmt = select(OpenLibraryWork).where(
                    OpenLibraryWork.key == normalized_key
                )
                work = session.exec(stmt).first()

                if not work or not work.data:
                    return None

                return self._parse_book_data(work.key, work.data)

        except OperationalError:
            logger.exception("Database error getting book %s", key)
            return None
        except Exception:
            logger.exception("Unexpected error getting book %s", key)
            return None

    def get_work_raw(self, key: str) -> dict[str, Any] | None:
        """Get raw work JSON data by key from dump.

        Parameters
        ----------
        key : str
            Work key (e.g., "OL82563W" or "/works/OL82563W").

        Returns
        -------
        dict[str, Any] | None
            Raw work JSON data if found, None otherwise.
        """
        try:
            with get_session(self._engine) as session:
                # Normalize key (ensure it has /works/ prefix for DB lookup)
                if not key.startswith("/works/"):
                    normalized_key = f"/works/{key.replace('works/', '')}"
                else:
                    normalized_key = key

                stmt = select(OpenLibraryWork.data).where(
                    OpenLibraryWork.key == normalized_key
                )
                result = session.exec(stmt).first()
                return result if result else None
        except OperationalError:
            logger.exception("Database error getting work data for %s", key)
            return None
        except Exception:
            logger.exception("Unexpected error getting work data for %s", key)
            return None
