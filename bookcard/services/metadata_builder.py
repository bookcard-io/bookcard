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

"""Shared metadata builder utility.

This module provides a unified way to extract and structure book metadata
from BookWithFullRelations, eliminating DRY violations across services.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from bookcard.repositories.models import BookWithFullRelations  # noqa: TC001


@dataclass
class StructuredMetadata:
    """Structured representation of book metadata.

    Provides a unified data structure for all metadata fields,
    allowing different export formats to consume the same data.

    Attributes
    ----------
    id : int
        Book ID.
    title : str
        Book title.
    authors : list[str]
        List of author names.
    uuid : str
        Unique identifier.
    author_sort : str | None
        Sortable author name.
    publisher : str | None
        Publisher name.
    pubdate : str | None
        Publication date as ISO string.
    timestamp : str | None
        Timestamp as ISO string.
    description : str | None
        Book description.
    languages : list[str] | None
        List of language codes.
    identifiers : list[dict[str, str]] | None
        List of identifiers.
    series : str | None
        Series name.
    series_index : float | None
        Series position.
    tags : list[str] | None
        List of tags.
    rating : int | None
        Rating value.
    isbn : str | None
        ISBN identifier.
    formats : list[dict[str, str | int]] | None
        List of file formats.
    """

    id: int
    title: str
    authors: list[str]
    uuid: str
    author_sort: str | None = None
    publisher: str | None = None
    pubdate: str | None = None
    timestamp: str | None = None
    description: str | None = None
    languages: list[str] | None = None
    identifiers: list[dict[str, str]] | None = None
    series: str | None = None
    series_index: float | None = None
    tags: list[str] | None = None
    rating: int | None = None
    isbn: str | None = None
    formats: list[dict[str, str | int]] | None = None


class MetadataBuilder:
    """Builder for extracting structured metadata from book data.

    Follows SRP by focusing solely on metadata extraction and normalization.
    Eliminates DRY violations by providing a single source of truth for
    metadata extraction logic.
    """

    @staticmethod
    def build(book_with_rels: BookWithFullRelations) -> StructuredMetadata:
        """Build structured metadata from book data.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        StructuredMetadata
            Structured metadata representation.

        Raises
        ------
        ValueError
            If book ID is missing.
        """
        book = book_with_rels.book
        if book.id is None:
            msg = "Book must have an ID to build metadata"
            raise ValueError(msg)

        return StructuredMetadata(
            id=book.id,
            title=book.title,
            authors=book_with_rels.authors,
            uuid=book.uuid or f"calibre-book-{book.id}",
            author_sort=book.author_sort,
            publisher=book_with_rels.publisher,
            pubdate=MetadataBuilder._format_date(book.pubdate),
            timestamp=MetadataBuilder._format_timestamp(book.timestamp),
            description=book_with_rels.description,
            languages=book_with_rels.languages,
            identifiers=book_with_rels.identifiers,
            series=book_with_rels.series,
            series_index=book.series_index,
            tags=book_with_rels.tags,
            rating=book_with_rels.rating,
            isbn=book.isbn,
            formats=book_with_rels.formats,
        )

    @staticmethod
    def _format_date(date: datetime | None) -> str | None:
        """Format date as ISO string.

        Parameters
        ----------
        date : datetime | None
            Date to format.

        Returns
        -------
        str | None
            ISO formatted date string or None.
        """
        if date is None:
            return None
        if isinstance(date, datetime):
            return date.isoformat()
        return str(date)

    @staticmethod
    def _format_timestamp(timestamp: datetime | None) -> str | None:
        """Format timestamp as ISO string with UTC timezone.

        Parameters
        ----------
        timestamp : datetime | None
            Timestamp to format.

        Returns
        -------
        str | None
            ISO formatted timestamp string or None.
        """
        if timestamp is None:
            return None
        if isinstance(timestamp, datetime):
            return timestamp.astimezone(UTC).isoformat()
        return str(timestamp)
