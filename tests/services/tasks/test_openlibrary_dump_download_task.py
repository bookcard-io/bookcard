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

"""Tests for OpenLibraryDumpDownloadTask to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from fundamental.services.tasks.openlibrary_dump_download_task import (
    OpenLibraryDumpDownloadTask,
)


@pytest.fixture
def mock_update_progress() -> MagicMock:
    """Create a mock update_progress callback.

    Returns
    -------
    MagicMock
        Mock update_progress callback.
    """
    return MagicMock()


@pytest.fixture
def worker_context(mock_update_progress: MagicMock) -> dict[str, Any]:
    """Create worker context dictionary.

    Parameters
    ----------
    mock_update_progress : MagicMock
        Mock update_progress callback.

    Returns
    -------
    dict[str, Any]
        Worker context dictionary.
    """
    return {
        "session": MagicMock(),
        "task_service": MagicMock(),
        "update_progress": mock_update_progress,
    }


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create temporary directory for downloads.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary path fixture.

    Returns
    -------
    Path
        Temporary directory path.
    """
    return tmp_path


@pytest.fixture
def metadata_with_urls(temp_dir: Path) -> dict[str, Any]:
    """Create metadata with URLs.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory path.

    Returns
    -------
    dict[str, Any]
        Metadata dictionary with URLs.
    """
    return {
        "urls": ["https://example.com/file1.txt", "https://example.com/file2.txt"],
        "data_directory": str(temp_dir),
    }


@pytest.mark.parametrize(
    ("urls", "data_directory", "should_raise"),
    [
        (["https://example.com/file.txt"], "/test/data", False),
        ([], "/test/data", True),
        (None, "/test/data", True),
        ("not_a_list", "/test/data", True),
        (["https://example.com/file.txt"], "/custom/path", False),
    ],
)
class TestOpenLibraryDumpDownloadTaskInit:
    """Test OpenLibraryDumpDownloadTask initialization."""

    def test_init_validation(
        self,
        urls: list[str] | str | None,
        data_directory: str,
        should_raise: bool,
    ) -> None:
        """Test __init__ URL validation.

        Parameters
        ----------
        urls : list[str] | None | str
            URLs list or invalid value.
        data_directory : str
            Data directory path.
        should_raise : bool
            Whether ValueError should be raised.
        """
        metadata: dict[str, Any] = {
            "urls": urls,
            "data_directory": data_directory,
        }
        if should_raise:
            with pytest.raises(ValueError, match="urls is required"):
                OpenLibraryDumpDownloadTask(
                    task_id=1,
                    user_id=1,
                    metadata=metadata,
                )
        else:
            task = OpenLibraryDumpDownloadTask(
                task_id=1,
                user_id=1,
                metadata=metadata,
            )
            assert task.urls == urls
            assert task.dump_dir == Path(data_directory) / "openlibrary" / "dump"

    def test_init_default_data_directory(
        self,
        urls: list[str] | str | None,
        data_directory: str,
        should_raise: bool,
    ) -> None:
        """Test __init__ with default data_directory.

        Parameters
        ----------
        urls : list[str] | None | str
            URLs list or invalid value.
        data_directory : str
            Data directory path.
        should_raise : bool
            Whether ValueError should be raised.
        """
        if should_raise:
            return

        metadata: dict[str, Any] = {"urls": urls}
        task = OpenLibraryDumpDownloadTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.dump_dir == Path("/data") / "openlibrary" / "dump"


