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

"""Cover art extraction strategy for FBZ (compressed FB2) files.

FBZ is a ZIP archive containing an FB2 file.
Extracts the FB2 file from the archive and uses FB2 extractor.
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from bookcard.services.cover_extractors.base import CoverExtractionStrategy
from bookcard.services.cover_extractors.fb2 import Fb2CoverExtractor


class FbzCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for FBZ files.

    FBZ files are ZIP archives containing FB2 files.
    We extract the FB2 file and use the FB2 extractor.
    """

    def __init__(self) -> None:
        """Initialize FBZ extractor with FB2 extractor."""
        self._fb2_extractor = Fb2CoverExtractor()

    def can_handle(self, file_format: str) -> bool:
        """Check if format is FBZ."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper == "FBZ"

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from FBZ file.

        FBZ is a ZIP archive containing an FB2 file.
        We extract the FB2 file and use FB2 extractor.

        Parameters
        ----------
        file_path : Path
            Path to the FBZ file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if extraction fails.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as fbz_zip:
                # Find the FB2 file in the archive
                fb2_files = [
                    f for f in fbz_zip.namelist() if f.lower().endswith(".fb2")
                ]
                if not fb2_files:
                    return None

                # Use the first FB2 file found
                fb2_filename = fb2_files[0]

                # Extract FB2 file to temporary location
                with tempfile.NamedTemporaryFile(
                    suffix=".fb2", delete=False
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    temp_file.write(fbz_zip.read(fb2_filename))

                try:
                    # Use FB2 extractor on the extracted file
                    return self._fb2_extractor.extract_cover(temp_path)
                finally:
                    # Clean up temporary file
                    if temp_path.exists():
                        temp_path.unlink()

        except (zipfile.BadZipFile, OSError, KeyError):
            return None
