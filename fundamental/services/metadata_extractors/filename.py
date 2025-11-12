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

"""Fallback metadata extraction strategy using filename."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fundamental.services.book_metadata import BookMetadata
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path


class FilenameMetadataExtractor(MetadataExtractionStrategy):
    """Fallback metadata extraction strategy using filename."""

    def can_handle(self, _file_format: str) -> bool:
        """Return True as this is the fallback strategy."""
        return True

    def extract(self, file_path: Path, _original_filename: str) -> BookMetadata:
        """Extract basic metadata from filename.

        Attempts to infer author and title from filename patterns:
        - "Author - Title" -> Author: "Author", Title: "Title"
        - "Author - Title: Subtitle" -> Author: "Author", Title: "Title: Subtitle"
        - "Author - Title - Extra" -> Author: "Author", Title: "Title - Extra"
        """
        stem = file_path.stem
        if not stem or stem.strip() == "":
            return BookMetadata(title="Unknown", author="Unknown")

        # Split by " - " (space-dash-space) to separate author and title
        parts = stem.split(" - ", 1)
        if len(parts) == 2:
            author = parts[0].strip()
            title = parts[1].strip()
            # If author is empty after split, fall back to Unknown
            if not author:
                author = "Unknown"
            # If title is empty after split, use the whole stem as title
            if not title:
                title = stem
        else:
            # No " - " separator found, use entire stem as title
            title = stem
            author = "Unknown"

        return BookMetadata(title=title, author=author)
