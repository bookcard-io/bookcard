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

"""Comic archive service for extracting pages from comic book archives.

Supports CBZ (ZIP), CBR (RAR), CB7 (7z), and CBC (collection) formats.
Follows SRP by focusing solely on archive extraction and page management.
"""

from __future__ import annotations

import re
import tempfile
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import rarfile
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Callable

# Image extensions supported by comic archives
IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
)


@dataclass
class ComicPageInfo:
    """Information about a comic page.

    Attributes
    ----------
    page_number : int
        Page number (1-based index).
    filename : str
        Original filename in archive.
    width : int | None
        Image width in pixels (None if not yet determined).
    height : int | None
        Image height in pixels (None if not yet determined).
    file_size : int
        File size in bytes.
    """

    page_number: int
    filename: str
    width: int | None = None
    height: int | None = None
    file_size: int = 0


@dataclass
class ComicPage:
    """Comic page with image data.

    Attributes
    ----------
    page_number : int
        Page number (1-based index).
    image_data : bytes
        Raw image data.
    filename : str
        Original filename in archive.
    width : int
        Image width in pixels.
    height : int
        Image height in pixels.
    """

    page_number: int
    image_data: bytes
    filename: str
    width: int
    height: int


def _natural_sort_key(filename: str) -> tuple[int | str, ...]:
    """Generate sort key for natural sorting of filenames.

    Handles numeric sequences in filenames (e.g., "page_001.jpg" vs "page_10.jpg").

    Parameters
    ----------
    filename : str
        Filename to generate sort key for.

    Returns
    -------
    tuple[int | str, ...]
        Sort key tuple.
    """
    parts: list[int | str] = []
    for part in re.split(r"(\d+)", filename):
        if part.isdigit():
            parts.append(int(part))
        else:
            parts.append(part.lower())
    return tuple(parts)


