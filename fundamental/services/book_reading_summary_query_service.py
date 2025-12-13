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

"""Query service for denormalized reading summary used by book list UIs."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from fundamental.api.schemas.books import BookReadingSummary
from fundamental.models.reading import ReadingProgress, ReadStatus


class BookReadingSummaryQueryService:
    """Build reading summary read-models for books.

    This is a CQRS-style query service: it composes data from the reading domain
    (progress + status) into a lightweight view model used by list UIs.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize the query service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def get_summaries(
        self,
        user_id: int,
        library_id: int,
        book_ids: list[int],
    ) -> dict[int, BookReadingSummary]:
        """Return reading summaries for the given book IDs.

        Parameters
        ----------
        user_id : int
            User ID.
        library_id : int
            Library ID.
        book_ids : list[int]
            Book IDs to summarize.

        Returns
        -------
        dict[int, BookReadingSummary]
            Mapping of book_id to reading summary. Books with no status and no
            progress are omitted from the mapping.
        """
        if not book_ids:
            return {}

        unique_book_ids = list(dict.fromkeys(book_ids))

        status_stmt = (
            select(
                ReadStatus.book_id,
                ReadStatus.status,
                ReadStatus.updated_at,
            )
            .where(
                ReadStatus.user_id == user_id,
                ReadStatus.library_id == library_id,
                col(ReadStatus.book_id).in_(unique_book_ids),
            )
            .order_by(ReadStatus.book_id)
        )

        progress_stmt = (
            select(
                ReadingProgress.book_id,
                func.max(ReadingProgress.progress).label("max_progress"),
                func.max(ReadingProgress.updated_at).label("progress_updated_at"),
            )
            .where(
                ReadingProgress.user_id == user_id,
                ReadingProgress.library_id == library_id,
                col(ReadingProgress.book_id).in_(unique_book_ids),
            )
            .group_by(ReadingProgress.book_id)
        )

        status_rows = self._session.exec(status_stmt).all()
        progress_rows = self._session.exec(progress_stmt).all()

        by_book_id: dict[int, BookReadingSummary] = {}

        for book_id, status, status_updated_at in status_rows:
            by_book_id[int(book_id)] = BookReadingSummary(
                read_status=status.value if status is not None else None,
                max_progress=None,
                status_updated_at=_as_dt(status_updated_at),
                progress_updated_at=None,
            )

        for book_id, max_progress, progress_updated_at in progress_rows:
            bid = int(book_id)
            existing = by_book_id.get(bid)
            if existing is None:
                by_book_id[bid] = BookReadingSummary(
                    read_status=None,
                    max_progress=float(max_progress)
                    if max_progress is not None
                    else None,
                    status_updated_at=None,
                    progress_updated_at=_as_dt(progress_updated_at),
                )
            else:
                existing.max_progress = (
                    float(max_progress) if max_progress is not None else None
                )
                existing.progress_updated_at = _as_dt(progress_updated_at)

        # Drop empty summaries (no status and no progress)
        return {
            book_id: summary
            for book_id, summary in by_book_id.items()
            if summary.read_status is not None or summary.max_progress is not None
        }


def _as_dt(value: object) -> datetime | None:
    """Convert value to datetime when safe."""
    return value if isinstance(value, datetime) else None
