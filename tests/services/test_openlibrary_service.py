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

"""Tests for OpenLibraryService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.config import AppConfig
from bookcard.models.tasks import TaskType
from bookcard.services.openlibrary_service import OpenLibraryService
from bookcard.services.tasks.base import TaskRunner


@pytest.fixture
def mock_task_runner() -> MagicMock:
    """Create a mock task runner."""
    runner = MagicMock(spec=TaskRunner)
    runner.enqueue.return_value = 123
    return runner


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock app config."""
    config = MagicMock(spec=AppConfig)
    config.data_directory = "/data/directory"
    return config


@pytest.fixture
def service(mock_task_runner: MagicMock, mock_config: MagicMock) -> OpenLibraryService:
    """Create OpenLibraryService instance."""
    return OpenLibraryService(mock_task_runner, mock_config)


class TestOpenLibraryServiceInit:
    """Test OpenLibraryService initialization."""

    def test_init_stores_dependencies(
        self, mock_task_runner: MagicMock, mock_config: MagicMock
    ) -> None:
        """Test __init__ stores task_runner and config."""
        service = OpenLibraryService(mock_task_runner, mock_config)
        assert service._task_runner == mock_task_runner
        assert service._config == mock_config


class TestCreateDownloadTask:
    """Test create_download_task method."""

    @pytest.mark.parametrize(
        ("urls", "expected_error"),
        [
            ([], ValueError),
            (None, ValueError),
        ],
    )
    def test_create_download_task_no_urls(
        self,
        service: OpenLibraryService,
        urls: list[str] | None,
        expected_error: type[Exception],
    ) -> None:
        """Test create_download_task raises ValueError when no URLs provided."""
        with pytest.raises(expected_error, match="No URLs provided"):
            service.create_download_task(urls, user_id=1)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "urls",
        [
            ["https://example.com/file1.json"],
            ["https://example.com/file1.json", "https://example.com/file2.json"],
            [
                "https://example.com/file1.json",
                "https://example.com/file2.json",
                "https://example.com/file3.json",
            ],
        ],
    )
    def test_create_download_task_success(
        self,
        service: OpenLibraryService,
        mock_task_runner: MagicMock,
        mock_config: MagicMock,
        urls: list[str],
    ) -> None:
        """Test create_download_task enqueues task with correct parameters."""
        task_id = service.create_download_task(urls, user_id=1)

        assert task_id == 123
        mock_task_runner.enqueue.assert_called_once_with(
            task_type=TaskType.OPENLIBRARY_DUMP_DOWNLOAD,
            payload={"urls": urls},
            user_id=1,
            metadata={
                "task_type": TaskType.OPENLIBRARY_DUMP_DOWNLOAD,
                "urls": urls,
                "data_directory": mock_config.data_directory,
            },
        )


class TestCreateIngestTask:
    """Test create_ingest_task method."""

    def test_create_ingest_task_success(
        self,
        service: OpenLibraryService,
        mock_task_runner: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Test create_ingest_task enqueues task with correct parameters."""
        task_id = service.create_ingest_task(user_id=1)

        assert task_id == 123
        mock_task_runner.enqueue.assert_called_once_with(
            task_type=TaskType.OPENLIBRARY_DUMP_INGEST,
            payload={},
            user_id=1,
            metadata={
                "task_type": TaskType.OPENLIBRARY_DUMP_INGEST,
                "data_directory": mock_config.data_directory,
                "process_authors": True,
                "process_works": True,
                "process_editions": True,
            },
        )

    @pytest.mark.parametrize("user_id", [1, 2, 100])
    def test_create_ingest_task_different_users(
        self,
        service: OpenLibraryService,
        mock_task_runner: MagicMock,
        user_id: int,
    ) -> None:
        """Test create_ingest_task with different user IDs."""
        task_id = service.create_ingest_task(user_id=user_id)

        assert task_id == 123
        mock_task_runner.enqueue.assert_called_once()
        call_kwargs = mock_task_runner.enqueue.call_args[1]
        assert call_kwargs["user_id"] == user_id
