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

"""Archive handler interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.services.comic.archive.image_processor import ImageProcessor
    from bookcard.services.comic.archive.models import ArchiveMetadata, PageDetails


class ArchiveHandler(ABC):
    """Interface for archive format handlers."""

    @abstractmethod
    def scan_metadata(
        self,
        file_path: Path,
        *,
        last_modified_ns: int,
    ) -> ArchiveMetadata:
        """Scan archive and return its metadata.

        Parameters
        ----------
        file_path : Path
            Path to the archive.
        last_modified_ns : int
            Modification time used for metadata.

        Returns
        -------
        ArchiveMetadata
            Format-specific archive metadata.
        """

    @abstractmethod
    def extract_page(
        self,
        file_path: Path,
        *,
        filename: str,
        metadata: ArchiveMetadata,
    ) -> bytes:
        """Extract a page image from the archive.

        Parameters
        ----------
        file_path : Path
            Path to the archive.
        filename : str
            Entry name of the requested page.
        metadata : ArchiveMetadata
            Metadata previously returned by `scan_metadata`.

        Returns
        -------
        bytes
            Raw image bytes.
        """

    @abstractmethod
    def get_page_details(
        self,
        file_path: Path,
        *,
        metadata: ArchiveMetadata,
        include_dimensions: bool,
        image_processor: ImageProcessor,
    ) -> dict[str, PageDetails]:
        """Get per-page details (sizes and optional dimensions).

        Parameters
        ----------
        file_path : Path
            Path to the archive.
        metadata : ArchiveMetadata
            Metadata previously returned by `scan_metadata`.
        include_dimensions : bool
            If True, compute width/height for each image entry.
        image_processor : ImageProcessor
            Image processor used to compute dimensions.

        Returns
        -------
        dict[str, PageDetails]
            Mapping from entry name to details.
        """
