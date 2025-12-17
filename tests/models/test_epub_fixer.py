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

"""Tests for EPUB fixer models to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from bookcard.models.epub_fixer import EPUBFixRun


@pytest.fixture
def epub_fix_run() -> EPUBFixRun:
    """Create a basic EPUB fix run."""
    return EPUBFixRun(
        id=1,
        started_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("completed_at", "expected_duration"),
    [
        (None, None),
        (10.0, 10.0),
        (30.0, 30.0),
    ],
)
def test_epub_fix_run_duration(
    epub_fix_run: EPUBFixRun,
    completed_at: float | None,
    expected_duration: float | None,
) -> None:
    """Test duration property (covers lines 150-158)."""
    if completed_at is not None:
        now = datetime.now(UTC)
        epub_fix_run.started_at = now - timedelta(seconds=completed_at)
        epub_fix_run.completed_at = now
    else:
        epub_fix_run.completed_at = None

    duration = epub_fix_run.duration
    if expected_duration is None:
        assert duration is None
    else:
        assert duration is not None
        assert duration == pytest.approx(expected_duration, abs=1.0)


def test_epub_fix_run_duration_with_naive_started_at(
    epub_fix_run: EPUBFixRun,
) -> None:
    """Test duration property with naive started_at (covers lines 150-152)."""
    now_utc = datetime.now(UTC)
    naive_start = now_utc.replace(tzinfo=None) - timedelta(seconds=10)
    epub_fix_run.started_at = naive_start
    epub_fix_run.completed_at = now_utc

    duration = epub_fix_run.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_epub_fix_run_duration_with_naive_completed_at(
    epub_fix_run: EPUBFixRun,
) -> None:
    """Test duration property with naive completed_at (covers lines 154-156)."""
    now_utc = datetime.now(UTC)
    epub_fix_run.started_at = now_utc - timedelta(seconds=10)
    naive_completed = now_utc.replace(tzinfo=None)
    epub_fix_run.completed_at = naive_completed

    duration = epub_fix_run.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


@pytest.mark.parametrize(
    ("total_files_processed", "total_files_fixed", "expected"),
    [
        (0, 0, None),
        (10, 5, 0.5),
        (10, 10, 1.0),
        (10, 0, 0.0),
        (100, 75, 0.75),
    ],
)
def test_epub_fix_run_success_rate(
    epub_fix_run: EPUBFixRun,
    total_files_processed: int,
    total_files_fixed: int,
    expected: float | None,
) -> None:
    """Test success_rate property (covers lines 169-171)."""
    epub_fix_run.total_files_processed = total_files_processed
    epub_fix_run.total_files_fixed = total_files_fixed

    success_rate = epub_fix_run.success_rate
    if expected is None:
        assert success_rate is None
    else:
        assert success_rate is not None
        assert success_rate == expected
