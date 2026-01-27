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

"""YAML format exporter for book metadata."""

from __future__ import annotations

from bookcard.repositories.models import BookWithFullRelations  # noqa: TC001
from bookcard.services.metadata_builder import MetadataBuilder
from bookcard.services.metadata_export_utils import (
    FilenameGenerator,
    MetadataExportResult,
    MetadataSerializer,
)
from bookcard.services.metadata_exporters.base import MetadataExporter

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class YamlExporter(MetadataExporter):
    """Exporter for YAML format metadata.

    Follows SRP by focusing solely on YAML format export.
    """

    def can_handle(self, format_type: str) -> bool:
        """Check if this exporter can handle YAML format.

        Parameters
        ----------
        format_type : str
            Format type identifier.

        Returns
        -------
        bool
            True if format is 'yaml'.
        """
        return format_type.lower() == "yaml"

    def export(self, book_with_rels: BookWithFullRelations) -> MetadataExportResult:
        """Export metadata as YAML.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.

        Returns
        -------
        MetadataExportResult
            YAML content, filename, and media type.

        Raises
        ------
        ValueError
            If PyYAML is not installed.
        """
        if yaml is None:
            msg = "YAML export requires PyYAML. Install with: pip install pyyaml"
            raise ValueError(msg)

        structured_metadata = MetadataBuilder.build(book_with_rels)
        metadata_dict = MetadataSerializer.to_dict(structured_metadata)
        yaml_content = yaml.dump(
            metadata_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        filename = FilenameGenerator.generate(
            book_with_rels, book_with_rels.book, "yaml"
        )

        return MetadataExportResult(
            content=yaml_content,
            filename=filename,
            media_type="text/yaml",
        )
