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

"""Base class for ebook metadata enforcers.

Abstract base for format-specific metadata enforcement in ebook files.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from fundamental.repositories.models import BookWithFullRelations


class EbookMetadataEnforcer(ABC):
    """Abstract base class for ebook metadata enforcers.

    Defines interface for updating metadata embedded in ebook files.
    Follows SOC by separating format-specific implementations.

    Parameters
    ----------
    supported_formats : list[str]
        List of file format extensions this enforcer supports (e.g., ['epub', 'azw3']).
    """

    def __init__(self, supported_formats: list[str]) -> None:
        """Initialize ebook metadata enforcer.

        Parameters
        ----------
        supported_formats : list[str]
            Supported file format extensions.
        """
        self._supported_formats = [fmt.lower() for fmt in supported_formats]

    def can_handle(self, file_format: str) -> bool:
        """Check if this enforcer can handle the given format.

        Parameters
        ----------
        file_format : str
            File format extension (e.g., 'epub', 'azw3').

        Returns
        -------
        bool
            True if this enforcer supports the format, False otherwise.
        """
        return file_format.lower() in self._supported_formats

    @abstractmethod
    def enforce_metadata(
        self,
        book_with_rels: BookWithFullRelations,
        file_path: Path,
    ) -> bool:
        """Enforce metadata in an ebook file.

        Updates embedded metadata in the ebook file to match current
        database metadata.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all related metadata.
        file_path : Path
            Path to the ebook file to update.

        Returns
        -------
        bool
            True if metadata was successfully updated, False otherwise.

        Raises
        ------
        FileNotFoundError
            If ebook file does not exist.
        ValueError
            If file format is not supported or metadata is invalid.
        """
        raise NotImplementedError
