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

"""Tests for `SendFormatService`."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.auth import EBookFormat, EReaderDevice, UserSetting
from bookcard.models.core import Book
from bookcard.repositories import BookWithFullRelations
from bookcard.services.send_format_service import SendFormatService
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a dummy session with configurable exec results."""
    return DummySession()


@pytest.fixture
def book() -> Book:
    """Create a minimal book."""
    return Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="Author/Test Book (1)",
    )


def _book_with_formats(book: Book, formats: list[str]) -> BookWithFullRelations:
    """Create `BookWithFullRelations` with specified formats."""
    return BookWithFullRelations(
        book=book,
        authors=["Author One"],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[
            {"format": fmt, "name": f"test.{fmt.lower()}", "size": 1000}
            for fmt in formats
        ],
    )


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (None, ["EPUB", "PDF"]),
        ("", ["EPUB", "PDF"]),
        ('["pdf","epub","pdf","  azw3  "]', ["PDF", "EPUB", "AZW3"]),
        ("pdf, epub, pdf", ["PDF", "EPUB"]),
        ('{"not":"a list"}', ["EPUB", "PDF"]),
    ],
)
def test_get_user_format_priority_parsing(
    session: DummySession,
    raw_value: str | None,
    expected: list[str],
) -> None:
    """User setting is parsed as JSON list or CSV; invalid defaults."""
    if raw_value is not None:
        setting = UserSetting(user_id=1, key="send_format_priority", value=raw_value)
        session.add_exec_result([setting])
    else:
        session.add_exec_result([])

    service = SendFormatService(session)  # type: ignore[arg-type]
    assert service.get_user_format_priority(user_id=1) == expected


@pytest.mark.parametrize(
    ("requested_format", "expected"),
    [
        ("epub", "EPUB"),
        ("PDF", "PDF"),
        ("mobi", "MOBI"),
    ],
)
def test_select_format_explicit_request_wins(
    session: DummySession,
    book: Book,
    requested_format: str,
    expected: str,
) -> None:
    """Explicit requested_format always wins (case-insensitive)."""
    book_with_rels = _book_with_formats(book, ["EPUB", "PDF"])
    service = SendFormatService(session)  # type: ignore[arg-type]

    assert (
        service.select_format(
            user_id=1,
            to_email="device@example.com",
            requested_format=requested_format,
            book_with_rels=book_with_rels,
        )
        == expected
    )


def test_select_format_returns_none_when_book_has_no_formats(
    session: DummySession,
    book: Book,
) -> None:
    """No formats => selection returns None (caller decides behavior)."""
    book_with_rels = _book_with_formats(book, [])
    service = SendFormatService(session)  # type: ignore[arg-type]
    assert (
        service.select_format(
            user_id=1,
            to_email=None,
            requested_format=None,
            book_with_rels=book_with_rels,
        )
        is None
    )


def test_select_format_device_preferred_format_used_when_available(
    session: DummySession,
    book: Book,
) -> None:
    """Device preferred_format wins over user priority when available."""
    book_with_rels = _book_with_formats(book, ["EPUB", "PDF"])
    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="My Device",
        device_type="generic",
        is_default=True,
        preferred_format=EBookFormat.PDF,
    )

    repo = MagicMock()
    repo.find_by_email.return_value = device
    repo.find_default.return_value = None
    repo.find_by_user.return_value = []

    # If this were consulted, user priority would pick EPUB first; ensure device wins.
    session.add_exec_result([
        UserSetting(user_id=1, key="send_format_priority", value='["EPUB","PDF"]')
    ])

    with patch(
        "bookcard.services.send_format_service.ereader_repository.EReaderRepository",
        return_value=repo,
    ):
        service = SendFormatService(session)  # type: ignore[arg-type]
        assert (
            service.select_format(
                user_id=1,
                to_email="device@example.com",
                requested_format=None,
                book_with_rels=book_with_rels,
            )
            == "PDF"
        )


@pytest.mark.parametrize(
    ("device_pref", "priority_value", "expected"),
    [
        # Device preference not available => use user priority
        (EBookFormat.AZW3, '["PDF","EPUB"]', "PDF"),
        # No matching user priority => fall back to first available
        (EBookFormat.AZW3, '["MOBI"]', "PDF"),
    ],
)
def test_select_format_falls_back_when_device_preference_unavailable(
    session: DummySession,
    book: Book,
    device_pref: EBookFormat,
    priority_value: str,
    expected: str,
) -> None:
    """If device preferred format isn't present on book, use user priority then first."""
    # First available is PDF here; keep order stable to validate fallback.
    book_with_rels = _book_with_formats(book, ["PDF", "EPUB"])
    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="My Device",
        device_type="generic",
        is_default=True,
        preferred_format=device_pref,
    )

    repo = MagicMock()
    repo.find_by_email.return_value = device
    repo.find_default.return_value = None
    repo.find_by_user.return_value = []

    session.add_exec_result([
        UserSetting(user_id=1, key="send_format_priority", value=priority_value)
    ])

    with patch(
        "bookcard.services.send_format_service.ereader_repository.EReaderRepository",
        return_value=repo,
    ):
        service = SendFormatService(session)  # type: ignore[arg-type]
        assert (
            service.select_format(
                user_id=1,
                to_email="device@example.com",
                requested_format=None,
                book_with_rels=book_with_rels,
            )
            == expected
        )


def test_select_format_uses_user_priority_when_no_device_resolves(
    session: DummySession,
    book: Book,
) -> None:
    """If device cannot be resolved, user priority decides."""
    book_with_rels = _book_with_formats(book, ["PDF", "EPUB"])
    session.add_exec_result([
        UserSetting(user_id=1, key="send_format_priority", value='["EPUB","PDF"]')
    ])

    repo = MagicMock()
    repo.find_by_email.return_value = None
    repo.find_default.return_value = None
    repo.find_by_user.return_value = []

    with patch(
        "bookcard.services.send_format_service.ereader_repository.EReaderRepository",
        return_value=repo,
    ):
        service = SendFormatService(session)  # type: ignore[arg-type]
        assert (
            service.select_format(
                user_id=1,
                to_email="unknown@example.com",
                requested_format=None,
                book_with_rels=book_with_rels,
            )
            == "EPUB"
        )
