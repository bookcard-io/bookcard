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

"""CBZ (ZIP) handler."""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

from bookcard.services.comic.archive.exceptions import (
    ArchiveCorruptedError,
    ArchiveReadError,
)
from bookcard.services.comic.archive.handlers.base import ArchiveHandler
from bookcard.services.comic.archive.models import (
    ArchiveMetadata,
    PageDetails,
    ZipArchiveMetadata,
)
from bookcard.services.comic.archive.utils import (
    is_image_entry,
    natural_sort_key,
    validate_archive_entry_name,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.services.comic.archive.image_processor import ImageProcessor
    from bookcard.services.comic.archive.zip_encoding import ZipEncodingDetector


class CBZHandler(ArchiveHandler):
    """CBZ handler (ZIP-based comic archive)."""

    def __init__(self, encoding_detector: ZipEncodingDetector) -> None:
        """Create a CBZ handler.

        Parameters
        ----------
        encoding_detector : ZipEncodingDetector
            ZIP filename encoding detector.
        """
        self._encoding_detector = encoding_detector

    def scan_metadata(
        self, file_path: Path, *, last_modified_ns: int
    ) -> ZipArchiveMetadata:
        """Scan a CBZ archive and return metadata."""
        probe = self._encoding_detector.probe_path(file_path)
        page_names = [n for n in probe.filenames if is_image_entry(n)]
        for name in page_names:
            validate_archive_entry_name(name)

        page_names_sorted = tuple(sorted(page_names, key=natural_sort_key))
        return ZipArchiveMetadata(
            page_filenames=page_names_sorted,
            last_modified_ns=last_modified_ns,
            metadata_encoding=probe.encoding,
        )

    def extract_page(
        self,
        file_path: Path,
        *,
        filename: str,
        metadata: ArchiveMetadata,
    ) -> bytes:
        """Extract one image entry from a CBZ."""
        if not isinstance(metadata, ZipArchiveMetadata):
            msg = "CBZ handler received non-zip metadata"
            raise ArchiveReadError(msg)

        validate_archive_entry_name(filename)
        try:
            if metadata.metadata_encoding is None:
                with zipfile.ZipFile(file_path, "r") as zf:
                    return zf.read(filename)
            with zipfile.ZipFile(
                file_path, "r", metadata_encoding=metadata.metadata_encoding
            ) as zf:
                return zf.read(filename)
        except zipfile.BadZipFile as e:
            msg = f"Invalid CBZ archive: {file_path}: {e}"
            raise ArchiveCorruptedError(msg) from e
        except KeyError as e:
            # Filename was in metadata, but the archive changed between calls
            msg = f"Missing CBZ entry {filename!r} in {file_path}"
            raise ArchiveReadError(msg) from e
        except OSError as e:
            msg = f"Failed to read CBZ {file_path}: {e}"
            raise ArchiveReadError(msg) from e

    def get_page_details(
        self,
        file_path: Path,
        *,
        metadata: ArchiveMetadata,
        include_dimensions: bool,
        image_processor: ImageProcessor,
    ) -> dict[str, PageDetails]:
        """Get per-page sizes and optional dimensions for a CBZ."""
        if not isinstance(metadata, ZipArchiveMetadata):
            msg = "CBZ handler received non-zip metadata"
            raise ArchiveReadError(msg)

        details: dict[str, PageDetails] = {}
        try:
            if metadata.metadata_encoding is None:
                with zipfile.ZipFile(file_path, "r") as zf:
                    details = _cbz_details_from_zip(
                        zf,
                        metadata.page_filenames,
                        include_dimensions=include_dimensions,
                        image_processor=image_processor,
                    )
            else:
                with zipfile.ZipFile(
                    file_path, "r", metadata_encoding=metadata.metadata_encoding
                ) as zf:
                    details = _cbz_details_from_zip(
                        zf,
                        metadata.page_filenames,
                        include_dimensions=include_dimensions,
                        image_processor=image_processor,
                    )
        except zipfile.BadZipFile as e:
            msg = f"Invalid CBZ archive: {file_path}: {e}"
            raise ArchiveCorruptedError(msg) from e
        except OSError as e:
            msg = f"Failed to read CBZ {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        return details


def _cbz_details_from_zip(
    zf: zipfile.ZipFile,
    filenames: tuple[str, ...],
    *,
    include_dimensions: bool,
    image_processor: ImageProcessor,
) -> dict[str, PageDetails]:
    details: dict[str, PageDetails] = {}
    for name in filenames:
        validate_archive_entry_name(name)
        info = zf.getinfo(name)
        width: int | None = None
        height: int | None = None
        if include_dimensions:
            data = zf.read(name)
            width, height = image_processor.get_dimensions(data)
        details[name] = PageDetails(
            file_size=info.file_size, width=width, height=height
        )
    return details
