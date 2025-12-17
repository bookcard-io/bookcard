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

"""Service for exporting book metadata in various formats.

This service encapsulates the business logic for converting book metadata
into different formats: OPF (XML), JSON, and YAML.

Follows Strategy pattern with format-specific exporters, enabling easy
extension with new formats while maintaining SRP and Open/Closed Principle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.repositories.models import BookWithFullRelations  # noqa: TC001
from bookcard.services.metadata_exporters import (
    JsonExporter,
    MetadataExporter,
    OpfExporter,
    YamlExporter,
)
from bookcard.services.opf_service import OpfService

if TYPE_CHECKING:
    from bookcard.services.metadata_export_utils import MetadataExportResult


class MetadataExportService:
    """Service for exporting book metadata in various formats.

    Follows SRP by focusing solely on coordinating format exporters.
    Uses IOC by accepting exporters and OpfService as dependencies,
    allowing the service to be tested independently.
    Uses Strategy pattern with exporter registry to avoid if statements.
    Follows Open/Closed Principle by allowing new exporters to be added
    without modifying this service.
    """

    def __init__(
        self,
        opf_service: OpfService | None = None,
        exporters: list[MetadataExporter] | None = None,
    ) -> None:
        """Initialize the metadata export service.

        Parameters
        ----------
        opf_service : OpfService | None
            OPF service instance. If None, creates a new instance.
        exporters : list[MetadataExporter] | None
            List of format exporters. If None, uses default exporters.
        """
        opf_svc = opf_service or OpfService()
        # Strategy pattern: registry maps format names to exporter instances
        if exporters is None:
            self._exporters: list[MetadataExporter] = [
                OpfExporter(opf_service=opf_svc),
                JsonExporter(),
                YamlExporter(),
            ]
        else:
            self._exporters = exporters

    def export_metadata(
        self,
        book_with_rels: BookWithFullRelations,
        format_type: str = "opf",
    ) -> MetadataExportResult:
        """Export book metadata in the specified format.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.
        format_type : str
            Export format: 'opf', 'json', or 'yaml' (default: 'opf').

        Returns
        -------
        MetadataExportResult
            Generated metadata content, filename, and media type.

        Raises
        ------
        ValueError
            If format is unsupported.
        """
        format_lower = format_type.lower()

        # Find exporter that can handle this format
        exporter = next(
            (exp for exp in self._exporters if exp.can_handle(format_lower)),
            None,
        )

        if exporter is None:
            # Dynamically determine supported formats from available exporters
            supported_formats = set()
            test_formats = ["opf", "json", "yaml"]
            for exp in self._exporters:
                for fmt in test_formats:
                    if exp.can_handle(fmt):
                        supported_formats.add(fmt)
            supported = ", ".join(sorted(supported_formats))
            msg = f"Unsupported format: {format_type}. Supported formats: {supported}"
            raise ValueError(msg)

        return exporter.export(book_with_rels)
