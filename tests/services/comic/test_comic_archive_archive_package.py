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

"""Comprehensive unit tests for the comic archive package.

These tests are intentionally focused on the refactored comic archive backend:
- handlers (CBZ/CBC/CBR/CB7)
- ZIP encoding detection
- utilities and safety validation
- LRU metadata caching
- image processing
"""

from __future__ import annotations

import builtins
import os
import sys
import types
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Self, cast

import pytest

from bookcard.services.comic.archive import (
    ArchiveCorruptedError,
    ArchiveReadError,
    ImageProcessingError,
    InvalidArchiveEntryNameError,
    UnsupportedFormatError,
    create_comic_archive_service,
)
from bookcard.services.comic.archive.handlers.cb7 import CB7Handler
from bookcard.services.comic.archive.handlers.cbc import CBCHandler
from bookcard.services.comic.archive.handlers.cbr import CBRHandler
from bookcard.services.comic.archive.handlers.cbz import CBZHandler
from bookcard.services.comic.archive.image_processor import ImageProcessor
from bookcard.services.comic.archive.metadata_provider import (
    ArchiveMetadataScanner,
    LruArchiveMetadataProvider,
)
from bookcard.services.comic.archive.models import (
    ArchiveMetadata,
    CbcArchiveMetadata,
    ZipArchiveMetadata,
)
from bookcard.services.comic.archive.page_details_provider import LruPageDetailsProvider
from bookcard.services.comic.archive.service import ComicArchiveService
from bookcard.services.comic.archive.utils import (
    is_image_entry,
    natural_sort_key,
    validate_archive_entry_name,
)
from bookcard.services.comic.archive.zip_encoding import ZipEncodingDetector

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_archive_public_imports_smoke() -> None:
    # Ensures `bookcard.services.comic.archive.__init__` is executed.
    import bookcard.services.comic.archive as archive

    assert hasattr(archive, "ComicArchiveService")
    assert hasattr(archive, "create_comic_archive_service")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("page1.jpg", True),
        ("PAGE1.JPEG", True),
        ("a/b/c.png", True),
        ("folder/", False),
        ("folder/page1.png/", False),
        ("page1.txt", False),
    ],
)
def test_is_image_entry(name: str, expected: bool) -> None:
    assert is_image_entry(name) is expected


@pytest.mark.parametrize(
    "name",
    [
        "",
        "/abs/path.png",
        "../traversal.png",
        "a/../b.png",
        r"..\evil.png",
        r"a\..\b.png",
    ],
)
def test_validate_archive_entry_name_rejects_unsafe(name: str) -> None:
    with pytest.raises(InvalidArchiveEntryNameError):
        validate_archive_entry_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "page1.png",
        "nested/page2.jpg",
        "nested\\page3.jpeg",
        "a/b/c.webp",
    ],
)
def test_validate_archive_entry_name_accepts_safe(name: str) -> None:
    validate_archive_entry_name(name)


def test_natural_sort_key_is_case_insensitive_and_numeric() -> None:
    names = ["Page10.jpg", "page2.jpg", "PAGE1.jpg"]
    assert sorted(names, key=natural_sort_key) == [
        "PAGE1.jpg",
        "page2.jpg",
        "Page10.jpg",
    ]


def test_image_processor_success(rgb_png_bytes: bytes) -> None:
    width, height = ImageProcessor().get_dimensions(rgb_png_bytes)
    assert (width, height) == (100, 80)


def test_image_processor_invalid_bytes_raises() -> None:
    with pytest.raises(ImageProcessingError):
        _ = ImageProcessor().get_dimensions(b"not an image")


