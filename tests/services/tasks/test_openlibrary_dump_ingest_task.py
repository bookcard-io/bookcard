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

"""Tests for OpenLibraryDumpIngestTask to achieve 100% coverage."""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from fundamental.models.openlibrary import (
    OpenLibraryAuthorWork,
    OpenLibraryEditionIsbn,
)
from fundamental.services.tasks.openlibrary_dump_ingest_task import (
    OpenLibraryDumpIngestTask,
)


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock SQLModel session.

    Returns
    -------
    MagicMock
        Mock session object.
    """
    session = MagicMock()
    session.connection.return_value.execute = MagicMock()
    return session


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
def worker_context(
    mock_session: MagicMock, mock_update_progress: MagicMock
) -> dict[str, Any]:
    """Create worker context dictionary.

    Parameters
    ----------
    mock_session : MagicMock
        Mock session object.
    mock_update_progress : MagicMock
        Mock update_progress callback.

    Returns
    -------
    dict[str, Any]
        Worker context dictionary.
    """
    return {
        "session": mock_session,
        "update_progress": mock_update_progress,
    }


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create temporary directory for test files.

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
def base_metadata(temp_dir: Path) -> dict[str, Any]:
    """Create base metadata dictionary.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory path.

    Returns
    -------
    dict[str, Any]
        Base metadata dictionary.
    """
    return {"data_directory": str(temp_dir)}


def create_gzip_dump_file(file_path: Path, lines: list[str]) -> None:
    """Create a gzipped dump file for testing.

    Parameters
    ----------
    file_path : Path
        Path to create the file.
    lines : list[str]
        Lines to write to the file.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


@pytest.mark.parametrize(
    (
        "data_directory",
        "batch_size",
        "process_authors",
        "process_works",
        "process_editions",
    ),
    [
        ("/test/data", 10000, True, True, True),
        ("/custom/path", 5000, False, True, False),
        ("/data", 20000, True, False, True),
    ],
)
class TestOpenLibraryDumpIngestTaskInit:
    """Test OpenLibraryDumpIngestTask initialization."""

    def test_init_with_metadata(
        self,
        data_directory: str,
        batch_size: int,
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
    ) -> None:
        """Test __init__ with various metadata configurations.

        Parameters
        ----------
        data_directory : str
            Data directory path.
        batch_size : int
            Batch size for processing.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        """
        metadata: dict[str, Any] = {
            "data_directory": data_directory,
            "process_authors": process_authors,
            "process_works": process_works,
            "process_editions": process_editions,
        }
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.base_dir == Path(data_directory) / "openlibrary"
        assert task.dump_dir == Path(data_directory) / "openlibrary" / "dump"
        assert task.batch_size == 10000  # default
        assert task.process_authors == process_authors
        assert task.process_works == process_works
        assert task.process_editions == process_editions

    def test_init_with_defaults(
        self,
        data_directory: str,
        batch_size: int,
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
    ) -> None:
        """Test __init__ with default values.

        Parameters
        ----------
        data_directory : str
            Data directory path.
        batch_size : int
            Batch size for processing.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        """
        metadata: dict[str, Any] = {}
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        assert task.base_dir == Path("/data") / "openlibrary"
        assert task.process_authors is True  # default
        assert task.process_works is True  # default
        assert task.process_editions is True  # default


