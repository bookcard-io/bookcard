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

"""Tests for OpenLibrary record processors to achieve 100% coverage."""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock

import pytest

from fundamental.models.openlibrary import (
    OpenLibraryAuthor,
    OpenLibraryAuthorWork,
    OpenLibraryEdition,
    OpenLibraryEditionIsbn,
    OpenLibraryWork,
)
from fundamental.services.tasks.openlibrary.batch import BatchProcessor
from fundamental.services.tasks.openlibrary.models import DumpRecord
from fundamental.services.tasks.openlibrary.processors import (
    AuthorRecordProcessor,
    EditionRecordProcessor,
    WorkRecordProcessor,
)


@pytest.fixture
def mock_author_work_batch() -> MagicMock:
    """Create a mock author-work batch processor.

    Returns
    -------
    MagicMock
        Mock batch processor.
    """
    return MagicMock(spec=BatchProcessor)


@pytest.fixture
def mock_isbn_batch() -> MagicMock:
    """Create a mock ISBN batch processor.

    Returns
    -------
    MagicMock
        Mock batch processor.
    """
    return MagicMock(spec=BatchProcessor)


@pytest.fixture
def author_record() -> DumpRecord:
    """Create an author dump record.

    Returns
    -------
    DumpRecord
        Author record.
    """
    return DumpRecord(
        record_type="author",
        key="/authors/OL123A",
        revision=1,
        last_modified=date(2008, 4, 1),
        data={"name": "Test Author"},
    )


@pytest.fixture
def work_record() -> DumpRecord:
    """Create a work dump record.

    Returns
    -------
    DumpRecord
        Work record.
    """
    return DumpRecord(
        record_type="work",
        key="/works/OL456W",
        revision=2,
        last_modified=date(2009, 5, 15),
        data={
            "title": "Test Work",
            "authors": [{"author": {"key": "/authors/OL123A"}}],
        },
    )


@pytest.fixture
def edition_record() -> DumpRecord:
    """Create an edition dump record.

    Returns
    -------
    DumpRecord
        Edition record.
    """
    return DumpRecord(
        record_type="edition",
        key="/editions/OL789E",
        revision=3,
        last_modified=date(2010, 6, 20),
        data={
            "isbn_13": ["1234567890123"],
            "works": [{"key": "/works/OL456W"}],
        },
    )


class TestAuthorRecordProcessor:
    """Test AuthorRecordProcessor."""

    @pytest.fixture
    def processor(self) -> AuthorRecordProcessor:
        """Create processor instance.

        Returns
        -------
        AuthorRecordProcessor
            Processor instance.
        """
        return AuthorRecordProcessor()

    def test_can_process_author(
        self, processor: AuthorRecordProcessor, author_record: DumpRecord
    ) -> None:
        """Test can_process returns True for author records.

        Parameters
        ----------
        processor : AuthorRecordProcessor
            Processor instance.
        author_record : DumpRecord
            Author record.
        """
        assert processor.can_process(author_record) is True

    def test_can_process_non_author(
        self, processor: AuthorRecordProcessor, work_record: DumpRecord
    ) -> None:
        """Test can_process returns False for non-author records.

        Parameters
        ----------
        processor : AuthorRecordProcessor
            Processor instance.
        work_record : DumpRecord
            Work record.
        """
        assert processor.can_process(work_record) is False

    def test_process_record(
        self, processor: AuthorRecordProcessor, author_record: DumpRecord
    ) -> None:
        """Test processing author record.

        Parameters
        ----------
        processor : AuthorRecordProcessor
            Processor instance.
        author_record : DumpRecord
            Author record.
        """
        result = processor.process_record(author_record)

        assert len(result) == 1
        assert isinstance(result[0], OpenLibraryAuthor)
        assert result[0].key == author_record.key
        assert result[0].type == author_record.record_type
        assert result[0].revision == author_record.revision
        assert result[0].last_modified == author_record.last_modified
        assert result[0].data == author_record.data


