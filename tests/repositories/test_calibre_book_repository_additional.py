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

"""Additional tests for Calibre book repository to achieve 100% coverage.

This file covers edge cases and early return paths that were not covered
in the main test file.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from fundamental.models.core import (
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    Identifier,
)
from fundamental.repositories import CalibreBookRepository
from fundamental.repositories.book_relationship_manager import (
    BookRelationshipManager,
)
from fundamental.repositories.session_manager import CalibreSessionManager

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def temp_repo() -> Generator[CalibreBookRepository, None, None]:
    """Create a CalibreBookRepository with a temporary database.

    Yields
    ------
    CalibreBookRepository
        Repository instance with temporary database path.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()
        repo = CalibreBookRepository(str(tmpdir))
        try:
            yield repo
        finally:
            # Dispose engine to release database connections (important on Windows)
            repo.dispose()


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock session with common setup.

    Returns
    -------
    MagicMock
        Mock session with added/deleted tracking.
    """
    session = MagicMock()
    session.added = []
    session.deleted = []
    session.add = lambda x: session.added.append(x)
    session.delete = lambda x: session.deleted.append(x)
    session.flush = MagicMock()
    return session


def test_register_title_sort_connection_record_parameter(
    temp_repo: CalibreBookRepository,
) -> None:
    """Test _register_title_sort uses connection_record parameter (covers lines 245-246).

    This test ensures the connection_record parameter is assigned to _,
    which is required by the event listener signature even though it's unused.
    """
    # Create engine to trigger _register_title_sort registration
    # Type cast to access private method for testing
    session_manager = temp_repo._session_manager
    assert isinstance(session_manager, CalibreSessionManager)
    engine = session_manager._get_engine()

    # Create a connection to trigger the connect event
    # This will call _register_title_sort with both dbapi_conn and connection_record
    with engine.connect() as conn:
        # Get the raw SQLite connection
        raw_conn = conn.connection.dbapi_connection
        assert raw_conn is not None
        cursor = raw_conn.cursor()

        # Verify the title_sort function was registered by using it
        # The function should return the input as-is (or empty string if None)
        cursor.execute("SELECT title_sort(?)", ("test",))
        row = cursor.fetchone()
        assert row is not None
        result = row[0]
        assert result == "test"

        # Test with None (should return empty string)
        cursor.execute("SELECT title_sort(?)", (None,))
        row = cursor.fetchone()
        assert row is not None
        result = row[0]
        assert result == ""


def test_update_book_series_no_change(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _update_book_series early return when series hasn't changed (covers line 996).

    When the current series ID matches the target series ID, the method
    should return early without making any changes.
    """
    # Setup: existing link with series ID 1
    existing_link = BookSeriesLink(book=1, series=1)
    mock_exec = MagicMock()
    mock_exec.first.return_value = existing_link
    mock_session.exec.return_value = mock_exec

    # Update with same series ID
    temp_repo._relationship_manager.update_series(mock_session, 1, series_id=1)

    # Verify no changes were made
    assert len(mock_session.added) == 0
    assert len(mock_session.deleted) == 0


def test_update_book_tags_no_change(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _update_book_tags early return when tags haven't changed (covers line 1037).

    When the current tags match the new tags (after normalization),
    the method should return early without making any changes.
    """
    # Setup: existing tags query returns ["Tag 1", "Tag 2"]
    mock_exec = MagicMock()
    mock_exec.all.return_value = ["Tag 1", "Tag 2"]
    mock_session.exec.return_value = mock_exec

    # Update with same tags (case/whitespace variations should normalize to same)
    temp_repo._relationship_manager.update_tags(mock_session, 1, ["tag 1", "TAG 2"])

    # Verify no changes were made (early return should prevent deletion/addition)
    assert len(mock_session.added) == 0
    assert len(mock_session.deleted) == 0
    # Should only have one exec call (for getting current tags)
    assert mock_session.exec.call_count == 1


def test_update_book_identifiers_no_change(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _update_book_identifiers early return when identifiers haven't changed (covers line 1096).

    When the current identifiers match the new identifiers (after normalization),
    the method should return early without making any changes.
    """
    # Setup: existing identifiers
    existing_ident1 = Identifier(book=1, type="isbn", val="1234567890")
    existing_ident2 = Identifier(book=1, type="doi", val="10.1234/test")
    mock_exec = MagicMock()
    mock_exec.all.return_value = [existing_ident1, existing_ident2]
    mock_session.exec.return_value = mock_exec

    # Update with same identifiers (case/whitespace variations should normalize to same)
    temp_repo._relationship_manager.update_identifiers(
        mock_session,
        1,
        [
            {"type": "ISBN", "val": " 1234567890 "},
            {"type": "DOI", "val": "10.1234/test"},
        ],
    )

    # Verify no changes were made
    assert len(mock_session.added) == 0
    assert len(mock_session.deleted) == 0


def test_update_book_publisher_no_change(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _update_book_publisher early return when publisher hasn't changed (covers line 1175).

    When the current publisher ID matches the target publisher ID,
    the method should return early without making any changes.
    """
    # Setup: existing link with publisher ID 1
    existing_link = BookPublisherLink(book=1, publisher=1)
    mock_exec = MagicMock()
    mock_exec.first.return_value = existing_link
    mock_session.exec.return_value = mock_exec

    # Update with same publisher ID
    temp_repo._relationship_manager.update_publisher(mock_session, 1, publisher_id=1)

    # Verify no changes were made
    assert len(mock_session.added) == 0
    assert len(mock_session.deleted) == 0


def test_resolve_language_ids_none_codes(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _resolve_language_ids returns empty list when language_codes is None (covers line 1261).

    When both language_ids and language_codes are None, the method
    should return an empty list.
    """
    # Type cast to access private method for testing
    relationship_manager = temp_repo._relationship_manager
    assert isinstance(relationship_manager, BookRelationshipManager)
    result = relationship_manager._resolve_language_ids(
        mock_session, language_ids=None, language_codes=None
    )

    assert result == []


def test_update_book_language_no_change(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _update_book_language early return when languages haven't changed (covers line 1366).

    When the current language IDs match the target language IDs,
    the method should return early without making any changes.
    """
    # Setup: existing language links
    existing_link1 = BookLanguageLink(book=1, lang_code=1, item_order=0)
    existing_link2 = BookLanguageLink(book=1, lang_code=2, item_order=1)
    mock_exec = MagicMock()
    mock_exec.all.return_value = [existing_link1, existing_link2]
    mock_session.exec.return_value = mock_exec

    # Update with same language IDs
    temp_repo._relationship_manager.update_languages(
        mock_session, 1, language_ids=[1, 2]
    )

    # Verify no changes were made
    assert len(mock_session.added) == 0
    assert len(mock_session.deleted) == 0


def test_update_book_rating_no_change(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _update_book_rating early return when rating hasn't changed (covers line 1412).

    When the current rating ID matches the target rating ID,
    the method should return early without making any changes.
    """
    # Setup: existing link with rating ID 1
    existing_link = BookRatingLink(book=1, rating=1)
    mock_exec = MagicMock()
    mock_exec.first.return_value = existing_link
    mock_session.exec.return_value = mock_exec

    # Update with same rating ID
    temp_repo._relationship_manager.update_rating(mock_session, 1, rating_id=1)

    # Verify no changes were made
    assert len(mock_session.added) == 0
    assert len(mock_session.deleted) == 0
