# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
