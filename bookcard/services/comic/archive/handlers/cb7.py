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

"""CB7 (7z) handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.services.comic.archive.exceptions import ArchiveReadError
from bookcard.services.comic.archive.handlers.base import ArchiveHandler
from bookcard.services.comic.archive.models import ArchiveMetadata, PageDetails
from bookcard.services.comic.archive.utils import (
    is_image_entry,
    natural_sort_key,
    validate_archive_entry_name,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.services.comic.archive.image_processor import ImageProcessor


class CB7Handler(ArchiveHandler):
    """CB7 handler (7z-based comic archive)."""

    def scan_metadata(
        self, file_path: Path, *, last_modified_ns: int
    ) -> ArchiveMetadata:
        """Scan a CB7 archive and return metadata."""
        try:
            import py7zr
        except ImportError as e:
            msg = "py7zr library required for CB7 support"
            raise ArchiveReadError(msg) from e

        try:
            with py7zr.SevenZipFile(file_path, "r") as z:
                names = z.getnames()
        except OSError as e:
            msg = f"Failed to read CB7 {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        page_names = [n for n in names if is_image_entry(n)]
        for name in page_names:
            validate_archive_entry_name(name)

        return ArchiveMetadata(
            page_filenames=tuple(sorted(page_names, key=natural_sort_key)),
            last_modified_ns=last_modified_ns,
        )

    def extract_page(
        self,
        file_path: Path,
        *,
        filename: str,
        metadata: ArchiveMetadata,
    ) -> bytes:
        """Extract one image entry from a CB7."""
        _ = metadata  # required by interface; unused for CB7
        try:
            import py7zr
        except ImportError as e:
            msg = "py7zr library required for CB7 support"
            raise ArchiveReadError(msg) from e

        validate_archive_entry_name(filename)
        try:
            with py7zr.SevenZipFile(file_path, "r") as z:
                file_data = z.read([filename])
                return file_data[filename].read()
        except (KeyError, OSError) as e:
            msg = f"Failed to extract {filename!r} from CB7 {file_path}: {e}"
            raise ArchiveReadError(msg) from e

    def get_page_details(
        self,
        file_path: Path,
        *,
        metadata: ArchiveMetadata,
        include_dimensions: bool,
        image_processor: ImageProcessor,
    ) -> dict[str, PageDetails]:
        """Get per-page sizes and optional dimensions for a CB7."""
        try:
            import py7zr
        except ImportError as e:
            msg = "py7zr library required for CB7 support"
            raise ArchiveReadError(msg) from e

        details: dict[str, PageDetails] = {}
        try:
            with py7zr.SevenZipFile(file_path, "r") as z:
                size_by_name: dict[str, int] = {}
                for entry in z.list():
                    name = getattr(entry, "filename", None) or getattr(
                        entry, "name", None
                    )
                    if not isinstance(name, str):
                        continue
                    raw_size = (
                        getattr(entry, "uncompressed", None)
                        or getattr(entry, "uncompressed_size", None)
                        or getattr(entry, "size", None)
                    )
                    if isinstance(raw_size, int):
                        size_by_name[name] = raw_size

                for name in metadata.page_filenames:
                    validate_archive_entry_name(name)
                    file_size = int(size_by_name.get(name, 0) or 0)
                    width: int | None = None
                    height: int | None = None
                    if include_dimensions:
                        file_data = z.read([name])
                        data = file_data[name].read()
                        width, height = image_processor.get_dimensions(data)
                    details[name] = PageDetails(
                        file_size=file_size, width=width, height=height
                    )
        except OSError as e:
            msg = f"Failed to read CB7 {file_path}: {e}"
            raise ArchiveReadError(msg) from e
        except (KeyError, ValueError) as e:
            msg = f"Failed to extract entries from CB7 {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        return details
