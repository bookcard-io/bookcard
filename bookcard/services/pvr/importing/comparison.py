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

"""File comparison utility."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileComparer:
    """Utility for comparing files."""

    def __init__(self, chunk_size: int = 8192) -> None:
        """Initialize file comparer.

        Parameters
        ----------
        chunk_size : int, optional
            Size of chunks to read for comparison, by default 8192.
        """
        self._chunk_size = chunk_size

    def are_identical(self, file1: Path, file2: Path) -> bool:
        """Check if files are identical using size and content sampling.

        Parameters
        ----------
        file1 : Path
            First file path.
        file2 : Path
            Second file path.

        Returns
        -------
        bool
            True if files are identical, False otherwise.
        """
        if not self._have_same_size(file1, file2):
            return False

        return self._have_same_content(file1, file2)

    def _have_same_size(self, file1: Path, file2: Path) -> bool:
        """Check if files have same size."""
        try:
            return file1.stat().st_size == file2.stat().st_size
        except OSError:
            return False

    def _have_same_content(self, file1: Path, file2: Path) -> bool:
        """Sample file content to check for differences."""
        try:
            with file1.open("rb") as f1, file2.open("rb") as f2:
                # Check beginning
                if f1.read(self._chunk_size) != f2.read(self._chunk_size):
                    return False

                # Check end if file is large enough
                size = file1.stat().st_size
                if size > self._chunk_size:
                    seek_pos = max(0, size - self._chunk_size)
                    f1.seek(seek_pos)
                    f2.seek(seek_pos)
                    return f1.read() == f2.read()

                return True
        except OSError:
            return False