class TestOpenLibraryDumpIngestTaskParseLine:
    """Test OpenLibraryDumpIngestTask._parse_line method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    @pytest.mark.parametrize(
        ("line", "expected_type", "expected_key", "has_revision", "has_date"),
        [
            (
                'author\t/authors/OL123A\t1\t2008-04-01T00:00:00\t{"name": "Test"}',
                "author",
                "/authors/OL123A",
                True,
                True,
            ),
            (
                'work\t/works/OL456W\t2\t2009-05-15T12:30:00Z\t{"title": "Book"}',
                "work",
                "/works/OL456W",
                True,
                True,
            ),
            (
                'edition\t/editions/OL789E\t3\t2010-06-20\t{"isbn": "123"}',
                "edition",
                "/editions/OL789E",
                True,
                True,
            ),
            (
                'author\t/authors/OL999A\t\t\t{"name": "No date"}',
                "author",
                "/authors/OL999A",
                False,
                False,
            ),
        ],
    )
    def test_parse_line_valid(
        self,
        task: OpenLibraryDumpIngestTask,
        line: str,
        expected_type: str,
        expected_key: str,
        has_revision: bool,
        has_date: bool,
    ) -> None:
        """Test parsing valid lines.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        line : str
            Line to parse.
        expected_type : str
            Expected record type.
        expected_key : str
            Expected key.
        has_revision : bool
            Whether revision should be present.
        has_date : bool
            Whether date should be present.
        """
        result = task._parse_line(line)
        assert result is not None
        record_type, key, revision, last_modified, data = result
        assert record_type == expected_type
        assert key == expected_key
        if has_revision:
            assert revision is not None
        else:
            assert revision is None
        if has_date:
            assert last_modified is not None
        else:
            assert last_modified is None
        assert isinstance(data, dict)

    @pytest.mark.parametrize(
        "line",
        [
            "invalid",
            "too\tfew\tparts",
            "author\tkey\trev\tdate",
            "author\tkey\trev\tdate\tinvalid_json{",
        ],
    )
    def test_parse_line_invalid(
        self, task: OpenLibraryDumpIngestTask, line: str
    ) -> None:
        """Test parsing invalid lines.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        line : str
            Invalid line to parse.
        """
        result = task._parse_line(line)
        assert result is None


class TestOpenLibraryDumpIngestTaskProcessAuthorsFile:
    """Test OpenLibraryDumpIngestTask._process_authors_file method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )
        task.batch_size = 2  # Small batch for testing
        return task

    def test_process_authors_file_success(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test successful processing of authors file.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        authors_file = temp_dir / "ol_dump_authors_latest.txt.gz"
        lines = [
            'author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{"name": "Author 1"}',
            'author\t/authors/OL2A\t2\t2009-05-01T00:00:00\t{"name": "Author 2"}',
            'author\t/authors/OL3A\t3\t2010-06-01T00:00:00\t{"name": "Author 3"}',
        ]
        create_gzip_dump_file(authors_file, lines)

        count = task._process_authors_file(
            authors_file,
            mock_session,
            mock_update_progress,
            0.0,
            1.0,
        )

        assert count == 3
        assert mock_session.bulk_save_objects.call_count >= 1
        assert mock_session.commit.call_count >= 1

    def test_process_authors_file_not_found(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing non-existent authors file.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        authors_file = temp_dir / "nonexistent.txt.gz"

        count = task._process_authors_file(
            authors_file,
            mock_session,
            mock_update_progress,
            0.0,
            1.0,
        )

        assert count == 0

    def test_process_authors_file_cancelled(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing authors file with cancellation.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        authors_file = temp_dir / "ol_dump_authors_latest.txt.gz"
        lines = [
            'author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{"name": "Author 1"}',
        ]
        create_gzip_dump_file(authors_file, lines)

        task.mark_cancelled()

        with pytest.raises(InterruptedError, match="Task cancelled"):
            task._process_authors_file(
                authors_file,
                mock_session,
                mock_update_progress,
                0.0,
                1.0,
            )

    def test_process_authors_file_skips_non_author_keys(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing authors file skips non-author keys.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        authors_file = temp_dir / "ol_dump_authors_latest.txt.gz"
        lines = [
            'author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{"name": "Author 1"}',
            'work\t/works/OL1W\t1\t2008-04-01T00:00:00\t{"title": "Work 1"}',
        ]
        create_gzip_dump_file(authors_file, lines)

        count = task._process_authors_file(
            authors_file,
            mock_session,
            mock_update_progress,
            0.0,
            1.0,
        )

        assert count == 1  # Only author record counted

    def test_process_authors_file_error_handling(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test error handling during authors file processing.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        authors_file = temp_dir / "ol_dump_authors_latest.txt.gz"
        lines = [
            'author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{"name": "Author 1"}',
        ]
        create_gzip_dump_file(authors_file, lines)

        mock_session.bulk_save_objects.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            task._process_authors_file(
                authors_file,
                mock_session,
                mock_update_progress,
                0.0,
                1.0,
            )

        mock_session.rollback.assert_called_once()


class TestOpenLibraryDumpIngestTaskExtractAuthorWorks:
    """Test OpenLibraryDumpIngestTask._extract_author_works method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    @pytest.mark.parametrize(
        ("data", "work_key", "expected_count"),
        [
            (
                {"authors": [{"author": {"key": "/authors/OL1A"}}]},
                "/works/OL1W",
                1,
            ),
            (
                {
                    "authors": [
                        {"author": {"key": "/authors/OL1A"}},
                        {"author": {"key": "/authors/OL2A"}},
                    ]
                },
                "/works/OL1W",
                2,
            ),
            (
                {
                    "authors": [
                        {"author": {"key": "/authors/OL1A"}},
                        {"author": {"key": "/authors/OL1A"}},  # duplicate
                    ]
                },
                "/works/OL1W",
                1,  # deduplicated
            ),
            ({"authors": []}, "/works/OL1W", 0),
            ({}, "/works/OL1W", 0),
            ({"authors": "not_a_list"}, "/works/OL1W", 0),
            ({"authors": [{"author": {}}]}, "/works/OL1W", 0),
            ({"authors": [{"not_author": "value"}]}, "/works/OL1W", 0),
        ],
    )
    def test_extract_author_works(
        self,
        task: OpenLibraryDumpIngestTask,
        data: dict[str, Any],
        work_key: str,
        expected_count: int,
    ) -> None:
        """Test extracting author-works relationships.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        data : dict[str, Any]
            Work data dictionary.
        work_key : str
            Work key identifier.
        expected_count : int
            Expected number of author-works.
        """
        result = task._extract_author_works(data, work_key)
        assert len(result) == expected_count
        for item in result:
            assert isinstance(item, OpenLibraryAuthorWork)
            assert item.work_key == work_key


class TestOpenLibraryDumpIngestTaskDeduplicateBatches:
    """Test deduplication methods."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    def test_deduplicate_author_works_batch(
        self, task: OpenLibraryDumpIngestTask
    ) -> None:
        """Test deduplicating author-works batch.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        """
        batch = [
            OpenLibraryAuthorWork(author_key="/authors/OL1A", work_key="/works/OL1W"),
            OpenLibraryAuthorWork(
                author_key="/authors/OL1A", work_key="/works/OL1W"
            ),  # duplicate
            OpenLibraryAuthorWork(author_key="/authors/OL2A", work_key="/works/OL1W"),
        ]

        result = task._deduplicate_author_works_batch(batch)

        assert len(result) == 2
        assert result[0].author_key == "/authors/OL1A"
        assert result[1].author_key == "/authors/OL2A"

    def test_deduplicate_isbns_batch(self, task: OpenLibraryDumpIngestTask) -> None:
        """Test deduplicating ISBNs batch.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        """
        batch = [
            OpenLibraryEditionIsbn(edition_key="/editions/OL1E", isbn="1234567890"),
            OpenLibraryEditionIsbn(
                edition_key="/editions/OL1E", isbn="1234567890"
            ),  # duplicate
            OpenLibraryEditionIsbn(edition_key="/editions/OL1E", isbn="0987654321"),
        ]

        result = task._deduplicate_isbns_batch(batch)

        assert len(result) == 2
        assert result[0].isbn == "1234567890"
        assert result[1].isbn == "0987654321"


class TestOpenLibraryDumpIngestTaskCommitBatches:
    """Test OpenLibraryDumpIngestTask._commit_batches method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    def test_commit_batches_with_author_works(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
    ) -> None:
        """Test committing batches with author-works.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        """
        author_works = [
            OpenLibraryAuthorWork(author_key="/authors/OL1A", work_key="/works/OL1W"),
            OpenLibraryAuthorWork(
                author_key="/authors/OL1A", work_key="/works/OL1W"
            ),  # duplicate
        ]

        task._commit_batches(mock_session, author_works)

        mock_session.bulk_save_objects.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_commit_batches_with_isbns(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
    ) -> None:
        """Test committing batches with ISBNs.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        """
        isbns = [
            OpenLibraryEditionIsbn(edition_key="/editions/OL1E", isbn="1234567890"),
            OpenLibraryEditionIsbn(
                edition_key="/editions/OL1E", isbn="1234567890"
            ),  # duplicate
        ]

        task._commit_batches(mock_session, isbns)

        mock_session.bulk_save_objects.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_commit_batches_empty(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
    ) -> None:
        """Test committing empty batches.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        """
        task._commit_batches(mock_session, [])

        mock_session.bulk_save_objects.assert_not_called()
        mock_session.commit.assert_not_called()


class TestOpenLibraryDumpIngestTaskProcessWorksFile:
    """Test OpenLibraryDumpIngestTask._process_works_file method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )
        task.batch_size = 2  # Small batch for testing
        return task

    def test_process_works_file_success(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test successful processing of works file.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        works_file = temp_dir / "ol_dump_works_latest.txt.gz"
        lines = [
            'work\t/works/OL1W\t1\t2008-04-01T00:00:00\t{"title": "Work 1", "authors": [{"author": {"key": "/authors/OL1A"}}]}',
            'work\t/works/OL2W\t2\t2009-05-01T00:00:00\t{"title": "Work 2"}',
        ]
        create_gzip_dump_file(works_file, lines)

        works_count, author_works_count = task._process_works_file(
            works_file,
            mock_session,
            mock_update_progress,
            0.0,
            1.0,
        )

        assert works_count == 2
        assert author_works_count == 1  # One work has authors
        assert mock_session.bulk_save_objects.call_count >= 1
        assert mock_session.commit.call_count >= 1

    def test_process_works_file_not_found(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing non-existent works file.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        works_file = temp_dir / "nonexistent.txt.gz"

        works_count, author_works_count = task._process_works_file(
            works_file,
            mock_session,
            mock_update_progress,
            0.0,
            1.0,
        )

        assert works_count == 0
        assert author_works_count == 0

    def test_process_works_file_cancelled(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing works file with cancellation.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        works_file = temp_dir / "ol_dump_works_latest.txt.gz"
        lines = [
            'work\t/works/OL1W\t1\t2008-04-01T00:00:00\t{"title": "Work 1"}',
        ]
        create_gzip_dump_file(works_file, lines)

        task.mark_cancelled()

        with pytest.raises(InterruptedError, match="Task cancelled"):
            task._process_works_file(
                works_file,
                mock_session,
                mock_update_progress,
                0.0,
                1.0,
            )


class TestOpenLibraryDumpIngestTaskExtractWorkKey:
    """Test OpenLibraryDumpIngestTask._extract_work_key method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            ({"works": [{"key": "/works/OL1W"}]}, "/works/OL1W"),
            ({"works": []}, None),
            ({}, None),
            ({"works": "not_a_list"}, None),
            ({"works": [{"not_key": "value"}]}, None),
            ({"works": [None]}, None),
        ],
    )
    def test_extract_work_key(
        self,
        task: OpenLibraryDumpIngestTask,
        data: dict[str, Any],
        expected: str | None,
    ) -> None:
        """Test extracting work key from edition data.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        data : dict[str, Any]
            Edition data dictionary.
        expected : str | None
            Expected work key or None.
        """
        result = task._extract_work_key(data)
        assert result == expected


class TestOpenLibraryDumpIngestTaskExtractIsbns:
    """Test OpenLibraryDumpIngestTask._extract_isbns method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    @pytest.mark.parametrize(
        ("data", "edition_key", "expected_count"),
        [
            ({"isbn_13": ["1234567890123"]}, "/editions/OL1E", 1),
            ({"isbn_10": ["1234567890"]}, "/editions/OL1E", 1),
            ({"isbn": ["1234567890"]}, "/editions/OL1E", 1),
            (
                {
                    "isbn_13": ["1234567890123"],
                    "isbn_10": ["1234567890"],
                },
                "/editions/OL1E",
                2,
            ),
            (
                {
                    "isbn_13": ["1234567890123", "1234567890123"],  # duplicate
                },
                "/editions/OL1E",
                1,
            ),
            ({"isbn_13": []}, "/editions/OL1E", 0),
            ({}, "/editions/OL1E", 0),
            ({"isbn_13": "not_a_list"}, "/editions/OL1E", 0),
            ({"isbn_13": [123]}, "/editions/OL1E", 0),  # not a string
            ({"isbn_13": ["  ", ""]}, "/editions/OL1E", 0),  # empty strings
        ],
    )
    def test_extract_isbns(
        self,
        task: OpenLibraryDumpIngestTask,
        data: dict[str, Any],
        edition_key: str,
        expected_count: int,
    ) -> None:
        """Test extracting ISBNs from edition data.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        data : dict[str, Any]
            Edition data dictionary.
        edition_key : str
            Edition key identifier.
        expected_count : int
            Expected number of ISBNs.
        """
        result = task._extract_isbns(data, edition_key)
        assert len(result) == expected_count
        for item in result:
            assert isinstance(item, OpenLibraryEditionIsbn)
            assert item.edition_key == edition_key
            assert item.isbn.strip() == item.isbn  # should be cleaned


class TestOpenLibraryDumpIngestTaskProcessEditionsFile:
    """Test OpenLibraryDumpIngestTask._process_editions_file method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )
        task.batch_size = 2  # Small batch for testing
        return task

    def test_process_editions_file_success(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test successful processing of editions file.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        editions_file = temp_dir / "ol_dump_editions_latest.txt.gz"
        lines = [
            'edition\t/editions/OL1E\t1\t2008-04-01T00:00:00\t{"isbn_13": ["1234567890123"], "works": [{"key": "/works/OL1W"}]}',
            'edition\t/editions/OL2E\t2\t2009-05-01T00:00:00\t{"isbn_10": ["1234567890"]}',
        ]
        create_gzip_dump_file(editions_file, lines)

        editions_count, isbns_count = task._process_editions_file(
            editions_file,
            mock_session,
            mock_update_progress,
            0.0,
            1.0,
        )

        assert editions_count == 2
        assert isbns_count == 2  # One ISBN per edition
        assert mock_session.bulk_save_objects.call_count >= 1
        assert mock_session.commit.call_count >= 1

    def test_process_editions_file_not_found(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing non-existent editions file.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        editions_file = temp_dir / "nonexistent.txt.gz"

        editions_count, isbns_count = task._process_editions_file(
            editions_file,
            mock_session,
            mock_update_progress,
            0.0,
            1.0,
        )

        assert editions_count == 0
        assert isbns_count == 0

    def test_process_editions_file_cancelled(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing editions file with cancellation.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        editions_file = temp_dir / "ol_dump_editions_latest.txt.gz"
        lines = [
            'edition\t/editions/OL1E\t1\t2008-04-01T00:00:00\t{"isbn_13": ["1234567890123"]}',
        ]
        create_gzip_dump_file(editions_file, lines)

        task.mark_cancelled()

        with pytest.raises(InterruptedError, match="Task cancelled"):
            task._process_editions_file(
                editions_file,
                mock_session,
                mock_update_progress,
                0.0,
                1.0,
            )


class TestOpenLibraryDumpIngestTaskUpdateProgress:
    """Test OpenLibraryDumpIngestTask._update_progress_if_needed method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    @pytest.mark.parametrize(
        ("processed_count", "should_update"),
        [
            (100000, True),
            (200000, True),
            (50000, False),
            (99999, False),
        ],
    )
    def test_update_progress_if_needed(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_update_progress: MagicMock,
        processed_count: int,
        should_update: bool,
    ) -> None:
        """Test progress update threshold.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        processed_count : int
            Number of records processed.
        should_update : bool
            Whether progress should be updated.
        """
        task._update_progress_if_needed(
            processed_count,
            0.0,
            1.0,
            "test_file.txt",
            "authors",
            mock_update_progress,
        )

        if should_update:
            mock_update_progress.assert_called()
        else:
            mock_update_progress.assert_not_called()


class TestOpenLibraryDumpIngestTaskGetTablesToTruncate:
    """Test OpenLibraryDumpIngestTask._get_tables_to_truncate method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    @pytest.mark.parametrize(
        ("process_authors", "process_works", "process_editions", "expected_tables"),
        [
            (
                True,
                True,
                True,
                [
                    "openlibrary_authors",
                    "openlibrary_works",
                    "openlibrary_author_works",
                    "openlibrary_editions",
                    "openlibrary_edition_isbns",
                ],
            ),
            (True, False, False, ["openlibrary_authors"]),
            (False, True, False, ["openlibrary_works", "openlibrary_author_works"]),
            (False, False, True, ["openlibrary_editions", "openlibrary_edition_isbns"]),
        ],
    )
    def test_get_tables_to_truncate(
        self,
        task: OpenLibraryDumpIngestTask,
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
        expected_tables: list[str],
    ) -> None:
        """Test getting tables to truncate.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        expected_tables : list[str]
            Expected table names.
        """
        task.process_authors = process_authors
        task.process_works = process_works
        task.process_editions = process_editions

        result = task._get_tables_to_truncate()

        assert set(result) == set(expected_tables)


class TestOpenLibraryDumpIngestTaskTruncateTables:
    """Test OpenLibraryDumpIngestTask._truncate_tables method."""

    @pytest.fixture
    def task(self, base_metadata: dict[str, Any]) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        return OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=base_metadata,
        )

    def test_truncate_tables(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
    ) -> None:
        """Test truncating tables.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        """
        task._truncate_tables(mock_session, mock_update_progress)

        mock_session.connection.return_value.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_update_progress.assert_called()


class TestOpenLibraryDumpIngestTaskValidateEnabledFileTypes:
    """Test OpenLibraryDumpIngestTask._validate_enabled_file_types method."""

    @pytest.mark.parametrize(
        ("process_authors", "process_works", "process_editions", "should_raise"),
        [
            (True, True, True, False),
            (True, False, False, False),
            (False, True, False, False),
            (False, False, True, False),
            (False, False, False, True),
        ],
    )
    def test_validate_enabled_file_types(
        self,
        base_metadata: dict[str, Any],
        process_authors: bool,
        process_works: bool,
        process_editions: bool,
        should_raise: bool,
    ) -> None:
        """Test validation of enabled file types.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.
        process_authors : bool
            Whether to process authors.
        process_works : bool
            Whether to process works.
        process_editions : bool
            Whether to process editions.
        should_raise : bool
            Whether ValueError should be raised.
        """
        metadata = base_metadata.copy()
        metadata.update({
            "process_authors": process_authors,
            "process_works": process_works,
            "process_editions": process_editions,
        })
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )

        if should_raise:
            with pytest.raises(
                ValueError, match="At least one file type must be enabled"
            ):
                task._validate_enabled_file_types()
        else:
            task._validate_enabled_file_types()  # Should not raise


class TestOpenLibraryDumpIngestTaskProcessAllFiles:
    """Test OpenLibraryDumpIngestTask._process_all_files method."""

    @pytest.fixture
    def task(
        self, base_metadata: dict[str, Any], temp_dir: Path
    ) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.
        temp_dir : Path
            Temporary directory path.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        metadata = base_metadata.copy()
        metadata["data_directory"] = str(temp_dir)
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        task.batch_size = 2  # Small batch for testing
        return task

    def test_process_all_files_authors_only(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing with authors only.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        task.process_authors = True
        task.process_works = False
        task.process_editions = False

        authors_file = task.dump_dir / "ol_dump_authors_latest.txt.gz"
        create_gzip_dump_file(
            authors_file,
            [
                'author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{"name": "Author 1"}',
            ],
        )

        result = task._process_all_files(mock_session, mock_update_progress, 0.33)

        assert result[0] == 1  # authors_count
        assert result[1] == 0  # works_count
        assert result[2] == 0  # author_works_count
        assert result[3] == 0  # editions_count
        assert result[4] == 0  # isbns_count

    def test_process_all_files_editions_missing(
        self,
        task: OpenLibraryDumpIngestTask,
        mock_session: MagicMock,
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test processing when editions file is missing.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        mock_session : MagicMock
            Mock session object.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        task.process_authors = False
        task.process_works = False
        task.process_editions = True

        # Don't create editions file

        result = task._process_all_files(mock_session, mock_update_progress, 0.33)

        assert result[3] == 0  # editions_count
        assert result[4] == 0  # isbns_count


class TestOpenLibraryDumpIngestTaskRun:
    """Test OpenLibraryDumpIngestTask run method."""

    @pytest.fixture
    def task(
        self, base_metadata: dict[str, Any], temp_dir: Path
    ) -> OpenLibraryDumpIngestTask:
        """Create task instance.

        Parameters
        ----------
        base_metadata : dict[str, Any]
            Base metadata dictionary.
        temp_dir : Path
            Temporary directory path.

        Returns
        -------
        OpenLibraryDumpIngestTask
            Task instance.
        """
        metadata = base_metadata.copy()
        metadata["data_directory"] = str(temp_dir)
        task = OpenLibraryDumpIngestTask(
            task_id=1,
            user_id=1,
            metadata=metadata,
        )
        task.batch_size = 2  # Small batch for testing
        return task

    def test_run_success(
        self,
        task: OpenLibraryDumpIngestTask,
        worker_context: dict[str, Any],
        mock_update_progress: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test successful run execution.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        mock_update_progress : MagicMock
            Mock update_progress callback.
        temp_dir : Path
            Temporary directory path.
        """
        # Create dump files
        authors_file = task.dump_dir / "ol_dump_authors_latest.txt.gz"
        create_gzip_dump_file(
            authors_file,
            [
                'author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{"name": "Author 1"}',
            ],
        )

        works_file = task.dump_dir / "ol_dump_works_latest.txt.gz"
        create_gzip_dump_file(
            works_file,
            [
                'work\t/works/OL1W\t1\t2008-04-01T00:00:00\t{"title": "Work 1"}',
            ],
        )

        task.run(worker_context)

        # Check final progress update
        final_call = mock_update_progress.call_args_list[-1]
        assert final_call[0][0] == 1.0

    def test_run_cancelled(
        self,
        task: OpenLibraryDumpIngestTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Test run when cancelled.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        """
        task.mark_cancelled()

        task.run(worker_context)

        # Should return early without processing

    def test_run_no_file_types_enabled(
        self,
        task: OpenLibraryDumpIngestTask,
        worker_context: dict[str, Any],
    ) -> None:
        """Test run when no file types are enabled.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        """
        task.process_authors = False
        task.process_works = False
        task.process_editions = False

        with pytest.raises(ValueError, match="At least one file type must be enabled"):
            task.run(worker_context)

    def test_run_exception(
        self,
        task: OpenLibraryDumpIngestTask,
        worker_context: dict[str, Any],
        mock_session: MagicMock,
    ) -> None:
        """Test run with exception triggers rollback.

        Parameters
        ----------
        task : OpenLibraryDumpIngestTask
            Task instance.
        worker_context : dict[str, Any]
            Worker context dictionary.
        mock_session : MagicMock
            Mock session object.
        """
        mock_session.connection.return_value.execute.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            task.run(worker_context)

        mock_session.rollback.assert_called()
