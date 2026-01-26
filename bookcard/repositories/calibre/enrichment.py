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

"""Book enrichment helpers.

This module centralizes multi-query "fanout" for adding full metadata to a list
of `BookWithRelations`.
"""

from __future__ import annotations

import json
from functools import cache
from typing import TYPE_CHECKING, Any, TypedDict, cast

from sqlalchemy import func
from sqlalchemy import select as sa_select
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from sqlalchemy.sql.elements import ColumnElement
    from sqlalchemy.sql.schema import Table
    from sqlalchemy.sql.selectable import CTE, Subquery
    from sqlmodel import Session

from bookcard.models.core import (
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.models.media import Data
from bookcard.repositories.models import BookWithFullRelations, BookWithRelations


class _FullDetails(TypedDict):
    tags: list[str]
    tag_ids: list[int]
    author_ids: list[int]
    identifiers: list[dict[str, str]]
    description: str | None
    publisher: str | None
    publisher_id: int | None
    languages: list[str]
    language_ids: list[int]
    rating: int | None
    rating_id: int | None
    series_id: int | None


class BookEnrichmentService:
    """Build enriched `BookWithFullRelations` results from base book rows."""

    def __init__(self, calibre_db_path: Path | None = None) -> None:
        self._calibre_db_path = calibre_db_path

    @staticmethod
    def _json_loads_array(value: str | None) -> list:
        """Parse a JSON array payload, defaulting to empty list."""
        if not value:
            return []
        loaded = json.loads(value)
        if isinstance(loaded, list):
            return loaded
        return []

    @staticmethod
    def _empty_full_details() -> _FullDetails:
        """Create an empty full-details payload for a book."""
        return {
            "tags": [],
            "tag_ids": [],
            "author_ids": [],
            "identifiers": [],
            "description": None,
            "publisher": None,
            "publisher_id": None,
            "languages": [],
            "language_ids": [],
            "rating": None,
            "rating_id": None,
            "series_id": None,
        }

    @staticmethod
    @cache
    def _table(model: type[SQLModel]) -> Table:
        """Return the SQLAlchemy table for a SQLModel model."""
        return SQLModel.metadata.tables[model.__tablename__]

    @staticmethod
    @cache
    def _col(model: type[SQLModel], attr: str) -> ColumnElement[object]:
        """Return a SQLAlchemy column for a SQLModel model."""
        return BookEnrichmentService._table(model).c[attr]

    @staticmethod
    def _base_books_cte(book_ids: list[int]) -> CTE:
        book_id = BookEnrichmentService._col(Book, "id")
        return (
            sa_select(book_id.label("book_id"))
            .where(book_id.in_(book_ids))
            .cte("base_books")
        )

    @staticmethod
    def _tags_subquery(book_ids: list[int]) -> Subquery:
        link_book = BookEnrichmentService._col(BookTagLink, "book")
        link_tag = BookEnrichmentService._col(BookTagLink, "tag")
        tag_id = BookEnrichmentService._col(Tag, "id")
        tag_name = BookEnrichmentService._col(Tag, "name")
        return (
            sa_select(
                link_book.label("book_id"),
                func.json_group_array(
                    func.json_object("id", tag_id, "name", tag_name)
                ).label("tags_json"),
            )
            .select_from(BookTagLink)
            .join(Tag, link_tag == tag_id)
            .where(link_book.in_(book_ids))
            .group_by(link_book)
            .subquery()
        )

    @staticmethod
    def _author_ids_subquery(book_ids: list[int]) -> Subquery:
        link_book = BookEnrichmentService._col(BookAuthorLink, "book")
        link_author = BookEnrichmentService._col(BookAuthorLink, "author")
        return (
            sa_select(
                link_book.label("book_id"),
                func.json_group_array(link_author).label("author_ids_json"),
            )
            .select_from(BookAuthorLink)
            .where(
                link_book.in_(book_ids),
                link_author.is_not(None),
            )
            .group_by(link_book)
            .subquery()
        )

    @staticmethod
    def _identifiers_subquery(book_ids: list[int]) -> Subquery:
        ident_book = BookEnrichmentService._col(Identifier, "book")
        ident_type = BookEnrichmentService._col(Identifier, "type")
        ident_val = BookEnrichmentService._col(Identifier, "val")
        return (
            sa_select(
                ident_book.label("book_id"),
                func.json_group_array(
                    func.json_object(
                        "type",
                        ident_type,
                        "val",
                        ident_val,
                    )
                ).label("identifiers_json"),
            )
            .select_from(Identifier)
            .where(ident_book.in_(book_ids))
            .group_by(ident_book)
            .subquery()
        )

    @staticmethod
    def _languages_subquery(book_ids: list[int]) -> Subquery:
        link_book = BookEnrichmentService._col(BookLanguageLink, "book")
        link_lang_code = BookEnrichmentService._col(BookLanguageLink, "lang_code")
        lang_id = BookEnrichmentService._col(Language, "id")
        lang_code = BookEnrichmentService._col(Language, "lang_code")
        return (
            sa_select(
                link_book.label("book_id"),
                func.json_group_array(
                    func.json_object("id", lang_id, "code", lang_code)
                ).label("languages_json"),
            )
            .select_from(BookLanguageLink)
            .join(Language, lang_id == link_lang_code)
            .where(link_book.in_(book_ids))
            .group_by(link_book)
            .subquery()
        )

    @staticmethod
    def _publisher_subquery(book_ids: list[int]) -> Subquery:
        link_book = BookEnrichmentService._col(BookPublisherLink, "book")
        link_publisher = BookEnrichmentService._col(BookPublisherLink, "publisher")
        publisher_id = BookEnrichmentService._col(Publisher, "id")
        publisher_name = BookEnrichmentService._col(Publisher, "name")
        return (
            sa_select(
                link_book.label("book_id"),
                func.max(publisher_id).label("publisher_id"),
                func.max(publisher_name).label("publisher_name"),
            )
            .select_from(BookPublisherLink)
            .join(Publisher, link_publisher == publisher_id)
            .where(link_book.in_(book_ids))
            .group_by(link_book)
            .subquery()
        )

    @staticmethod
    def _rating_subquery(book_ids: list[int]) -> Subquery:
        link_book = BookEnrichmentService._col(BookRatingLink, "book")
        link_rating = BookEnrichmentService._col(BookRatingLink, "rating")
        rating_id = BookEnrichmentService._col(Rating, "id")
        rating_value = BookEnrichmentService._col(Rating, "rating")
        return (
            sa_select(
                link_book.label("book_id"),
                func.max(rating_id).label("rating_id"),
                func.max(rating_value).label("rating_value"),
            )
            .select_from(BookRatingLink)
            .join(Rating, link_rating == rating_id)
            .where(link_book.in_(book_ids))
            .group_by(link_book)
            .subquery()
        )

    @staticmethod
    def _series_subquery(book_ids: list[int]) -> Subquery:
        link_book = BookEnrichmentService._col(BookSeriesLink, "book")
        link_series = BookEnrichmentService._col(BookSeriesLink, "series")
        series_id = BookEnrichmentService._col(Series, "id")
        return (
            sa_select(
                link_book.label("book_id"),
                func.max(series_id).label("series_id"),
            )
            .select_from(BookSeriesLink)
            .join(Series, link_series == series_id)
            .where(link_book.in_(book_ids))
            .group_by(link_book)
            .subquery()
        )

    @staticmethod
    def _description_subquery(book_ids: list[int]) -> Subquery:
        comment_book = BookEnrichmentService._col(Comment, "book")
        comment_text = BookEnrichmentService._col(Comment, "text")
        return (
            sa_select(
                comment_book.label("book_id"),
                func.max(comment_text).label("description"),
            )
            .select_from(Comment)
            .where(comment_book.in_(book_ids))
            .group_by(comment_book)
            .subquery()
        )

    def _parse_full_details_mapping(
        self, row: Mapping[str, object]
    ) -> tuple[int, _FullDetails]:
        book_id_obj = row.get("book_id")
        if not isinstance(book_id_obj, int):
            msg = "Expected 'book_id' to be an int"
            raise TypeError(msg)
        book_id = book_id_obj
        details = self._empty_full_details()

        tags_json = row.get("tags_json")
        self._parse_tags_into(
            details, tags_json if isinstance(tags_json, str) else None
        )

        author_ids_json = row.get("author_ids_json")
        self._parse_author_ids_into(
            details, author_ids_json if isinstance(author_ids_json, str) else None
        )

        identifiers_json = row.get("identifiers_json")
        self._parse_identifiers_into(
            details, identifiers_json if isinstance(identifiers_json, str) else None
        )

        languages_json = row.get("languages_json")
        self._parse_languages_into(
            details, languages_json if isinstance(languages_json, str) else None
        )

        self._parse_scalars_into(
            details,
            publisher_name=row.get("publisher_name"),
            publisher_id=row.get("publisher_id"),
            rating_value=row.get("rating_value"),
            rating_id=row.get("rating_id"),
            series_id=row.get("series_id"),
            description=row.get("description"),
        )

        return book_id, details

    def _parse_tags_into(self, details: _FullDetails, tags_json: str | None) -> None:
        tags_payload = self._json_loads_array(tags_json)
        for item in tags_payload:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if isinstance(name, str):
                details["tags"].append(name)
            tag_id = item.get("id")
            if isinstance(tag_id, int):
                details["tag_ids"].append(tag_id)

    def _parse_author_ids_into(
        self, details: _FullDetails, author_ids_json: str | None
    ) -> None:
        author_ids_payload = self._json_loads_array(author_ids_json)
        details["author_ids"] = [v for v in author_ids_payload if isinstance(v, int)]

    def _parse_identifiers_into(
        self, details: _FullDetails, identifiers_json: str | None
    ) -> None:
        identifiers_payload = self._json_loads_array(identifiers_json)
        for item in identifiers_payload:
            if not isinstance(item, dict):
                continue
            t = item.get("type")
            v = item.get("val")
            if isinstance(t, str) and isinstance(v, str):
                details["identifiers"].append({"type": t, "val": v})

    def _parse_languages_into(
        self, details: _FullDetails, languages_json: str | None
    ) -> None:
        languages_payload = self._json_loads_array(languages_json)
        for item in languages_payload:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            if isinstance(code, str):
                details["languages"].append(code)
            lang_id = item.get("id")
            if isinstance(lang_id, int):
                details["language_ids"].append(lang_id)

    @staticmethod
    def _parse_scalars_into(
        details: _FullDetails,
        *,
        publisher_name: object,
        publisher_id: object,
        rating_value: object,
        rating_id: object,
        series_id: object,
        description: object,
    ) -> None:
        details["publisher"] = (
            publisher_name if isinstance(publisher_name, str) else None
        )
        details["publisher_id"] = (
            publisher_id if isinstance(publisher_id, int) else None
        )
        details["rating"] = rating_value if isinstance(rating_value, int) else None
        details["rating_id"] = rating_id if isinstance(rating_id, int) else None
        details["series_id"] = series_id if isinstance(series_id, int) else None
        details["description"] = description if isinstance(description, str) else None

    def _fetch_full_details_maps(
        self,
        session: Session,
        book_ids: list[int],
    ) -> dict[int, _FullDetails]:
        """Fetch all non-format enrichment details in one query."""
        base_books = self._base_books_cte(book_ids)
        tags_subq = self._tags_subquery(book_ids)
        author_ids_subq = self._author_ids_subquery(book_ids)
        identifiers_subq = self._identifiers_subquery(book_ids)
        languages_subq = self._languages_subquery(book_ids)
        publisher_subq = self._publisher_subquery(book_ids)
        rating_subq = self._rating_subquery(book_ids)
        series_subq = self._series_subquery(book_ids)
        description_subq = self._description_subquery(book_ids)

        stmt = (
            sa_select(
                base_books.c.book_id,
                func.coalesce(tags_subq.c.tags_json, "[]").label("tags_json"),
                func.coalesce(author_ids_subq.c.author_ids_json, "[]").label(
                    "author_ids_json"
                ),
                func.coalesce(identifiers_subq.c.identifiers_json, "[]").label(
                    "identifiers_json"
                ),
                func.coalesce(languages_subq.c.languages_json, "[]").label(
                    "languages_json"
                ),
                publisher_subq.c.publisher_name,
                publisher_subq.c.publisher_id,
                rating_subq.c.rating_value,
                rating_subq.c.rating_id,
                series_subq.c.series_id,
                description_subq.c.description,
            )
            .select_from(base_books)
            .outerjoin(tags_subq, tags_subq.c.book_id == base_books.c.book_id)
            .outerjoin(
                author_ids_subq, author_ids_subq.c.book_id == base_books.c.book_id
            )
            .outerjoin(
                identifiers_subq, identifiers_subq.c.book_id == base_books.c.book_id
            )
            .outerjoin(languages_subq, languages_subq.c.book_id == base_books.c.book_id)
            .outerjoin(publisher_subq, publisher_subq.c.book_id == base_books.c.book_id)
            .outerjoin(rating_subq, rating_subq.c.book_id == base_books.c.book_id)
            .outerjoin(series_subq, series_subq.c.book_id == base_books.c.book_id)
            .outerjoin(
                description_subq, description_subq.c.book_id == base_books.c.book_id
            )
        )

        details: dict[int, _FullDetails] = {}
        for row in session.exec(cast("Any", stmt)).mappings().all():
            book_id, parsed = self._parse_full_details_mapping(row)
            details[book_id] = parsed
        return details

    def enrich_books_with_full_details(
        self,
        session: Session,
        books: list[BookWithRelations],
    ) -> list[BookWithFullRelations]:
        """Enrich a list of `BookWithRelations` with full details.

        Parameters
        ----------
        session : Session
            Database session.
        books : list[BookWithRelations]
            Base books.

        Returns
        -------
        list[BookWithFullRelations]
            Enriched books.
        """
        if not books:
            return []

        book_ids = [b.book.id for b in books if b.book.id is not None]
        if not book_ids:
            return []

        details_map = self._fetch_full_details_maps(session, book_ids)
        formats_map = self._fetch_formats_map(session, book_ids)

        enriched: list[BookWithFullRelations] = []
        for base in books:
            book_id = base.book.id
            if book_id is None:
                continue

            details = details_map.get(book_id) or self._empty_full_details()

            enriched.append(
                BookWithFullRelations(
                    book=base.book,
                    authors=base.authors,
                    author_ids=details["author_ids"],
                    series=base.series,
                    series_id=details["series_id"],
                    tags=details["tags"],
                    tag_ids=details["tag_ids"],
                    identifiers=details["identifiers"],
                    description=details["description"],
                    publisher=details["publisher"],
                    publisher_id=details["publisher_id"],
                    languages=details["languages"],
                    language_ids=details["language_ids"],
                    rating=details["rating"],
                    rating_id=details["rating_id"],
                    formats=formats_map.get(book_id, []),
                )
            )

        return enriched

    def enrich_books_for_list(
        self,
        session: Session,
        books: list[BookWithRelations],
    ) -> None:
        """Populate list-level metadata on `BookWithRelations`.

        Parameters
        ----------
        session : Session
            Database session.
        books : list[BookWithRelations]
            Books to enrich in-place.
        """
        book_ids = [b.book.id for b in books if b.book.id is not None]
        if not book_ids:
            return

        details_map = self._fetch_full_details_maps(session, book_ids)
        for b in books:
            book_id = b.book.id
            if book_id is None:
                continue
            details = details_map.get(book_id) or self._empty_full_details()
            b.series_id = details["series_id"]
            b.publisher = details["publisher"]
            b.publisher_id = details["publisher_id"]
            b.tags = details["tags"]
            b.tag_ids = details["tag_ids"]
            b.author_ids = details["author_ids"]

    def fetch_formats_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[dict[str, str | int]]]:
        """Fetch formats map for given book IDs.

        Parameters
        ----------
        session : Session
            Database session.
        book_ids : list[int]
            Book IDs to fetch formats for.

        Returns
        -------
        dict[int, list[dict[str, str | int]]]
            Mapping of book ID to list of format dictionaries.
        """
        return self._fetch_formats_map(session, book_ids)

    def _fetch_formats_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[dict[str, str | int]]]:
        data_book = self._col(Data, "book")
        data_format = self._col(Data, "format")
        data_size = self._col(Data, "uncompressed_size")
        data_name = self._col(Data, "name")
        book_id = self._col(Book, "id")
        book_path = self._col(Book, "path")
        formats_stmt = (
            sa_select(
                data_book,
                data_format,
                data_size,
                data_name,
                book_path,
            )
            .select_from(Data)
            .join(Book, data_book == book_id)
            .where(data_book.in_(book_ids))
            .order_by(data_book, data_format)
        )
        formats_map: dict[int, list[dict[str, str | int]]] = {}

        library_root = None
        if self._calibre_db_path:
            if self._calibre_db_path.is_dir():
                library_root = self._calibre_db_path
            else:
                library_root = self._calibre_db_path.parent

        for bid, fmt, size, name, path in session.exec(cast("Any", formats_stmt)).all():
            if self._validate_format_exists(library_root, path, fmt, name, bid):
                formats_map.setdefault(bid, []).append({
                    "format": fmt,
                    "size": size,
                    "name": name or "",
                })
        return formats_map

    def _validate_format_exists(
        self,
        library_root: Path | None,
        book_path: str | None,
        fmt: str,
        name: str | None,
        book_id: int,
    ) -> bool:
        """Check if format file exists on disk."""
        if not library_root or not book_path:
            return True  # Cannot validate, assume exists (or should we assume not?)
            # Existing behavior was to trust DB. If we can't check, trust DB.

        book_dir = library_root / book_path
        format_lower = fmt.lower()

        # 1. Check with stored name
        file_name = name or f"{book_id}"
        candidate = book_dir / f"{file_name}.{format_lower}"
        if candidate.exists():
            return True

        # 2. Check with book ID
        candidate = book_dir / f"{book_id}.{format_lower}"
        if candidate.exists():
            return True

        # 3. Check directory scan
        if book_dir.exists():
            for file_in_dir in book_dir.iterdir():
                if (
                    file_in_dir.is_file()
                    and file_in_dir.suffix.lower() == f".{format_lower}"
                ):
                    return True

        return False
