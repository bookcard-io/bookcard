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

"""Tests for authors routes to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import FileResponse, Response

import bookcard.api.routes.authors as authors
from bookcard.api.schemas.author import (
    AuthorMergeRecommendRequest,
    AuthorMergeRequest,
    AuthorUpdate,
    PhotoFromUrlRequest,
    PhotoUploadResponse,
)
from bookcard.models.auth import User
from tests.conftest import DummySession


def _create_mock_user() -> User:
    """Create a mock user for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


class MockAuthorService:
    """Mock AuthorService for testing."""

    def __init__(self) -> None:
        self._author_data: dict[str, dict[str, object]] = {}
        self._photos: dict[str, list[object]] = {}
        self._list_result: tuple[list[dict[str, object]], int] = ([], 0)

    def get_author_by_id_or_key(
        self,
        author_id: str,
        include_similar: bool = True,
        library_id: int | None = None,
    ) -> dict[str, object]:
        """Mock get_author_by_id_or_key."""
        if author_id not in self._author_data:
            raise ValueError("author_not_found")
        return self._author_data[author_id]

    def list_authors_for_active_library(
        self, page: int, page_size: int, filter_type: str | None = None
    ) -> tuple[list[dict[str, object]], int]:
        """Mock list_authors_for_active_library."""
        return self._list_result

    def update_author(
        self, author_id: str, update_dict: dict[str, object]
    ) -> dict[str, object]:
        """Mock update_author."""
        if author_id not in self._author_data:
            raise ValueError("author_not_found")
        author = self._author_data[author_id].copy()
        author.update(update_dict)
        return author

    def get_author_photos(self, author_id: str) -> list[object]:
        """Mock get_author_photos."""
        return self._photos.get(author_id, [])

    def upload_author_photo(
        self,
        author_id: str,
        file_content: bytes,
        filename: str,
        set_as_primary: bool = False,
    ) -> object:
        """Mock upload_author_photo."""
        photo = MagicMock()
        photo.id = 1
        photo.file_path = f"photos/{author_id}/{filename}"
        return photo

    def upload_photo_from_url(
        self, author_id: str, url: str, set_as_primary: bool = False
    ) -> object:
        """Mock upload_photo_from_url."""
        photo = MagicMock()
        photo.id = 1
        photo.file_path = f"photos/{author_id}/photo.jpg"
        return photo

    def get_author_photo_by_id(self, author_id: str, photo_id: int) -> object | None:
        """Mock get_author_photo_by_id."""
        photos = self._photos.get(author_id, [])
        if photos and len(photos) > 0:
            photo = MagicMock()
            photo.id = photo_id
            photo.file_path = f"photos/{author_id}/photo_{photo_id}.jpg"
            photo.file_name = f"photo_{photo_id}.jpg"
            photo.mime_type = "image/jpeg"
            return photo
        return None

    def delete_photo(self, author_id: str, photo_id: int) -> None:
        """Mock delete_photo."""
        if author_id not in self._photos:
            raise ValueError("photo_not_found")


class MockRematchService:
    """Mock AuthorRematchService for testing."""

    def determine_openlibrary_key(
        self, provided_olid: str | None, author_data: dict[str, object]
    ) -> str:
        """Mock determine_openlibrary_key."""
        if provided_olid:
            return provided_olid
        key = author_data.get("key")
        if isinstance(key, str):
            return key
        return "OL123A"

    def resolve_library_and_author_ids(
        self, author_id: str, author_data: dict[str, object]
    ) -> tuple[int, int, int | None]:
        """Mock resolve_library_and_author_ids."""
        return (1, 1, 1)

    def get_calibre_author_dict(
        self, library_id: int, calibre_author_id: int
    ) -> dict[str, object]:
        """Mock get_calibre_author_dict."""
        return {"id": calibre_author_id, "name": "Test Author"}

    def enqueue_rematch_job(
        self,
        library_id: int,
        author_dict: dict[str, object],
        openlibrary_key: str,
        author_metadata_id: int | None,
    ) -> None:
        """Mock enqueue_rematch_job."""


