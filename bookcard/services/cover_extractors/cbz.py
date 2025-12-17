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

"""Cover art extraction strategy for CBZ, CBR, CB7, CBC (comic book) files.

Comic book formats are archives containing images. The first page/image
is typically the cover. CBZ is ZIP, CBR is RAR, CB7 is 7z, CBC is a collection.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image

from bookcard.services.cover_extractors.base import CoverExtractionStrategy

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class CbzCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for CBZ, CBR, CB7, CBC files.

    Note: CBR (RAR) and CB7 (7z) support requires additional libraries.
    For now, only CBZ (ZIP) is fully supported.
    """

    def __init__(self) -> None:
        """Initialize extractor with format-specific extraction strategies."""
        # Strategy pattern: map file suffixes to extraction methods
        self._extraction_strategies: dict[str, Callable[[Path], bytes | None]] = {
            ".cbz": self._extract_from_cbz,
            ".cbr": self._extract_from_cbr,
            ".cb7": self._extract_from_cb7,
            ".cbc": self._extract_from_cbc,
        }

    def can_handle(self, file_format: str) -> bool:
        """Check if format is CBZ, CBR, CB7, or CBC."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper in ("CBZ", "CBR", "CB7", "CBC")

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from comic book file.

        Parameters
        ----------
        file_path : Path
            Path to the comic book file.

        Returns
        -------
        bytes | None
            Cover image data as bytes (JPEG), or None if extraction fails.
        """
        suffix = file_path.suffix.lower()
        extractor = self._extraction_strategies.get(suffix)
        if extractor:
            return extractor(file_path)
        return None

    def _extract_from_cbz(self, file_path: Path) -> bytes | None:
        """Extract cover from CBZ (ZIP archive).

        Parameters
        ----------
        file_path : Path
            Path to the CBZ file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if extraction fails.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as cbz_zip:
                # Find image files (sorted to get first page)
                image_files = [
                    f
                    for f in sorted(cbz_zip.namelist())
                    if f.lower().endswith((
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ))
                ]

                if not image_files:
                    return None

                # Use first image as cover
                first_image = image_files[0]
                image_data = cbz_zip.read(first_image)

                # Process and convert to JPEG
                return self._process_image(image_data)
        except (zipfile.BadZipFile, OSError, KeyError):
            return None

    def _extract_from_cbr(self, file_path: Path) -> bytes | None:
        """Extract cover from CBR (RAR archive).

        Parameters
        ----------
        file_path : Path
            Path to the CBR file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if extraction fails.
        """
        # CBR requires rarfile library
        try:
            # local import for mocking
            import rarfile
        except ImportError:
            # rarfile not available
            return None

        try:
            with rarfile.RarFile(file_path, "r") as cbr_rar:
                # Find image files (sorted to get first page)
                image_files = [
                    f
                    for f in sorted(cbr_rar.namelist())
                    if f.lower().endswith((
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ))
                ]

                if not image_files:
                    return None

                # Use first image as cover
                first_image = image_files[0]
                image_data = cbr_rar.read(first_image)

                # Process and convert to JPEG
                result = self._process_image(image_data)
        except (OSError, ValueError, TypeError, AttributeError, rarfile.Error):
            return None
        else:
            return result

    def _extract_from_cb7(self, file_path: Path) -> bytes | None:
        """Extract cover from CB7 (7z archive).

        Parameters
        ----------
        file_path : Path
            Path to the CB7 file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if extraction fails.
        """
        # CB7 requires py7zr library
        try:
            import py7zr  # type: ignore[import-untyped]

            with py7zr.SevenZipFile(file_path, "r") as cb7_7z:
                # Find image files (sorted to get first page)
                image_files = [
                    f
                    for f in sorted(cb7_7z.getnames())
                    if f.lower().endswith((
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".webp",
                    ))
                ]

                if not image_files:
                    return None

                # Use first image as cover
                first_image = image_files[0]
                image_data = cb7_7z.read([first_image])[first_image].read()

                # Process and convert to JPEG
                return self._process_image(image_data)
        except ImportError:
            # py7zr not available
            return None
        except (OSError, ValueError, TypeError, AttributeError):
            return None

    def _extract_from_cbc(self, file_path: Path) -> bytes | None:
        """Extract cover from CBC (comic book collection).

        CBC is typically a ZIP archive containing multiple CBZ files.
        We extract the first CBZ and use its cover.

        Parameters
        ----------
        file_path : Path
            Path to the CBC file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if extraction fails.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as cbc_zip:
                # Find CBZ files
                cbz_files = [
                    f for f in sorted(cbc_zip.namelist()) if f.lower().endswith(".cbz")
                ]

                if not cbz_files:
                    return None

                # Extract first CBZ to temp and process
                from pathlib import Path as PathLib

                first_cbz = cbz_files[0]
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".cbz", delete=False) as temp:
                    temp_path = PathLib(temp.name)
                    temp.write(cbc_zip.read(first_cbz))

                try:
                    return self._extract_from_cbz(temp_path)
                finally:
                    if temp_path.exists():
                        temp_path.unlink()
        except (zipfile.BadZipFile, OSError, KeyError):
            return None

    def _process_image(self, image_data: bytes) -> bytes | None:
        """Process image data and convert to JPEG if needed.

        Parameters
        ----------
        image_data : bytes
            Raw image data.

        Returns
        -------
        bytes | None
            JPEG image data as bytes, or None if processing fails.
        """
        try:
            img = Image.open(BytesIO(image_data))
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")
            # Save to bytes as JPEG
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()
        except (OSError, ValueError, TypeError, AttributeError):
            return None
