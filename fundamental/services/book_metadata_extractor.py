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

"""Book metadata extraction service.

Extracts metadata from book files (EPUB, PDF, MOBI, etc.) following
the same approach as calibre-web. Falls back to filename-based extraction
if format-specific extraction fails.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fundamental.services.metadata_extractors import (
    FilenameMetadataExtractor,
    MetadataExtractionStrategy,
)
from fundamental.services.metadata_extractors.epub import EpubMetadataExtractor
from fundamental.services.metadata_extractors.fb2 import Fb2MetadataExtractor
from fundamental.services.metadata_extractors.mobi import MobiMetadataExtractor
from fundamental.services.metadata_extractors.opds import OpdsMetadataExtractor
from fundamental.services.metadata_extractors.pdf import PdfMetadataExtractor

if TYPE_CHECKING:
    from pathlib import Path

    from fundamental.services.book_metadata import BookMetadata


class BookMetadataExtractor:
    """Extract metadata from book files using strategy pattern.

    Supports multiple formats through pluggable extraction strategies.
    To add a new format, create a MetadataExtractionStrategy subclass
    and register it with register_strategy().
    """

    def __init__(self) -> None:
        """Initialize extractor with default strategies."""
        self._strategies: list[MetadataExtractionStrategy] = [
            EpubMetadataExtractor(),
            PdfMetadataExtractor(),
            MobiMetadataExtractor(),
            Fb2MetadataExtractor(),
            OpdsMetadataExtractor(),
            FilenameMetadataExtractor(),  # Fallback - must be last
        ]

    def register_strategy(self, strategy: MetadataExtractionStrategy) -> None:
        """Register a new metadata extraction strategy.

        Parameters
        ----------
        strategy : MetadataExtractionStrategy
            Strategy to register. Will be tried before the filename fallback.
        """
        # Insert before the filename fallback (last strategy)
        self._strategies.insert(-1, strategy)

    def extract_metadata(
        self,
        file_path: Path,
        file_format: str,
        original_filename: str | None = None,
    ) -> BookMetadata:
        """Extract metadata from a book file.

        Parameters
        ----------
        file_path : Path
            Path to the book file.
        file_format : str
            File format extension (e.g., 'epub', 'pdf', 'mobi').
        original_filename : str | None
            Original filename for fallback (default: file_path.name).

        Returns
        -------
        BookMetadata
            Extracted metadata. Falls back to filename-based extraction
            if format-specific extraction fails.
        """
        if original_filename is None:
            original_filename = file_path.name

        file_format_upper = file_format.upper().lstrip(".")

        # Try each strategy until one succeeds
        for strategy in self._strategies:
            if not strategy.can_handle(file_format_upper):
                continue
            try:
                return strategy.extract(file_path, original_filename)
            except (ValueError, ImportError, OSError, KeyError):
                # Try next strategy on failure
                continue

        # Should never reach here (FilenameMetadataExtractor always succeeds)
        return FilenameMetadataExtractor().extract(file_path, original_filename)