class MockMergeService:
    """Mock AuthorMergeService for testing."""

    def recommend_keep_author(self, author_ids: list[str]) -> dict[str, object]:
        """Mock recommend_keep_author."""
        return {"recommended_keep_author_id": author_ids[0], "authors": []}

    def merge_authors(
        self, author_ids: list[str], keep_author_id: str
    ) -> dict[str, object]:
        """Mock merge_authors."""
        return {"merged_author_id": keep_author_id, "name": "Merged Author"}


class MockPermissionHelper:
    """Mock AuthorPermissionHelper for testing."""

    def __init__(self, session: object | None = None) -> None:
        """Initialize mock permission helper."""

    def check_read_permission(
        self, user: User, author_data: dict[str, object] | None = None
    ) -> None:
        """Mock check_read_permission - always allows."""

    def check_write_permission(
        self, user: User, author_data: dict[str, object] | None = None
    ) -> None:
        """Mock check_write_permission - always allows."""

    def check_send_permission(
        self,
        user: User,
        book_with_rels: object | None = None,
        book_id: int | None = None,
        session: object | None = None,
    ) -> None:
        """Mock check_send_permission - always allows."""

    def check_create_permission(
        self,
        user: User,
    ) -> None:
        """Mock check_create_permission - always allows."""


def _setup_route_mocks(
    monkeypatch: pytest.MonkeyPatch,
    session: DummySession,
    mock_service: MockAuthorService,
) -> tuple[MockPermissionHelper, MockRematchService, MockMergeService]:
    """Set up mocks for route dependencies."""

    def mock_get_author_service(sess: object, req: Request) -> MockAuthorService:
        return mock_service

    monkeypatch.setattr(authors, "_get_author_service", mock_get_author_service)

    def mock_get_rematch_service(
        sess: object, req: Request, author_svc: MockAuthorService
    ) -> MockRematchService:
        return MockRematchService()

    monkeypatch.setattr(authors, "_get_rematch_service", mock_get_rematch_service)

    def mock_get_merge_service(sess: object, req: Request) -> MockMergeService:
        return MockMergeService()

    monkeypatch.setattr(authors, "_get_merge_service", mock_get_merge_service)

    def mock_get_permission_helper(sess: object) -> MockPermissionHelper:
        return MockPermissionHelper()

    monkeypatch.setattr(authors, "_get_permission_helper", mock_get_permission_helper)

    return MockPermissionHelper(), MockRematchService(), MockMergeService()


