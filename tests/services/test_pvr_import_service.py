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

"""Unit tests for PVRImportService."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.models.pvr import (
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.services.ingest.file_discovery_service import (
    FileDiscoveryService,
    FileGroup,
)
from bookcard.services.ingest.ingest_processor_service import IngestProcessorService
from bookcard.services.pvr_import_service import PVRImportService
from bookcard.services.tracked_book_service import TrackedBookService


@pytest.fixture
def mock_session() -> MagicMock:
    """Mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_ingest_service() -> MagicMock:
    """Mock ingest processor service."""
    return MagicMock(spec=IngestProcessorService)


@pytest.fixture
def mock_tracked_book_service() -> MagicMock:
    """Mock tracked book service."""
    return MagicMock(spec=TrackedBookService)


@pytest.fixture
def mock_file_discovery_service() -> MagicMock:
    """Mock file discovery service."""
    return MagicMock(spec=FileDiscoveryService)


@pytest.fixture
def pvr_import_service(
    mock_session: MagicMock,
    mock_ingest_service: MagicMock,
    mock_tracked_book_service: MagicMock,
    mock_file_discovery_service: MagicMock,
) -> PVRImportService:
    """Create PVRImportService instance with mocked dependencies."""
    return PVRImportService(
        session=mock_session,
        ingest_service=mock_ingest_service,
        tracked_book_service=mock_tracked_book_service,
        file_discovery_service=mock_file_discovery_service,
    )


@pytest.fixture
def sample_tracked_book() -> TrackedBook:
    """Create a sample tracked book."""
    return TrackedBook(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        status=TrackedBookStatus.DOWNLOADING,
        library_id=1,
    )


@pytest.fixture
def sample_download_item(sample_tracked_book: TrackedBook) -> DownloadItem:
    """Create a sample download item."""
    item = DownloadItem(
        id=100,
        tracked_book_id=sample_tracked_book.id,
        download_client_id=1,
        client_item_id="hash123",
        title="Test Book Release",
        download_url="magnet:?xt=urn:btih:...",
        file_path="/downloads/Test Book",
        status=DownloadItemStatus.COMPLETED,
    )
    # Manually set relationship for test since we're not using real DB
    item.tracked_book = sample_tracked_book
    return item


