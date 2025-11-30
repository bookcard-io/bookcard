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

"""Book cover art extraction service.

Extracts cover art from book files (EPUB, PDF, MOBI, FB2, etc.) following
the same approach as foliate-js. Uses strategy pattern for format-specific
extraction.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from fundamental.services.cover_extractors import (
    CbzCoverExtractor,
    CoverExtractionStrategy,
    DocxCoverExtractor,
    EpubCoverExtractor,
    Fb2CoverExtractor,
    FbzCoverExtractor,
    HtmlCoverExtractor,
    KepubCoverExtractor,
    MobiCoverExtractor,
    OdtCoverExtractor,
    PdfCoverExtractor,
)

if TYPE_CHECKING:
    from pathlib import Path


class BookCoverExtractor:
    """Extract cover art from book files using strategy pattern.

    Supports multiple formats through pluggable extraction strategies.
    To add a new format, create a CoverExtractionStrategy subclass
    and register it with register_strategy().
    """

    def __init__(self) -> None:
        """Initialize extractor with default strategies.

        Strategies are ordered by format prevalence and specificity.
        More specific formats (e.g., KEPUB, FBZ) come before their base formats.
        """
        self._strategies: list[CoverExtractionStrategy] = [
            # Specific variants first (before base formats)
            KepubCoverExtractor(),  # KEPUB (before EPUB)
            FbzCoverExtractor(),  # FBZ (before FB2)
            # Common formats (high prevalence)
            EpubCoverExtractor(),
            PdfCoverExtractor(),
            MobiCoverExtractor(),  # Also handles AZW, AZW3, AZW4, PRC
            Fb2CoverExtractor(),
            # Document formats
            DocxCoverExtractor(),
            OdtCoverExtractor(),
            # Web-based formats
            HtmlCoverExtractor(),  # Also handles HTMLZ
            # Comic book formats
            CbzCoverExtractor(),  # Also handles CBR, CB7, CBC
        ]

    def register_strategy(self, strategy: CoverExtractionStrategy) -> None:
        """Register a new cover extraction strategy.

        Parameters
        ----------
        strategy : CoverExtractionStrategy
            Strategy to register. Will be tried in order.
        """
        self._strategies.append(strategy)

    def extract_cover(
        self,
        file_path: Path,
        file_format: str,
    ) -> bytes | None:
        """Extract cover art from a book file.

        Parameters
        ----------
        file_path : Path
            Path to the book file.
        file_format : str
            File format extension (e.g., 'epub', 'pdf', 'mobi').

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if no cover found or extraction fails.
        """
        file_format_upper = file_format.upper().lstrip(".")

        # Try each strategy until one succeeds
        for strategy in self._strategies:
            if not strategy.can_handle(file_format_upper):
                continue
            with suppress(Exception):
                cover_data = strategy.extract_cover(file_path)
                if cover_data:
                    return cover_data

        return None
