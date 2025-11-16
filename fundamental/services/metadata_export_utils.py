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

"""Utility functions for metadata export operations.

This module provides shared utilities for metadata export services,
following SOC by separating cross-cutting concerns like filename generation
and metadata serialization.
"""

from __future__ import annotations

from dataclasses import dataclass

from fundamental.models.core import Book  # noqa: TC001
from fundamental.repositories.models import BookWithFullRelations  # noqa: TC001
from fundamental.services.metadata_builder import StructuredMetadata  # noqa: TC001


@dataclass
class MetadataExportResult:
    """Result of metadata export generation.

    Attributes
    ----------
    content : str
        Generated metadata content as string.
    filename : str
        Suggested filename for the exported file.
    media_type : str
        MIME type for the content.
    """

    content: str
    filename: str
    media_type: str


class FilenameGenerator:
    """Utility for generating safe filenames from book metadata.

    Follows SRP by focusing solely on filename generation logic.
    Eliminates DRY violations by providing a single source of truth
    for filename generation across services.
    """

    @staticmethod
    def generate(
        book_with_rels: BookWithFullRelations,
        book: Book,
        extension: str,
    ) -> str:
        """Generate a safe filename for exported metadata files.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with relations containing author information.
        book : Book
            Book instance containing title and ID.
        extension : str
            File extension (without dot), e.g., 'opf', 'json', 'yaml'.

        Returns
        -------
        str
            Sanitized filename in format: "Author - Title.extension".

        Examples
        --------
        >>> filename = FilenameGenerator.generate(
        ...     book_with_rels,
        ...     book,
        ...     "opf",
        ... )
        >>> # Returns: "John Doe - My Book.opf"
        """
        authors_str = (
            ", ".join(book_with_rels.authors) if book_with_rels.authors else ""
        )
        safe_author = "".join(
            c for c in authors_str if c.isalnum() or c in (" ", "-", "_", ",")
        ).strip()
        if not safe_author:
            safe_author = "Unknown"

        safe_title = "".join(
            c for c in book.title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        if not safe_title:
            safe_title = f"book_{book.id}"

        return f"{safe_author} - {safe_title}.{extension}"


class MetadataSerializer:
    """Utility for serializing structured metadata to dictionary format.

    Follows SRP by focusing solely on metadata serialization logic.
    Provides a consistent way to convert StructuredMetadata to dictionaries
    for JSON/YAML export formats.
    """

    @staticmethod
    def to_dict(structured: StructuredMetadata) -> dict:
        """Convert structured metadata to dictionary, omitting None values.

        Parameters
        ----------
        structured : StructuredMetadata
            Structured metadata instance.

        Returns
        -------
        dict
            Dictionary containing non-None metadata fields.

        Examples
        --------
        >>> metadata_dict = MetadataSerializer.to_dict(
        ...     structured_metadata
        ... )
        >>> # Returns: {"id": 1, "title": "Book", "authors": ["Author"], ...}
        """
        metadata: dict = {
            "id": structured.id,
            "title": structured.title,
            "authors": structured.authors,
            "uuid": structured.uuid,
        }

        MetadataSerializer._add_optional_string_fields(metadata, structured)
        MetadataSerializer._add_optional_list_fields(metadata, structured)
        MetadataSerializer._add_series_fields(metadata, structured)
        MetadataSerializer._add_optional_numeric_fields(metadata, structured)

        return metadata

    @staticmethod
    def _add_optional_string_fields(
        metadata: dict, structured: StructuredMetadata
    ) -> None:
        """Add optional string fields to metadata dictionary.

        Parameters
        ----------
        metadata : dict
            Dictionary to add fields to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        optional_strings = {
            "author_sort": structured.author_sort,
            "publisher": structured.publisher,
            "pubdate": structured.pubdate,
            "timestamp": structured.timestamp,
            "description": structured.description,
            "isbn": structured.isbn,
        }
        metadata.update({k: v for k, v in optional_strings.items() if v})

    @staticmethod
    def _add_optional_list_fields(
        metadata: dict, structured: StructuredMetadata
    ) -> None:
        """Add optional list fields to metadata dictionary.

        Parameters
        ----------
        metadata : dict
            Dictionary to add fields to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        optional_lists = {
            "languages": structured.languages,
            "identifiers": structured.identifiers,
            "tags": structured.tags,
            "formats": structured.formats,
        }
        metadata.update({k: v for k, v in optional_lists.items() if v})

    @staticmethod
    def _add_series_fields(metadata: dict, structured: StructuredMetadata) -> None:
        """Add series-related fields to metadata dictionary.

        Parameters
        ----------
        metadata : dict
            Dictionary to add fields to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.series:
            metadata["series"] = structured.series
            if structured.series_index is not None:
                metadata["series_index"] = structured.series_index

    @staticmethod
    def _add_optional_numeric_fields(
        metadata: dict, structured: StructuredMetadata
    ) -> None:
        """Add optional numeric fields to metadata dictionary.

        Parameters
        ----------
        metadata : dict
            Dictionary to add fields to.
        structured : StructuredMetadata
            Structured metadata instance.
        """
        if structured.rating is not None:
            metadata["rating"] = structured.rating
