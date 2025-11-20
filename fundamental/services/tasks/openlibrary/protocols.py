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

"""Protocols for dependency injection in OpenLibrary dump ingestion.

These protocols define interfaces specific to OpenLibrary dump ingestion
that allow for dependency injection and improved testability following
the Dependency Inversion Principle.
"""

from typing import Any, Protocol


class DatabaseRepository(Protocol):
    """Protocol for database operations.

    Abstracts database operations to allow for different implementations
    and improved testability.
    """

    def bulk_save(self, objects: list[Any]) -> None:
        """Bulk save objects to database.

        Parameters
        ----------
        objects : list[Any]
            List of model objects to save.
        """
        ...

    def commit(self) -> None:
        """Commit current transaction."""
        ...

    def rollback(self) -> None:
        """Rollback current transaction."""
        ...

    def truncate_tables(self, table_names: list[str]) -> None:
        """Truncate specified tables.

        Parameters
        ----------
        table_names : list[str]
            List of table names to truncate.
        """
        ...


__all__ = ["DatabaseRepository"]
