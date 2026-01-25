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

"""Metadata caching for archive scanning."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from bookcard.services.comic.archive.exceptions import ArchiveReadError

if TYPE_CHECKING:
    from bookcard.services.comic.archive.models import ArchiveMetadata


class ArchiveMetadataScanner(Protocol):
    """Protocol for scanning archive metadata."""

    def __call__(self, file_path: Path, *, last_modified_ns: int) -> ArchiveMetadata:
        """Scan archive metadata for a given file path."""
        ...


@dataclass
class LruArchiveMetadataProvider:
    """LRU-cached archive metadata provider."""

    scanner: ArchiveMetadataScanner
    maxsize: int = 50

    def __post_init__(self) -> None:
        """Initialize the internal LRU cache wrapper."""

        @lru_cache(maxsize=self.maxsize)
        def cached(resolved_path: str, mtime_ns: int) -> ArchiveMetadata:
            return self.scanner(Path(resolved_path), last_modified_ns=mtime_ns)

        self._cached = cached

    def get(self, file_path: Path) -> ArchiveMetadata:
        """Get metadata for an archive path (cached by path + mtime).

        Parameters
        ----------
        file_path : Path
            Path to the archive.

        Returns
        -------
        ArchiveMetadata
            Metadata for the archive.

        Raises
        ------
        ArchiveReadError
            If the file cannot be stat'd.
        """
        try:
            resolved = file_path.resolve()
            mtime_ns = resolved.stat().st_mtime_ns
        except OSError as e:
            msg = f"Failed to stat archive {file_path}: {e}"
            raise ArchiveReadError(msg) from e
        return self._cached(str(resolved), mtime_ns)

    def clear(self) -> None:
        """Clear the metadata cache."""
        self._cached.cache_clear()
