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

"""Read-model composition for book responses.

This module implements a CQRS-style read-model service that enriches base
book DTOs with optional computed fields required by list/detail UIs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.api.schemas.books import BookRead


class BookReadModelService:
    """Service for enriching book API DTOs with optional includes.

    Parameters
    ----------
    session : Session
        Active SQLModel session used to build user-specific read models.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize the read-model service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        # Import here to avoid eager application imports at module import time
        # (helps prevent cycles during startup and in tests).
        from bookcard.services.book_reading_summary_query_service import (
            BookReadingSummaryQueryService,
        )

        self._summary_query = BookReadingSummaryQueryService(session)

    def apply_includes(
        self,
        *,
        book_reads: list[BookRead],
        include: str | None,
        user_id: int | None,
        library_id: int,
    ) -> list[BookRead]:
        """Apply optional includes to a list of books.

        Parameters
        ----------
        book_reads : list[BookRead]
            Base book DTOs to enrich.
        include : str | None
            Comma-separated include list (e.g., ``"reading_summary"``).
        user_id : int | None
            Current user ID. If None, user-specific includes are skipped.
        library_id : int
            Active library ID (used for user-specific includes).

        Returns
        -------
        list[BookRead]
            The same list instance, enriched in-place for efficiency.
        """
        includes = _parse_include(include)
        if "reading_summary" not in includes or user_id is None:
            return book_reads

        summaries = self._summary_query.get_summaries(
            user_id=user_id,
            library_id=library_id,
            book_ids=[b.id for b in book_reads],
        )
        for book in book_reads:
            book.reading_summary = summaries.get(book.id)

        return book_reads

    def apply_includes_to_one(
        self,
        *,
        book_read: BookRead,
        include: str | None,
        user_id: int | None,
        library_id: int,
    ) -> BookRead:
        """Apply optional includes to a single book.

        Parameters
        ----------
        book_read : BookRead
            Base book DTO to enrich.
        include : str | None
            Comma-separated include list (e.g., ``"reading_summary"``).
        user_id : int | None
            Current user ID. If None, user-specific includes are skipped.
        library_id : int
            Active library ID (used for user-specific includes).

        Returns
        -------
        BookRead
            The same object instance, enriched in-place for efficiency.
        """
        self.apply_includes(
            book_reads=[book_read],
            include=include,
            user_id=user_id,
            library_id=library_id,
        )
        return book_read


def _parse_include(include: str | None) -> set[str]:
    """Parse comma-separated include query parameter.

    Parameters
    ----------
    include : str | None
        Raw include parameter value.

    Returns
    -------
    set[str]
        Normalized include tokens.
    """
    if include is None:
        return set()
    return {token.strip() for token in include.split(",") if token.strip()}
