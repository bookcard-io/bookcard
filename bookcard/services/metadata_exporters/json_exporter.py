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

"""JSON format exporter for book metadata."""

from __future__ import annotations

import json

from bookcard.repositories.models import BookWithFullRelations  # noqa: TC001
from bookcard.services.metadata_builder import MetadataBuilder
from bookcard.services.metadata_export_utils import (
    FilenameGenerator,
    MetadataExportResult,
    MetadataSerializer,
)
from bookcard.services.metadata_exporters.base import MetadataExporter


class JsonExporter(MetadataExporter):
    """Exporter for JSON format metadata.

    Follows SRP by focusing solely on JSON format export.
    """

    def can_handle(self, format_type: str) -> bool:
        """Check if this exporter can handle JSON format.

        Parameters
        ----------
        format_type : str
            Format type identifier.

        Returns
        -------
        bool
            True if format is 'json'.
        """
        return format_type.lower() == "json"

    def export(self, book_with_rels: BookWithFullRelations) -> MetadataExportResult:
        """Export metadata as JSON.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        MetadataExportResult
            JSON content, filename, and media type.
        """
        structured_metadata = MetadataBuilder.build(book_with_rels)
        metadata_dict = MetadataSerializer.to_dict(structured_metadata)
        json_content = json.dumps(metadata_dict, indent=2, ensure_ascii=False)

        filename = FilenameGenerator.generate(
            book_with_rels, book_with_rels.book, "json"
        )

        return MetadataExportResult(
            content=json_content,
            filename=filename,
            media_type="application/json",
        )
