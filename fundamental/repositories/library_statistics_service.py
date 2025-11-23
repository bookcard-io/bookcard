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

"""Library statistics service for calculating library statistics.

This module handles statistics calculation following SRP.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, select

from fundamental.models.core import (
    Book,
    BookAuthorLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
)
from fundamental.models.media import Data
from fundamental.repositories.interfaces import ILibraryStatisticsService


class LibraryStatisticsService(ILibraryStatisticsService):
    """Service for calculating library statistics.

    Handles statistics calculation following SRP.
    """

    def get_statistics(self, session: Session) -> dict[str, int | float]:
        """Get library statistics.

        Parameters
        ----------
        session : Session
            Database session.

        Returns
        -------
        dict[str, int | float]
            Dictionary with statistics keys:
            - 'total_books': Total number of books
            - 'total_series': Total number of unique series
            - 'total_authors': Total number of unique authors
            - 'total_tags': Total number of unique tags
            - 'total_ratings': Total number of books with ratings
            - 'total_content_size': Total file size in bytes
        """
        # Count total books
        books_stmt = select(func.count(Book.id))
        total_books = session.exec(books_stmt).one() or 0

        # Count unique series (series that are linked to books)
        series_stmt = select(
            func.count(func.distinct(BookSeriesLink.series))
        ).select_from(BookSeriesLink)
        total_series = session.exec(series_stmt).one() or 0

        # Count unique authors (authors that are linked to books)
        authors_stmt = select(
            func.count(func.distinct(BookAuthorLink.author))
        ).select_from(BookAuthorLink)
        total_authors = session.exec(authors_stmt).one() or 0

        # Count unique tags (tags that are linked to books)
        tags_stmt = select(func.count(func.distinct(BookTagLink.tag))).select_from(
            BookTagLink
        )
        total_tags = session.exec(tags_stmt).one() or 0

        # Count books with ratings (books that have a rating link)
        ratings_stmt = select(
            func.count(func.distinct(BookRatingLink.book))
        ).select_from(BookRatingLink)
        total_ratings = session.exec(ratings_stmt).one() or 0

        # Sum total content size
        content_size_stmt = select(func.sum(Data.uncompressed_size))
        total_content_size = session.exec(content_size_stmt).one() or 0
        if total_content_size is None:
            total_content_size = 0

        return {
            "total_books": total_books,
            "total_series": total_series,
            "total_authors": total_authors,
            "total_tags": total_tags,
            "total_ratings": total_ratings,
            "total_content_size": int(total_content_size),
        }
