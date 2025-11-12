# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Book cover art extraction service.

Extracts cover art from book files (EPUB, PDF, MOBI, FB2, etc.) following
the same approach as foliate-js. Uses strategy pattern for format-specific
extraction.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from fundamental.services.cover_extractors import (
    CoverExtractionStrategy,
    EpubCoverExtractor,
    Fb2CoverExtractor,
    MobiCoverExtractor,
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
        """Initialize extractor with default strategies."""
        self._strategies: list[CoverExtractionStrategy] = [
            EpubCoverExtractor(),
            PdfCoverExtractor(),
            MobiCoverExtractor(),
            Fb2CoverExtractor(),
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
