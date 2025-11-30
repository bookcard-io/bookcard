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

"""Metadata extraction strategy for RTF (Rich Text Format) files.

RTF files contain metadata in the document header using control words.
Extracts title, author, subject, and other metadata from RTF control words.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from fundamental.services.book_metadata import BookMetadata
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

# RTF control words for metadata
RTF_METADATA_CONTROL_WORDS = {
    "title": r"\\title\s*([^\{\}\\]+)",
    "author": r"\\author\s*([^\{\}\\]+)",
    "subject": r"\\subject\s*([^\{\}\\]+)",
    "keywords": r"\\keywords\s*([^\{\}\\]+)",
    "operator": r"\\operator\s*([^\{\}\\]+)",
    "company": r"\\company\s*([^\{\}\\]+)",
    "manager": r"\\manager\s*([^\{\}\\]+)",
    "category": r"\\category\s*([^\{\}\\]+)",
    "comment": r"\\comment\s*([^\{\}\\]+)",
    "doccomm": r"\\doccomm\s*([^\{\}\\]+)",
    "hlinkbase": r"\\hlinkbase\s*([^\{\}\\]+)",
    "creatim": r"\\creatim\s*([^\{\}\\]+)",
    "revtim": r"\\revtim\s*([^\{\}\\]+)",
    "printim": r"\\printim\s*([^\{\}\\]+)",
    "buptim": r"\\buptim\s*([^\{\}\\]+)",
}


class RtfMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for RTF files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is RTF."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper == "RTF"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from RTF file.

        Parameters
        ----------
        file_path : Path
            Path to the RTF file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as rtf_file:
                # Read first 50KB (metadata is usually in the header)
                content = rtf_file.read(50000)
                return self._parse_rtf_content(content, original_filename)
        except (OSError, UnicodeDecodeError):
            # Try with different encoding
            try:
                with file_path.open(
                    "r", encoding="latin-1", errors="ignore"
                ) as rtf_file:
                    content = rtf_file.read(50000)
                    return self._parse_rtf_content(content, original_filename)
            except (OSError, UnicodeDecodeError):
                return self._extract_from_filename(original_filename)

    def _parse_rtf_content(self, content: str, original_filename: str) -> BookMetadata:
        """Parse RTF content to extract metadata.

        Parameters
        ----------
        content : str
            RTF content.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        metadata: dict[str, str] = {}

        # Extract metadata using control word patterns
        for key, pattern in RTF_METADATA_CONTROL_WORDS.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove RTF control characters and braces
                value = self._clean_rtf_text(value)
                if value:
                    metadata[key] = value

        # Extract title
        title = metadata.get("title") or self._extract_title_from_filename(
            original_filename
        )

        # Extract author
        author = metadata.get("author", "Unknown")

        # Extract description (from subject or comment)
        description = (
            metadata.get("subject")
            or metadata.get("comment")
            or metadata.get("doccomm")
            or ""
        )

        # Extract tags (from keywords or category)
        tags = []
        if metadata.get("keywords"):
            # Keywords might be comma-separated
            keywords = metadata.get("keywords", "").split(",")
            tags.extend([kw.strip() for kw in keywords if kw.strip()])
        if metadata.get("category"):
            tags.append(metadata.get("category", ""))

        # Extract publisher (from company)
        publisher = metadata.get("company")

        return BookMetadata(
            title=title,
            author=author,
            description=description,
            tags=tags if tags else None,
            publisher=publisher,
        )

    def _clean_rtf_text(self, text: str) -> str:
        """Clean RTF text by removing control characters.

        Parameters
        ----------
        text : str
            RTF text with control characters.

        Returns
        -------
        str
            Cleaned text.
        """
        # Remove RTF control words (simple approach)
        # Remove \'XX hex codes
        text = re.sub(r"\\'[0-9a-fA-F]{2}", "", text)
        # Remove \uXXXX unicode escapes
        text = re.sub(r"\\u-?\d+", "", text)
        # Remove braces
        text = text.replace("{", "").replace("}", "")
        # Remove backslashes (but keep escaped ones)
        text = re.sub(r"\\(?!['u\{\}])", "", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_from_filename(self, filename: str) -> BookMetadata:
        """Extract metadata from filename only.

        Parameters
        ----------
        filename : str
            Filename.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        title = self._extract_title_from_filename(filename)
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
        return stem.strip() or filename
