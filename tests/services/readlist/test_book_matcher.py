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

"""Tests for book matcher service."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlmodel import Session, create_engine

from bookcard.database import create_all_tables, get_session
from bookcard.models.config import Library
from bookcard.models.core import Book, BookSeriesLink, Series
from bookcard.services.readlist.book_matcher import BookMatcherService
from bookcard.services.readlist.interfaces import BookReference


@pytest.fixture
def temp_calibre_db() -> Iterator[Path]:
    """Create a temporary Calibre database for testing."""
    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "metadata.db"
        engine = create_engine(f"sqlite:///{db_path}")
        try:
            create_all_tables(engine)
            yield db_path
        finally:
            # Ensure engine is disposed to release database file on Windows
            engine.dispose()


@pytest.fixture
def library(temp_calibre_db: Path) -> Library:
    """Create a test library configuration."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path=str(temp_calibre_db.parent),
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def calibre_session(temp_calibre_db: Path) -> Iterator[Session]:
    """Create a session for the test Calibre database."""
    engine = create_engine(f"sqlite:///{temp_calibre_db}")
    try:
        with get_session(engine) as session:
            yield session
    finally:
        # Ensure engine is disposed to release database file on Windows
        engine.dispose()


def test_book_matcher_exact_match(library: Library, calibre_session: Session) -> None:
    """Test exact matching of books."""
    # Create test data
    series = Series(name="Test Series", id=1)
    calibre_session.add(series)
    calibre_session.commit()

    book = Book(
        id=1,
        title="Test Book",
        series_index=1.0,
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
    )
    calibre_session.add(book)
    calibre_session.add(BookSeriesLink(book=1, series=1))
    calibre_session.commit()

    matcher = BookMatcherService(library)
    ref = BookReference(series="Test Series", volume=1.0, year=2020)
    results = matcher.match_books([ref], library_id=0)

    assert len(results) == 1
    assert results[0].book_id == 1
    assert results[0].confidence == 1.0
    assert results[0].match_type == "exact"


def test_book_matcher_no_match(library: Library) -> None:
    """Test when no match is found."""
    matcher = BookMatcherService(library)
    ref = BookReference(series="Non-existent Series", volume=1.0)
    results = matcher.match_books([ref], library_id=0)

    assert len(results) == 1
    assert results[0].book_id is None
    assert results[0].confidence == 0.0
    assert results[0].match_type == "none"
