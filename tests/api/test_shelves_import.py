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

"""Tests for shelf import endpoint."""

import tempfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import NoReturn
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from bookcard.api.deps import get_current_user, get_db_session, get_visible_library_ids
from bookcard.api.routes.shelves import router as shelves_router
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.models.shelves import Shelf, ShelfTypeEnum
from bookcard.services.shelf_service import ShelfService
from tests.conftest import TEST_ENCRYPTION_KEY, DummySession


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


@pytest.fixture
def test_shelf() -> Shelf:
    """Create a test shelf."""
    from datetime import UTC, datetime

    return Shelf(
        id=1,
        name="Test Shelf",
        description="Test description",
        is_public=False,
        shelf_type=ShelfTypeEnum.SHELF,
        user_id=1,
        library_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_modified=datetime.now(UTC),
    )


@pytest.fixture
def mock_session() -> DummySession:
    """Create a mock database session."""
    return DummySession()


@pytest.fixture
def mock_shelf_service(test_shelf: Shelf) -> MagicMock:
    """Create a mock shelf service."""
    service = MagicMock(spec=ShelfService)
    # Mock import_read_list to return a successful result
    from bookcard.services.readlist.import_service import ImportResult

    result = ImportResult()
    result.total_books = 1
    result.matched = []
    result.unmatched = []
    result.errors = []
    service.import_read_list.return_value = result
    return service


def _mock_library() -> Library:
    """Create a mock Library used across import tests."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )


def _patch_route_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    test_shelf: Shelf,
    mock_shelf_service: MagicMock,
    *,
    allow_permissions: bool = True,
) -> None:
    """Apply monkeypatches common to all import tests."""
    mock_library = _mock_library()
    _factory = lambda *a, **kw: MagicMock()  # noqa: E731

    mock_repo = MagicMock()
    mock_repo.get.return_value = test_shelf
    monkeypatch.setattr(
        "bookcard.api.routes.shelves.ShelfRepository", lambda *a, **kw: mock_repo
    )

    mock_link_repo = MagicMock()
    mock_link_repo.find_by_shelf.return_value = []
    monkeypatch.setattr(
        "bookcard.api.routes.shelves.BookShelfLinkRepository",
        lambda *a, **kw: mock_link_repo,
    )

    monkeypatch.setattr(
        "bookcard.api.routes.shelves._resolve_active_library",
        lambda session, user_id=None: mock_library,
    )

    mock_lib_service = MagicMock()
    mock_lib_service.get_active_library.return_value = mock_library
    mock_lib_service.get_library.return_value = mock_library
    monkeypatch.setattr(
        "bookcard.api.routes.shelves.LibraryService", lambda *a, **kw: mock_lib_service
    )

    mock_perm_service = MagicMock()
    if allow_permissions:
        mock_perm_service.check_permission.return_value = None
    else:
        from fastapi import HTTPException, status

        def _deny(*a: object, **kw: object) -> NoReturn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="permission_denied"
            )

        mock_perm_service.check_permission.side_effect = _deny
    monkeypatch.setattr(
        "bookcard.api.routes.shelves.PermissionService",
        lambda *a, **kw: mock_perm_service,
    )

    monkeypatch.setattr(
        "bookcard.api.routes.shelves.ShelfService", lambda *a, **kw: mock_shelf_service
    )
    monkeypatch.setattr(
        "bookcard.api.routes.shelves._shelf_service",
        lambda *a, **kw: mock_shelf_service,
    )


def _mock_import_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch ReadListImportService with a dummy result."""
    from bookcard.services.readlist.import_service import ImportResult

    mock_svc = MagicMock()
    result = ImportResult()
    result.total_books = 1
    result.matched = []
    result.unmatched = []
    result.errors = []
    mock_svc.import_read_list.return_value = result
    monkeypatch.setattr(
        "bookcard.services.shelf_service.ReadListImportService",
        lambda *a, **kw: mock_svc,
    )


def _build_app(
    test_user: User,
    mock_session: DummySession,
) -> FastAPI:
    """Create a FastAPI app with dependency overrides."""
    from bookcard.config import AppConfig

    app = FastAPI()
    app.include_router(shelves_router, prefix="/api")

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_visible_library_ids] = lambda: [1]

    temp_data_dir = tempfile.mkdtemp()
    app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
        data_directory=temp_data_dir,
    )
    return app


@pytest.fixture
def app(
    test_user: User,
    mock_session: DummySession,
    mock_shelf_service: MagicMock,
    test_shelf: Shelf,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    """Create a FastAPI app with shelves router and mocked dependencies."""
    _patch_route_dependencies(monkeypatch, test_shelf, mock_shelf_service)
    _mock_import_service(monkeypatch)
    return _build_app(test_user, mock_session)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Create authentication headers."""
    return {"Authorization": "Bearer test_token"}


def test_import_read_list_endpoint(
    client: TestClient,
    auth_headers: dict[str, str],
    test_shelf: Shelf,
) -> None:
    """Test importing a read list."""
    xml_content = """<?xml version="1.0"?>
<ReadingList>
    <Name>Test List</Name>
    <Books>
        <Book>
            <Series>Test Series</Series>
            <Volume>1</Volume>
        </Book>
    </Books>
</ReadingList>"""

    with NamedTemporaryFile(mode="w", suffix=".cbl", delete=False) as f:
        f.write(xml_content)
        f.flush()
        file_path = Path(f.name)

    try:
        with Path(file_path).open("rb") as file:
            response = client.post(
                f"/api/shelves/{test_shelf.id}/import",
                headers=auth_headers,
                files={"file": ("test.cbl", file, "application/xml")},
                data={"importer": "comicrack", "auto_match": "false"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "total_books" in data
        assert "matched" in data
        assert "unmatched" in data
        assert "errors" in data
    finally:
        file_path.unlink()


def test_import_read_list_permission_denied(
    test_user: User,
    mock_session: DummySession,
    mock_shelf_service: MagicMock,
    test_shelf: Shelf,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that import requires edit permission."""
    _patch_route_dependencies(
        monkeypatch, test_shelf, mock_shelf_service, allow_permissions=False
    )

    app = _build_app(test_user, mock_session)
    client = TestClient(app)
    auth_headers = {"Authorization": "Bearer test_token"}

    xml_content = """<?xml version="1.0"?>
<ReadingList>
    <Name>Test List</Name>
    <Books>
        <Book>
            <Series>Test Series</Series>
            <Volume>1</Volume>
        </Book>
    </Books>
</ReadingList>"""

    with NamedTemporaryFile(mode="w", suffix=".cbl", delete=False) as f:
        f.write(xml_content)
        f.flush()
        file_path = Path(f.name)

    try:
        with Path(file_path).open("rb") as file:
            response = client.post(
                f"/api/shelves/{test_shelf.id}/import",
                headers=auth_headers,
                files={"file": ("test.cbl", file, "application/xml")},
                data={"importer": "comicrack", "auto_match": "false"},
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "permission_denied"
    finally:
        file_path.unlink()
