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

"""Tests for OpenLibrary batch processors to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.models.openlibrary import (
    OpenLibraryAuthorWork,
    OpenLibraryEditionIsbn,
)
from bookcard.services.tasks.openlibrary.batch import (
    AuthorWorkBatchProcessor,
    BatchProcessor,
    IsbnBatchProcessor,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock database repository.

    Returns
    -------
    MagicMock
        Mock repository object.
    """
    return MagicMock()


class TestBatchProcessor:
    """Test BatchProcessor base class."""

    @pytest.fixture
    def processor(self, mock_repository: MagicMock) -> BatchProcessor[str]:
        """Create processor instance.

        Parameters
        ----------
        mock_repository : MagicMock
            Mock repository.

        Returns
        -------
        BatchProcessor[str]
            Processor instance.
        """
        return BatchProcessor(mock_repository, batch_size=3)

    def test_init(
        self, processor: BatchProcessor[str], mock_repository: MagicMock
    ) -> None:
        """Test processor initialization.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        mock_repository : MagicMock
            Mock repository.
        """
        assert processor.repository == mock_repository
        assert processor.batch_size == 3
        assert processor._current_batch == []

    def test_add_below_batch_size(
        self, processor: BatchProcessor[str], mock_repository: MagicMock
    ) -> None:
        """Test add items below batch size.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        mock_repository : MagicMock
            Mock repository.
        """
        processor.add(["item1", "item2"])

        assert len(processor._current_batch) == 2
        mock_repository.bulk_save.assert_not_called()

    def test_add_reaches_batch_size(
        self, processor: BatchProcessor[str], mock_repository: MagicMock
    ) -> None:
        """Test add items that reach batch size triggers flush.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        mock_repository : MagicMock
            Mock repository.
        """
        processor.add(["item1", "item2", "item3"])

        assert len(processor._current_batch) == 0  # Flushed
        mock_repository.bulk_save.assert_called_once()
        mock_repository.commit.assert_called_once()

    def test_add_exceeds_batch_size(
        self, processor: BatchProcessor[str], mock_repository: MagicMock
    ) -> None:
        """Test add items that exceed batch size.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        mock_repository : MagicMock
            Mock repository.
        """
        processor.add(["item1", "item2", "item3", "item4"])

        assert len(processor._current_batch) == 0  # Flushed
        mock_repository.bulk_save.assert_called_once()
        mock_repository.commit.assert_called_once()

    def test_flush_with_items(
        self, processor: BatchProcessor[str], mock_repository: MagicMock
    ) -> None:
        """Test flush with items in batch.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        mock_repository : MagicMock
            Mock repository.
        """
        items = ["item1", "item2"]
        processor._current_batch = items.copy()

        processor.flush()

        assert len(processor._current_batch) == 0
        # Verify bulk_save was called (the exact items are tested via _deduplicate test)
        mock_repository.bulk_save.assert_called_once()
        mock_repository.commit.assert_called_once()

    def test_flush_empty(
        self, processor: BatchProcessor[str], mock_repository: MagicMock
    ) -> None:
        """Test flush with empty batch.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        mock_repository : MagicMock
            Mock repository.
        """
        processor._current_batch = []

        processor.flush()

        mock_repository.bulk_save.assert_not_called()
        mock_repository.commit.assert_not_called()

    def test_flush_with_empty_deduplication(
        self, processor: BatchProcessor[str], mock_repository: MagicMock
    ) -> None:
        """Test flush when deduplication returns empty list.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        mock_repository : MagicMock
            Mock repository.
        """
        # Override _deduplicate to return empty list
        processor._deduplicate = lambda items: []  # type: ignore[method-assign]
        processor._current_batch = ["item1", "item2"]

        processor.flush()

        assert len(processor._current_batch) == 0
        mock_repository.bulk_save.assert_not_called()
        mock_repository.commit.assert_not_called()

    def test_deduplicate(self, processor: BatchProcessor[str]) -> None:
        """Test _deduplicate returns items as-is.

        Parameters
        ----------
        processor : BatchProcessor[str]
            Processor instance.
        """
        items = ["item1", "item2", "item1"]

        result = processor._deduplicate(items)

        assert result == items  # Base class doesn't deduplicate


