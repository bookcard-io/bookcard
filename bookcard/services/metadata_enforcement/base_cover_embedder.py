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

"""Base class for cover embedders.

Defines the interface for embedding cover images into different file formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseCoverEmbedder(ABC):
    """Abstract base class for cover embedding strategies.

    Implementations handle format-specific logic for embedding covers
    into file contents (e.g. EPUB archives, CBZ archives).
    """

    @abstractmethod
    def embed_cover(
        self,
        contents: object,
        cover_path: Path,
        **kwargs: object,
    ) -> bool:
        """Embed cover image into contents.

        Parameters
        ----------
        contents : object
            The parsed file contents (e.g. EPUBContents).
            Type depends on the specific implementation.
        cover_path : Path
            Path to the new cover image file.
        **kwargs : object
            Additional format-specific arguments (e.g. opf_path for EPUB).

        Returns
        -------
        bool
            True if cover was successfully embedded, False otherwise.
        """
