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

"""Service for importing book metadata from various formats.

This service encapsulates the business logic for converting metadata files
into BookUpdate format. Supports OPF (XML), JSON, and YAML formats.

Follows Strategy pattern with format-specific importers, enabling easy
extension with new formats while maintaining SRP and Open/Closed Principle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.services.metadata_importers import (
    MetadataImporter,
    OpfImporter,
    YamlImporter,
)

if TYPE_CHECKING:
    from bookcard.api.schemas.books import BookUpdate


class MetadataImportService:
    """Service for importing book metadata from various formats.

    Follows SRP by focusing solely on coordinating format importers.
    Uses IOC by accepting importers as dependencies, allowing the service
    to be tested independently.
    Uses Strategy pattern with importer registry to avoid if statements.
    Follows Open/Closed Principle by allowing new importers to be added
    without modifying this service.
    """

    def __init__(
        self,
        importers: list[MetadataImporter] | None = None,
    ) -> None:
        """Initialize the metadata import service.

        Parameters
        ----------
        importers : list[MetadataImporter] | None
            List of format importers. If None, uses default importers.
        """
        # Strategy pattern: registry maps format names to importer instances
        if importers is None:
            self._importers: list[MetadataImporter] = [
                OpfImporter(),
                YamlImporter(),
            ]
        else:
            self._importers = importers

    def import_metadata(
        self,
        content: str,
        format_type: str,
    ) -> BookUpdate:
        """Import book metadata from content string in the specified format.

        Parameters
        ----------
        content : str
            File content as string.
        format_type : str
            Import format: 'opf', 'json', or 'yaml'.

        Returns
        -------
        BookUpdate
            Book update object ready for form application.

        Raises
        ------
        ValueError
            If format is unsupported or parsing fails.
        """
        format_lower = format_type.lower()

        # Find importer that can handle this format
        importer = next(
            (imp for imp in self._importers if imp.can_handle(format_lower)),
            None,
        )

        if importer is None:
            # Dynamically determine supported formats from available importers
            supported_formats = set()
            test_formats = ["opf", "json", "yaml", "yml"]
            for imp in self._importers:
                for fmt in test_formats:
                    if imp.can_handle(fmt):
                        supported_formats.add(fmt)
            supported = ", ".join(sorted(supported_formats))
            msg = f"Unsupported format: {format_type}. Supported formats: {supported}"
            raise ValueError(msg)

        return importer.import_metadata(content)
