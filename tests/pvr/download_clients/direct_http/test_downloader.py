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

"""Tests for Direct HTTP downloader module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import httpx
import pytest

from bookcard.pvr.download_clients.direct_http.downloader import FileDownloader
from bookcard.pvr.download_clients.direct_http.protocols import StreamingHttpClient
from bookcard.pvr.exceptions import PVRProviderError


class TestFileDownloader:
    """Test FileDownloader class."""

    def test_init(self, mock_time_provider: MagicMock) -> None:
        """Test initialization."""
        downloader = FileDownloader(mock_time_provider)
        assert downloader._time == mock_time_provider

    def test_download_success(
        self, mock_time_provider: MagicMock, temp_dir: Path
    ) -> None:
        """Test successful download."""
        downloader = FileDownloader(mock_time_provider)
        client = MagicMock(spec=StreamingHttpClient)
        response = MagicMock()
        response.headers = httpx.Headers({"content-length": "1000"})
        response.raise_for_status = Mock()
        response.iter_bytes = Mock(return_value=iter([b"chunk1", b"chunk2", b"chunk3"]))
        client.stream.return_value.__enter__ = Mock(return_value=response)
        client.stream.return_value.__exit__ = Mock(return_value=False)

        state_manager = MagicMock()
        file_path = temp_dir / "test_file.pdf"

        downloader.download(
            client, "https://example.com/file.pdf", file_path, "test-id", state_manager
        )

        assert file_path.exists()
        assert file_path.read_bytes() == b"chunk1chunk2chunk3"
        state_manager.update_info.assert_called_once()
        assert state_manager.update_progress.call_count >= 1

    def test_download_with_headers(
        self, mock_time_provider: MagicMock, temp_dir: Path
    ) -> None:
        """Test download with custom headers."""
        downloader = FileDownloader(mock_time_provider)
        client = MagicMock(spec=StreamingHttpClient)
        response = MagicMock()
        response.headers = httpx.Headers({"content-length": "1000"})
        response.raise_for_status = Mock()
        response.iter_bytes = Mock(return_value=iter([b"data"]))
        client.stream.return_value.__enter__ = Mock(return_value=response)
        client.stream.return_value.__exit__ = Mock(return_value=False)

        state_manager = MagicMock()
        file_path = temp_dir / "test_file.pdf"
        headers = {"Referer": "https://example.com"}

        downloader.download(
            client,
            "https://example.com/file.pdf",
            file_path,
            "test-id",
            state_manager,
            headers=headers,
        )

        client.stream.assert_called_once_with(
            "GET",
            "https://example.com/file.pdf",
            follow_redirects=True,
            headers=headers,
        )

    def test_download_no_content_length(
        self, mock_time_provider: MagicMock, temp_dir: Path
    ) -> None:
        """Test download without content-length header."""
        downloader = FileDownloader(mock_time_provider)
        client = MagicMock(spec=StreamingHttpClient)
        response = MagicMock()
        response.headers = httpx.Headers({})
        response.raise_for_status = Mock()
        response.iter_bytes = Mock(return_value=iter([b"chunk"]))
        client.stream.return_value.__enter__ = Mock(return_value=response)
        client.stream.return_value.__exit__ = Mock(return_value=False)

        state_manager = MagicMock()
        file_path = temp_dir / "test_file.pdf"

        downloader.download(
            client, "https://example.com/file.pdf", file_path, "test-id", state_manager
        )

        assert file_path.exists()
        state_manager.update_info.assert_called_once_with("test-id", 0, str(file_path))

    def test_download_empty_chunks(
        self, mock_time_provider: MagicMock, temp_dir: Path
    ) -> None:
        """Test download with empty chunks."""
        downloader = FileDownloader(mock_time_provider)
        client = MagicMock(spec=StreamingHttpClient)
        response = MagicMock()
        response.headers = httpx.Headers({"content-length": "1000"})
        response.raise_for_status = Mock()
        response.iter_bytes = Mock(return_value=iter([b"chunk", b""]))
        client.stream.return_value.__enter__ = Mock(return_value=response)
        client.stream.return_value.__exit__ = Mock(return_value=False)

        state_manager = MagicMock()
        file_path = temp_dir / "test_file.pdf"

        downloader.download(
            client, "https://example.com/file.pdf", file_path, "test-id", state_manager
        )

        assert file_path.exists()
        assert file_path.read_bytes() == b"chunk"

    def test_download_os_error(
        self, mock_time_provider: MagicMock, temp_dir: Path
    ) -> None:
        """Test download with OSError."""
        downloader = FileDownloader(mock_time_provider)
        client = MagicMock(spec=StreamingHttpClient)
        response = MagicMock()
        response.headers = httpx.Headers({"content-length": "1000"})
        response.raise_for_status = Mock()
        response.iter_bytes = Mock(side_effect=OSError("Disk full"))
        client.stream.return_value.__enter__ = Mock(return_value=response)
        client.stream.return_value.__exit__ = Mock(return_value=False)

        state_manager = MagicMock()
        file_path = temp_dir / "test_file.pdf"

        with pytest.raises(PVRProviderError, match="File Error"):
            downloader.download(
                client,
                "https://example.com/file.pdf",
                file_path,
                "test-id",
                state_manager,
            )

    def test_download_progress_updates(
        self, mock_time_provider: MagicMock, temp_dir: Path
    ) -> None:
        """Test that progress is updated during download."""
        downloader = FileDownloader(mock_time_provider)
        client = MagicMock(spec=StreamingHttpClient)
        response = MagicMock()
        response.headers = httpx.Headers({"content-length": "10000"})
        response.raise_for_status = Mock()
        # Simulate multiple chunks
        chunks = [b"x" * 1000] * 10
        response.iter_bytes = Mock(return_value=iter(chunks))
        client.stream.return_value.__enter__ = Mock(return_value=response)
        client.stream.return_value.__exit__ = Mock(return_value=False)

        # Mock time to control update intervals - need enough values for all calls
        # time() is called: start_time, then in loop (now), then final (now)
        call_count = [0]

        def time_mock() -> float:
            times = [0.0, 0.6, 1.2, 1.8, 2.4, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
            idx = call_count[0]
            call_count[0] += 1
            return times[min(idx, len(times) - 1)]

        mock_time_provider.time.side_effect = time_mock

        state_manager = MagicMock()
        file_path = temp_dir / "test_file.pdf"

        downloader.download(
            client, "https://example.com/file.pdf", file_path, "test-id", state_manager
        )

        # Should have multiple progress updates
        assert state_manager.update_progress.call_count > 1

    def test_download_final_update(
        self, mock_time_provider: MagicMock, temp_dir: Path
    ) -> None:
        """Test that final progress update is made."""
        downloader = FileDownloader(mock_time_provider)
        client = MagicMock(spec=StreamingHttpClient)
        response = MagicMock()
        response.headers = httpx.Headers({"content-length": "1000"})
        response.raise_for_status = Mock()
        response.iter_bytes = Mock(return_value=iter([b"chunk"]))
        client.stream.return_value.__enter__ = Mock(return_value=response)
        client.stream.return_value.__exit__ = Mock(return_value=False)

        # time() is called: start_time, then final (now)
        call_count = [0]

        def time_mock() -> float:
            times = [0.0, 1.0, 2.0]
            idx = call_count[0]
            call_count[0] += 1
            return times[min(idx, len(times) - 1)]

        mock_time_provider.time.side_effect = time_mock

        state_manager = MagicMock()
        file_path = temp_dir / "test_file.pdf"

        downloader.download(
            client, "https://example.com/file.pdf", file_path, "test-id", state_manager
        )

        # Check final update with progress=1.0
        final_call = state_manager.update_progress.call_args_list[-1]
        assert final_call[0][2] == 1.0  # progress should be 1.0