def test_lru_metadata_provider_caches_by_path_and_mtime(tmp_path: Path) -> None:
    p = tmp_path / "a.cbz"
    p.write_bytes(b"dummy")

    calls: list[tuple[str, int]] = []

    def scan(path: Path, *, last_modified_ns: int) -> ArchiveMetadata:
        calls.append((str(path), last_modified_ns))
        return ArchiveMetadata(
            page_filenames=("page1.png",), last_modified_ns=last_modified_ns
        )

    provider = LruArchiveMetadataProvider(
        scanner=cast("ArchiveMetadataScanner", scan),
        maxsize=5,
    )

    m1 = provider.get(p)
    m2 = provider.get(p)
    assert m1 == m2
    assert len(calls) == 1

    # Force mtime change to invalidate cache key
    before = p.stat().st_mtime_ns
    os.utime(p, ns=(before, before + 2_000_000_000))
    _ = provider.get(p)
    assert len(calls) == 2


def test_lru_metadata_provider_stat_failure_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.cbz"
    provider = LruArchiveMetadataProvider(
        scanner=cast(
            "ArchiveMetadataScanner",
            lambda _p, *, last_modified_ns: ArchiveMetadata(
                page_filenames=(), last_modified_ns=last_modified_ns
            ),
        ),
        maxsize=1,
    )
    with pytest.raises(ArchiveReadError):
        _ = provider.get(missing)


class _FakeZip:
    def __init__(self, names: list[str]) -> None:
        self._names = names

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False

    def namelist(self) -> list[str]:
        return list(self._names)


def test_zip_encoding_detector_probes_preferred_first() -> None:
    detector = ZipEncodingDetector(encodings=("a", "b", "c"))
    seen: list[str | None] = []

    def opener(enc: str | None) -> _FakeZip:
        seen.append(enc)
        if enc == "b":
            return _FakeZip(["x"])
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "boom")

    result = detector._probe(opener, preferred="b", label="test")  # type: ignore[attr-defined]
    assert result.encoding == "b"
    assert seen[0] == "b"


@pytest.mark.parametrize(
    ("exc", "expected_type"),
    [
        (zipfile.BadZipFile("bad"), ArchiveCorruptedError),
        (OSError("nope"), ArchiveReadError),
    ],
)
def test_zip_encoding_detector_non_decode_errors_raise(
    exc: Exception, expected_type: type[Exception]
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))

    def opener(_enc: str | None) -> _FakeZip:
        raise exc

    with pytest.raises(expected_type):
        _ = detector._probe(opener, preferred=None, label="x")  # type: ignore[attr-defined]


def test_zip_encoding_detector_fallback_to_default_behavior() -> None:
    detector = ZipEncodingDetector(encodings=("a", "b"))

    def opener(enc: str | None) -> _FakeZip:
        if enc is None:
            return _FakeZip(["ok.png"])
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "boom")

    result = detector._probe(opener, preferred=None, label="x")  # type: ignore[attr-defined]
    assert result.encoding is None
    assert result.filenames == ["ok.png"]


def test_zip_encoding_detector_fallback_decode_failure_raises() -> None:
    detector = ZipEncodingDetector(encodings=("a",))

    def opener(_enc: str | None) -> _FakeZip:
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "boom")

    with pytest.raises(ArchiveReadError, match=r"Failed to decode ZIP filenames"):
        _ = detector._probe(opener, preferred=None, label="x")  # type: ignore[attr-defined]


