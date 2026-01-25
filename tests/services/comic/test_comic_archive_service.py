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

"""Tests for the refactored comic archive service."""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

import pytest

from bookcard.services.comic.archive import PageNotFoundError, UnsupportedFormatError
from bookcard.services.comic.archive.utils import natural_sort_key

if TYPE_CHECKING:
    from pathlib import Path

    from bookcard.services.comic.archive.image_processor import ImageProcessor
    from bookcard.services.comic.archive.models import ArchiveMetadata, PageDetails
    from bookcard.services.comic.archive.service import (
        ComicArchiveService,
    )


@pytest.fixture
def service(comic_archive_service: ComicArchiveService) -> ComicArchiveService:
    """Backward-compatible alias for `comic_archive_service` fixture."""
    return comic_archive_service


def test_natural_sort_key_orders_numeric_parts() -> None:
    names = ["page10.jpg", "page2.jpg", "page1.jpg"]
    assert sorted(names, key=natural_sort_key) == [
        "page1.jpg",
        "page2.jpg",
        "page10.jpg",
    ]


def test_list_pages_cbz(
    service: ComicArchiveService, tmp_path: Path, rgb_png_bytes: bytes
) -> None:
    cbz = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz, "w") as zf:
        zf.writestr("page2.png", rgb_png_bytes)
        zf.writestr("page1.jpg", rgb_png_bytes)

    pages = service.list_pages(cbz)
    assert [p.page_number for p in pages] == [1, 2]
    assert [p.filename for p in pages] == ["page1.jpg", "page2.png"]
    assert [p.file_size for p in pages] == [len(rgb_png_bytes), len(rgb_png_bytes)]
    assert [p.width for p in pages] == [None, None]
    assert [p.height for p in pages] == [None, None]


def test_get_page_cbz(
    service: ComicArchiveService, tmp_path: Path, rgb_png_bytes: bytes
) -> None:
    cbz = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz, "w") as zf:
        zf.writestr("page1.png", rgb_png_bytes)

    page = service.get_page(cbz, 1)
    assert page.page_number == 1
    assert page.filename == "page1.png"
    assert page.image_data == rgb_png_bytes
    assert (page.width, page.height) == (100, 80)


def test_get_page_out_of_range(
    service: ComicArchiveService, tmp_path: Path, rgb_png_bytes: bytes
) -> None:
    cbz = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz, "w") as zf:
        zf.writestr("page1.png", rgb_png_bytes)

    with pytest.raises(PageNotFoundError):
        service.get_page(cbz, 2)


def test_unsupported_format(service: ComicArchiveService, tmp_path: Path) -> None:
    f = tmp_path / "test.epub"
    f.write_bytes(b"nope")
    with pytest.raises(UnsupportedFormatError):
        service.list_pages(f)


def test_metadata_is_cached(
    service: ComicArchiveService, tmp_path: Path, rgb_png_bytes: bytes
) -> None:
    cbz = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz, "w") as zf:
        zf.writestr("page1.png", rgb_png_bytes)

    handler = service.handlers[".cbz"]
    calls = {"n": 0}
    orig = handler.scan_metadata

    def wrapped(path: Path, *, last_modified_ns: int) -> ArchiveMetadata:
        calls["n"] += 1
        return orig(path, last_modified_ns=last_modified_ns)

    handler.scan_metadata = wrapped  # type: ignore[method-assign]
    try:
        _ = service.get_page(cbz, 1)
        _ = service.get_page(cbz, 1)
        assert calls["n"] == 1
    finally:
        handler.scan_metadata = orig  # type: ignore[method-assign]


def test_page_details_are_cached(
    service: ComicArchiveService, tmp_path: Path, rgb_png_bytes: bytes
) -> None:
    """Ensure per-page details are cached for repeated list_pages calls."""
    cbz = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz, "w") as zf:
        zf.writestr("page1.png", rgb_png_bytes)

    handler = service.handlers[".cbz"]
    calls = {"n": 0}
    orig = handler.get_page_details

    def wrapped(
        file_path: Path,
        *,
        metadata: ArchiveMetadata,
        include_dimensions: bool,
        image_processor: ImageProcessor,
    ) -> dict[str, PageDetails]:
        calls["n"] += 1
        return orig(
            file_path,
            metadata=metadata,
            include_dimensions=include_dimensions,
            image_processor=image_processor,
        )

    handler.get_page_details = wrapped  # type: ignore[method-assign]
    try:
        _ = service.list_pages(cbz, include_dimensions=False)
        _ = service.list_pages(cbz, include_dimensions=False)
        assert calls["n"] == 1
    finally:
        handler.get_page_details = orig  # type: ignore[method-assign]