class TestAuthorWorkBatchProcessor:
    """Test AuthorWorkBatchProcessor."""

    @pytest.fixture
    def processor(self, mock_repository: MagicMock) -> AuthorWorkBatchProcessor:
        """Create processor instance.

        Parameters
        ----------
        mock_repository : MagicMock
            Mock repository.

        Returns
        -------
        AuthorWorkBatchProcessor
            Processor instance.
        """
        return AuthorWorkBatchProcessor(mock_repository, batch_size=3)

    def test_deduplicate_removes_duplicates(
        self, processor: AuthorWorkBatchProcessor
    ) -> None:
        """Test deduplication removes duplicate author-work pairs.

        Parameters
        ----------
        processor : AuthorWorkBatchProcessor
            Processor instance.
        """
        items = [
            OpenLibraryAuthorWork(author_key="/authors/OL1A", work_key="/works/OL1W"),
            OpenLibraryAuthorWork(
                author_key="/authors/OL1A", work_key="/works/OL1W"
            ),  # duplicate
            OpenLibraryAuthorWork(author_key="/authors/OL2A", work_key="/works/OL1W"),
        ]

        result = processor._deduplicate(items)

        assert len(result) == 2
        assert result[0].author_key == "/authors/OL1A"
        assert result[1].author_key == "/authors/OL2A"

    def test_deduplicate_all_unique(self, processor: AuthorWorkBatchProcessor) -> None:
        """Test deduplication with all unique pairs.

        Parameters
        ----------
        processor : AuthorWorkBatchProcessor
            Processor instance.
        """
        items = [
            OpenLibraryAuthorWork(author_key="/authors/OL1A", work_key="/works/OL1W"),
            OpenLibraryAuthorWork(author_key="/authors/OL2A", work_key="/works/OL1W"),
            OpenLibraryAuthorWork(author_key="/authors/OL1A", work_key="/works/OL2W"),
        ]

        result = processor._deduplicate(items)

        assert len(result) == 3

    def test_deduplicate_empty(self, processor: AuthorWorkBatchProcessor) -> None:
        """Test deduplication with empty list.

        Parameters
        ----------
        processor : AuthorWorkBatchProcessor
            Processor instance.
        """
        result = processor._deduplicate([])

        assert result == []


class TestIsbnBatchProcessor:
    """Test IsbnBatchProcessor."""

    @pytest.fixture
    def processor(self, mock_repository: MagicMock) -> IsbnBatchProcessor:
        """Create processor instance.

        Parameters
        ----------
        mock_repository : MagicMock
            Mock repository.

        Returns
        -------
        IsbnBatchProcessor
            Processor instance.
        """
        return IsbnBatchProcessor(mock_repository, batch_size=3)

    def test_deduplicate_removes_duplicates(
        self, processor: IsbnBatchProcessor
    ) -> None:
        """Test deduplication removes duplicate edition-ISBN pairs.

        Parameters
        ----------
        processor : IsbnBatchProcessor
            Processor instance.
        """
        items = [
            OpenLibraryEditionIsbn(edition_key="/editions/OL1E", isbn="1234567890"),
            OpenLibraryEditionIsbn(
                edition_key="/editions/OL1E", isbn="1234567890"
            ),  # duplicate
            OpenLibraryEditionIsbn(edition_key="/editions/OL1E", isbn="0987654321"),
        ]

        result = processor._deduplicate(items)

        assert len(result) == 2
        assert result[0].isbn == "1234567890"
        assert result[1].isbn == "0987654321"

    def test_deduplicate_all_unique(self, processor: IsbnBatchProcessor) -> None:
        """Test deduplication with all unique pairs.

        Parameters
        ----------
        processor : IsbnBatchProcessor
            Processor instance.
        """
        items = [
            OpenLibraryEditionIsbn(edition_key="/editions/OL1E", isbn="1234567890"),
            OpenLibraryEditionIsbn(edition_key="/editions/OL2E", isbn="1234567890"),
            OpenLibraryEditionIsbn(edition_key="/editions/OL1E", isbn="0987654321"),
        ]

        result = processor._deduplicate(items)

        assert len(result) == 3

    def test_deduplicate_empty(self, processor: IsbnBatchProcessor) -> None:
        """Test deduplication with empty list.

        Parameters
        ----------
        processor : IsbnBatchProcessor
            Processor instance.
        """
        result = processor._deduplicate([])

        assert result == []