def test_get_author_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_author_service creates AuthorService (covers lines 88-98)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()

    with (
        patch("bookcard.api.routes.authors.AuthorRepository") as mock_repo_class,
        patch("bookcard.api.routes.authors.LibraryRepository") as mock_lib_repo_class,
        patch("bookcard.api.routes.authors.LibraryService") as mock_lib_service_class,
        patch("bookcard.api.routes.authors.AuthorService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_lib_repo = MagicMock()
        mock_lib_repo_class.return_value = mock_lib_repo

        mock_lib_service = MagicMock()
        mock_lib_service_class.return_value = mock_lib_service

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        result = authors._get_author_service(session, request)  # type: ignore[arg-type]

        assert result is not None
        mock_repo_class.assert_called_once_with(session)
        mock_lib_repo_class.assert_called_once_with(session)
        mock_lib_service_class.assert_called_once()
        mock_service_class.assert_called_once()


def test_get_rematch_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_rematch_service creates AuthorRematchService (covers lines 122-133)."""

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type("App", (), {"state": type("State", (), {})()})()

    session = DummySession()
    request = DummyRequest()
    mock_author_service = MockAuthorService()

    with (
        patch("bookcard.api.routes.authors.LibraryRepository") as mock_lib_repo_class,
        patch("bookcard.api.routes.authors.LibraryService") as mock_lib_service_class,
        patch("bookcard.api.routes.authors.AuthorRematchService") as mock_service_class,
    ):
        mock_lib_repo = MagicMock()
        mock_lib_repo_class.return_value = mock_lib_repo

        mock_lib_service = MagicMock()
        mock_lib_service_class.return_value = mock_lib_service

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        result = authors._get_rematch_service(
            session,  # type: ignore[arg-type]
            request,  # type: ignore[arg-type]
            mock_author_service,  # type: ignore[arg-type]
        )

        assert result is not None
        mock_lib_repo_class.assert_called_once_with(session)
        mock_lib_service_class.assert_called_once()
        mock_service_class.assert_called_once()


def test_get_merge_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_merge_service creates AuthorMergeService (covers lines 181-191)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    request = DummyRequest()

    with (
        patch("bookcard.api.routes.authors.AuthorRepository") as mock_repo_class,
        patch("bookcard.api.routes.authors.LibraryRepository") as mock_lib_repo_class,
        patch("bookcard.api.routes.authors.LibraryService") as mock_lib_service_class,
        patch("bookcard.api.routes.authors.AuthorMergeService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_lib_repo = MagicMock()
        mock_lib_repo_class.return_value = mock_lib_repo

        mock_lib_service = MagicMock()
        mock_lib_service_class.return_value = mock_lib_service

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        result = authors._get_merge_service(session, request)  # type: ignore[arg-type]

        assert result is not None
        mock_repo_class.assert_called_once_with(session)
        mock_lib_repo_class.assert_called_once_with(session)
        mock_lib_service_class.assert_called_once()
        mock_service_class.assert_called_once()


@pytest.mark.asyncio
async def test_parse_rematch_request_json() -> None:
    """Test _parse_rematch_request parses JSON (covers lines 210-212)."""

    class DummyHeaders:
        def __init__(self, headers: dict[str, str]) -> None:
            self._headers = headers

        def get(self, key: str, default: str = "") -> str:
            return self._headers.get(key, default)

    class DummyRequest:
        def __init__(self) -> None:
            self.headers = DummyHeaders({"content-type": "application/json"})
            self._json_data = {"openlibrary_key": "OL123A"}

        async def json(self) -> dict[str, object]:
            return self._json_data

    request = DummyRequest()
    result = await authors._parse_rematch_request(request)  # type: ignore[arg-type]

    assert result == {"openlibrary_key": "OL123A"}


@pytest.mark.asyncio
async def test_parse_rematch_request_no_json() -> None:
    """Test _parse_rematch_request returns None when no JSON (covers lines 210-215)."""

    class DummyHeaders:
        def __init__(self, headers: dict[str, str]) -> None:
            self._headers = headers

        def get(self, key: str, default: str = "") -> str:
            return self._headers.get(key, default)

    class DummyRequest:
        def __init__(self) -> None:
            self.headers = DummyHeaders({"content-type": "text/plain"})

    request = DummyRequest()
    result = await authors._parse_rematch_request(request)  # type: ignore[arg-type]

    assert result is None


@pytest.mark.asyncio
async def test_parse_rematch_request_parse_error() -> None:
    """Test _parse_rematch_request handles parse errors (covers lines 213-214)."""

    class DummyHeaders:
        def __init__(self, headers: dict[str, str]) -> None:
            self._headers = headers

        def get(self, key: str, default: str = "") -> str:
            return self._headers.get(key, default)

    class DummyRequest:
        def __init__(self) -> None:
            self.headers = DummyHeaders({"content-type": "application/json"})

        async def json(self) -> dict[str, object]:
            raise ValueError("Invalid JSON")

    request = DummyRequest()
    result = await authors._parse_rematch_request(request)  # type: ignore[arg-type]

    assert result is None


def test_get_author_or_raise_success() -> None:
    """Test _get_author_or_raise returns author data (covers lines 241-254)."""
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author", "key": "OL123A"}

    result = authors._get_author_or_raise("1", mock_service)  # type: ignore[arg-type]

    assert result["id"] == "1"
    assert result["name"] == "Test Author"


def test_get_author_or_raise_not_found() -> None:
    """Test _get_author_or_raise raises HTTPException when not found (covers lines 250-252)."""
    mock_service = MockAuthorService()

    with pytest.raises(HTTPException):
        authors._get_author_or_raise("999", mock_service)  # type: ignore[arg-type]


def test_list_authors_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_authors returns paginated results (covers lines 306-322)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._list_result = (
        [{"id": "1", "name": "Author 1"}, {"id": "2", "name": "Author 2"}],
        2,
    )

    _mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with patch(
        "bookcard.api.routes.authors.PermissionService"
    ) as mock_perm_service_class:
        mock_perm_service = MagicMock()
        mock_perm_service.check_permission.return_value = None
        mock_perm_service_class.return_value = mock_perm_service

        result = authors.list_authors(
            current_user=current_user,
            session=session,
            author_service=mock_service,
            page=1,
            page_size=20,
            filter_type=None,
        )

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 20


def test_list_authors_with_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_authors with filter (covers lines 306-322)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._list_result = (
        [{"id": "1", "name": "Author 1", "is_unmatched": True}],
        1,
    )

    _mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with patch(
        "bookcard.api.routes.authors.PermissionService"
    ) as mock_perm_service_class:
        mock_perm_service = MagicMock()
        mock_perm_service.check_permission.return_value = None
        mock_perm_service_class.return_value = mock_perm_service

        result = authors.list_authors(
            current_user=current_user,
            session=session,
            author_service=mock_service,
            page=1,
            page_size=20,
            filter_type="unmatched",
        )

        assert result["total"] == 1


def test_list_authors_page_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_authors validates page parameters (covers lines 299-304)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._list_result = ([], 0)

    _mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with patch(
        "bookcard.api.routes.authors.PermissionService"
    ) as mock_perm_service_class:
        mock_perm_service = MagicMock()
        mock_perm_service.check_permission.return_value = None
        mock_perm_service_class.return_value = mock_perm_service

        # Test page < 1
        result = authors.list_authors(
            current_user=current_user,
            session=session,
            author_service=mock_service,
            page=0,
            page_size=20,
        )
        assert result["page"] == 1

        # Test page_size > 100
        result = authors.list_authors(
            current_user=current_user,
            session=session,
            author_service=mock_service,
            page=1,
            page_size=200,
        )
        assert result["page_size"] == 100


def test_list_authors_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test list_authors handles errors (covers lines 313-314)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service.list_authors_for_active_library = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("no_active_library")
    )

    _mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with patch(
        "bookcard.api.routes.authors.PermissionService"
    ) as mock_perm_service_class:
        mock_perm_service = MagicMock()
        mock_perm_service.check_permission.return_value = None
        mock_perm_service_class.return_value = mock_perm_service

        with pytest.raises(HTTPException):
            authors.list_authors(
                current_user=current_user,
                session=session,
                author_service=mock_service,
            )


def test_get_author_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_author returns author (covers lines 355-358)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = authors.get_author(
        author_id="1",
        current_user=current_user,
        library_id=1,
        author_service=mock_service,
        permission_helper=mock_permission_helper,
    )

    assert result["id"] == "1"
    assert result["name"] == "Test Author"


def test_update_author_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_author succeeds (covers lines 399-406)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Old Name"}

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    update = AuthorUpdate(name="New Name")
    result = authors.update_author(
        author_id="1",
        update=update,
        current_user=current_user,
        author_service=mock_service,
        permission_helper=mock_permission_helper,
    )

    assert result["name"] == "New Name"


def test_update_author_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_author handles errors (covers lines 405-406)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service.update_author = MagicMock(side_effect=ValueError("author_not_found"))  # type: ignore[assignment]

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    update = AuthorUpdate(name="New Name")
    with pytest.raises(HTTPException):
        authors.update_author(
            author_id="999",
            update=update,
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
        )


@pytest.mark.asyncio
async def test_rematch_author_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test rematch_author succeeds (covers lines 464-500)."""

    class DummyHeaders:
        def __init__(self, headers: dict[str, str]) -> None:
            self._headers = headers

        def get(self, key: str, default: str = "") -> str:
            return self._headers.get(key, default)

    class DummyRequest:
        def __init__(self) -> None:
            self.headers = DummyHeaders({"content-type": "application/json"})
            self.app = type("App", (), {"state": type("State", (), {})()})()

        async def json(self) -> dict[str, object]:
            return {"openlibrary_key": "OL123A"}

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author", "key": "OL123A"}

    mock_permission_helper, mock_rematch_service, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request = DummyRequest()
    result = await authors.rematch_author(
        author_id="1",
        request=request,
        current_user=current_user,
        author_service=mock_service,
        rematch_service=mock_rematch_service,
        permission_helper=mock_permission_helper,
    )

    assert "message" in result
    assert "openlibrary_key" in result


@pytest.mark.asyncio
async def test_rematch_author_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test rematch_author handles errors (covers lines 501-502)."""

    class DummyHeaders:
        def __init__(self, headers: dict[str, str]) -> None:
            self._headers = headers

        def get(self, key: str, default: str = "") -> str:
            return self._headers.get(key, default)

    class DummyRequest:
        def __init__(self) -> None:
            self.headers = DummyHeaders({})
            self.app = type("App", (), {"state": type("State", (), {})()})()

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_permission_helper, mock_rematch_service, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )
    mock_rematch_service.determine_openlibrary_key = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("no_openlibrary_key")
    )

    request = DummyRequest()
    with pytest.raises(HTTPException):
        await authors.rematch_author(
            author_id="1",
            request=request,
            current_user=current_user,
            author_service=mock_service,
            rematch_service=mock_rematch_service,
            permission_helper=mock_permission_helper,
        )


def test_recommend_merge_author_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test recommend_merge_author succeeds (covers lines 510-553)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Author 1"}
    mock_service._author_data["2"] = {"id": "2", "name": "Author 2"}

    mock_permission_helper, _, mock_merge_service = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request_body = AuthorMergeRecommendRequest(author_ids=["1", "2"])
    result = authors.recommend_merge_author(
        request_body=request_body,
        current_user=current_user,
        author_service=mock_service,
        merge_service=mock_merge_service,
        permission_helper=mock_permission_helper,
    )

    assert "recommended_keep_author_id" in result


def test_merge_authors_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test merge_authors succeeds (covers lines 561-607)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Author 1"}
    mock_service._author_data["2"] = {"id": "2", "name": "Author 2"}

    mock_permission_helper, _, mock_merge_service = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request_body = AuthorMergeRequest(author_ids=["1", "2"], keep_author_id="1")
    result = authors.merge_authors(
        request_body=request_body,
        current_user=current_user,
        author_service=mock_service,
        merge_service=mock_merge_service,
        permission_helper=mock_permission_helper,
    )

    assert "merged_author_id" in result


def test_upload_author_photo_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_author_photo succeeds (covers lines 645-680)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    mock_file = MagicMock()
    mock_file.filename = "photo.jpg"
    mock_file.file.read.return_value = b"fake image data"

    result = authors.upload_author_photo(
        author_id="1",
        current_user=current_user,
        author_service=mock_service,
        permission_helper=mock_permission_helper,
        file=mock_file,
    )

    assert isinstance(result, PhotoUploadResponse)
    assert result.photo_id == 1


def test_upload_author_photo_no_filename(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_author_photo raises 400 when no filename (covers lines 648-652)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    mock_file = MagicMock()
    mock_file.filename = None

    with pytest.raises(HTTPException) as exc_info:
        authors.upload_author_photo(
            author_id="1",
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            file=mock_file,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "filename_required"


def test_upload_author_photo_read_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_author_photo handles read error (covers lines 654-660)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    mock_file = MagicMock()
    mock_file.filename = "photo.jpg"
    mock_file.file.read.side_effect = Exception("Read error")

    with pytest.raises(HTTPException) as exc_info:
        authors.upload_author_photo(
            author_id="1",
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            file=mock_file,
        )
    assert exc_info.value.status_code == 500
    assert "failed_to_read_file" in exc_info.value.detail


def test_upload_photo_from_url_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_photo_from_url succeeds (covers lines 721-741)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request = PhotoFromUrlRequest(url="https://example.com/photo.jpg")

    result = authors.upload_photo_from_url(
        author_id="1",
        current_user=current_user,
        author_service=mock_service,
        permission_helper=mock_permission_helper,
        request=request,
    )

    assert isinstance(result, PhotoUploadResponse)
    assert result.photo_id == 1


def test_upload_photo_from_url_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_photo_from_url handles errors (covers lines 740-749)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service.upload_photo_from_url = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("invalid_url")
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request = PhotoFromUrlRequest(url="invalid-url")

    with pytest.raises(HTTPException):
        authors.upload_photo_from_url(
            author_id="1",
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            request=request,
        )


def test_upload_photo_from_url_unexpected_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upload_photo_from_url handles unexpected errors (covers lines 742-749)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service.upload_photo_from_url = MagicMock(  # type: ignore[assignment]
        side_effect=RuntimeError("Database error")
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request = PhotoFromUrlRequest(url="https://example.com/photo.jpg")

    with pytest.raises(HTTPException) as exc_info:
        authors.upload_photo_from_url(
            author_id="1",
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            request=request,
        )
    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


def test_get_author_photo_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_author_photo returns file (covers lines 793-825)."""

    class DummyRequest:
        def __init__(self, temp_dir: str) -> None:
            class DummyConfig:
                data_directory = temp_dir

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service._photos["1"] = [MagicMock()]  # Has photos

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        photo_path = Path(tmpdir) / "photos" / "1" / "photo_1.jpg"
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        photo_path.write_bytes(b"fake image")

        request = DummyRequest(tmpdir)
        photo = mock_service.get_author_photo_by_id("1", 1)
        if photo:
            photo.file_path = str(photo_path.relative_to(tmpdir))  # type: ignore[assignment]

        result = authors.get_author_photo(
            author_id="1",
            photo_id=1,
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            request=request,
        )

        assert isinstance(result, FileResponse)


def test_get_author_photo_not_found_author(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_author_photo returns 404 when author not found (covers lines 793-799)."""

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    # Mock get_author_by_id_or_key to raise ValueError which will be mapped to HTTPException
    mock_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("author_not_found")
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    request = DummyRequest()
    # Mock AuthorExceptionMapper to return 404 HTTPException
    with patch("bookcard.api.routes.authors.AuthorExceptionMapper") as mock_mapper:
        from fastapi import HTTPException

        mock_mapper.map_value_error_to_http_exception.return_value = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="author_not_found"
        )

        result = authors.get_author_photo(
            author_id="999",
            photo_id=1,
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            request=request,
        )

        assert isinstance(result, Response)
        assert result.status_code == 404


def test_get_author_photo_not_found_photo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_author_photo returns 404 when photo not found (covers lines 802-805)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service.get_author_photo_by_id = MagicMock(return_value=None)  # type: ignore[assignment]

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type("App", (), {"state": type("State", (), {})()})()

    request = DummyRequest()
    result = authors.get_author_photo(
        author_id="1",
        photo_id=999,
        current_user=current_user,
        author_service=mock_service,
        permission_helper=mock_permission_helper,
        request=request,
    )

    assert isinstance(result, Response)
    assert result.status_code == 404


def test_delete_author_photo_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_author_photo succeeds (covers lines 868-876)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service._photos["1"] = [MagicMock()]

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    result = authors.delete_author_photo(
        author_id="1",
        photo_id=1,
        current_user=current_user,
        author_service=mock_service,
        permission_helper=mock_permission_helper,
    )

    assert isinstance(result, Response)
    assert result.status_code == 204


def test_delete_author_photo_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_author_photo handles errors (covers lines 873-874)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service.delete_photo = MagicMock(side_effect=ValueError("photo_not_found"))  # type: ignore[assignment]

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with pytest.raises(HTTPException):
        authors.delete_author_photo(
            author_id="1",
            photo_id=999,
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
        )


def test_get_permission_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_permission_helper creates AuthorPermissionHelper (covers line 149)."""
    session = DummySession()

    with patch(
        "bookcard.api.routes.authors.AuthorPermissionHelper"
    ) as mock_helper_class:
        mock_helper = MagicMock()
        mock_helper_class.return_value = mock_helper

        result = authors._get_permission_helper(session)  # type: ignore[arg-type]

        assert result is not None
        mock_helper_class.assert_called_once_with(session)


def test_list_authors_page_size_less_than_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test list_authors validates page_size < 1 (covers line 302)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._list_result = ([], 0)

    _mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with patch(
        "bookcard.api.routes.authors.PermissionService"
    ) as mock_perm_service_class:
        mock_perm_service = MagicMock()
        mock_perm_service.check_permission.return_value = None
        mock_perm_service_class.return_value = mock_perm_service

        result = authors.list_authors(
            current_user=current_user,
            session=session,
            author_service=mock_service,
            page=1,
            page_size=0,
        )
        assert result["page_size"] == 20


def test_update_author_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_author handles ValueError (covers lines 405-406)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service.update_author = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("author_not_found")
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    update = AuthorUpdate(name="New Name")
    with pytest.raises(HTTPException):
        authors.update_author(
            author_id="1",
            update=update,
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
        )


def test_recommend_merge_author_permission_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test recommend_merge_author handles permission errors (covers lines 547-548)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("author_not_found")
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request_body = AuthorMergeRecommendRequest(author_ids=["999", "998"])
    with pytest.raises(HTTPException):
        authors.recommend_merge_author(
            request_body=request_body,
            current_user=current_user,
            author_service=mock_service,
            merge_service=MockMergeService(),
            permission_helper=mock_permission_helper,
        )


def test_recommend_merge_author_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test recommend_merge_author handles service errors (covers lines 552-553)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Author 1"}
    mock_service._author_data["2"] = {"id": "2", "name": "Author 2"}

    mock_permission_helper, _, mock_merge_service = _setup_route_mocks(
        monkeypatch, session, mock_service
    )
    mock_merge_service.recommend_keep_author = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("invalid_author_ids")
    )

    request_body = AuthorMergeRecommendRequest(author_ids=["1", "2"])
    with pytest.raises(HTTPException):
        authors.recommend_merge_author(
            request_body=request_body,
            current_user=current_user,
            author_service=mock_service,
            merge_service=mock_merge_service,
            permission_helper=mock_permission_helper,
        )


def test_merge_authors_permission_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test merge_authors handles permission errors (covers lines 598-599)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("author_not_found")
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    request_body = AuthorMergeRequest(author_ids=["999", "998"], keep_author_id="999")
    with pytest.raises(HTTPException):
        authors.merge_authors(
            request_body=request_body,
            current_user=current_user,
            author_service=mock_service,
            merge_service=MockMergeService(),
            permission_helper=mock_permission_helper,
        )


def test_merge_authors_service_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test merge_authors handles service errors (covers lines 606-607)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Author 1"}
    mock_service._author_data["2"] = {"id": "2", "name": "Author 2"}

    mock_permission_helper, _, mock_merge_service = _setup_route_mocks(
        monkeypatch, session, mock_service
    )
    mock_merge_service.merge_authors = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("invalid_author_ids")
    )

    request_body = AuthorMergeRequest(author_ids=["1", "2"], keep_author_id="1")
    with pytest.raises(HTTPException):
        authors.merge_authors(
            request_body=request_body,
            current_user=current_user,
            author_service=mock_service,
            merge_service=mock_merge_service,
            permission_helper=mock_permission_helper,
        )


def test_upload_author_photo_service_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_author_photo handles service errors (covers lines 679-680)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}
    mock_service.upload_author_photo = MagicMock(  # type: ignore[assignment]
        side_effect=ValueError("invalid_file_format")
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    mock_file = MagicMock()
    mock_file.filename = "photo.jpg"
    mock_file.file.read.return_value = b"fake image data"

    with pytest.raises(HTTPException):
        authors.upload_author_photo(
            author_id="1",
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            file=mock_file,
        )


def test_get_author_photo_404_http_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_author_photo returns 404 for HTTPException 404 (covers line 799)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service.get_author_by_id_or_key = MagicMock(  # type: ignore[assignment]
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="not_found"
        )
    )

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                data_directory = "/tmp"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    request = DummyRequest()
    result = authors.get_author_photo(
        author_id="999",
        photo_id=1,
        current_user=current_user,
        author_service=mock_service,
        permission_helper=mock_permission_helper,
        request=request,
    )

    assert isinstance(result, Response)
    assert result.status_code == 404