class TestOpenLibraryDumpDownloadTaskDownloadFile:
    """Test OpenLibraryDumpDownloadTask._download_file method."""

    @pytest.fixture
    def task(self, metadata_with_urls: dict[str, Any]) -> OpenLibraryDumpDownloadTask:
        """Create task instance.

        Parameters
        ----------
        metadata_with_urls : dict[str, Any]
            Metadata with URLs.

        Returns
        -------
        OpenLibraryDumpDownloadTask
            Task instance.
        """
        return OpenLibraryDumpDownloadTask(
            task_id=1,
            user_id=1,
            metadata=metadata_with_urls,
        )

    @pytest.fixture
    def mock_httpx_response(self) -> Mock:
        """Create mock httpx response.

        Returns
        -------
        Mock
            Mock response object.
        """
        response = Mock()
        response.headers = {"content-length": "1000"}
        response.raise_for_status = Mock()
        response.iter_bytes = Mock(return_value=[b"chunk1", b"chunk2", b"chunk3"])
        return response

    @pytest.fixture
    def mock_httpx_client(self, mock_httpx_response: Mock) -> Mock:
        """Create mock httpx client.

        Parameters
        ----------
        mock_httpx_response : Mock
            Mock response object.

        Returns
        -------
        Mock
            Mock client object.
        """
        client = Mock()
        stream_context = MagicMock()
        stream_context.__enter__ = Mock(return_value=mock_httpx_response)
        stream_context.__exit__ = Mock(return_value=False)
        client.stream = Mock(return_value=stream_context)
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        return client

    @patch("fundamental.services.tasks.openlibrary_dump_download_task.httpx.Client")
    def test_download_file_success(
        self,
        mock_client_class: Mock,
        task: OpenLibraryDumpDownloadTask,
        mock_httpx_client: Mock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test successful file download.

        Parameters
        ----------
        mock_client_class : Mock
            Mock httpx.Client class.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        mock_httpx_client : Mock
            Mock httpx client.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        mock_client_class.return_value = mock_httpx_client
        url = "https://example.com/test_file.txt"

        file_path = task._download_file(url, mock_update_progress, 0, 2)

        assert file_path == str(task.dump_dir / "test_file.txt")
        assert (task.dump_dir / "test_file.txt").exists()
        mock_update_progress.assert_called()

    @patch("fundamental.services.tasks.openlibrary_dump_download_task.httpx.Client")
    def test_download_file_no_filename(
        self,
        mock_client_class: Mock,
        task: OpenLibraryDumpDownloadTask,
        mock_httpx_client: Mock,
        mock_update_progress: MagicMock,
    ) -> None:
        """Test download with URL that has no filename.

        Parameters
        ----------
        mock_client_class : Mock
            Mock httpx.Client class.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        mock_httpx_client : Mock
            Mock httpx client.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        mock_client_class.return_value = mock_httpx_client
        url = "https://example.com/"

        file_path = task._download_file(url, mock_update_progress, 0, 1)

        assert file_path == str(task.dump_dir / "download")
        assert (task.dump_dir / "download").exists()

    @patch("fundamental.services.tasks.openlibrary_dump_download_task.httpx.Client")
    def test_download_file_no_content_length(
        self,
        mock_client_class: Mock,
        task: OpenLibraryDumpDownloadTask,
        mock_httpx_client: Mock,
        mock_update_progress: MagicMock,
    ) -> None:
        """Test download with no content-length header.

        Parameters
        ----------
        mock_client_class : Mock
            Mock httpx.Client class.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        mock_httpx_client : Mock
            Mock httpx client.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[b"chunk1"])
        stream_context = MagicMock()
        stream_context.__enter__ = Mock(return_value=mock_response)
        stream_context.__exit__ = Mock(return_value=False)
        mock_httpx_client.stream = Mock(return_value=stream_context)
        mock_client_class.return_value = mock_httpx_client

        url = "https://example.com/test.txt"
        file_path = task._download_file(url, mock_update_progress, 0, 1)

        assert file_path == str(task.dump_dir / "test.txt")
        mock_update_progress.assert_called()

    @patch("fundamental.services.tasks.openlibrary_dump_download_task.httpx.Client")
    def test_download_file_cancelled(
        self,
        mock_client_class: Mock,
        task: OpenLibraryDumpDownloadTask,
        mock_httpx_client: Mock,
        mock_update_progress: MagicMock,
    ) -> None:
        """Test download cancellation during download.

        Parameters
        ----------
        mock_client_class : Mock
            Mock httpx.Client class.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        mock_httpx_client : Mock
            Mock httpx client.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        mock_response = Mock()
        mock_response.headers = {"content-length": "1000"}
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[b"chunk1", b"chunk2"])
        stream_context = MagicMock()
        stream_context.__enter__ = Mock(return_value=mock_response)
        stream_context.__exit__ = Mock(return_value=False)
        mock_httpx_client.stream = Mock(return_value=stream_context)
        mock_client_class.return_value = mock_httpx_client

        task.mark_cancelled()

        url = "https://example.com/test.txt"
        with pytest.raises(InterruptedError, match="Task cancelled"):
            task._download_file(url, mock_update_progress, 0, 1)

        # File should be deleted on cancellation
        assert not (task.dump_dir / "test.txt").exists()

    @patch("fundamental.services.tasks.openlibrary_dump_download_task.httpx.Client")
    def test_download_file_http_error(
        self,
        mock_client_class: Mock,
        task: OpenLibraryDumpDownloadTask,
        mock_httpx_client: Mock,
        mock_update_progress: MagicMock,
    ) -> None:
        """Test download with HTTP error.

        Parameters
        ----------
        mock_client_class : Mock
            Mock httpx.Client class.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        mock_httpx_client : Mock
            Mock httpx client.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=Mock()
        )
        stream_context = MagicMock()
        stream_context.__enter__ = Mock(return_value=mock_response)
        stream_context.__exit__ = Mock(return_value=False)
        mock_httpx_client.stream = Mock(return_value=stream_context)
        mock_client_class.return_value = mock_httpx_client

        url = "https://example.com/test.txt"
        with pytest.raises(httpx.HTTPStatusError):
            task._download_file(url, mock_update_progress, 0, 1)


