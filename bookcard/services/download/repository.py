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

"""Repository pattern for download items.

Follows DIP by abstracting persistence operations.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bookcard.models.pvr import DownloadItem

if TYPE_CHECKING:
    from sqlmodel import Session


class DownloadItemRepository(ABC):
    """Abstract repository for download item persistence.

    Follows Repository pattern to abstract database operations.
    """

    @abstractmethod
    def add(self, item: DownloadItem) -> None:
        """Add a new download item.

        Parameters
        ----------
        item : DownloadItem
            Download item to add.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, item_id: int) -> DownloadItem | None:
        """Get a download item by ID.

        Parameters
        ----------
        item_id : int
            Download item ID.

        Returns
        -------
        DownloadItem | None
            Download item if found, None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, item: DownloadItem) -> None:
        """Update an existing download item.

        Parameters
        ----------
        item : DownloadItem
            Download item to update.
        """
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        """Commit pending changes."""
        raise NotImplementedError

    @abstractmethod
    def refresh(self, item: DownloadItem) -> None:
        """Refresh item from database.

        Parameters
        ----------
        item : DownloadItem
            Item to refresh.
        """
        raise NotImplementedError


class SQLModelDownloadItemRepository(DownloadItemRepository):
    """SQLModel-based implementation of DownloadItemRepository."""

    def __init__(self, session: "Session") -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def add(self, item: DownloadItem) -> None:
        """Add a new download item."""
        self._session.add(item)

    def get(self, item_id: int) -> DownloadItem | None:
        """Get a download item by ID."""
        return self._session.get(DownloadItem, item_id)

    def update(self, item: DownloadItem) -> None:
        """Update an existing download item."""
        self._session.add(item)

    def commit(self) -> None:
        """Commit pending changes."""
        self._session.commit()

    def refresh(self, item: DownloadItem) -> None:
        """Refresh item from database."""
        self._session.refresh(item)