def test_get_author_photo_file_not_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_author_photo returns 404 when file doesn't exist (covers line 814)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_photo = MagicMock()
    mock_photo.file_path = "photos/1/nonexistent.jpg"
    mock_photo.file_name = "nonexistent.jpg"
    mock_photo.mime_type = "image/jpeg"
    mock_service.get_author_photo_by_id = MagicMock(return_value=mock_photo)  # type: ignore[assignment]

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with tempfile.TemporaryDirectory() as tmpdir:

        class DummyRequest:
            def __init__(self, temp_dir: str) -> None:
                class DummyConfig:
                    data_directory = temp_dir

                self.app = type(
                    "App",
                    (),
                    {"state": type("State", (), {"config": DummyConfig()})()},
                )()

        request = DummyRequest(tmpdir)
        result = authors.get_author_photo(
            author_id="1",
            photo_id=1,
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            request=request,
        )

        assert isinstance(result, Response)
        assert result.status_code == 404


def test_get_author_photo_invalid_media_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_author_photo handles invalid media type (covers line 819)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockAuthorService()
    mock_service._author_data["1"] = {"id": "1", "name": "Test Author"}

    mock_permission_helper, _, _ = _setup_route_mocks(
        monkeypatch, session, mock_service
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        photo_path = Path(tmpdir) / "photos" / "1" / "photo_1.jpg"
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        photo_path.write_bytes(b"fake image")

        class DummyRequest:
            def __init__(self, temp_dir: str) -> None:
                class DummyConfig:
                    data_directory = temp_dir

                self.app = type(
                    "App",
                    (),
                    {"state": type("State", (), {"config": DummyConfig()})()},
                )()

        request = DummyRequest(tmpdir)
        mock_photo = MagicMock()
        mock_photo.file_path = str(photo_path.relative_to(tmpdir))
        mock_photo.file_name = "photo_1.jpg"
        mock_photo.mime_type = "application/pdf"  # Invalid media type
        mock_service.get_author_photo_by_id = MagicMock(return_value=mock_photo)  # type: ignore[assignment]

        result = authors.get_author_photo(
            author_id="1",
            photo_id=1,
            current_user=current_user,
            author_service=mock_service,
            permission_helper=mock_permission_helper,
            request=request,
        )

        assert isinstance(result, FileResponse)
        assert result.media_type == "image/jpeg"  # Should default to image/jpeg
