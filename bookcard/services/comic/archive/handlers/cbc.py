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

"""CBC (collection) handler.

CBC is modeled as a ZIP containing one or more CBZ files. We use the first CBZ
as the content source.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

from bookcard.services.comic.archive.exceptions import (
    ArchiveCorruptedError,
    ArchiveReadError,
)
from bookcard.services.comic.archive.handlers.base import ArchiveHandler
from bookcard.services.comic.archive.models import (
    ArchiveMetadata,
    CbcArchiveMetadata,
    PageDetails,
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


class CBCHandler(ArchiveHandler):
    """CBC handler (ZIP-of-CBZ collection)."""

    def __init__(self, encoding_detector: ZipEncodingDetector) -> None:
        """Create a CBC handler.

        Parameters
        ----------
        encoding_detector : ZipEncodingDetector
            ZIP filename encoding detector used for the inner CBZ.
        """
        self._encoding_detector = encoding_detector

    def scan_metadata(
        self, file_path: Path, *, last_modified_ns: int
    ) -> CbcArchiveMetadata:
        """Scan a CBC archive and return metadata."""
        first_cbz_entry: str | None = None
        try:
            with zipfile.ZipFile(file_path, "r") as outer:
                cbz_entries = [
                    n
                    for n in sorted(outer.namelist())
                    if n.lower().endswith(".cbz") and not n.endswith("/")
                ]
                if not cbz_entries:
                    return CbcArchiveMetadata(
                        page_filenames=(),
                        last_modified_ns=last_modified_ns,
                        metadata_encoding=None,
                        first_cbz_entry=None,
                    )
                first_cbz_entry = cbz_entries[0]
                validate_archive_entry_name(first_cbz_entry)
                inner_bytes = outer.read(first_cbz_entry)
        except zipfile.BadZipFile as e:
            msg = f"Invalid CBC archive: {file_path}: {e}"
            raise ArchiveCorruptedError(msg) from e
        except OSError as e:
            msg = f"Failed to read CBC {file_path}: {e}"
            raise ArchiveReadError(msg) from e
        except KeyError as e:
            msg = f"Missing CBC entry {first_cbz_entry!r} in {file_path}"
            raise ArchiveReadError(msg) from e

        probe = self._encoding_detector.probe_bytes(
            inner_bytes, label=f"{file_path}!{first_cbz_entry}"
        )
        page_names = [n for n in probe.filenames if is_image_entry(n)]
        for name in page_names:
            validate_archive_entry_name(name)

        return CbcArchiveMetadata(
            page_filenames=tuple(sorted(page_names, key=natural_sort_key)),
            last_modified_ns=last_modified_ns,
            metadata_encoding=probe.encoding,
            first_cbz_entry=first_cbz_entry,
        )

    def extract_page(
        self,
        file_path: Path,
        *,
        filename: str,
        metadata: ArchiveMetadata,
    ) -> bytes:
        """Extract one image entry from the first CBZ inside the CBC."""
        if not isinstance(metadata, CbcArchiveMetadata):
            msg = "CBC handler received non-CBC metadata"
            raise ArchiveReadError(msg)

        if not metadata.first_cbz_entry:
            msg = f"No CBZ entries found in CBC {file_path}"
            raise ArchiveReadError(msg)

        validate_archive_entry_name(filename)

        try:
            with zipfile.ZipFile(file_path, "r") as outer:
                inner_bytes = outer.read(metadata.first_cbz_entry)
        except zipfile.BadZipFile as e:
            msg = f"Invalid CBC archive: {file_path}: {e}"
            raise ArchiveCorruptedError(msg) from e
        except (KeyError, OSError) as e:
            msg = f"Failed to read inner CBZ {metadata.first_cbz_entry!r} from CBC {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        try:
            bio = BytesIO(inner_bytes)
            if metadata.metadata_encoding is None:
                with zipfile.ZipFile(bio, "r") as inner:
                    return inner.read(filename)
            with zipfile.ZipFile(
                bio, "r", metadata_encoding=metadata.metadata_encoding
            ) as inner:
                return inner.read(filename)
        except zipfile.BadZipFile as e:
            msg = (
                f"Invalid inner CBZ in CBC {file_path}!{metadata.first_cbz_entry}: {e}"
            )
            raise ArchiveCorruptedError(msg) from e
        except KeyError as e:
            msg = f"Missing CBZ entry {filename!r} in CBC {file_path}!{metadata.first_cbz_entry}"
            raise ArchiveReadError(msg) from e
        except OSError as e:
            msg = f"Failed to read CBZ entry {filename!r} in CBC {file_path}!{metadata.first_cbz_entry}: {e}"
            raise ArchiveReadError(msg) from e

    def get_page_details(
        self,
        file_path: Path,
        *,
        metadata: ArchiveMetadata,
        include_dimensions: bool,
        image_processor: ImageProcessor,
    ) -> dict[str, PageDetails]:
        """Get per-page sizes and optional dimensions for the first CBZ in a CBC."""
        if not isinstance(metadata, CbcArchiveMetadata):
            msg = "CBC handler received non-CBC metadata"
            raise ArchiveReadError(msg)

        if not metadata.first_cbz_entry:
            return {
                name: PageDetails(file_size=0, width=None, height=None)
                for name in metadata.page_filenames
            }

        try:
            with zipfile.ZipFile(file_path, "r") as outer:
                inner_bytes = outer.read(metadata.first_cbz_entry)
        except zipfile.BadZipFile as e:
            msg = f"Invalid CBC archive: {file_path}: {e}"
            raise ArchiveCorruptedError(msg) from e
        except (KeyError, OSError) as e:
            msg = f"Failed to read inner CBZ {metadata.first_cbz_entry!r} from CBC {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        details: dict[str, PageDetails] = {}
        try:
            bio = BytesIO(inner_bytes)
            if metadata.metadata_encoding is None:
                with zipfile.ZipFile(bio, "r") as inner:
                    details = _cbc_details_from_zip(
                        inner,
                        metadata.page_filenames,
                        include_dimensions=include_dimensions,
                        image_processor=image_processor,
                    )
            else:
                with zipfile.ZipFile(
                    bio, "r", metadata_encoding=metadata.metadata_encoding
                ) as inner:
                    details = _cbc_details_from_zip(
                        inner,
                        metadata.page_filenames,
                        include_dimensions=include_dimensions,
                        image_processor=image_processor,
                    )
        except zipfile.BadZipFile as e:
            msg = (
                f"Invalid inner CBZ in CBC {file_path}!{metadata.first_cbz_entry}: {e}"
            )
            raise ArchiveCorruptedError(msg) from e
        except OSError as e:
            msg = f"Failed to read inner CBZ bytes in CBC {file_path}: {e}"
            raise ArchiveReadError(msg) from e

        return details


def _cbc_details_from_zip(
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