class TestOpenLibraryDumpDownloadTaskRaiseAllFailed:
    """Test OpenLibraryDumpDownloadTask._raise_all_failed_error method."""

    @pytest.fixture
    def task(self, metadata_with_urls: dict[str, Any]) -> OpenLibraryDumpDownloadTask:
        """Create task instance.

        Parameters
        ----------
        metadata_with_urls : dict[str, Any]
            Metadata with URLs.

        Returns
        -------
        OpenLibraryDumpDownloadTask
            Task instance.
        """
        return OpenLibraryDumpDownloadTask(
            task_id=1,
            user_id=1,
            metadata=metadata_with_urls,
        )

    def test_raise_all_failed_error(self, task: OpenLibraryDumpDownloadTask) -> None:
        """Test _raise_all_failed_error raises RuntimeError.

        Parameters
        ----------
        task : OpenLibraryDumpDownloadTask
            Task instance.
        """
        failed_files = [
            "https://example.com/file1.txt",
            "https://example.com/file2.txt",
        ]
        with pytest.raises(RuntimeError, match="Failed to download all files"):
            task._raise_all_failed_error(failed_files)


class TestOpenLibraryDumpDownloadTaskRun:
    """Test OpenLibraryDumpDownloadTask run method."""

    @pytest.fixture
    def task(self, metadata_with_urls: dict[str, Any]) -> OpenLibraryDumpDownloadTask:
        """Create task instance.

        Parameters
        ----------
        metadata_with_urls : dict[str, Any]
            Metadata with URLs.

        Returns
        -------
        OpenLibraryDumpDownloadTask
            Task instance.
        """
        return OpenLibraryDumpDownloadTask(
            task_id=1,
            user_id=1,
            metadata=metadata_with_urls,
        )

    @patch(
        "fundamental.services.tasks.openlibrary_dump_download_task.OpenLibraryDumpDownloadTask._download_file"
    )
    def test_run_success(
        self,
        mock_download: Mock,
        task: OpenLibraryDumpDownloadTask,
        worker_context: dict[str, Any],
        mock_update_progress: MagicMock,
    ) -> None:
        """Test successful run with all files downloaded.

        Parameters
        ----------
        mock_download : Mock
            Mock _download_file method.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        mock_download.side_effect = [
            str(task.dump_dir / "file1.txt"),
            str(task.dump_dir / "file2.txt"),
        ]

        task.run(worker_context)

        assert mock_download.call_count == 2
        assert task.metadata["downloaded_files"] == [
            str(task.dump_dir / "file1.txt"),
            str(task.dump_dir / "file2.txt"),
        ]
        # Check final progress update
        final_call = mock_update_progress.call_args_list[-1]
        assert final_call[0][0] == 1.0

    @patch(
        "fundamental.services.tasks.openlibrary_dump_download_task.OpenLibraryDumpDownloadTask._download_file"
    )
    def test_run_cancelled_before_processing(
        self,
        mock_download: Mock,
        task: OpenLibraryDumpDownloadTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Test run when cancelled before processing.

        Parameters
        ----------
        mock_download : Mock
            Mock _download_file method.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        """
        task.mark_cancelled()

        task.run(worker_context)

        mock_download.assert_not_called()

    @patch(
        "fundamental.services.tasks.openlibrary_dump_download_task.OpenLibraryDumpDownloadTask._download_file"
    )
    def test_run_cancelled_during_download(
        self,
        mock_download: Mock,
        task: OpenLibraryDumpDownloadTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Test run when cancelled during download.

        Parameters
        ----------
        mock_download : Mock
            Mock _download_file method.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        """
        # Simulate cancellation after first file
        call_count = 0

        def side_effect(*args: object, **kwargs: object) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                task.mark_cancelled()
            return str(task.dump_dir / f"file{call_count}.txt")

        mock_download.side_effect = side_effect

        task.run(worker_context)

        # Should stop after cancellation
        assert call_count == 1

    @patch(
        "fundamental.services.tasks.openlibrary_dump_download_task.OpenLibraryDumpDownloadTask._download_file"
    )
    def test_run_partial_failure(
        self,
        mock_download: Mock,
        task: OpenLibraryDumpDownloadTask,
        worker_context: dict[str, Any],
        mock_update_progress: MagicMock,
    ) -> None:
        """Test run with partial file download failures.

        Parameters
        ----------
        mock_download : Mock
            Mock _download_file method.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        mock_download.side_effect = [
            str(task.dump_dir / "file1.txt"),
            Exception("Download failed"),
        ]

        task.run(worker_context)

        assert len(task.metadata["downloaded_files"]) == 1
        assert len(task.metadata["failed_files"]) == 1
        assert task.metadata["failed_files"][0] == task.urls[1]

    @patch(
        "fundamental.services.tasks.openlibrary_dump_download_task.OpenLibraryDumpDownloadTask._download_file"
    )
    def test_run_all_failed(
        self,
        mock_download: Mock,
        task: OpenLibraryDumpDownloadTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Test run when all files fail to download.

        Parameters
        ----------
        mock_download : Mock
            Mock _download_file method.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        """
        mock_download.side_effect = Exception("Download failed")

        with pytest.raises(RuntimeError, match="Failed to download all files"):
            task.run(worker_context)

    @patch(
        "fundamental.services.tasks.openlibrary_dump_download_task.OpenLibraryDumpDownloadTask._download_file"
    )
    def test_run_exception(
        self,
        mock_download: Mock,
        task: OpenLibraryDumpDownloadTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Test run with unexpected exception.

        When all files fail, it raises a RuntimeError about all files failing.

        Parameters
        ----------
        mock_download : Mock
            Mock _download_file method.
        task : OpenLibraryDumpDownloadTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        """
        mock_download.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(RuntimeError, match="Failed to download all files"):
            task.run(worker_context)
