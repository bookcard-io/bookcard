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

"""High-level comic archive service.

This module wires together:
- format handlers (CBZ/CBR/CB7/CBC)
- metadata caching (LRU)
- image processing (dimensions)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bookcard.services.comic.archive.exceptions import (
    PageNotFoundError,
    UnsupportedFormatError,
)
from bookcard.services.comic.archive.handlers import (
    CB7Handler,
    CBCHandler,
    CBRHandler,
    CBZHandler,
)
from bookcard.services.comic.archive.image_processor import ImageProcessor
from bookcard.services.comic.archive.metadata_provider import LruArchiveMetadataProvider
from bookcard.services.comic.archive.models import (
    ArchiveMetadata,
    ComicPage,
    ComicPageInfo,
)
from bookcard.services.comic.archive.page_details_provider import LruPageDetailsProvider
from bookcard.services.comic.archive.zip_encoding import ZipEncodingDetector

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.services.comic.archive.handlers.base import ArchiveHandler

DEFAULT_ZIP_METADATA_ENCODINGS: tuple[str, ...] = (
    "utf-8",
    "shift_jis",
    "iso-8859-1",
    "cp437",
    "ms932",
)


@dataclass
class ComicArchiveService:
    """Service for extracting pages from comic book archives."""

    handlers: dict[str, ArchiveHandler]
    metadata_provider: LruArchiveMetadataProvider
    details_provider: LruPageDetailsProvider
    image_processor: ImageProcessor

    def register_handler(self, extension: str, handler: ArchiveHandler) -> None:
        """Register or replace an archive handler.

        Parameters
        ----------
        extension : str
            File extension including dot (e.g. ".cbz").
        handler : ArchiveHandler
            Handler implementation.
        """
        self.handlers[extension.lower()] = handler

    def list_pages(
        self, file_path: Path, *, include_dimensions: bool = False
    ) -> list[ComicPageInfo]:
        """List pages in an archive.

        Parameters
        ----------
        file_path : Path
            Archive path.

        Returns
        -------
        list[ComicPageInfo]
            Page info list in display order (1-based).
        """
        metadata = self.metadata_provider.get(file_path)
        details_by_name = self.details_provider.get(
            file_path, include_dimensions=include_dimensions
        )

        pages: list[ComicPageInfo] = []
        for i, name in enumerate(metadata.page_filenames):
            details = details_by_name.get(name)
            if details is None:
                pages.append(
                    ComicPageInfo(
                        page_number=i + 1,
                        filename=name,
                        width=None,
                        height=None,
                        file_size=0,
                    )
                )
            else:
                pages.append(
                    ComicPageInfo(
                        page_number=i + 1,
                        filename=name,
                        width=details.width,
                        height=details.height,
                        file_size=details.file_size,
                    )
                )

        return pages

    def get_page(self, file_path: Path, page_number: int) -> ComicPage:
        """Extract a specific page from an archive.

        Parameters
        ----------
        file_path : Path
            Archive path.
        page_number : int
            Page number (1-based).

        Returns
        -------
        ComicPage
            Extracted page.

        Raises
        ------
        PageNotFoundError
            If the page number is out of range.
        UnsupportedFormatError
            If the file extension is not supported.
        """
        metadata = self.metadata_provider.get(file_path)
        if page_number < 1 or page_number > len(metadata.page_filenames):
            msg = f"Page number {page_number} out of range (1-{len(metadata.page_filenames)})"
            raise PageNotFoundError(msg)

        handler = self._get_handler(file_path)
        filename = metadata.page_filenames[page_number - 1]
        image_data = handler.extract_page(
            file_path, filename=filename, metadata=metadata
        )
        width, height = self.image_processor.get_dimensions(image_data)
        return ComicPage(
            page_number=page_number,
            image_data=image_data,
            filename=filename,
            width=width,
            height=height,
        )

    def _scan_metadata(
        self, file_path: Path, *, last_modified_ns: int
    ) -> ArchiveMetadata:
        handler = self._get_handler(file_path)
        return handler.scan_metadata(file_path, last_modified_ns=last_modified_ns)

    def _get_handler(self, file_path: Path) -> ArchiveHandler:
        suffix = file_path.suffix.lower()
        handler = self.handlers.get(suffix)
        if handler is None:
            msg = f"Unsupported comic format: {suffix}"
            raise UnsupportedFormatError(msg)
        return handler


def create_comic_archive_service(
    *,
    zip_metadata_encodings: tuple[str, ...] = DEFAULT_ZIP_METADATA_ENCODINGS,
    cache_size: int = 50,
) -> ComicArchiveService:
    """Create a production-configured comic archive service.

    Parameters
    ----------
    zip_metadata_encodings : tuple[str, ...]
        Encodings to probe for ZIP filename decoding (CBZ and CBC inner CBZ).
    cache_size : int
        Maximum number of archive metadata entries to keep in LRU.

    Returns
    -------
    ComicArchiveService
        Configured service instance.
    """
    encoding_detector = ZipEncodingDetector(encodings=zip_metadata_encodings)
    cbz = CBZHandler(encoding_detector)
    cbc = CBCHandler(encoding_detector)
    cbr = CBRHandler()
    cb7 = CB7Handler()

    handlers: dict[str, ArchiveHandler] = {
        ".cbz": cbz,
        ".cbc": cbc,
        ".cbr": cbr,
        ".cb7": cb7,
    }

    def scan(file_path: Path, *, last_modified_ns: int) -> ArchiveMetadata:
        suffix = file_path.suffix.lower()
        handler = handlers.get(suffix)
        if handler is None:
            msg = f"Unsupported comic format: {suffix}"
            raise UnsupportedFormatError(msg)
        return handler.scan_metadata(file_path, last_modified_ns=last_modified_ns)

    provider = LruArchiveMetadataProvider(scanner=scan, maxsize=cache_size)
    image_processor = ImageProcessor()
    details_provider = LruPageDetailsProvider(
        handlers=handlers,
        metadata_provider=provider,
        image_processor=image_processor,
        maxsize=cache_size,
    )
    return ComicArchiveService(
        handlers=handlers,
        metadata_provider=provider,
        details_provider=details_provider,
        image_processor=image_processor,
    )
