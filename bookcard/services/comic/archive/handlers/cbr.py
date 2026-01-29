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

"""CBR (RAR) handler."""

from __future__ import annotations

import subprocess  # noqa: S404
from typing import TYPE_CHECKING

import rarfile

from bookcard.services.comic.archive.exceptions import ArchiveReadError
from bookcard.services.comic.archive.handlers.base import ArchiveHandler
from bookcard.services.comic.archive.models import ArchiveMetadata, PageDetails
from bookcard.services.comic.archive.rar_extractor import extract_member_with_bsdtar
from bookcard.services.comic.archive.utils import (
    is_image_entry,
    natural_sort_key,
    validate_archive_entry_name,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.services.comic.archive.image_processor import ImageProcessor


class CBRHandler(ArchiveHandler):
    """CBR handler (RAR-based comic archive)."""

    def scan_metadata(
        self, file_path: Path, *, last_modified_ns: int
    ) -> ArchiveMetadata:
        """Scan a CBR archive and return metadata."""
        try:
            with rarfile.RarFile(file_path, "r") as rf:
                names = rf.namelist()
        except (rarfile.Error, OSError) as e:
            msg = f"Failed to read CBR {file_path}: {e}"
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
        """Extract one image entry from a CBR."""
        _ = metadata  # required by interface; unused for CBR
        validate_archive_entry_name(filename)
        try:
            with rarfile.RarFile(file_path, "r") as rf:
                try:
                    return rf.read(filename)
                except rarfile.BadRarFile:
                    # `rarfile` delegates extraction to external tools. In some
                    # environments, its tool backend selection can fail even for
                    # valid archives. Prefer a direct `bsdtar` call as a fallback
                    # (if available), as it has proven more reliable for CBRs.
                    #
                    # If `bsdtar` is unavailable or also fails, we'll surface the
                    # original rarfile error below.
                    return extract_member_with_bsdtar(file_path, filename=filename)
        except (
            rarfile.Error,
            OSError,
            KeyError,
            FileNotFoundError,
            subprocess.CalledProcessError,
        ) as e:
            msg = f"Failed to extract {filename!r} from CBR {file_path}: {e}"
            raise ArchiveReadError(msg) from e

    def get_page_details(
        self,
        file_path: Path,
        *,
        metadata: ArchiveMetadata,
        include_dimensions: bool,
        image_processor: ImageProcessor,
    ) -> dict[str, PageDetails]:
        """Get per-page sizes and optional dimensions for a CBR."""
        details: dict[str, PageDetails] = {}
        try:
            with rarfile.RarFile(file_path, "r") as rf:
                for name in metadata.page_filenames:
                    validate_archive_entry_name(name)
                    file_size = 0
                    try:
                        info = rf.getinfo(name)
                        file_size = int(getattr(info, "file_size", 0) or 0)
                    except (KeyError, AttributeError, TypeError, ValueError):
                        file_size = 0

                    width: int | None = None
                    height: int | None = None
                    if include_dimensions:
                        try:
                            data = rf.read(name)
                        except rarfile.BadRarFile:
                            data = extract_member_with_bsdtar(file_path, filename=name)
                        width, height = image_processor.get_dimensions(data)

                    details[name] = PageDetails(
                        file_size=file_size, width=width, height=height
                    )
        except (
            rarfile.Error,
            OSError,
            FileNotFoundError,
            subprocess.CalledProcessError,
        ) as e:
            msg = f"Failed to read CBR {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        return details