class TestWorkRecordProcessor:
    """Test WorkRecordProcessor."""

    @pytest.fixture
    def processor(self, mock_author_work_batch: MagicMock) -> WorkRecordProcessor:
        """Create processor instance.

        Parameters
        ----------
        mock_author_work_batch : MagicMock
            Mock batch processor.

        Returns
        -------
        WorkRecordProcessor
            Processor instance.
        """
        return WorkRecordProcessor(mock_author_work_batch)

    def test_can_process_work(
        self, processor: WorkRecordProcessor, work_record: DumpRecord
    ) -> None:
        """Test can_process returns True for work records.

        Parameters
        ----------
        processor : WorkRecordProcessor
            Processor instance.
        work_record : DumpRecord
            Work record.
        """
        assert processor.can_process(work_record) is True

    def test_can_process_non_work(
        self, processor: WorkRecordProcessor, author_record: DumpRecord
    ) -> None:
        """Test can_process returns False for non-work records.

        Parameters
        ----------
        processor : WorkRecordProcessor
            Processor instance.
        author_record : DumpRecord
            Author record.
        """
        assert processor.can_process(author_record) is False

    def test_process_record_with_authors(
        self,
        processor: WorkRecordProcessor,
        work_record: DumpRecord,
        mock_author_work_batch: MagicMock,
    ) -> None:
        """Test processing work record with authors.

        Parameters
        ----------
        processor : WorkRecordProcessor
            Processor instance.
        work_record : DumpRecord
            Work record.
        mock_author_work_batch : MagicMock
            Mock batch processor.
        """
        result = processor.process_record(work_record)

        assert len(result) == 1
        assert isinstance(result[0], OpenLibraryWork)
        assert result[0].key == work_record.key
        mock_author_work_batch.add.assert_called_once()
        added_items = mock_author_work_batch.add.call_args[0][0]
        assert len(added_items) == 1
        assert isinstance(added_items[0], OpenLibraryAuthorWork)

    def test_process_record_no_authors(
        self,
        processor: WorkRecordProcessor,
        mock_author_work_batch: MagicMock,
    ) -> None:
        """Test processing work record without authors.

        Parameters
        ----------
        processor : WorkRecordProcessor
            Processor instance.
        mock_author_work_batch : MagicMock
            Mock batch processor.
        """
        work_record = DumpRecord(
            record_type="work",
            key="/works/OL456W",
            revision=2,
            last_modified=date(2009, 5, 15),
            data={"title": "Test Work"},
        )

        result = processor.process_record(work_record)

        assert len(result) == 1
        mock_author_work_batch.add.assert_not_called()

    @pytest.mark.parametrize(
        ("data", "expected_count"),
        [
            ({"authors": [{"author": {"key": "/authors/OL1A"}}]}, 1),
            (
                {
                    "authors": [
                        {"author": {"key": "/authors/OL1A"}},
                        {"author": {"key": "/authors/OL2A"}},
                    ]
                },
                2,
            ),
            (
                {
                    "authors": [
                        {"author": {"key": "/authors/OL1A"}},
                        {"author": {"key": "/authors/OL1A"}},  # duplicate
                    ]
                },
                1,  # deduplicated
            ),
            ({"authors": []}, 0),
            ({}, 0),
            ({"authors": "not_a_list"}, 0),
            ({"authors": [{"author": {}}]}, 0),
            ({"authors": [{"not_author": "value"}]}, 0),
            # Test case for string author format (fixes AttributeError)
            ({"authors": [{"author": "/authors/OL1A"}]}, 1),
            (
                {
                    "authors": [
                        {"author": "/authors/OL1A"},
                        {"author": {"key": "/authors/OL2A"}},
                    ]
                },
                2,  # Mixed formats
            ),
        ],
    )
    def test_extract_author_works(
        self,
        processor: WorkRecordProcessor,
        data: dict[str, Any],
        expected_count: int,
    ) -> None:
        """Test extracting author-works relationships.

        Parameters
        ----------
        processor : WorkRecordProcessor
            Processor instance.
        data : dict[str, Any]
            Work data dictionary.
        expected_count : int
            Expected number of author-works.
        """
        work_key = "/works/OL1W"
        result = processor._extract_author_works(data, work_key)

        assert len(result) == expected_count
        for item in result:
            assert isinstance(item, OpenLibraryAuthorWork)
            assert item.work_key == work_key


