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

"""Tests for book upload workflow and task adapters."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bookcard.services.tasks.book_upload_task import BookUploadTask
from bookcard.services.tasks.book_upload_workflow import (
    AuthorResolver,
    BookUploadWorkflow,
    DuplicateChecker,
    FileInfo,
    FileMetadataProvider,
    PostProcessorRunner,
    ProgressTracker,
    TitleResolver,
    UploadContext,
    UploadFileValidator,
    UploadResult,
)
from bookcard.services.tasks.exceptions import TaskCancelledError


@pytest.fixture
def temp_file() -> Path:
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as f:
        f.write(b"test content")
        return Path(f.name)


def test_file_info_from_metadata(temp_file: Path) -> None:
    """FileInfo should parse metadata and defaults."""
    info = FileInfo.from_metadata({
        "file_path": str(temp_file),
        "filename": "t.epub",
        "file_format": "epub",
    })
    assert info.file_path == temp_file
    assert info.filename == "t.epub"
    assert info.file_format == "epub"


def test_file_info_missing_path() -> None:
    """FileInfo should raise when file_path is missing."""
    with pytest.raises(ValueError, match="file_path is required in task metadata"):
        FileInfo.from_metadata({})


def test_upload_file_validator_success(temp_file: Path) -> None:
    """UploadFileValidator should return file size."""
    validator = UploadFileValidator()
    info = FileInfo.from_metadata({
        "file_path": str(temp_file),
        "filename": "t.epub",
        "file_format": "epub",
    })
    assert validator.validate(info) > 0


def test_upload_file_validator_not_found() -> None:
    """UploadFileValidator should raise for missing file."""
    validator = UploadFileValidator()
    info = FileInfo.from_metadata({
        "file_path": "/missing/file.epub",
        "filename": "file.epub",
        "file_format": "epub",
    })
    with pytest.raises(FileNotFoundError, match="File not found"):
        validator.validate(info)


def test_upload_file_validator_directory() -> None:
    """UploadFileValidator should reject directories."""
    validator = UploadFileValidator()
    with tempfile.TemporaryDirectory() as tmpdir:
        info = FileInfo.from_metadata({
            "file_path": tmpdir,
            "filename": "dir",
            "file_format": "epub",
        })
        with pytest.raises(ValueError, match="file_path is a directory"):
            validator.validate(info)


def test_title_resolver_prefers_file_metadata() -> None:
    """TitleResolver should prefer embedded metadata title."""
    resolver = TitleResolver()
    file_metadata = MagicMock(title="Embedded Title")
    info = FileInfo.from_metadata({
        "file_path": "/tmp/file.epub",
        "filename": "File Name.epub",
    })
    assert resolver.resolve(file_metadata, {"title": "Payload Title"}, info) == (
        "Embedded Title"
    )


def test_title_resolver_fallbacks() -> None:
    """TitleResolver should fallback to payload, then filename stem."""
    resolver = TitleResolver()
    info = FileInfo.from_metadata({
        "file_path": "/tmp/file.epub",
        "filename": "File Name.epub",
    })
    assert resolver.resolve(None, {"title": "Payload Title"}, info) == "Payload Title"
    assert resolver.resolve(None, {}, info) == "File Name"


def test_author_resolver() -> None:
    """AuthorResolver should ignore unknown author."""
    resolver = AuthorResolver()
    assert resolver.resolve(None) is None
    assert resolver.resolve(MagicMock(author="Unknown")) is None
    assert resolver.resolve(MagicMock(author="Author")) == "Author"


def test_file_metadata_provider_caches() -> None:
    """FileMetadataProvider should cache metadata."""
    metadata_service = MagicMock()
    metadata_service.extract_metadata.return_value = (MagicMock(title="T"), None)
    provider = FileMetadataProvider(metadata_service=metadata_service)
    info = FileInfo.from_metadata({
        "file_path": "/tmp/file.epub",
        "filename": "File.epub",
        "file_format": "epub",
    })
    first = provider.get(info)
    second = provider.get(info)
    assert first is second
    metadata_service.extract_metadata.assert_called_once()


def test_file_metadata_provider_handles_error() -> None:
    """FileMetadataProvider should return None on extraction errors."""
    metadata_service = MagicMock()
    metadata_service.extract_metadata.side_effect = ValueError("boom")
    provider = FileMetadataProvider(metadata_service=metadata_service)
    info = FileInfo.from_metadata({
        "file_path": "/tmp/file.epub",
        "filename": "File.epub",
        "file_format": "epub",
    })
    assert provider.get(info) is None


def test_duplicate_checker_skip() -> None:
    """DuplicateChecker should raise on skip policy."""
    from bookcard.services.duplicate_detection.book_duplicate_handler import (
        DuplicateCheckResult,
    )

    handler = MagicMock()
    handler.check_duplicate.return_value = DuplicateCheckResult(
        is_duplicate=True,
        duplicate_book_id=1,
        should_skip=True,
        should_overwrite=False,
    )
    checker = DuplicateChecker(handler=handler)
    with pytest.raises(ValueError, match="Duplicate book found"):
        checker.check_and_handle(
            library=MagicMock(),
            book_service=MagicMock(),
            file_info=MagicMock(),
            title="T",
            author_name="A",
        )


def test_duplicate_checker_overwrite() -> None:
    """DuplicateChecker should delete when overwrite policy."""
    from bookcard.services.duplicate_detection.book_duplicate_handler import (
        DuplicateCheckResult,
    )

    handler = MagicMock()
    handler.check_duplicate.return_value = DuplicateCheckResult(
        is_duplicate=True,
        duplicate_book_id=5,
        should_skip=False,
        should_overwrite=True,
    )
    book_service = MagicMock()
    checker = DuplicateChecker(handler=handler)
    checker.check_and_handle(
        library=MagicMock(),
        book_service=book_service,
        file_info=MagicMock(),
        title="T",
        author_name="A",
    )
    book_service.delete_book.assert_called_once_with(
        book_id=5, delete_files_from_drive=True
    )


def test_post_processor_runner_handles_errors() -> None:
    """PostProcessorRunner should swallow processor errors."""
    runner = PostProcessorRunner()
    processor = MagicMock()
    processor.supports_format.return_value = True
    processor.process.side_effect = ValueError("boom")
    runner.run(
        session=MagicMock(),
        book_id=1,
        library=MagicMock(),
        user_id=1,
        processors=[processor],
        file_format="epub",
    )
    processor.process.assert_called_once()


def test_progress_tracker_cancels() -> None:
    """ProgressTracker should raise on cancellation."""
    tracker = ProgressTracker(lambda *_: None, lambda: True, task_id=99)
    with pytest.raises(TaskCancelledError):
        tracker.update(0.1)


def test_workflow_execute_success(temp_file: Path) -> None:
    """BookUploadWorkflow should orchestrate dependencies."""
    file_info = FileInfo.from_metadata({
        "file_path": str(temp_file),
        "filename": temp_file.name,
        "file_format": "epub",
    })
    workflow = BookUploadWorkflow(
        file_validator=MagicMock(validate=MagicMock(return_value=42)),
        library_accessor=MagicMock(
            get_active_library=MagicMock(return_value=MagicMock())
        ),
        metadata_provider=MagicMock(get=MagicMock(return_value=MagicMock(title="T"))),
        title_resolver=MagicMock(resolve=MagicMock(return_value="Title")),
        author_resolver=MagicMock(resolve=MagicMock(return_value="Author")),
        duplicate_checker=MagicMock(check_and_handle=MagicMock()),
        book_adder=MagicMock(add=MagicMock(return_value=123)),
        post_processor_factory=MagicMock(build=MagicMock(return_value=[])),
        post_processor_runner=MagicMock(run=MagicMock()),
    )
    context = UploadContext(
        session=MagicMock(),
        update_progress=MagicMock(),
        check_cancelled=lambda: False,
        task_id=1,
        user_id=1,
        file_info=file_info,
        task_metadata={},
        post_processors=None,
    )
    result = workflow.execute(context)
    assert result == UploadResult(book_id=123, title="Title", file_size=42)


def test_book_upload_task_sets_metadata(temp_file: Path) -> None:
    """BookUploadTask should set metadata from workflow result."""
    workflow = MagicMock()
    workflow.execute.return_value = UploadResult(
        book_id=11, title="Title", file_size=12
    )
    task = BookUploadTask(
        task_id=1,
        user_id=1,
        metadata={
            "file_path": str(temp_file),
            "filename": temp_file.name,
            "file_format": "epub",
        },
        workflow=workflow,
    )
    worker_context = {
        "session": MagicMock(),
        "task_service": MagicMock(),
        "update_progress": MagicMock(),
    }
    task.run(worker_context)
    assert task.metadata["book_ids"] == [11]
    assert task.metadata["title"] == "Title"
    assert task.metadata["file_size"] == 12
