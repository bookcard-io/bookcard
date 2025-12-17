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

"""OPF format exporter for book metadata."""

from __future__ import annotations

from bookcard.repositories.models import BookWithFullRelations  # noqa: TC001
from bookcard.services.metadata_export_utils import MetadataExportResult
from bookcard.services.metadata_exporters.base import MetadataExporter
from bookcard.services.opf_service import OpfService


class OpfExporter(MetadataExporter):
    """Exporter for OPF (Open Packaging Format) XML metadata.

    Follows SRP by focusing solely on OPF format export.
    Uses IOC by accepting OpfService as a dependency.
    """

    def __init__(self, opf_service: OpfService | None = None) -> None:
        """Initialize OPF exporter.

        Parameters
        ----------
        opf_service : OpfService | None
            OPF service instance. If None, creates a new instance.
        """
        self._opf_service = opf_service or OpfService()

    def can_handle(self, format_type: str) -> bool:
        """Check if this exporter can handle OPF format.

        Parameters
        ----------
        format_type : str
            Format type identifier.

        Returns
        -------
        bool
            True if format is 'opf'.
        """
        return format_type.lower() == "opf"

    def export(self, book_with_rels: BookWithFullRelations) -> MetadataExportResult:
        """Export metadata as OPF XML.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        MetadataExportResult
            OPF XML content, filename, and media type.
        """
        opf_result = self._opf_service.generate_opf(book_with_rels)
        return MetadataExportResult(
            content=opf_result.xml_content,
            filename=opf_result.filename,
            media_type="application/oebps-package+xml",
        )
