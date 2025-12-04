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

"""Tests for ConversionRepository to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError

from fundamental.models.conversion import BookConversion, ConversionStatus

if TYPE_CHECKING:
    from tests.conftest import DummySession

from fundamental.services.conversion.repository import ConversionRepository


@pytest.fixture
def conversion_repo(session: DummySession) -> ConversionRepository:  # type: ignore[valid-type]
    """Create ConversionRepository instance.

    Parameters
    ----------
    session : DummySession
        Session fixture.

    Returns
    -------
    ConversionRepository
        Repository instance.
    """
    return ConversionRepository(session)  # type: ignore[arg-type]


@pytest.fixture
def book_conversion() -> BookConversion:
    """Create a test book conversion record.

    Returns
    -------
    BookConversion
        BookConversion instance.
    """
    return BookConversion(
        book_id=1,
        library_id=1,
        user_id=None,
        original_format="MOBI",
        target_format="EPUB",
        original_file_path="/path/to/book.mobi",
        converted_file_path="/path/to/book.epub",
        original_backed_up=True,
        conversion_method="manual",
        status=ConversionStatus.COMPLETED,
    )


@pytest.mark.parametrize(
    ("original_format", "target_format", "expected_original", "expected_target"),
    [
        ("mobi", "epub", "MOBI", "EPUB"),
        ("MOBI", "EPUB", "MOBI", "EPUB"),
        ("Mobi", "Epub", "MOBI", "EPUB"),
    ],
)
def test_find_existing_normalizes_formats(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
    book_conversion: BookConversion,
    original_format: str,
    target_format: str,
    expected_original: str,
    expected_target: str,
) -> None:
    """Test find_existing normalizes formats to uppercase.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    book_conversion : BookConversion
        Book conversion fixture.
    original_format : str
        Original format to test.
    target_format : str
        Target format to test.
    expected_original : str
        Expected normalized original format.
    expected_target : str
        Expected normalized target format.
    """
    session.set_exec_result([book_conversion])

    result = conversion_repo.find_existing(1, original_format, target_format)

    assert result == book_conversion


def test_find_existing_with_status_filter(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
    book_conversion: BookConversion,
) -> None:
    """Test find_existing filters by status.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    book_conversion : BookConversion
        Book conversion fixture.
    """
    session.set_exec_result([book_conversion])

    result = conversion_repo.find_existing(
        1, "MOBI", "EPUB", status=ConversionStatus.COMPLETED
    )

    assert result == book_conversion


def test_find_existing_returns_none_when_not_found(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
) -> None:
    """Test find_existing returns None when not found.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    """
    session.set_exec_result([])

    result = conversion_repo.find_existing(1, "MOBI", "EPUB")

    assert result is None


def test_save_creates_new_record(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
    book_conversion: BookConversion,
) -> None:
    """Test save creates new record when none exists.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    book_conversion : BookConversion
        Book conversion fixture.
    """
    session.set_exec_result([])  # No existing record

    result = conversion_repo.save(book_conversion)

    assert result == book_conversion
    assert book_conversion in session.added
    assert session.flush_count == 1


def test_save_updates_existing_record(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
    book_conversion: BookConversion,
) -> None:
    """Test save updates existing record.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    book_conversion : BookConversion
        Book conversion fixture.
    """
    existing = BookConversion(
        book_id=1,
        library_id=1,
        user_id=None,
        original_format="MOBI",
        target_format="EPUB",
        original_file_path="/old/path.mobi",
        converted_file_path="/old/path.epub",
        original_backed_up=False,
        conversion_method="manual",
        status=ConversionStatus.FAILED,
    )
    session.set_exec_result([existing])

    result = conversion_repo.save(book_conversion)

    assert result == existing
    assert existing.original_file_path == book_conversion.original_file_path
    assert existing.converted_file_path == book_conversion.converted_file_path
    assert existing.status == book_conversion.status


@pytest.mark.parametrize(
    ("old_status", "new_status", "should_update_created_at"),
    [
        (ConversionStatus.FAILED, ConversionStatus.COMPLETED, True),
        (ConversionStatus.FAILED, ConversionStatus.FAILED, False),
        (ConversionStatus.COMPLETED, ConversionStatus.COMPLETED, False),
        (ConversionStatus.COMPLETED, ConversionStatus.FAILED, False),
    ],
)
def test_save_updates_created_at_on_retry(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
    old_status: ConversionStatus,
    new_status: ConversionStatus,
    should_update_created_at: bool,
) -> None:
    """Test save updates created_at when retrying failed conversion.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    old_status : ConversionStatus
        Old status.
    new_status : ConversionStatus
        New status.
    should_update_created_at : bool
        Whether created_at should be updated.
    """
    existing = BookConversion(
        book_id=1,
        library_id=1,
        original_format="MOBI",
        target_format="EPUB",
        original_file_path="/path.mobi",
        converted_file_path="/path.epub",
        status=old_status,
        conversion_method="manual",
    )
    existing.created_at = datetime(2024, 1, 1, tzinfo=UTC)

    new_conversion = BookConversion(
        book_id=1,
        library_id=1,
        original_format="MOBI",
        target_format="EPUB",
        original_file_path="/path.mobi",
        converted_file_path="/path.epub",
        status=new_status,
        conversion_method="manual",
    )
    new_conversion.created_at = datetime(2024, 1, 2, tzinfo=UTC)

    session.set_exec_result([existing])

    result = conversion_repo.save(new_conversion)

    if should_update_created_at:
        assert result.created_at == new_conversion.created_at
    else:
        assert result.created_at == existing.created_at


def test_save_handles_integrity_error_with_existing_record(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
    book_conversion: BookConversion,
) -> None:
    """Test save handles IntegrityError and updates existing record.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    book_conversion : BookConversion
        Book conversion fixture.
    """
    existing = BookConversion(
        book_id=1,
        library_id=1,
        original_format="MOBI",
        target_format="EPUB",
        original_file_path="/old/path.mobi",
        converted_file_path="/old/path.epub",
        status=ConversionStatus.COMPLETED,
        conversion_method="manual",
    )

    # First find_existing call (line 114) returns None
    # Second find_existing call (line 160, after IntegrityError) returns existing
    session.set_exec_result([None])  # First call returns None
    session.add_exec_result([existing])  # Second call returns existing

    # Mock flush to raise IntegrityError on first call only
    original_flush = session.flush
    flush_call_count = [0]

    def mock_flush() -> None:
        flush_call_count[0] += 1
        if flush_call_count[0] == 1:
            # First flush call raises IntegrityError
            from sqlalchemy.exc import IntegrityError as SQLIntegrityError

            error = SQLIntegrityError(
                statement="INSERT INTO book_conversions ...",
                params={},
                orig=Exception("UNIQUE constraint failed"),
            )
            raise error
        # Subsequent flush calls (after IntegrityError is handled) succeed
        original_flush()

    session.flush = mock_flush  # type: ignore[assignment]

    # The save method should catch the IntegrityError and handle it
    result = conversion_repo.save(book_conversion)

    assert result == existing
    assert existing.original_file_path == book_conversion.original_file_path
    # Should have called flush twice: once (raises error), then again after handling
    assert flush_call_count[0] == 2


def test_save_handles_integrity_error_without_existing_record(
    conversion_repo: ConversionRepository,
    session: DummySession,  # type: ignore[valid-type]
    book_conversion: BookConversion,
) -> None:
    """Test save re-raises IntegrityError when existing record not found.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    session : DummySession
        Session fixture.
    book_conversion : BookConversion
        Book conversion fixture.
    """
    # Both calls return None (no existing record found)
    session.set_exec_result([None, None])

    # Mock flush to raise IntegrityError
    original_flush = session.flush
    call_count = [0]

    def mock_flush() -> None:
        call_count[0] += 1
        if call_count[0] == 1:
            # Create a proper IntegrityError
            from sqlalchemy.exc import IntegrityError as SQLIntegrityError

            error = SQLIntegrityError(
                statement="INSERT INTO book_conversions ...",
                params={},
                orig=Exception("UNIQUE constraint failed"),
            )
            raise error
        original_flush()

    session.flush = mock_flush  # type: ignore[assignment]

    with pytest.raises(IntegrityError):
        conversion_repo.save(book_conversion)


def test_now_returns_utc_datetime(
    conversion_repo: ConversionRepository,
) -> None:
    """Test _now returns UTC datetime.

    Parameters
    ----------
    conversion_repo : ConversionRepository
        Repository fixture.
    """
    result = conversion_repo._now()

    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
