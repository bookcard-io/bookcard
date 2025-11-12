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

"""Base class for cover art extraction strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class CoverExtractionStrategy(ABC):
    """Abstract base class for cover art extraction strategies.

    Each format (EPUB, PDF, etc.) implements this interface to provide
    format-specific cover art extraction.
    """

    @abstractmethod
    def can_handle(self, file_format: str) -> bool:
        """Check if this strategy can handle the given file format.

        Parameters
        ----------
        file_format : str
            File format extension (e.g., 'epub', 'pdf').

        Returns
        -------
        bool
            True if this strategy can handle the format.
        """

    @abstractmethod
    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover art from a book file.

        Parameters
        ----------
        file_path : Path
            Path to the book file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if no cover found.

        Raises
        ------
        Exception
            If extraction fails (will be caught and ignored).
        """
