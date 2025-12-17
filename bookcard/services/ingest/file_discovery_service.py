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

"""File discovery service for ingest.

Discovers book files in the ingest directory and filters by supported formats.
Follows SRP by focusing solely on file discovery.
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003

logger = logging.getLogger(__name__)


@dataclass
class FileGroup:
    """Represents a group of files that belong to the same book.

    Attributes
    ----------
    book_key : str
        Unique identifier for this book group (e.g., normalized title-author).
    files : list[Path]
        List of file paths in this group.
    metadata_hint : dict | None
        Optional metadata hint extracted from files (title, authors, etc.).
    """

    book_key: str
    files: list[Path]
    metadata_hint: dict | None = None


class FileDiscoveryService:
    """Service for discovering book files in the ingest directory.

    Recursively scans the ingest directory and filters files by supported formats.
    Follows SRP by focusing solely on file discovery.

    Parameters
    ----------
    supported_formats : list[str]
        List of supported file extensions (without dots).
    ignore_patterns : list[str]
        List of file patterns to ignore (e.g., ["*.tmp", "*.bak"]).
    """

    def __init__(
        self,
        supported_formats: list[str],
        ignore_patterns: list[str] | None = None,
    ) -> None:
        """Initialize file discovery service.

        Parameters
        ----------
        supported_formats : list[str]
            List of supported file extensions (without dots).
        ignore_patterns : list[str] | None
            Optional list of file patterns to ignore.
        """
        self._supported_formats = {fmt.lower().lstrip(".") for fmt in supported_formats}
        self._ignore_patterns = ignore_patterns or []

    def discover_files(self, ingest_dir: Path) -> list[Path]:
        """Discover all book files in the ingest directory.

        Recursively scans the directory and returns all files that match
        supported formats and don't match ignore patterns.

        Parameters
        ----------
        ingest_dir : Path
            Root directory to scan.

        Returns
        -------
        list[Path]
            List of discovered book file paths.

        Raises
        ------
        FileNotFoundError
            If ingest directory does not exist.
        """
        if not ingest_dir.exists():
            msg = f"Ingest directory does not exist: {ingest_dir}"
            raise FileNotFoundError(msg)

        if not ingest_dir.is_dir():
            msg = f"Ingest path is not a directory: {ingest_dir}"
            raise ValueError(msg)

        discovered_files: list[Path] = []

        # Recursively walk the directory
        for file_path in ingest_dir.rglob("*"):
            if not file_path.is_file():
                continue

            # Check if file should be ignored
            if self._should_ignore(file_path):
                logger.debug("Ignoring file: %s", file_path)
                continue

            # Check if file is a supported book format
            if self._is_book_file(file_path):
                discovered_files.append(file_path)
                logger.debug("Discovered book file: %s", file_path)

        logger.info(
            "Discovered %d book files in %s",
            len(discovered_files),
            ingest_dir,
        )
        return discovered_files

    def _is_book_file(self, path: Path) -> bool:
        """Check if a file is a supported book format.

        Parameters
        ----------
        path : Path
            File path to check.

        Returns
        -------
        bool
            True if file is a supported book format, False otherwise.
        """
        # Get file extension (without dot, lowercase)
        ext = path.suffix.lower().lstrip(".")
        if not ext:
            return False

        return ext in self._supported_formats

    def _should_ignore(self, path: Path) -> bool:
        """Check if a file should be ignored based on patterns.

        Parameters
        ----------
        path : Path
            File path to check.

        Returns
        -------
        bool
            True if file should be ignored, False otherwise.
        """
        filename = path.name
        for pattern in self._ignore_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def group_files_by_directory(self, files: list[Path]) -> list[FileGroup]:
        """Group files by their immediate parent directory.

        This is a simple grouping strategy that groups files in the same
        directory together. More sophisticated grouping (by metadata)
        is handled by MetadataExtractionService.

        Parameters
        ----------
        files : list[Path]
            List of file paths to group.

        Returns
        -------
        list[FileGroup]
            List of file groups, one per directory.
        """
        groups: dict[Path, list[Path]] = {}

        for file_path in files:
            parent_dir = file_path.parent
            if parent_dir not in groups:
                groups[parent_dir] = []
            groups[parent_dir].append(file_path)

        file_groups: list[FileGroup] = []
        for parent_dir, group_files in groups.items():
            # Create a book key from the parent directory name
            book_key = self._create_book_key_from_path(parent_dir)
            file_groups.append(
                FileGroup(
                    book_key=book_key,
                    files=group_files,
                    metadata_hint=None,
                )
            )

        return file_groups

    def _create_book_key_from_path(self, path: Path) -> str:
        """Create a book key from a file path.

        Parameters
        ----------
        path : Path
            File or directory path.

        Returns
        -------
        str
            Normalized book key.
        """
        # Use the path as the key, normalized
        # For files, use parent directory name; for directories, use directory name
        key = path.parent.name if path.is_file() else path.name

        # Normalize: lowercase, replace spaces with underscores
        key = key.lower().replace(" ", "_")
        # Remove special characters
        key = "".join(c for c in key if c.isalnum() or c in ("_", "-"))
        return key or "unknown"
