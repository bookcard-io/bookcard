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

"""Metadata extraction strategy for KEPUB (Kobo EPUB) files.

KEPUB is essentially EPUB with Kobo-specific extensions.
Reuses EPUB extraction logic since KEPUB files are EPUB-compatible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.services.metadata_extractors.base import MetadataExtractionStrategy
from bookcard.services.metadata_extractors.epub import EpubMetadataExtractor

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.services.book_metadata import BookMetadata


class KepubMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for KEPUB files.

    KEPUB files are EPUB files with Kobo-specific extensions.
    We reuse the EPUB extractor since they share the same structure.
    """

    def __init__(self) -> None:
        """Initialize KEPUB extractor with EPUB extractor."""
        self._epub_extractor = EpubMetadataExtractor()

    def can_handle(self, file_format: str) -> bool:
        """Check if format is KEPUB."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper == "KEPUB"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from KEPUB file.

        KEPUB files are EPUB-compatible, so we delegate to EPUB extractor.

        Parameters
        ----------
        file_path : Path
            Path to the KEPUB file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        # KEPUB is EPUB-compatible, so use EPUB extractor
        return self._epub_extractor.extract(file_path, original_filename)
