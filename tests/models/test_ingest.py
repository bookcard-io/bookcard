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

"""Tests for ingest models to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from bookcard.models.ingest import IngestHistory, IngestStatus


@pytest.fixture
def ingest_history() -> IngestHistory:
    """Create a basic ingest history record."""
    return IngestHistory(
        id=1,
        file_path="/test/path.epub",
        status=IngestStatus.PENDING,
    )


@pytest.mark.parametrize(
    ("started_at", "completed_at", "expected_duration"),
    [
        (None, None, None),
        (
            datetime.now(UTC) - timedelta(seconds=10),
            datetime.now(UTC),
            10.0,
        ),
        (
            datetime.now(UTC) - timedelta(seconds=30),
            datetime.now(UTC),
            30.0,
        ),
    ],
)
def test_ingest_history_duration(
    ingest_history: IngestHistory,
    started_at: datetime | None,
    completed_at: datetime | None,
    expected_duration: float | None,
) -> None:
    """Test duration property (covers lines 130-138)."""
    ingest_history.started_at = started_at
    ingest_history.completed_at = completed_at

    duration = ingest_history.duration
    if expected_duration is None:
        assert duration is None
    else:
        assert duration is not None
        assert duration == pytest.approx(expected_duration, abs=1.0)


def test_ingest_history_duration_with_naive_started_at(
    ingest_history: IngestHistory,
) -> None:
    """Test duration property with naive started_at (covers lines 130-132)."""
    now_utc = datetime.now(UTC)
    naive_start = now_utc.replace(tzinfo=None) - timedelta(seconds=10)
    ingest_history.started_at = naive_start
    ingest_history.completed_at = now_utc

    duration = ingest_history.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_ingest_history_duration_with_naive_completed_at(
    ingest_history: IngestHistory,
) -> None:
    """Test duration property with naive completed_at (covers lines 134-136)."""
    now_utc = datetime.now(UTC)
    ingest_history.started_at = now_utc - timedelta(seconds=10)
    naive_completed = now_utc.replace(tzinfo=None)
    ingest_history.completed_at = naive_completed

    duration = ingest_history.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_ingest_history_duration_uses_current_time_when_no_completed_at(
    ingest_history: IngestHistory,
) -> None:
    """Test duration property uses current time when completed_at is None (covers lines 134-136)."""
    now_utc = datetime.now(UTC)
    ingest_history.started_at = now_utc - timedelta(seconds=5)
    ingest_history.completed_at = None

    duration = ingest_history.duration
    assert duration is not None
    assert duration == pytest.approx(5.0, abs=1.0)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (IngestStatus.PENDING, False),
        (IngestStatus.PROCESSING, False),
        (IngestStatus.COMPLETED, True),
        (IngestStatus.FAILED, True),
    ],
)
def test_ingest_history_is_complete(
    ingest_history: IngestHistory,
    status: IngestStatus,
    expected: bool,
) -> None:
    """Test is_complete property (covers line 149)."""
    ingest_history.status = status
    assert ingest_history.is_complete == expected