class TestPVRImportService:
    """Test suite for PVRImportService."""

    def test_import_pending_downloads_success(
        self,
        pvr_import_service: PVRImportService,
        mock_session: MagicMock,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test finding and importing pending downloads."""
        # Setup
        mock_session.exec.return_value.all.return_value = [sample_download_item]

        # Mock process_completed_download to avoid actual processing logic in this test
        with patch.object(
            pvr_import_service, "process_completed_download"
        ) as mock_process:
            # Execute
            count = pvr_import_service.import_pending_downloads()

            # Verify
            assert count == 1
            mock_process.assert_called_once_with(sample_download_item)
            mock_session.exec.assert_called_once()

    def test_import_pending_downloads_error_handling(
        self,
        pvr_import_service: PVRImportService,
        mock_session: MagicMock,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test error handling loop in import_pending_downloads."""
        # Setup - return 2 items
        item2 = DownloadItem(id=101, status=DownloadItemStatus.COMPLETED)
        mock_session.exec.return_value.all.return_value = [sample_download_item, item2]

        with patch.object(
            pvr_import_service, "process_completed_download"
        ) as mock_process:
            # First call raises exception, second succeeds
            mock_process.side_effect = [ValueError("Processing error"), None]

            # Execute
            count = pvr_import_service.import_pending_downloads()

            # Verify
            assert count == 1  # Only 1 successful
            assert mock_process.call_count == 2

    def test_process_completed_download_validation(
        self,
        pvr_import_service: PVRImportService,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test validation in process_completed_download."""
        # Case 1: Not completed
        sample_download_item.status = DownloadItemStatus.DOWNLOADING
        with pytest.raises(ValueError, match="not completed"):
            pvr_import_service.process_completed_download(sample_download_item)

        # Case 2: No file path
        sample_download_item.status = DownloadItemStatus.COMPLETED
        sample_download_item.file_path = None
        with pytest.raises(ValueError, match="no file path"):
            pvr_import_service.process_completed_download(sample_download_item)

        # Case 3: Path does not exist
        sample_download_item.file_path = "/nonexistent/path"
        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(FileNotFoundError, match="does not exist"),
        ):
            pvr_import_service.process_completed_download(sample_download_item)

    @patch("tempfile.TemporaryDirectory")
    @patch("bookcard.services.pvr_import_service.shutil")
    def test_process_completed_download_success(
        self,
        mock_shutil: MagicMock,
        mock_temp_dir: MagicMock,
        pvr_import_service: PVRImportService,
        mock_file_discovery_service: MagicMock,
        mock_ingest_service: MagicMock,
        mock_session: MagicMock,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test successful processing of a completed download."""
        # Setup mocks
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/pvr_import_123"

        # Mock Path.exists to return True
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
        ):
            # Mock file discovery
            book_file = Path("/tmp/pvr_import_123/book.epub")
            mock_file_discovery_service.discover_files.return_value = [book_file]

            # Mock grouping
            file_group = FileGroup(book_key="book", files=[book_file])
            mock_file_discovery_service.group_files_by_directory.return_value = [
                file_group
            ]

            # Mock ingest service returns
            mock_ingest_service.process_file_group.return_value = 555  # history_id
            mock_ingest_service.get_active_library.return_value = Library(id=99)
            mock_ingest_service.add_book_to_library.return_value = 777  # book_id

            # Execute
            pvr_import_service.process_completed_download(sample_download_item)

            # Verify flow
            # 1. Prepare files (copy/extract)
            mock_shutil.copy2.assert_called()  # assuming file copy for single file

            # 2. Discovery
            mock_file_discovery_service.discover_files.assert_called()
            mock_file_discovery_service.group_files_by_directory.assert_called()

            # 3. Ingest
            mock_ingest_service.process_file_group.assert_called_with(file_group)
            mock_ingest_service.fetch_and_store_metadata.assert_called()
            mock_ingest_service.add_book_to_library.assert_called()
            mock_ingest_service.finalize_history.assert_called_with(555, [777])

            # 4. Update tracked book
            assert (
                sample_download_item.tracked_book.status == TrackedBookStatus.COMPLETED
            )
            assert sample_download_item.tracked_book.matched_book_id == 777
            assert sample_download_item.tracked_book.matched_library_id == 99

            # 5. DB commit
            assert mock_session.add.call_count >= 1
            mock_session.commit.assert_called()

    @patch("tempfile.TemporaryDirectory")
    def test_process_completed_download_no_files_found(
        self,
        mock_temp_dir: MagicMock,
        pvr_import_service: PVRImportService,
        mock_file_discovery_service: MagicMock,
        mock_session: MagicMock,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test processing when no book files are found."""
        # Setup
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/pvr_import_123"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("bookcard.services.pvr_import_service.shutil"),
        ):
            # Return empty list for discovery
            mock_file_discovery_service.discover_files.return_value = []

            # Execute
            pvr_import_service.process_completed_download(sample_download_item)

            # Verify failure handling
            assert sample_download_item.tracked_book.status == TrackedBookStatus.FAILED
            assert sample_download_item.tracked_book.error_message is not None
            assert (
                "No supported book files found"
                in sample_download_item.tracked_book.error_message
            )
            assert sample_download_item.error_message is not None
            assert "No supported book files found" in sample_download_item.error_message
            mock_session.commit.assert_called()

    @patch("tempfile.TemporaryDirectory")
    def test_process_completed_download_ingest_failure(
        self,
        mock_temp_dir: MagicMock,
        pvr_import_service: PVRImportService,
        mock_file_discovery_service: MagicMock,
        mock_ingest_service: MagicMock,
        mock_session: MagicMock,
        sample_download_item: DownloadItem,
    ) -> None:
        """Test handling of ingest service failure."""
        # Setup
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/pvr_import_123"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("bookcard.services.pvr_import_service.shutil"),
        ):
            # Setup valid file discovery
            book_file = Path("/tmp/pvr_import_123/book.epub")
            mock_file_discovery_service.discover_files.return_value = [book_file]
            mock_file_discovery_service.group_files_by_directory.return_value = [
                FileGroup(book_key="book", files=[book_file])
            ]

            # Make ingest raise error
            mock_ingest_service.process_file_group.side_effect = RuntimeError(
                "Ingest crashed"
            )

            # Execute
            pvr_import_service.process_completed_download(sample_download_item)

            # Verify failure handling
            assert sample_download_item.tracked_book.status == TrackedBookStatus.FAILED
            assert sample_download_item.tracked_book.error_message is not None
            assert "Ingest failed" in sample_download_item.tracked_book.error_message
            mock_session.commit.assert_called()

    @pytest.mark.parametrize(
        ("filename", "is_archive"),
        [
            ("book.zip", True),
            ("book.tar", True),
            ("book.rar", True),
            ("book.epub", False),
            ("book.pdf", False),
            ("book.txt", False),
        ],
    )
    def test_is_archive(
        self,
        pvr_import_service: PVRImportService,
        filename: str,
        is_archive: bool,
    ) -> None:
        """Test archive detection."""
        path = Path(filename)
        assert pvr_import_service._is_archive(path) == is_archive

    @patch("bookcard.services.pvr_import_service.shutil")
    def test_prepare_files_archive(
        self,
        mock_shutil: MagicMock,
        pvr_import_service: PVRImportService,
    ) -> None:
        """Test prepare_files with archive."""
        source = Path("/downloads/book.zip")
        dest = Path("/tmp/extract")

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch.object(pvr_import_service, "_is_archive", return_value=True),
        ):
            pvr_import_service._prepare_files(source, dest)

            mock_shutil.unpack_archive.assert_called_once_with(source, dest)
            mock_shutil.copy2.assert_not_called()

    @patch("bookcard.services.pvr_import_service.shutil")
    def test_prepare_files_directory(
        self,
        mock_shutil: MagicMock,
        pvr_import_service: PVRImportService,
    ) -> None:
        """Test prepare_files with directory."""
        source = MagicMock(spec=Path)
        source.is_file.return_value = False
        source.is_dir.return_value = True
        dest = Path("/tmp/extract")

        # Setup directory iteration
        file1 = MagicMock(spec=Path)
        file1.is_dir.return_value = False
        file1.name = "file1.txt"

        dir1 = MagicMock(spec=Path)
        dir1.is_dir.return_value = True
        dir1.name = "subdir"

        source.iterdir.return_value = [file1, dir1]

        pvr_import_service._prepare_files(source, dest)

        # Check calls
        mock_shutil.copy2.assert_called_with(file1, dest)
        mock_shutil.copytree.assert_called_with(dir1, dest / "subdir")
