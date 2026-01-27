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

"""Conversion repository for managing BookConversion records.

Handles database operations for conversion history,
following SRP by focusing solely on conversion record persistence.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from bookcard.models.conversion import (
    BookConversion,
    ConversionStatus,
)

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)


class ConversionRepository:
    """Repository for managing BookConversion records.

    Handles all database operations related to conversion history,
    including finding existing conversions and saving new ones.

    Parameters
    ----------
    session : Session
        Database session.
    """

    def __init__(self, session: Session) -> None:
        """Initialize conversion repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def find_existing(
        self,
        book_id: int,
        original_format: str,
        target_format: str,
        status: ConversionStatus | None = None,
    ) -> BookConversion | None:
        """Find existing conversion record.

        Parameters
        ----------
        book_id : int
            Book ID.
        original_format : str
            Source format.
        target_format : str
            Target format.
        status : ConversionStatus | None
            Optional status filter (default: None, finds any status).

        Returns
        -------
        BookConversion | None
            Existing conversion if found, None otherwise.
        """
        stmt = (
            select(BookConversion)
            .where(BookConversion.book_id == book_id)
            .where(BookConversion.original_format == original_format.upper())
            .where(BookConversion.target_format == target_format.upper())
        )
        if status:
            stmt = stmt.where(BookConversion.status == status)
        return self._session.exec(stmt).first()

    def save(self, conversion: BookConversion) -> BookConversion:
        """Save or update a conversion record.

        If a record already exists for the same book_id, original_format,
        and target_format combination, it will be updated instead of
        creating a new one.

        Parameters
        ----------
        conversion : BookConversion
            Conversion record to save.

        Returns
        -------
        BookConversion
            Saved conversion record.
        """
        # Check for existing conversion record (any status)
        existing = self.find_existing(
            book_id=conversion.book_id,
            original_format=conversion.original_format,
            target_format=conversion.target_format,
        )

        if existing:
            # Update existing record
            old_status = existing.status
            existing.original_file_path = conversion.original_file_path
            existing.converted_file_path = conversion.converted_file_path
            existing.user_id = conversion.user_id
            existing.conversion_method = conversion.conversion_method
            existing.original_backed_up = conversion.original_backed_up
            existing.status = conversion.status
            existing.error_message = conversion.error_message
            existing.completed_at = conversion.completed_at

            # Only update created_at if this is a new attempt
            # (status changed from FAILED to non-FAILED)
            if (
                old_status == ConversionStatus.FAILED
                and conversion.status != ConversionStatus.FAILED
            ):
                existing.created_at = conversion.created_at

            self._session.add(existing)
            self._session.flush()
            return existing

        # Create new record
        self._session.add(conversion)
        try:
            self._session.flush()
        except IntegrityError:
            # Handle race condition: another process may have created the record
            # between our check and the insert
            self._session.rollback()
            logger.warning(
                "Duplicate conversion record detected, fetching existing: "
                "book_id=%d, %s -> %s",
                conversion.book_id,
                conversion.original_format,
                conversion.target_format,
            )
            # Fetch the existing record
            existing = self.find_existing(
                book_id=conversion.book_id,
                original_format=conversion.original_format,
                target_format=conversion.target_format,
            )
            if existing:
                # Update it with new values
                existing.original_file_path = conversion.original_file_path
                existing.converted_file_path = conversion.converted_file_path
                existing.user_id = conversion.user_id
                existing.conversion_method = conversion.conversion_method
                existing.original_backed_up = conversion.original_backed_up
                existing.status = conversion.status
                existing.error_message = conversion.error_message
                existing.completed_at = conversion.completed_at
                self._session.add(existing)
                self._session.flush()
                return existing
            # If still not found, re-raise the original error
            raise

        return conversion

    def _now(self) -> "datetime":
        """Get current UTC datetime.

        Returns
        -------
        datetime
            Current UTC datetime.
        """
        from datetime import UTC, datetime

        return datetime.now(UTC)
