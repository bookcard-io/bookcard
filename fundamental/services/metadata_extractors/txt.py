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

"""Metadata extraction strategy for plain text files (TXT).

Plain text files don't contain embedded metadata, so we extract
basic information from the filename and attempt to infer metadata
from the file content (first few lines).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from fundamental.services.book_metadata import BookMetadata
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

# Common title/author patterns in text files
TITLE_PATTERNS = [
    re.compile(r"^title[:\s]+(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^#\s+(.+)$", re.MULTILINE),  # Markdown-style title
    re.compile(r"^(.+)\n={3,}$", re.MULTILINE),  # Underlined title
    re.compile(r"^(.+)\n-{3,}$", re.MULTILINE),  # Underlined title with dashes
]

AUTHOR_PATTERNS = [
    re.compile(r"^author[:\s]+(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^by\s+(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^written by[:\s]+(.+)$", re.IGNORECASE | re.MULTILINE),
]


class TxtMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for plain text files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is TXT or TXTZ."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper in ("TXT", "TXTZ")

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from plain text file.

        Parameters
        ----------
        file_path : Path
            Path to the text file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        # For TXTZ (compressed), we'd need to decompress first
        # For now, treat it as regular TXT (will fall back to filename)
        if file_path.suffix.lower() == ".txtz":
            # TXTZ is a ZIP file containing a text file
            # For simplicity, fall back to filename extraction
            return self._extract_from_filename(file_path, original_filename)

        try:
            # Read first 50 lines to look for metadata patterns
            with file_path.open("r", encoding="utf-8", errors="ignore") as txt_file:
                content = txt_file.read(5000)  # Read first 5KB
                lines = content.split("\n")[:50]  # First 50 lines
                header_text = "\n".join(lines)

                # Try to extract title and author from content
                title = self._extract_title(header_text, original_filename)
                author = self._extract_author(header_text)

                return BookMetadata(title=title, author=author)
        except (OSError, UnicodeDecodeError):
            # If reading fails, fall back to filename
            return self._extract_from_filename(file_path, original_filename)

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from content or filename.

        Parameters
        ----------
        content : str
            File content (first few lines).
        filename : str
            Original filename.

        Returns
        -------
        str
            Extracted title.
        """
        # Try patterns in content
        for pattern in TITLE_PATTERNS:
            match = pattern.search(content)
            if match:
                title = match.group(1).strip()
                if title and len(title) < 200:  # Reasonable title length
                    return title

        # Fall back to filename
        return self._extract_title_from_filename(filename)

    def _extract_author(self, content: str) -> str:
        """Extract author from content.

        Parameters
        ----------
        content : str
            File content (first few lines).

        Returns
        -------
        str
            Extracted author or "Unknown".
        """
        for pattern in AUTHOR_PATTERNS:
            match = pattern.search(content)
            if match:
                author = match.group(1).strip()
                if author and len(author) < 100:  # Reasonable author length
                    return author

        return "Unknown"

    def _extract_from_filename(
        self, _file_path: Path, original_filename: str
    ) -> BookMetadata:
        """Extract metadata from filename only.

        Parameters
        ----------
        _file_path : Path
            Path to the file (unused, kept for interface consistency).
        original_filename : str
            Original filename.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        title = self._extract_title_from_filename(original_filename)
        return BookMetadata(title=title, author="Unknown")

    @staticmethod
    def _extract_title_from_filename(filename: str) -> str:
        """Extract title from filename.

        Parameters
        ----------
        filename : str
            Filename.

        Returns
        -------
        str
            Title (filename without extension).
        """
        from pathlib import Path

        stem = Path(filename).stem
        # Remove common prefixes/suffixes
        stem = re.sub(r"^\d+[-.\s]*", "", stem)  # Remove leading numbers
        stem = re.sub(r"[-_]", " ", stem)  # Replace dashes/underscores with spaces
        return stem.strip() or filename
