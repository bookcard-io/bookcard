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

"""Cover art extraction strategy for KEPUB (Kobo EPUB) files.

KEPUB is essentially EPUB with Kobo-specific extensions.
Reuses EPUB extraction logic since KEPUB files are EPUB-compatible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fundamental.services.cover_extractors.base import CoverExtractionStrategy
from fundamental.services.cover_extractors.epub import EpubCoverExtractor

if TYPE_CHECKING:
    from pathlib import Path


class KepubCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for KEPUB files.

    KEPUB files are EPUB-compatible, so we reuse the EPUB extractor.
    """

    def __init__(self) -> None:
        """Initialize KEPUB extractor with EPUB extractor."""
        self._epub_extractor = EpubCoverExtractor()

    def can_handle(self, file_format: str) -> bool:
        """Check if format is KEPUB."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper == "KEPUB"

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from KEPUB file.

        KEPUB files are EPUB-compatible, so we delegate to EPUB extractor.

        Parameters
        ----------
        file_path : Path
            Path to the KEPUB file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if extraction fails.
        """
        # KEPUB is EPUB-compatible, so use EPUB extractor
        return self._epub_extractor.extract_cover(file_path)