def test_zip_encoding_detector_probe_bytes_and_path_smoke(
    tmp_path: Path, make_zip_bytes: Callable[[dict[str, bytes]], bytes]
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    data = make_zip_bytes({"page1.png": b"x"})
    res_bytes = detector.probe_bytes(data, label="bytes")
    assert res_bytes.encoding == "utf-8"
    assert "page1.png" in res_bytes.filenames

    p = tmp_path / "a.zip"
    p.write_bytes(data)
    res_path = detector.probe_path(p)
    assert res_path.encoding == "utf-8"
    assert "page1.png" in res_path.filenames


def test_cbz_handler_scan_and_extract_branches(
    tmp_path: Path,
    make_zip_file: Callable[[Path, dict[str, bytes]], Path],
    rgb_png_bytes: bytes,
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBZHandler(detector)
    cbz = make_zip_file(
        tmp_path / "a.cbz",
        {
            "page2.png": rgb_png_bytes,
            "page1.jpg": rgb_png_bytes,
            "not_an_image.txt": b"x",
        },
    )

    md = handler.scan_metadata(cbz, last_modified_ns=123)
    assert md.page_filenames == ("page1.jpg", "page2.png")
    assert md.metadata_encoding == "utf-8"

    # extract_page: metadata_encoding not None branch
    data = handler.extract_page(cbz, filename="page1.jpg", metadata=md)
    assert data == rgb_png_bytes

    # extract_page: wrong metadata type
    with pytest.raises(ArchiveReadError, match="non-zip metadata"):
        _ = handler.extract_page(
            cbz,
            filename="page1.jpg",
            metadata=ArchiveMetadata(page_filenames=("page1.jpg",), last_modified_ns=1),
        )

    # extract_page: KeyError branch (metadata references missing entry)
    with pytest.raises(ArchiveReadError, match="Missing CBZ entry"):
        _ = handler.extract_page(
            cbz,
            filename="missing.png",
            metadata=ZipArchiveMetadata(
                page_filenames=("missing.png",),
                last_modified_ns=1,
                metadata_encoding=None,
            ),
        )

    # extract_page: BadZipFile branch
    bad = tmp_path / "bad.cbz"
    bad.write_bytes(b"not a zip")
    with pytest.raises(ArchiveCorruptedError):
        _ = handler.extract_page(
            bad,
            filename="page1.jpg",
            metadata=ZipArchiveMetadata(
                page_filenames=("page1.jpg",),
                last_modified_ns=1,
                metadata_encoding=None,
            ),
        )


def test_cbz_handler_scan_rejects_unsafe_entries(
    tmp_path: Path,
    make_zip_file: Callable[[Path, dict[str, bytes]], Path],
    rgb_png_bytes: bytes,
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBZHandler(detector)
    cbz = make_zip_file(
        tmp_path / "evil.cbz",
        {"../evil.png": rgb_png_bytes},
    )
    with pytest.raises(InvalidArchiveEntryNameError):
        _ = handler.scan_metadata(cbz, last_modified_ns=1)


def test_cbc_handler_no_cbz_entries(
    tmp_path: Path, make_zip_file: Callable[[Path, dict[str, bytes]], Path]
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)
    cbc = make_zip_file(tmp_path / "a.cbc", {"note.txt": b"x"})
    md = handler.scan_metadata(cbc, last_modified_ns=10)
    assert md.page_filenames == ()
    assert md.first_cbz_entry is None


def test_cbc_handler_scan_and_extract_success(
    tmp_path: Path,
    make_zip_file: Callable[[Path, dict[str, bytes]], Path],
    make_zip_bytes: Callable[[dict[str, bytes]], bytes],
    rgb_png_bytes: bytes,
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)

    inner = make_zip_bytes({"page2.png": rgb_png_bytes, "page1.jpg": rgb_png_bytes})
    cbc = make_zip_file(tmp_path / "a.cbc", {"comic.cbz": inner})

    md = handler.scan_metadata(cbc, last_modified_ns=10)
    assert md.first_cbz_entry == "comic.cbz"
    assert md.page_filenames == ("page1.jpg", "page2.png")

    extracted = handler.extract_page(cbc, filename="page2.png", metadata=md)
    assert extracted == rgb_png_bytes


def test_cbc_handler_extract_error_branches(
    tmp_path: Path, make_zip_file: Callable[[Path, dict[str, bytes]], Path]
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)

    cbc = make_zip_file(tmp_path / "a.cbc", {"comic.cbz": b"not a zip"})

    with pytest.raises(ArchiveReadError, match="non-CBC metadata"):
        _ = handler.extract_page(
            cbc,
            filename="page1.png",
            metadata=ArchiveMetadata(page_filenames=("page1.png",), last_modified_ns=1),
        )

    with pytest.raises(ArchiveReadError, match="No CBZ entries found"):
        _ = handler.extract_page(
            cbc,
            filename="page1.png",
            metadata=CbcArchiveMetadata(
                page_filenames=("page1.png",),
                last_modified_ns=1,
                metadata_encoding=None,
                first_cbz_entry=None,
            ),
        )

    with pytest.raises(ArchiveCorruptedError, match="Invalid inner CBZ"):
        _ = handler.extract_page(
            cbc,
            filename="page1.png",
            metadata=CbcArchiveMetadata(
                page_filenames=("page1.png",),
                last_modified_ns=1,
                metadata_encoding=None,
                first_cbz_entry="comic.cbz",
            ),
        )


def test_cbc_handler_outer_bad_zip_raises(tmp_path: Path) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)
    bad = tmp_path / "bad.cbc"
    bad.write_bytes(b"not a zip")

    with pytest.raises(ArchiveCorruptedError):
        _ = handler.scan_metadata(bad, last_modified_ns=1)

    with pytest.raises(ArchiveCorruptedError):
        _ = handler.extract_page(
            bad,
            filename="page1.png",
            metadata=CbcArchiveMetadata(
                page_filenames=("page1.png",),
                last_modified_ns=1,
                metadata_encoding=None,
                first_cbz_entry="comic.cbz",
            ),
        )


def test_create_comic_archive_service_registers_handlers() -> None:
    svc = create_comic_archive_service(cache_size=1, zip_metadata_encodings=("utf-8",))
    assert set(svc.handlers.keys()) == {".cbz", ".cbc", ".cbr", ".cb7"}


def test_comic_archive_service_register_handler_overrides(tmp_path: Path) -> None:
    svc = create_comic_archive_service(cache_size=1, zip_metadata_encodings=("utf-8",))

    @dataclass
    class _DummyHandler:
        def scan_metadata(
            self, _path: Path, *, last_modified_ns: int
        ) -> ArchiveMetadata:
            return ArchiveMetadata(
                page_filenames=("x.png",), last_modified_ns=last_modified_ns
            )

        def extract_page(
            self, _path: Path, *, filename: str, metadata: ArchiveMetadata
        ) -> bytes:
            return b"x"

    dummy = _DummyHandler()
    svc.register_handler(".cbz", dummy)  # type: ignore[arg-type]
    assert svc.handlers[".cbz"] is dummy


def test_comic_archive_service_get_page_unsupported_handler_path(
    tmp_path: Path,
) -> None:
    f = tmp_path / "x.cbz"
    f.write_bytes(b"x")

    def scan(_path: Path, *, last_modified_ns: int) -> ArchiveMetadata:
        return ArchiveMetadata(
            page_filenames=("page1.png",),
            last_modified_ns=last_modified_ns,
        )

    provider = LruArchiveMetadataProvider(
        scanner=cast("ArchiveMetadataScanner", scan),
        maxsize=1,
    )
    details_provider = LruPageDetailsProvider(
        handlers={},
        metadata_provider=provider,
        image_processor=ImageProcessor(),
        maxsize=1,
    )
    svc = ComicArchiveService(
        handlers={},
        metadata_provider=provider,
        details_provider=details_provider,
        image_processor=ImageProcessor(),
    )
    with pytest.raises(UnsupportedFormatError):
        _ = svc.get_page(f, 1)


def test_comic_archive_service_scan_metadata_method_smoke(
    tmp_path: Path,
    make_zip_file: Callable[[Path, dict[str, bytes]], Path],
    rgb_png_bytes: bytes,
) -> None:
    svc = create_comic_archive_service(cache_size=1, zip_metadata_encodings=("utf-8",))
    cbz = make_zip_file(tmp_path / "a.cbz", {"page1.png": rgb_png_bytes})
    md = svc._scan_metadata(cbz, last_modified_ns=123)
    assert md.page_filenames == ("page1.png",)


def test_cb7_handler_import_error_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    handler = CB7Handler()

    original_import = builtins.__import__

    def guarded_import(
        name: str,
        globs: dict[str, object] | None = None,
        locs: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "py7zr":
            raise ImportError("no py7zr")
        return original_import(name, globs, locs, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(ArchiveReadError, match="py7zr library required"):
        _ = handler.scan_metadata(tmp_path / "a.cb7", last_modified_ns=1)

    with pytest.raises(ArchiveReadError, match="py7zr library required"):
        _ = handler.extract_page(
            tmp_path / "a.cb7",
            filename="x.png",
            metadata=ArchiveMetadata(page_filenames=(), last_modified_ns=1),
        )


def test_cb7_handler_success_and_error_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, rgb_png_bytes: bytes
) -> None:
    handler = CB7Handler()

    class FakeSevenZipFile:
        def __init__(self, _path: Path, _mode: str) -> None:
            self._raise_on_enter = False

        def __enter__(self) -> Self:
            if self._raise_on_enter:
                raise OSError("boom")
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        def getnames(self) -> list[str]:
            return ["page2.png", "page1.jpg", "folder/"]

        def read(self, names: list[str]) -> dict[str, BytesIO]:
            if names == ["missing.png"]:
                raise KeyError("missing")
            return {names[0]: BytesIO(rgb_png_bytes)}

    fake_py7zr = types.SimpleNamespace(SevenZipFile=FakeSevenZipFile)
    monkeypatch.setitem(sys.modules, "py7zr", fake_py7zr)

    md = handler.scan_metadata(tmp_path / "a.cb7", last_modified_ns=1)
    assert md.page_filenames == ("page1.jpg", "page2.png")

    data = handler.extract_page(tmp_path / "a.cb7", filename="page1.jpg", metadata=md)
    assert data == rgb_png_bytes

    with pytest.raises(ArchiveReadError, match="Failed to extract"):
        _ = handler.extract_page(
            tmp_path / "a.cb7", filename="missing.png", metadata=md
        )


def test_cbr_handler_success_and_error_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    handler = CBRHandler()

    import rarfile

    monkeypatch.setattr(rarfile, "tool_setup", lambda *args, **kwargs: None)

    class FakeRarFile:
        def __init__(self, _path: Path, _mode: str) -> None:
            self._names = ["page2.png", "page1.jpg", "folder/"]

        def __enter__(self) -> Self:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        def namelist(self) -> list[str]:
            return list(self._names)

        def read(self, filename: str) -> bytes:
            if filename == "missing.png":
                raise KeyError(filename)
            return b"data"

    monkeypatch.setattr(rarfile, "RarFile", FakeRarFile)

    md = handler.scan_metadata(tmp_path / "a.cbr", last_modified_ns=2)
    assert md.page_filenames == ("page1.jpg", "page2.png")
    assert (
        handler.extract_page(tmp_path / "a.cbr", filename="page1.jpg", metadata=md)
        == b"data"
    )

    with pytest.raises(ArchiveReadError, match="Failed to extract"):
        _ = handler.extract_page(
            tmp_path / "a.cbr", filename="missing.png", metadata=md
        )

    class BoomRarFile(FakeRarFile):
        def __enter__(self) -> Self:
            raise rarfile.Error("boom")

    monkeypatch.setattr(rarfile, "RarFile", BoomRarFile)
    with pytest.raises(ArchiveReadError, match="Failed to read CBR"):
        _ = handler.scan_metadata(tmp_path / "a.cbr", last_modified_ns=2)


def test_cb7_handler_scan_oserror_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    handler = CB7Handler()

    class BoomSevenZipFile:
        def __init__(self, _path: Path, _mode: str) -> None:
            pass

        def __enter__(self) -> Self:
            raise OSError("boom")

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

    fake_py7zr = types.SimpleNamespace(SevenZipFile=BoomSevenZipFile)
    monkeypatch.setitem(sys.modules, "py7zr", fake_py7zr)

    with pytest.raises(ArchiveReadError, match=r"Failed to read CB7"):
        _ = handler.scan_metadata(tmp_path / "a.cb7", last_modified_ns=1)


def test_cbz_handler_extract_oserror_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, rgb_png_bytes: bytes
) -> None:
    import bookcard.services.comic.archive.handlers.cbz as cbz_module

    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBZHandler(detector)
    cbz = tmp_path / "a.cbz"
    with zipfile.ZipFile(cbz, "w") as zf:
        zf.writestr("page1.png", rgb_png_bytes)

    md = ZipArchiveMetadata(
        page_filenames=("page1.png",),
        last_modified_ns=1,
        metadata_encoding=None,
    )

    def boom_zipfile(*_args: object, **_kwargs: object) -> zipfile.ZipFile:
        raise OSError("boom")

    monkeypatch.setattr(cbz_module.zipfile, "ZipFile", boom_zipfile)

    with pytest.raises(ArchiveReadError, match=r"Failed to read CBZ"):
        _ = handler.extract_page(cbz, filename="page1.png", metadata=md)


def test_cbc_handler_scan_oserror_and_keyerror_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import bookcard.services.comic.archive.handlers.cbc as cbc_module

    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)
    cbc = tmp_path / "a.cbc"
    cbc.write_bytes(b"not used")

    class OSErrorZip:
        def __init__(self, _path: Path, _mode: str) -> None:
            pass

        def __enter__(self) -> Self:
            raise OSError("boom")

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

    monkeypatch.setattr(cbc_module.zipfile, "ZipFile", OSErrorZip)
    with pytest.raises(ArchiveReadError, match=r"Failed to read CBC"):
        _ = handler.scan_metadata(cbc, last_modified_ns=1)

    class KeyErrorZip:
        def __init__(self, _path: Path, _mode: str) -> None:
            pass

        def __enter__(self) -> Self:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        def namelist(self) -> list[str]:
            return ["comic.cbz"]

        def read(self, _name: str) -> bytes:
            raise KeyError(_name)

    monkeypatch.setattr(cbc_module.zipfile, "ZipFile", KeyErrorZip)
    with pytest.raises(ArchiveReadError, match=r"Missing CBC entry"):
        _ = handler.scan_metadata(cbc, last_modified_ns=1)


def test_cbc_handler_extract_outer_read_keyerror_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import bookcard.services.comic.archive.handlers.cbc as cbc_module

    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)
    cbc = tmp_path / "a.cbc"
    cbc.write_bytes(b"x")

    md = CbcArchiveMetadata(
        page_filenames=("page1.png",),
        last_modified_ns=1,
        metadata_encoding=None,
        first_cbz_entry="comic.cbz",
    )

    class OuterZip:
        def __init__(self, _path: Path, _mode: str) -> None:
            pass

        def __enter__(self) -> Self:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        def read(self, _name: str) -> bytes:
            raise KeyError(_name)

    monkeypatch.setattr(cbc_module.zipfile, "ZipFile", OuterZip)
    with pytest.raises(ArchiveReadError, match=r"Failed to read inner CBZ"):
        _ = handler.extract_page(cbc, filename="page1.png", metadata=md)


