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

"""LRU caching for per-page details (sizes and optional dimensions)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from bookcard.services.comic.archive.exceptions import (
    ArchiveReadError,
    UnsupportedFormatError,
)

if TYPE_CHECKING:
    from bookcard.services.comic.archive.handlers.base import ArchiveHandler
    from bookcard.services.comic.archive.image_processor import ImageProcessor
    from bookcard.services.comic.archive.metadata_provider import (
        LruArchiveMetadataProvider,
    )
    from bookcard.services.comic.archive.models import PageDetails


@dataclass
class LruPageDetailsProvider:
    """LRU-cached provider for per-page details.

    Notes
    -----
    Cache keys are `(resolved_path, mtime_ns, include_dimensions)`.
    """

    handlers: dict[str, ArchiveHandler]
    metadata_provider: LruArchiveMetadataProvider
    image_processor: ImageProcessor
    maxsize: int = 50

    def __post_init__(self) -> None:
        """Initialize the internal LRU cache wrapper."""

        @lru_cache(maxsize=self.maxsize)
        def cached(
            resolved_path: str, _mtime_ns: int, include_dimensions: bool
        ) -> dict[str, PageDetails]:
            file_path = Path(resolved_path)
            metadata = self.metadata_provider.get(file_path)
            suffix = file_path.suffix.lower()
            handler = self.handlers.get(suffix)
            if handler is None:
                msg = f"Unsupported comic format: {suffix}"
                raise UnsupportedFormatError(msg)
            return handler.get_page_details(
                file_path,
                metadata=metadata,
                include_dimensions=include_dimensions,
                image_processor=self.image_processor,
            )

        self._cached = cached

    def get(
        self, file_path: Path, *, include_dimensions: bool
    ) -> dict[str, PageDetails]:
        """Get page details for a given archive (cached).

        Parameters
        ----------
        file_path : Path
            Path to the archive.
        include_dimensions : bool
            Whether to compute and include width/height.

        Returns
        -------
        dict[str, PageDetails]
            Mapping from entry name to details.
        """
        try:
            resolved = file_path.resolve()
            mtime_ns = resolved.stat().st_mtime_ns
        except OSError as e:
            msg = f"Failed to stat archive {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        return self._cached(str(resolved), mtime_ns, include_dimensions)

    def clear(self) -> None:
        """Clear the page details cache."""
        self._cached.cache_clear()
