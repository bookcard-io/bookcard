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

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.api.routes.shelves import router as shelves_router
from fundamental.models.auth import User
from fundamental.models.shelves import Shelf, ShelfTypeEnum
from fundamental.services.shelf_service import ShelfService
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
    from fundamental.services.readlist.import_service import ImportResult

    result = ImportResult()
    result.total_books = 1
    result.matched = []
    result.unmatched = []
    result.errors = []
    service.import_read_list.return_value = result
    return service


@pytest.fixture
def app(
    test_user: User,
    mock_session: DummySession,
    mock_shelf_service: MagicMock,
    test_shelf: Shelf,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    """Create a FastAPI app with shelves router and mocked dependencies."""
    # Mock all the dependencies before creating the app
    from fundamental.models.config import Library

    mock_library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    # Mock ShelfRepository
    mock_repo = MagicMock()
    mock_repo.get.return_value = test_shelf

    def mock_shelf_repo_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_repo

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.ShelfRepository", mock_shelf_repo_init
    )

    # Mock BookShelfLinkRepository
    mock_link_repo = MagicMock()
    mock_link_repo.find_by_shelf.return_value = []

    def mock_link_repo_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_link_repo

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.BookShelfLinkRepository", mock_link_repo_init
    )

    # Mock LibraryService
    mock_lib_service = MagicMock()
    mock_lib_service.get_active_library.return_value = mock_library
    mock_lib_service.get_library.return_value = mock_library

    def mock_lib_service_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_lib_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.LibraryService", mock_lib_service_init
    )

    # Mock PermissionService
    mock_perm_service = MagicMock()
    mock_perm_service.check_permission.return_value = None

    def mock_perm_service_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_perm_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.PermissionService", mock_perm_service_init
    )

    # Mock ShelfService
    def mock_shelf_service_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_shelf_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.ShelfService", mock_shelf_service_init
    )

    # Mock _shelf_service dependency function to avoid creating real ShelfService
    def mock_shelf_service_dep(*args: object, **kwargs: object) -> MagicMock:
        return mock_shelf_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves._shelf_service", mock_shelf_service_dep
    )

    # Mock ReadListImportService
    from fundamental.services.readlist.import_service import ImportResult

    mock_import_service = MagicMock()
    import_result = ImportResult()
    import_result.total_books = 1
    import_result.matched = []
    import_result.unmatched = []
    import_result.errors = []
    mock_import_service.import_read_list.return_value = import_result

    def mock_import_service_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_import_service

    monkeypatch.setattr(
        "fundamental.services.shelf_service.ReadListImportService",
        mock_import_service_init,
    )

    # Create app and override dependencies
    app = FastAPI()
    app.include_router(shelves_router, prefix="/api")

    # Override dependencies
    def get_current_user_override() -> User:
        return test_user

    def get_db_session_override() -> DummySession:
        return mock_session

    app.dependency_overrides[get_current_user] = get_current_user_override
    app.dependency_overrides[get_db_session] = get_db_session_override

    # Set app state for config with temporary data directory
    from fundamental.config import AppConfig

    # Use a temporary directory for data_directory to avoid permission issues
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
    from fastapi import FastAPI, HTTPException, status

    # Create a separate app with permission denied
    from fundamental.models.config import Library

    mock_library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )

    # Mock ShelfRepository
    mock_repo = MagicMock()
    mock_repo.get.return_value = test_shelf

    def mock_shelf_repo_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_repo

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.ShelfRepository", mock_shelf_repo_init
    )

    # Mock BookShelfLinkRepository
    mock_link_repo = MagicMock()
    mock_link_repo.find_by_shelf.return_value = []

    def mock_link_repo_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_link_repo

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.BookShelfLinkRepository", mock_link_repo_init
    )

    # Mock LibraryService
    mock_lib_service = MagicMock()
    mock_lib_service.get_active_library.return_value = mock_library
    mock_lib_service.get_library.return_value = mock_library

    def mock_lib_service_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_lib_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.LibraryService", mock_lib_service_init
    )

    # Mock ShelfService
    def mock_shelf_service_init_denied(*args: object, **kwargs: object) -> MagicMock:
        return mock_shelf_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.ShelfService", mock_shelf_service_init_denied
    )

    # Mock _shelf_service dependency function to avoid creating real ShelfService
    def mock_shelf_service_dep_denied(*args: object, **kwargs: object) -> MagicMock:
        return mock_shelf_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves._shelf_service", mock_shelf_service_dep_denied
    )

    # Mock PermissionService to DENY permission
    mock_perm_service = MagicMock()

    def check_permission_denied(*args: object, **kwargs: object) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="permission_denied"
        )

    mock_perm_service.check_permission.side_effect = check_permission_denied

    def mock_perm_service_init(*args: object, **kwargs: object) -> MagicMock:
        return mock_perm_service

    monkeypatch.setattr(
        "fundamental.api.routes.shelves.PermissionService", mock_perm_service_init
    )

    # Create app
    app = FastAPI()
    app.include_router(shelves_router, prefix="/api")

    def get_current_user_override() -> User:
        return test_user

    def get_db_session_override() -> DummySession:
        return mock_session

    app.dependency_overrides[get_current_user] = get_current_user_override
    app.dependency_overrides[get_db_session] = get_db_session_override

    from fundamental.config import AppConfig

    # Use a temporary directory for data_directory to avoid permission issues
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
