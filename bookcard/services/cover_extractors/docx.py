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

"""Cover art extraction strategy for DOCX (Microsoft Word) files.

DOCX files are ZIP archives containing images in the media folder.
Extracts the first image from word/media/ as the cover.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image

from bookcard.services.cover_extractors.base import CoverExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path


class DocxCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for DOCX files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is DOCX."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper == "DOCX"

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from DOCX file.

        Parameters
        ----------
        file_path : Path
            Path to the DOCX file.

        Returns
        -------
        bytes | None
            Cover image data as bytes (JPEG), or None if extraction fails.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as docx_zip:
                # Find images in word/media/ folder
                media_files = [
                    f
                    for f in docx_zip.namelist()
                    if f.startswith("word/media/")
                    and f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp"))
                ]

                if not media_files:
                    return None

                # Use first image as cover
                first_image = media_files[0]
                image_data = docx_zip.read(first_image)

                # Process and convert to JPEG
                return self._process_image(image_data)
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