class ComicArchiveService:
    """Service for extracting pages from comic book archives.

    Supports CBZ (ZIP), CBR (RAR), CB7 (7z), and CBC (collection) formats.
    Follows SRP by focusing solely on archive extraction.
    Uses Strategy pattern for different archive formats.
    """

    def __init__(self) -> None:
        """Initialize comic archive service."""
        # Strategy pattern: map file suffixes to extraction methods
        self._extraction_strategies: dict[str, Callable[[Path], list[str]]] = {
            ".cbz": self._list_cbz_pages,
            ".cbr": self._list_cbr_pages,
            ".cb7": self._list_cb7_pages,
            ".cbc": self._list_cbc_pages,
        }

    def is_comic_format(self, file_format: str) -> bool:
        """Check if format is a supported comic book format.

        Parameters
        ----------
        file_format : str
            File format string (e.g., 'CBZ', 'CBR').

        Returns
        -------
        bool
            True if format is supported.
        """
        format_upper = file_format.upper().lstrip(".")
        return format_upper in ("CBZ", "CBR", "CB7", "CBC")

    def list_pages(self, file_path: Path) -> list[ComicPageInfo]:
        """List all pages in a comic archive.

        Parameters
        ----------
        file_path : Path
            Path to the comic archive file.

        Returns
        -------
        list[ComicPageInfo]
            List of page information, sorted by natural filename order.

        Raises
        ------
        ValueError
            If file format is not supported or file cannot be read.
        """
        suffix = file_path.suffix.lower()
        if suffix not in self._extraction_strategies:
            msg = f"Unsupported comic format: {suffix}"
            raise ValueError(msg)

        list_method = self._extraction_strategies[suffix]
        try:
            page_filenames = list_method(file_path)
        except Exception as e:
            msg = f"Failed to list pages from {file_path}: {e}"
            raise ValueError(msg) from e

        # Sort pages using natural sort
        page_filenames.sort(key=_natural_sort_key)

        # Build page info list
        pages: list[ComicPageInfo] = []
        for idx, filename in enumerate(page_filenames, start=1):
            pages.append(
                ComicPageInfo(
                    page_number=idx,
                    filename=filename,
                ),
            )

        return pages

    def get_page(
        self,
        file_path: Path,
        page_number: int,
    ) -> ComicPage:
        """Get a specific page from a comic archive.

        Parameters
        ----------
        file_path : Path
            Path to the comic archive file.
        page_number : int
            Page number (1-based).

        Returns
        -------
        ComicPage
            Page with image data and metadata.

        Raises
        ------
        ValueError
            If page number is invalid or page cannot be extracted.
        IndexError
            If page number is out of range.
        """
        pages = self.list_pages(file_path)
        if page_number < 1 or page_number > len(pages):
            msg = f"Page number {page_number} out of range (1-{len(pages)})"
            raise IndexError(msg)

        page_info = pages[page_number - 1]
        suffix = file_path.suffix.lower()

        # Extract page data based on format
        if suffix == ".cbz":
            image_data = self._extract_cbz_page(file_path, page_info.filename)
        elif suffix == ".cbr":
            image_data = self._extract_cbr_page(file_path, page_info.filename)
        elif suffix == ".cb7":
            image_data = self._extract_cb7_page(file_path, page_info.filename)
        elif suffix == ".cbc":
            image_data = self._extract_cbc_page(file_path, page_info.filename)
        else:
            msg = f"Unsupported comic format: {suffix}"
            raise ValueError(msg)

        # Get image dimensions
        try:
            img = Image.open(BytesIO(image_data))
            width, height = img.size
        except Exception as e:
            msg = f"Failed to read image dimensions: {e}"
            raise ValueError(msg) from e

        return ComicPage(
            page_number=page_number,
            image_data=image_data,
            filename=page_info.filename,
            width=width,
            height=height,
        )

    def _list_cbz_pages(self, file_path: Path) -> list[str]:
        """List page filenames from CBZ (ZIP archive).

        Parameters
        ----------
        file_path : Path
            Path to CBZ file.

        Returns
        -------
        list[str]
            List of image filenames.
        """
        with zipfile.ZipFile(file_path, "r") as cbz_zip:
            return [
                f
                for f in cbz_zip.namelist()
                if f.lower().endswith(IMAGE_EXTENSIONS) and not f.endswith("/")
            ]

    def _list_cbr_pages(self, file_path: Path) -> list[str]:
        """List page filenames from CBR (RAR archive).

        Parameters
        ----------
        file_path : Path
            Path to CBR file.

        Returns
        -------
        list[str]
            List of image filenames.

        Raises
        ------
        ImportError
            If rarfile library is not available.
        """
        with rarfile.RarFile(file_path, "r") as cbr_rar:
            return [
                f
                for f in cbr_rar.namelist()
                if f.lower().endswith(IMAGE_EXTENSIONS) and not f.endswith("/")
            ]

    def _list_cb7_pages(self, file_path: Path) -> list[str]:
        """List page filenames from CB7 (7z archive).

        Parameters
        ----------
        file_path : Path
            Path to CB7 file.

        Returns
        -------
        list[str]
            List of image filenames.

        Raises
        ------
        ImportError
            If py7zr library is not available.
        """
        try:
            import py7zr  # type: ignore[import-untyped]
        except ImportError as e:
            msg = "py7zr library required for CB7 support"
            raise ImportError(msg) from e

        with py7zr.SevenZipFile(file_path, "r") as cb7_7z:
            return [
                f
                for f in cb7_7z.getnames()
                if f.lower().endswith(IMAGE_EXTENSIONS) and not f.endswith("/")
            ]

    def _list_cbc_pages(self, file_path: Path) -> list[str]:
        """List page filenames from CBC (collection archive).

        CBC is a ZIP archive containing multiple CBZ files.
        We extract pages from the first CBZ.

        Parameters
        ----------
        file_path : Path
            Path to CBC file.

        Returns
        -------
        list[str]
            List of image filenames from first CBZ.
        """
        with zipfile.ZipFile(file_path, "r") as cbc_zip:
            # Find CBZ files
            cbz_files = [
                f for f in sorted(cbc_zip.namelist()) if f.lower().endswith(".cbz")
            ]

            if not cbz_files:
                return []

            # Extract first CBZ to temp and process
            first_cbz = cbz_files[0]
            with tempfile.NamedTemporaryFile(suffix=".cbz", delete=False) as temp:
                temp_path = Path(temp.name)
                temp.write(cbc_zip.read(first_cbz))

            try:
                return self._list_cbz_pages(temp_path)
            finally:
                if temp_path.exists():
                    temp_path.unlink()

    def _extract_cbz_page(self, file_path: Path, filename: str) -> bytes:
        """Extract page image from CBZ archive.

        Parameters
        ----------
        file_path : Path
            Path to CBZ file.
        filename : str
            Filename of page in archive.

        Returns
        -------
        bytes
            Image data as bytes.

        Raises
        ------
        KeyError
            If filename not found in archive.
        """
        with zipfile.ZipFile(file_path, "r") as cbz_zip:
            return cbz_zip.read(filename)

    def _extract_cbr_page(self, file_path: Path, filename: str) -> bytes:
        """Extract page image from CBR archive.

        Parameters
        ----------
        file_path : Path
            Path to CBR file.
        filename : str
            Filename of page in archive.

        Returns
        -------
        bytes
            Image data as bytes.

        Raises
        ------
        ImportError
            If rarfile library is not available.
        KeyError
            If filename not found in archive.
        """
        try:
            import rarfile  # type: ignore[import-untyped]
        except ImportError as e:
            msg = "rarfile library required for CBR support"
            raise ImportError(msg) from e

        with rarfile.RarFile(file_path, "r") as cbr_rar:
            return cbr_rar.read(filename)

    def _extract_cb7_page(self, file_path: Path, filename: str) -> bytes:
        """Extract page image from CB7 archive.

        Parameters
        ----------
        file_path : Path
            Path to CB7 file.
        filename : str
            Filename of page in archive.

        Returns
        -------
        bytes
            Image data as bytes.

        Raises
        ------
        ImportError
            If py7zr library is not available.
        KeyError
            If filename not found in archive.
        """
        try:
            import py7zr  # type: ignore[import-untyped]
        except ImportError as e:
            msg = "py7zr library required for CB7 support"
            raise ImportError(msg) from e

        with py7zr.SevenZipFile(file_path, "r") as cb7_7z:
            file_data = cb7_7z.read([filename])
            return file_data[filename].read()

    def _extract_cbc_page(self, file_path: Path, filename: str) -> bytes:
        """Extract page image from CBC archive.

        Parameters
        ----------
        file_path : Path
            Path to CBC file.
        filename : str
            Filename of page in archive (relative to first CBZ).

        Returns
        -------
        bytes
            Image data as bytes.
        """
        with zipfile.ZipFile(file_path, "r") as cbc_zip:
            # Find CBZ files
            cbz_files = [
                f for f in sorted(cbc_zip.namelist()) if f.lower().endswith(".cbz")
            ]

            if not cbz_files:
                msg = "No CBZ files found in CBC archive"
                raise ValueError(msg)

            # Extract first CBZ to temp and process
            first_cbz = cbz_files[0]
            with tempfile.NamedTemporaryFile(suffix=".cbz", delete=False) as temp:
                temp_path = Path(temp.name)
                temp.write(cbc_zip.read(first_cbz))

            try:
                return self._extract_cbz_page(temp_path, filename)
            finally:
                if temp_path.exists():
                    temp_path.unlink()
