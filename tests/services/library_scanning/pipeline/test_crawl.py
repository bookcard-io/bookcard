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

"""Tests for crawl stage to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.core import Author, Book, BookAuthorLink
from bookcard.repositories import CalibreBookRepository
from bookcard.services.library_scanning.pipeline.context import PipelineContext
from bookcard.services.library_scanning.pipeline.crawl import CrawlStage


@pytest.fixture
def mock_library() -> MagicMock:
    """Create a mock library."""
    library = MagicMock()
    library.calibre_db_path = "/test/path"
    library.calibre_db_file = "metadata.db"
    return library


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_data_source() -> MagicMock:
    """Create a mock data source."""
    return MagicMock()


@pytest.fixture
def mock_calibre_session() -> MagicMock:
    """Create a mock Calibre database session."""
    return MagicMock()


@pytest.fixture
def mock_calibre_repo(mock_calibre_session: MagicMock) -> MagicMock:
    """Create a mock Calibre repository."""
    repo = MagicMock(spec=CalibreBookRepository)
    repo.get_session.return_value.__enter__.return_value = mock_calibre_session
    repo.get_session.return_value.__exit__.return_value = None
    return repo


@pytest.fixture
def sample_authors() -> list[Author]:
    """Create sample authors."""
    return [
        Author(id=1, name="Author One"),
        Author(id=2, name="Author Two"),
    ]


@pytest.fixture
def sample_books() -> list[Book]:
    """Create sample books."""
    return [
        Book(id=1, title="Book One"),
        Book(id=2, title="Book Two"),
    ]


@pytest.fixture
def sample_links() -> list[BookAuthorLink]:
    """Create sample book-author links."""
    return [
        BookAuthorLink(book=1, author=1),
        BookAuthorLink(book=2, author=2),
    ]


@pytest.fixture
def pipeline_context(
    mock_library: MagicMock,
    mock_session: MagicMock,
    mock_data_source: MagicMock,
) -> PipelineContext:
    """Create a pipeline context."""
    return PipelineContext(
        library_id=1,
        library=mock_library,
        session=mock_session,
        data_source=mock_data_source,
    )


@pytest.fixture
def crawl_stage() -> CrawlStage:
    """Create a crawl stage instance."""
    return CrawlStage()


@pytest.fixture
def crawl_stage_with_limit() -> CrawlStage:
    """Create a crawl stage with author limit."""
    return CrawlStage(author_limit=1)


def test_crawl_stage_name(crawl_stage: CrawlStage) -> None:
    """Test crawl stage name property."""
    assert crawl_stage.name == "crawl"


def test_crawl_stage_get_progress_initial(crawl_stage: CrawlStage) -> None:
    """Test get_progress returns 0.0 initially."""
    assert crawl_stage.get_progress() == 0.0


@pytest.mark.parametrize(
    ("author_limit", "expected_count"),
    [
        (None, 2),
        (1, 1),
        # Note: limit=0 is treated as "no limit" in the implementation
        # (checks `if limit is not None and limit > 0`)
    ],
)
def test_crawl_stage_execute_with_author_limit(
    pipeline_context: PipelineContext,
    mock_calibre_repo: MagicMock,
    mock_calibre_session: MagicMock,
    sample_authors: list[Author],
    sample_books: list[Book],
    sample_links: list[BookAuthorLink],
    author_limit: int | None,
    expected_count: int,
) -> None:
    """Test crawl stage execute with author limit."""
    stage = CrawlStage(author_limit=author_limit)
    mock_calibre_session.exec.return_value.all.side_effect = [
        sample_authors,
        sample_books,
        sample_links,
    ]

    with patch(
        "bookcard.services.library_scanning.pipeline.crawl.CalibreBookRepository",
        return_value=mock_calibre_repo,
    ):
        result = stage.execute(pipeline_context)

    assert result.success is True
    assert len(pipeline_context.crawled_authors) == expected_count
    assert len(pipeline_context.crawled_books) == 2
    assert stage.get_progress() == 1.0


def test_crawl_stage_execute_success(
    pipeline_context: PipelineContext,
    mock_calibre_repo: MagicMock,
    mock_calibre_session: MagicMock,
    sample_authors: list[Author],
    sample_books: list[Book],
    sample_links: list[BookAuthorLink],
) -> None:
    """Test crawl stage execute successfully."""
    stage = CrawlStage()
    mock_calibre_session.exec.return_value.all.side_effect = [
        sample_authors,
        sample_books,
        sample_links,
    ]

    with patch(
        "bookcard.services.library_scanning.pipeline.crawl.CalibreBookRepository",
        return_value=mock_calibre_repo,
    ):
        result = stage.execute(pipeline_context)

    assert result.success is True
    assert len(pipeline_context.crawled_authors) == 2
    assert len(pipeline_context.crawled_books) == 2
    assert result.stats is not None
    assert result.stats["authors_crawled"] == 2
    assert result.stats["books_crawled"] == 2
    assert result.stats["book_author_links"] == 2
    assert stage.get_progress() == 1.0


def test_crawl_stage_execute_empty_results(
    pipeline_context: PipelineContext,
    mock_calibre_repo: MagicMock,
    mock_calibre_session: MagicMock,
) -> None:
    """Test crawl stage execute with empty results."""
    stage = CrawlStage()
    mock_calibre_session.exec.return_value.all.side_effect = [[], [], []]

    with patch(
        "bookcard.services.library_scanning.pipeline.crawl.CalibreBookRepository",
        return_value=mock_calibre_repo,
    ):
        result = stage.execute(pipeline_context)

    assert result.success is True
    assert len(pipeline_context.crawled_authors) == 0
    assert len(pipeline_context.crawled_books) == 0
    assert result.stats is not None
    assert result.stats["authors_crawled"] == 0
    assert result.stats["books_crawled"] == 0


def test_crawl_stage_execute_cancelled(
    pipeline_context: PipelineContext,
) -> None:
    """Test crawl stage execute when cancelled."""
    stage = CrawlStage()
    pipeline_context.cancelled = True

    result = stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "cancelled" in result.message.lower()


def test_crawl_stage_execute_exception(
    pipeline_context: PipelineContext,
    mock_calibre_repo: MagicMock,
) -> None:
    """Test crawl stage execute with exception."""
    stage = CrawlStage()
    mock_calibre_repo.get_session.side_effect = Exception("Database error")

    with patch(
        "bookcard.services.library_scanning.pipeline.crawl.CalibreBookRepository",
        return_value=mock_calibre_repo,
    ):
        result = stage.execute(pipeline_context)

    assert result.success is False
    assert result.message is not None
    assert "failed" in result.message.lower()


def test_crawl_stage_progress_updates(
    pipeline_context: PipelineContext,
    mock_calibre_repo: MagicMock,
    mock_calibre_session: MagicMock,
    sample_authors: list[Author],
    sample_books: list[Book],
    sample_links: list[BookAuthorLink],
) -> None:
    """Test crawl stage updates progress correctly."""
    stage = CrawlStage()
    mock_calibre_session.exec.return_value.all.side_effect = [
        sample_authors,
        sample_books,
        sample_links,
    ]
    progress_updates: list[tuple[float, dict | None]] = []

    def progress_callback(progress: float, metadata: dict | None = None) -> None:
        progress_updates.append((progress, metadata))

    pipeline_context.progress_callback = progress_callback

    with patch(
        "bookcard.services.library_scanning.pipeline.crawl.CalibreBookRepository",
        return_value=mock_calibre_repo,
    ):
        stage.execute(pipeline_context)

    # Should have multiple progress updates
    assert len(progress_updates) >= 3
    # Final progress should be 1.0
    assert progress_updates[-1][0] == 1.0
