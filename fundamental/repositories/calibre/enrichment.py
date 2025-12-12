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

from sqlmodel import Session, select

from fundamental.models.core import (
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
from fundamental.models.media import Data
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations


class BookEnrichmentService:
    """Build enriched `BookWithFullRelations` results from base book rows."""

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

        tags_map = self._fetch_tags_map(session, book_ids)
        identifiers_map = self._fetch_identifiers_map(session, book_ids)
        descriptions_map = self._fetch_descriptions_map(session, book_ids)
        publishers_map = self._fetch_publishers_map(session, book_ids)
        languages_map = self._fetch_languages_map(session, book_ids)
        ratings_map = self._fetch_ratings_map(session, book_ids)
        formats_map = self._fetch_formats_map(session, book_ids)
        series_ids_map = self._fetch_series_ids_map(session, book_ids)

        enriched: list[BookWithFullRelations] = []
        for base in books:
            book_id = base.book.id
            if book_id is None:
                continue

            publisher_name, publisher_id = publishers_map.get(book_id, (None, None))
            language_codes, language_ids = languages_map.get(book_id, ([], []))
            rating_value, rating_id = ratings_map.get(book_id, (None, None))

            enriched.append(
                BookWithFullRelations(
                    book=base.book,
                    authors=base.authors,
                    series=base.series,
                    series_id=series_ids_map.get(book_id),
                    tags=tags_map.get(book_id, []),
                    identifiers=identifiers_map.get(book_id, []),
                    description=descriptions_map.get(book_id),
                    publisher=publisher_name,
                    publisher_id=publisher_id,
                    languages=language_codes,
                    language_ids=language_ids,
                    rating=rating_value,
                    rating_id=rating_id,
                    formats=formats_map.get(book_id, []),
                )
            )

        return enriched

    def fetch_formats_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[dict[str, str | int]]]:
        """Fetch formats map for given book IDs."""
        return self._fetch_formats_map(session, book_ids)

    def _fetch_tags_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[str]]:
        tags_stmt = (
            select(BookTagLink.book, Tag.name)
            .join(Tag, BookTagLink.tag == Tag.id)
            .where(BookTagLink.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(BookTagLink.book, BookTagLink.id)
        )
        tags_map: dict[int, list[str]] = {}
        for book_id, tag_name in session.exec(tags_stmt).all():
            tags_map.setdefault(book_id, []).append(tag_name)
        return tags_map

    def _fetch_identifiers_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[dict[str, str]]]:
        identifiers_stmt = (
            select(Identifier.book, Identifier.type, Identifier.val)
            .where(Identifier.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(Identifier.book, Identifier.id)
        )
        identifiers_map: dict[int, list[dict[str, str]]] = {}
        for book_id, ident_type, ident_val in session.exec(identifiers_stmt).all():
            identifiers_map.setdefault(book_id, []).append({
                "type": ident_type,
                "val": ident_val,
            })
        return identifiers_map

    def _fetch_descriptions_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, str | None]:
        comments_stmt = select(Comment.book, Comment.text).where(
            Comment.book.in_(book_ids)  # type: ignore[attr-defined]
        )
        return dict(session.exec(comments_stmt).all())

    def _fetch_publishers_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, tuple[str | None, int | None]]:
        publishers_stmt = (
            select(BookPublisherLink.book, Publisher.name, Publisher.id)
            .join(Publisher, BookPublisherLink.publisher == Publisher.id)
            .where(BookPublisherLink.book.in_(book_ids))  # type: ignore[attr-defined]
        )
        publishers_map: dict[int, tuple[str | None, int | None]] = {}
        for book_id, pub_name, pub_id in session.exec(publishers_stmt).all():
            publishers_map[book_id] = (pub_name, pub_id)
        return publishers_map

    def _fetch_languages_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, tuple[list[str], list[int]]]:
        languages_stmt = (
            select(BookLanguageLink.book, Language.lang_code, Language.id)
            .join(Language, Language.id == BookLanguageLink.lang_code)
            .where(BookLanguageLink.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(BookLanguageLink.book, BookLanguageLink.item_order)
        )
        languages_map: dict[int, tuple[list[str], list[int]]] = {}
        for book_id, lang_code, lang_id in session.exec(languages_stmt).all():
            if book_id not in languages_map:
                languages_map[book_id] = ([], [])
            languages_map[book_id][0].append(lang_code)
            if lang_id is not None:
                languages_map[book_id][1].append(lang_id)
        return languages_map

    def _fetch_ratings_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, tuple[int | None, int | None]]:
        ratings_stmt = (
            select(BookRatingLink.book, Rating.rating, Rating.id)
            .join(Rating, BookRatingLink.rating == Rating.id)
            .where(BookRatingLink.book.in_(book_ids))  # type: ignore[attr-defined]
        )
        ratings_map: dict[int, tuple[int | None, int | None]] = {}
        for book_id, rating, rating_id in session.exec(ratings_stmt).all():
            ratings_map[book_id] = (rating, rating_id)
        return ratings_map

    def _fetch_formats_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, list[dict[str, str | int]]]:
        formats_stmt = (
            select(Data.book, Data.format, Data.uncompressed_size, Data.name)
            .where(Data.book.in_(book_ids))  # type: ignore[attr-defined]
            .order_by(Data.book, Data.format)
        )
        formats_map: dict[int, list[dict[str, str | int]]] = {}
        for book_id, fmt, size, name in session.exec(formats_stmt).all():
            formats_map.setdefault(book_id, []).append({
                "format": fmt,
                "size": size,
                "name": name or "",
            })
        return formats_map

    def _fetch_series_ids_map(
        self, session: Session, book_ids: list[int]
    ) -> dict[int, int | None]:
        series_ids_stmt = (
            select(BookSeriesLink.book, Series.id)
            .join(Series, BookSeriesLink.series == Series.id)
            .where(BookSeriesLink.book.in_(book_ids))  # type: ignore[attr-defined]
        )
        return dict(session.exec(series_ids_stmt).all())
