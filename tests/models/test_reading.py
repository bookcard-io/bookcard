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

"""Tests for reading models to achieve 100% coverage."""

from datetime import UTC, datetime, timedelta

import pytest

from bookcard.models.reading import ReadingSession


@pytest.fixture
def reading_session() -> ReadingSession:
    """Create a basic reading session."""
    return ReadingSession(
        id=1,
        user_id=1,
        library_id=1,
        book_id=1,
        format="EPUB",
        started_at=datetime.now(UTC),
    )


def test_reading_session_duration_not_ended(reading_session: ReadingSession) -> None:
    """Test duration property when session hasn't ended."""
    reading_session.ended_at = None
    assert reading_session.duration is None


def test_reading_session_duration_with_ended_at(
    reading_session: ReadingSession,
) -> None:
    """Test duration property with ended_at."""
    reading_session.started_at = datetime.now(UTC) - timedelta(seconds=10)
    reading_session.ended_at = datetime.now(UTC)
    duration = reading_session.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_reading_session_duration_with_naive_started_at(
    reading_session: ReadingSession,
) -> None:
    """Test duration property with naive started_at datetime."""
    # Create naive datetime by removing timezone info from UTC datetime
    # This simulates a naive datetime that the code will assume is UTC
    now_utc = datetime.now(UTC)
    naive_start = now_utc.replace(tzinfo=None) - timedelta(seconds=10)
    reading_session.started_at = naive_start
    reading_session.ended_at = now_utc
    duration = reading_session.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_reading_session_duration_with_naive_ended_at(
    reading_session: ReadingSession,
) -> None:
    """Test duration property with naive ended_at datetime."""
    # Create naive datetime by removing timezone info from UTC datetime
    # This simulates a naive datetime that the code will assume is UTC
    now_utc = datetime.now(UTC)
    reading_session.started_at = now_utc - timedelta(seconds=10)
    naive_end = now_utc.replace(tzinfo=None)
    reading_session.ended_at = naive_end
    duration = reading_session.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_reading_session_duration_long_session(reading_session: ReadingSession) -> None:
    """Test duration property for a long reading session."""
    reading_session.started_at = datetime.now(UTC) - timedelta(hours=2)
    reading_session.ended_at = datetime.now(UTC)
    duration = reading_session.duration
    assert duration is not None
    assert duration == pytest.approx(7200.0, abs=1.0)