def test_cbc_handler_extract_metadata_encoding_none_branch_and_inner_keyerror(
    tmp_path: Path,
    make_zip_file: Callable[[Path, dict[str, bytes]], Path],
    make_zip_bytes: Callable[[dict[str, bytes]], bytes],
    rgb_png_bytes: bytes,
) -> None:
    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)

    inner = make_zip_bytes({"page1.png": rgb_png_bytes})
    cbc = make_zip_file(tmp_path / "a.cbc", {"comic.cbz": inner})

    md_none = CbcArchiveMetadata(
        page_filenames=("missing.png",),
        last_modified_ns=1,
        metadata_encoding=None,
        first_cbz_entry="comic.cbz",
    )

    with pytest.raises(ArchiveReadError, match=r"Missing CBZ entry"):
        _ = handler.extract_page(cbc, filename="missing.png", metadata=md_none)


def test_cbc_handler_extract_inner_oserror_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_zip_file: Callable[[Path, dict[str, bytes]], Path],
    make_zip_bytes: Callable[[dict[str, bytes]], bytes],
    rgb_png_bytes: bytes,
) -> None:
    import bookcard.services.comic.archive.handlers.cbc as cbc_module

    detector = ZipEncodingDetector(encodings=("utf-8",))
    handler = CBCHandler(detector)

    inner = make_zip_bytes({"page1.png": rgb_png_bytes})
    cbc = make_zip_file(tmp_path / "a.cbc", {"comic.cbz": inner})

    md = CbcArchiveMetadata(
        page_filenames=("page1.png",),
        last_modified_ns=1,
        metadata_encoding=None,
        first_cbz_entry="comic.cbz",
    )

    real_zipfile = zipfile.ZipFile

    class InnerZip:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        def read(self, _name: str) -> bytes:
            raise OSError("boom")

    def dispatch_zipfile(
        file: BytesIO | os.PathLike[str] | str,
        mode: str = "r",
        *,
        metadata_encoding: str | None = None,
    ) -> zipfile.ZipFile | InnerZip:
        if isinstance(file, BytesIO):
            return InnerZip()
        if metadata_encoding is None:
            return real_zipfile(file, mode)  # ty:ignore[no-matching-overload]
        return real_zipfile(file, mode, metadata_encoding=metadata_encoding)  # ty:ignore[no-matching-overload]

    monkeypatch.setattr(cbc_module.zipfile, "ZipFile", dispatch_zipfile)

    with pytest.raises(ArchiveReadError, match=r"Failed to read CBZ entry"):
        _ = handler.extract_page(cbc, filename="page1.png", metadata=md)


