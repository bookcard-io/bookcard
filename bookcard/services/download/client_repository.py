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

"""Repository for download clients."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from bookcard.models.pvr import DownloadClientDefinition

if TYPE_CHECKING:
    from sqlmodel import Session


class DownloadClientRepository(ABC):
    """Abstract repository for download client persistence."""

    @abstractmethod
    def get_enabled_clients(self) -> list[DownloadClientDefinition]:
        """Get all enabled download clients.

        Returns
        -------
        list[DownloadClientDefinition]
            List of enabled download clients.
        """
        raise NotImplementedError


class SQLModelDownloadClientRepository(DownloadClientRepository):
    """SQLModel-based implementation of DownloadClientRepository."""

    def __init__(self, session: "Session") -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def get_enabled_clients(self) -> list[DownloadClientDefinition]:
        """Get all enabled download clients."""
        stmt = select(DownloadClientDefinition).where(
            DownloadClientDefinition.enabled == True  # noqa: E712
        )
        return list(self._session.exec(stmt).all())