class TestEditionRecordProcessor:
    """Test EditionRecordProcessor."""

    @pytest.fixture
    def processor(self, mock_isbn_batch: MagicMock) -> EditionRecordProcessor:
        """Create processor instance.

        Parameters
        ----------
        mock_isbn_batch : MagicMock
            Mock batch processor.

        Returns
        -------
        EditionRecordProcessor
            Processor instance.
        """
        return EditionRecordProcessor(mock_isbn_batch)

    def test_can_process_edition(
        self, processor: EditionRecordProcessor, edition_record: DumpRecord
    ) -> None:
        """Test can_process returns True for edition records.

        Parameters
        ----------
        processor : EditionRecordProcessor
            Processor instance.
        edition_record : DumpRecord
            Edition record.
        """
        assert processor.can_process(edition_record) is True

    def test_can_process_non_edition(
        self, processor: EditionRecordProcessor, author_record: DumpRecord
    ) -> None:
        """Test can_process returns False for non-edition records.

        Parameters
        ----------
        processor : EditionRecordProcessor
            Processor instance.
        author_record : DumpRecord
            Author record.
        """
        assert processor.can_process(author_record) is False

    def test_process_record_with_isbns(
        self,
        processor: EditionRecordProcessor,
        edition_record: DumpRecord,
        mock_isbn_batch: MagicMock,
    ) -> None:
        """Test processing edition record with ISBNs.

        Parameters
        ----------
        processor : EditionRecordProcessor
            Processor instance.
        edition_record : DumpRecord
            Edition record.
        mock_isbn_batch : MagicMock
            Mock batch processor.
        """
        result = processor.process_record(edition_record)

        assert len(result) == 1
        assert isinstance(result[0], OpenLibraryEdition)
        assert result[0].key == edition_record.key
        assert result[0].work_key == "/works/OL456W"
        mock_isbn_batch.add.assert_called_once()
        added_items = mock_isbn_batch.add.call_args[0][0]
        assert len(added_items) == 1
        assert isinstance(added_items[0], OpenLibraryEditionIsbn)

    def test_process_record_no_isbns(
        self,
        processor: EditionRecordProcessor,
        mock_isbn_batch: MagicMock,
    ) -> None:
        """Test processing edition record without ISBNs.

        Parameters
        ----------
        processor : EditionRecordProcessor
            Processor instance.
        mock_isbn_batch : MagicMock
            Mock batch processor.
        """
        edition_record = DumpRecord(
            record_type="edition",
            key="/editions/OL789E",
            revision=3,
            last_modified=date(2010, 6, 20),
            data={},
        )

        result = processor.process_record(edition_record)

        assert len(result) == 1
        mock_isbn_batch.add.assert_not_called()

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
        processor: EditionRecordProcessor,
        data: dict[str, Any],
        expected: str | None,
    ) -> None:
        """Test extracting work key from edition data.

        Parameters
        ----------
        processor : EditionRecordProcessor
            Processor instance.
        data : dict[str, Any]
            Edition data dictionary.
        expected : str | None
            Expected work key or None.
        """
        result = processor._extract_work_key(data)
        assert result == expected

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
        processor: EditionRecordProcessor,
        data: dict[str, Any],
        edition_key: str,
        expected_count: int,
    ) -> None:
        """Test extracting ISBNs from edition data.

        Parameters
        ----------
        processor : EditionRecordProcessor
            Processor instance.
        data : dict[str, Any]
            Edition data dictionary.
        edition_key : str
            Edition key identifier.
        expected_count : int
            Expected number of ISBNs.
        """
        result = processor._extract_isbns(data, edition_key)

        assert len(result) == expected_count
        for item in result:
            assert isinstance(item, OpenLibraryEditionIsbn)
            assert item.edition_key == edition_key
            assert item.isbn.strip() == item.isbn  # should be cleaned