def test_zip_encoding_detector_probe_path_and_bytes_fallback_and_exceptions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_zip_bytes: Callable[[dict[str, bytes]], bytes],
) -> None:
    import bookcard.services.comic.archive.zip_encoding as zip_encoding_module

    detector = ZipEncodingDetector(encodings=("bad-enc-1", "bad-enc-2"))
    zip_bytes = make_zip_bytes({"page1.png": b"x"})
    zip_path = tmp_path / "a.zip"
    zip_path.write_bytes(zip_bytes)

    class FakeZipFile:
        def __init__(
            self, _file: object, _mode: str, metadata_encoding: str | None = None
        ) -> None:
            self._metadata_encoding = metadata_encoding

        def __enter__(self) -> Self:
            if self._metadata_encoding is not None:
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "boom")
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

        def namelist(self) -> list[str]:
            return ["page1.png"]

    monkeypatch.setattr(zip_encoding_module.zipfile, "ZipFile", FakeZipFile)

    res_path = detector.probe_path(zip_path)
    assert res_path.encoding is None
    assert res_path.filenames == ["page1.png"]

    res_bytes = detector.probe_bytes(zip_bytes, label="bytes")
    assert res_bytes.encoding is None
    assert res_bytes.filenames == ["page1.png"]

    class BadZipFallback(FakeZipFile):
        def __enter__(self) -> Self:
            if self._metadata_encoding is None:
                raise zipfile.BadZipFile("bad")
            return super().__enter__()  # pragma: no cover

    monkeypatch.setattr(zip_encoding_module.zipfile, "ZipFile", BadZipFallback)
    with pytest.raises(ArchiveCorruptedError):
        _ = detector.probe_path(zip_path)

    class OSErrorFallback(FakeZipFile):
        def __enter__(self) -> Self:
            if self._metadata_encoding is None:
                raise OSError("boom")
            return super().__enter__()  # pragma: no cover

    monkeypatch.setattr(zip_encoding_module.zipfile, "ZipFile", OSErrorFallback)
    with pytest.raises(ArchiveReadError):
        _ = detector.probe_bytes(zip_bytes, label="bytes")
