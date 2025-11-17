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

"""Base class for metadata import format strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fundamental.api.schemas.books import BookUpdate


class MetadataImporter(ABC):
    """Abstract base class for metadata import format strategies.

    Each format (OPF, YAML) implements this interface to provide
    format-specific metadata import functionality.

    Follows Strategy pattern and Open/Closed Principle, allowing new formats
    to be added without modifying existing code.
    """

    @abstractmethod
    def can_handle(self, format_type: str) -> bool:
        """Check if this importer can handle the given format.

        Parameters
        ----------
        format_type : str
            Format type identifier (e.g., 'opf', 'yaml').

        Returns
        -------
        bool
            True if this importer can handle the format.
        """

    @abstractmethod
    def import_metadata(self, content: str) -> BookUpdate:
        """Import book metadata from content string.

        Parameters
        ----------
        content : str
            File content as string.

        Returns
        -------
        BookUpdate
            Book update object ready for form application.

        Raises
        ------
        ValueError
            If import fails due to missing dependencies or invalid data.
        """
