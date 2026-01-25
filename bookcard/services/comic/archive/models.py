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

"""Models for comic archive page information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComicPageInfo:
    """Information about a comic page.

    Attributes
    ----------
    page_number : int
        Page number (1-based index).
    filename : str
        Original filename in archive.
    width : int | None
        Image width in pixels, if known.
    height : int | None
        Image height in pixels, if known.
    file_size : int
        Uncompressed file size in bytes, if known.
    """

    page_number: int
    filename: str
    width: int | None
    height: int | None
    file_size: int


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class ArchiveMetadata:
    """Base archive metadata.

    Attributes
    ----------
    page_filenames : tuple[str, ...]
        Natural-sorted list of image entry names.
    last_modified_ns : int
        Last modified time (ns) used to validate cache entries.
    """

    page_filenames: tuple[str, ...]
    last_modified_ns: int


@dataclass(frozen=True)
class ZipArchiveMetadata(ArchiveMetadata):
    """ZIP-based archive metadata.

    Attributes
    ----------
    metadata_encoding : str | None
        ZIP filename decoding used to read entry names.
    """

    metadata_encoding: str | None


@dataclass(frozen=True)
class CbcArchiveMetadata(ZipArchiveMetadata):
    """CBC metadata (ZIP containing one or more CBZ files).

    Attributes
    ----------
    first_cbz_entry : str | None
        The selected CBZ entry inside the CBC.
    """

    first_cbz_entry: str | None


@dataclass(frozen=True)
class PageDetails:
    """Per-page details used to enrich page listings.

    Attributes
    ----------
    file_size : int
        Uncompressed entry size in bytes.
    width : int | None
        Image width in pixels, if computed.
    height : int | None
        Image height in pixels, if computed.
    """

    file_size: int
    width: int | None
    height: int | None
