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

"""Base class for metadata export format strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bookcard.repositories.models import BookWithFullRelations  # noqa: TC001

if TYPE_CHECKING:
    from bookcard.services.metadata_export_utils import MetadataExportResult


class MetadataExporter(ABC):
    """Abstract base class for metadata export format strategies.

    Each format (OPF, JSON, YAML) implements this interface to provide
    format-specific metadata export functionality.

    Follows Strategy pattern and Open/Closed Principle, allowing new formats
    to be added without modifying existing code.
    """

    @abstractmethod
    def can_handle(self, format_type: str) -> bool:
        """Check if this exporter can handle the given format.

        Parameters
        ----------
        format_type : str
            Format type identifier (e.g., 'opf', 'json', 'yaml').

        Returns
        -------
        bool
            True if this exporter can handle the format.
        """

    @abstractmethod
    def export(self, book_with_rels: BookWithFullRelations) -> MetadataExportResult:
        """Export book metadata in this exporter's format.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        MetadataExportResult
            Generated metadata content, filename, and media type.

        Raises
        ------
        ValueError
            If export fails due to missing dependencies or invalid data.
        """
