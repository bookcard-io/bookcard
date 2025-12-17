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

"""Library scanning state tracking models.

Tracks scan history and status for each library.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class LibraryScanState(SQLModel, table=True):
    """Library scan state model.

    Tracks scan history and status for each library.
    Used to determine incremental vs full scans.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    library_id : int
        Foreign key to Library.
    last_scan_at : datetime | None
        Timestamp of last successful scan.
    scan_status : str
        Current scan status (e.g., "pending", "running", "completed", "failed").
    books_scanned : int
        Number of books scanned in last scan.
    authors_scanned : int
        Number of authors scanned in last scan.
    created_at : datetime
        Record creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "library_scan_states"

    id: int | None = Field(default=None, primary_key=True)
    library_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("libraries.id", ondelete="CASCADE"),
            unique=True,
            index=True,
        ),
    )
    last_scan_at: datetime | None = Field(default=None, index=True)
    scan_status: str = Field(default="pending", max_length=50, index=True)
    books_scanned: int = Field(default=0)
    authors_scanned: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )
