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

"""Unit tests for comic API routes and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from PIL import Image

import bookcard.api.routes.comic as comic_routes
from bookcard.api.deps import get_current_user, get_db_session
from bookcard.models.auth import User
from bookcard.services.comic.archive import ArchiveReadError
from bookcard.services.comic.archive.models import ComicPageInfo

if TYPE_CHECKING:
    from collections.abc import Generator

    from bookcard.services.book_service import BookService


@dataclass
class _BookWithRels:
    """Minimal stand-in for `BookWithFullRelations` used by route helpers."""

    book: object
    formats: list[dict] = field(default_factory=list)


@pytest.fixture
def test_user() -> User:
    return User(id=1, username="test", is_admin=True)


@pytest.fixture
def rgba_png_bytes() -> bytes:
    img = Image.new("RGBA", (100, 80), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def app(test_user: User) -> FastAPI:
    app = FastAPI()
    app.include_router(comic_routes.router)

    def _session_dep() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db_session] = _session_dep
    app.dependency_overrides[get_current_user] = lambda: test_user
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def test__get_book_service_no_active_library(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLibraryService:
        def __init__(self, _session: object, _repo: object) -> None:
            pass

        def get_active_library(self) -> None:
            return None

    monkeypatch.setattr(comic_routes, "LibraryRepository", lambda _s: object())
    monkeypatch.setattr(comic_routes, "LibraryService", FakeLibraryService)

    with pytest.raises(HTTPException) as exc_info:
        _ = comic_routes._get_book_service(object())
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 404
    assert exc.detail == "no_active_library"


def test__get_book_service_returns_book_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    @dataclass
    class FakeLibrary:
        calibre_db_path: str
        path: str | None = None

    fake_library = FakeLibrary(calibre_db_path="/tmp")

    class FakeLibraryService:
        def __init__(self, _session: object, _repo: object) -> None:
            pass

        def get_active_library(self) -> FakeLibrary:
            return fake_library

    @dataclass
    class FakeBookService:
        library: FakeLibrary
        session: object

    monkeypatch.setattr(comic_routes, "LibraryRepository", lambda _s: object())
    monkeypatch.setattr(comic_routes, "LibraryService", FakeLibraryService)
    monkeypatch.setattr(comic_routes, "BookService", FakeBookService)

    svc = comic_routes._get_book_service(object())
    assert isinstance(svc, FakeBookService)
    assert svc.library is fake_library


@pytest.mark.parametrize(
    ("formats", "file_format", "expected_name"),
    [
        ([{"format": "CBZ", "name": "x"}], "cbz", "x"),
        ([{"format": "cbz", "name": "y"}], "CBZ", "y"),
    ],
)
def test__find_format_data_found(
    formats: list[dict], file_format: str, expected_name: str
) -> None:
    fmt = comic_routes._find_format_data(formats, file_format)
    assert fmt["name"] == expected_name


def test__find_format_data_not_found() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _ = comic_routes._find_format_data([{"format": "EPUB"}], "CBZ")
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 404
    assert "format_not_found" in str(exc.detail)


@pytest.mark.parametrize("library_root", ["", None])
def test__get_library_path_uses_calibre_db_path_parent_when_file(
    tmp_path: Path, library_root: str | None
) -> None:
    db_file = tmp_path / "metadata.db"
    db_file.write_text("x")

    class FakeLibrary:
        def __init__(self) -> None:
            self.library_root = library_root
            self.calibre_db_path = str(db_file)

    class FakeBookService:
        def __init__(self) -> None:
            self._library = FakeLibrary()

    p = comic_routes._get_library_path(FakeBookService())  # type: ignore[arg-type]
    assert p == tmp_path


def test__get_library_path_prefers_library_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()

    class FakeLibrary:
        def __init__(self) -> None:
            self.library_root = str(root)
            self.calibre_db_path = str(tmp_path / "metadata.db")

    class FakeBookService:
        def __init__(self) -> None:
            self._library = FakeLibrary()

    p = comic_routes._get_library_path(FakeBookService())  # type: ignore[arg-type]
    assert p == root


def test__get_library_path_uses_calibre_db_path_when_dir(tmp_path: Path) -> None:
    lib_dir = tmp_path / "library"
    lib_dir.mkdir()

    class FakeLibrary:
        def __init__(self) -> None:
            self.library_root = None
            self.calibre_db_path = str(lib_dir)

    class FakeBookService:
        def __init__(self) -> None:
            self._library = FakeLibrary()

    p = comic_routes._get_library_path(FakeBookService())  # type: ignore[arg-type]
    assert p == lib_dir


def test__find_comic_file_name_then_alt(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    alt = book_dir / "123.cbz"
    alt.write_bytes(b"x")

    found = comic_routes._find_comic_file(
        book_path=book_dir,
        format_data={"name": "Fancy Name"},
        book_id=123,
        file_format="CBZ",
    )
    assert found == alt


def test__find_comic_file_direct_name_hit(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    f = book_dir / "Fancy.cbz"
    f.write_bytes(b"x")

    found = comic_routes._find_comic_file(
        book_path=book_dir,
        format_data={"name": "Fancy"},
        book_id=123,
        file_format="CBZ",
    )
    assert found == f


def test__find_comic_file_not_found(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    with pytest.raises(HTTPException) as exc_info:
        _ = comic_routes._find_comic_file(
            book_path=book_dir,
            format_data={"name": "Nope"},
            book_id=123,
            file_format="CBZ",
        )
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 404
    assert "file_not_found" in str(exc.detail)


def test__get_comic_file_path_book_not_found() -> None:
    class FakeBookService:
        def get_book_full(self, _book_id: int) -> None:
            return None

    with pytest.raises(HTTPException) as exc_info:
        _ = comic_routes._get_comic_file_path(
            cast("BookService", FakeBookService()), book_id=1, file_format="CBZ"
        )
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 404
    assert exc.detail == "book_not_found"


def test__get_comic_file_path_missing_book_id() -> None:
    class FakeBook:
        id = None
        path = "x"

    class FakeBookService:
        def __init__(self) -> None:
            self._library = types.SimpleNamespace(  # type: ignore[name-defined]
                library_root=None,
                calibre_db_path="/tmp",
            )

        def get_book_full(self, _book_id: int) -> _BookWithRels:
            return _BookWithRels(
                book=FakeBook(),
                formats=[{"format": "CBZ", "name": None}],
            )

    import types

    with pytest.raises(HTTPException) as exc_info:
        _ = comic_routes._get_comic_file_path(
            cast("BookService", FakeBookService()), book_id=1, file_format="CBZ"
        )
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 500
    assert exc.detail == "book_missing_id"


def test__get_comic_file_path_success(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()

    book_dir = library_root / "Some Book"
    book_dir.mkdir()
    (book_dir / "123.cbz").write_bytes(b"x")

    class FakeBook:
        id = 123
        path = "Some Book"

    class FakeBookService:
        def __init__(self) -> None:
            self._library = types.SimpleNamespace(  # type: ignore[name-defined]
                library_root=str(library_root),
                calibre_db_path=str(library_root / "metadata.db"),
            )

        def get_book_full(self, _book_id: int) -> _BookWithRels:
            return _BookWithRels(
                book=FakeBook(),
                formats=[{"format": "CBZ", "name": None}],
            )

    import types

    p = comic_routes._get_comic_file_path(
        cast("BookService", FakeBookService()), book_id=123, file_format="CBZ"
    )
    assert p.name == "123.cbz"


def test_list_comic_pages_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    @dataclass
    class FakeBook:
        id: int = 1
        path: str = "x"

    class FakeBookService:
        def get_book_full(self, _book_id: int) -> _BookWithRels:
            return _BookWithRels(
                book=FakeBook(),
                formats=[{"format": "CBZ", "name": None}],
            )

    class FakePermissionHelper:
        def __init__(self, _session: object) -> None:
            pass

        def check_read_permission(self, _user: User, _book: object) -> None:
            return None

    class FakeArchiveService:
        def list_pages(
            self, _path: Path, *, include_dimensions: bool = False
        ) -> list[ComicPageInfo]:
            return [
                ComicPageInfo(
                    page_number=1,
                    filename="page1.png",
                    width=None,
                    height=None,
                    file_size=0,
                )
            ]

    f = tmp_path / "a.cbz"
    f.write_bytes(b"x")

    monkeypatch.setattr(comic_routes, "_get_book_service", lambda _s: FakeBookService())
    monkeypatch.setattr(comic_routes, "BookPermissionHelper", FakePermissionHelper)
    monkeypatch.setattr(comic_routes, "_get_comic_file_path", lambda *_a, **_k: f)
    monkeypatch.setattr(
        comic_routes, "create_comic_archive_service", lambda: FakeArchiveService()
    )

    res = client.get("/comic/1/pages", params={"file_format": "CBZ"})
    assert res.status_code == 200
    assert res.json() == [
        {
            "page_number": 1,
            "filename": "page1.png",
            "width": None,
            "height": None,
            "file_size": 0,
        }
    ]


def test_list_comic_pages_archive_error_mapped_to_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class FakeBookService:
        def get_book_full(self, _book_id: int) -> _BookWithRels:
            return _BookWithRels(
                book=object(),
                formats=[{"format": "CBZ", "name": None}],
            )

    class FakePermissionHelper:
        def __init__(self, _session: object) -> None:
            pass

        def check_read_permission(self, _user: User, _book: object) -> None:
            return None

    class FakeArchiveService:
        def list_pages(
            self, _path: Path, *, include_dimensions: bool = False
        ) -> list[ComicPageInfo]:
            raise ArchiveReadError("bad archive")

    f = tmp_path / "a.cbz"
    f.write_bytes(b"x")

    monkeypatch.setattr(comic_routes, "_get_book_service", lambda _s: FakeBookService())
    monkeypatch.setattr(comic_routes, "BookPermissionHelper", FakePermissionHelper)
    monkeypatch.setattr(comic_routes, "_get_comic_file_path", lambda *_a, **_k: f)
    monkeypatch.setattr(
        comic_routes, "create_comic_archive_service", lambda: FakeArchiveService()
    )

    res = client.get("/comic/1/pages", params={"file_format": "CBZ"})
    assert res.status_code == 400
    assert "bad archive" in res.json()["detail"]


def test_list_comic_pages_book_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeBookService:
        def get_book_full(self, _book_id: int) -> None:
            return None

    monkeypatch.setattr(comic_routes, "_get_book_service", lambda _s: FakeBookService())

    res = client.get("/comic/1/pages", params={"file_format": "CBZ"})
    assert res.status_code == 404
    assert res.json()["detail"] == "book_not_found"


def test_get_comic_page_thumbnail_success_and_fallback(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    rgba_png_bytes: bytes,
) -> None:
    @dataclass
    class FakePage:
        image_data: bytes

    class FakeBookService:
        def get_book_full(self, _book_id: int) -> _BookWithRels:
            return _BookWithRels(
                book=object(),
                formats=[{"format": "CBZ", "name": None}],
            )

    class FakePermissionHelper:
        def __init__(self, _session: object) -> None:
            pass

        def check_read_permission(self, _user: User, _book: object) -> None:
            return None

    class FakeArchiveService:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def get_page(self, _path: Path, _page_number: int) -> FakePage:
            return FakePage(image_data=self._payload)

    f = Path("/tmp/a.cbz")

    monkeypatch.setattr(comic_routes, "_get_book_service", lambda _s: FakeBookService())
    monkeypatch.setattr(comic_routes, "BookPermissionHelper", FakePermissionHelper)
    monkeypatch.setattr(comic_routes, "_get_comic_file_path", lambda *_a, **_k: f)

    # Success path: RGBA image is converted to JPEG thumbnail
    monkeypatch.setattr(
        comic_routes,
        "create_comic_archive_service",
        lambda: FakeArchiveService(rgba_png_bytes),
    )
    res = client.get(
        "/comic/1/pages/1",
        params={"file_format": "CBZ", "thumbnail": True, "max_width": 50},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/jpeg")
    assert res.content[:2] == b"\xff\xd8"  # JPEG magic

    # Fallback path: invalid bytes trigger try/except and return original bytes
    bad = b"not an image"
    monkeypatch.setattr(
        comic_routes, "create_comic_archive_service", lambda: FakeArchiveService(bad)
    )
    res2 = client.get(
        "/comic/1/pages/1",
        params={"file_format": "CBZ", "thumbnail": True},
    )
    assert res2.status_code == 200
    assert res2.content == bad


def test_get_comic_page_thumbnail_endpoint_delegates(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    rgba_png_bytes: bytes,
) -> None:
    @dataclass
    class FakePage:
        image_data: bytes

    class FakeBookService:
        def get_book_full(self, _book_id: int) -> _BookWithRels:
            return _BookWithRels(
                book=object(),
                formats=[{"format": "CBZ", "name": None}],
            )

    class FakePermissionHelper:
        def __init__(self, _session: object) -> None:
            pass

        def check_read_permission(self, _user: User, _book: object) -> None:
            return None

    class FakeArchiveService:
        def get_page(self, _path: Path, _page_number: int) -> FakePage:
            return FakePage(image_data=rgba_png_bytes)

    f = Path("/tmp/a.cbz")

    monkeypatch.setattr(comic_routes, "_get_book_service", lambda _s: FakeBookService())
    monkeypatch.setattr(comic_routes, "BookPermissionHelper", FakePermissionHelper)
    monkeypatch.setattr(comic_routes, "_get_comic_file_path", lambda *_a, **_k: f)
    monkeypatch.setattr(
        comic_routes, "create_comic_archive_service", lambda: FakeArchiveService()
    )

    res = client.get(
        "/comic/1/pages/1/thumbnail",
        params={"file_format": "CBZ", "max_width": 50},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/jpeg")


def test_get_comic_page_archive_error_mapped_to_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeBookService:
        def get_book_full(self, _book_id: int) -> _BookWithRels:
            return _BookWithRels(
                book=object(),
                formats=[{"format": "CBZ", "name": None}],
            )

    class FakePermissionHelper:
        def __init__(self, _session: object) -> None:
            pass

        def check_read_permission(self, _user: User, _book: object) -> None:
            return None

    class FakeArchiveService:
        def get_page(self, _path: Path, _page_number: int) -> object:
            raise ArchiveReadError("boom")

    f = Path("/tmp/a.cbz")

    monkeypatch.setattr(comic_routes, "_get_book_service", lambda _s: FakeBookService())
    monkeypatch.setattr(comic_routes, "BookPermissionHelper", FakePermissionHelper)
    monkeypatch.setattr(comic_routes, "_get_comic_file_path", lambda *_a, **_k: f)
    monkeypatch.setattr(
        comic_routes, "create_comic_archive_service", lambda: FakeArchiveService()
    )

    res = client.get("/comic/1/pages/1", params={"file_format": "CBZ"})
    assert res.status_code == 400
    assert "boom" in res.json()["detail"]


def test_get_comic_page_book_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeBookService:
        def get_book_full(self, _book_id: int) -> None:
            return None

    monkeypatch.setattr(comic_routes, "_get_book_service", lambda _s: FakeBookService())

    res = client.get("/comic/1/pages/1", params={"file_format": "CBZ"})
    assert res.status_code == 404
    assert res.json()["detail"] == "book_not_found"
