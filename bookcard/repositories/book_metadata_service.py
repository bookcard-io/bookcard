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

"""Book metadata service for metadata extraction.

This module handles metadata extraction following SRP.
"""

from pathlib import Path

from bookcard.repositories.interfaces import IBookMetadataService
from bookcard.services.book_cover_extractor import BookCoverExtractor
from bookcard.services.book_metadata import BookMetadata
from bookcard.services.book_metadata_extractor import BookMetadataExtractor


class BookMetadataService(IBookMetadataService):
    """Service for extracting book metadata and covers.

    Handles metadata extraction from book files following SRP.
    """

    def __init__(
        self,
        metadata_extractor: BookMetadataExtractor | None = None,
        cover_extractor: BookCoverExtractor | None = None,
    ) -> None:
        """Initialize metadata service.

        Parameters
        ----------
        metadata_extractor : BookMetadataExtractor | None
            Optional metadata extractor (creates default if None).
        cover_extractor : BookCoverExtractor | None
            Optional cover extractor (creates default if None).
        """
        self._metadata_extractor = metadata_extractor or BookMetadataExtractor()
        self._cover_extractor = cover_extractor or BookCoverExtractor()

    def extract_metadata(
        self,
        file_path: Path,
        file_format: str,
    ) -> tuple[BookMetadata, bytes | None]:
        """Extract metadata and cover art from book file.

        Parameters
        ----------
        file_path : Path
            Path to the book file.
        file_format : str
            File format extension.

        Returns
        -------
        tuple[BookMetadata, bytes | None]
            Tuple of (BookMetadata, cover_data).
        """
        metadata = self._metadata_extractor.extract_metadata(
            file_path, file_format, file_path.name
        )
        cover_data = self._cover_extractor.extract_cover(file_path, file_format)
        return metadata, cover_data
