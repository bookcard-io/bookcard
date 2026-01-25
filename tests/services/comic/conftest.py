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

"""Shared fixtures for comic service tests."""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from bookcard.services.comic.archive.service import (
    ComicArchiveService,
    create_comic_archive_service,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@pytest.fixture
def comic_archive_service() -> ComicArchiveService:
    """Create an isolated `ComicArchiveService` for unit tests."""
    svc = create_comic_archive_service(cache_size=50)
    svc.metadata_provider.clear()
    svc.details_provider.clear()
    return svc


@pytest.fixture
def rgb_png_bytes() -> bytes:
    """Create a small RGB PNG image as bytes."""
    img = Image.new("RGB", (100, 80), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def rgba_png_bytes() -> bytes:
    """Create a small RGBA PNG image as bytes."""
    img = Image.new("RGBA", (100, 80), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def make_zip_file() -> Callable[[Path, dict[str, bytes]], Path]:
    """Create a ZIP file with the provided entries.

    Parameters
    ----------
    Path
        Path to write the ZIP to.
    dict[str, bytes]
        Mapping from entry name to bytes content.

    Returns
    -------
    Callable[[Path, dict[str, bytes]], Path]
        Function that writes a ZIP to disk and returns the path.
    """

    def _make(path: Path, entries: dict[str, bytes]) -> Path:
        with zipfile.ZipFile(path, "w") as zf:
            for name, data in entries.items():
                zf.writestr(name, data)
        return path

    return _make


@pytest.fixture
def make_zip_bytes() -> Callable[[dict[str, bytes]], bytes]:
    """Create ZIP bytes for the provided entries."""

    def _make(entries: dict[str, bytes]) -> bytes:
        bio = BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            for name, data in entries.items():
                zf.writestr(name, data)
        return bio.getvalue()

    return _make
