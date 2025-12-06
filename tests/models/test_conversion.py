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

"""Tests for conversion models to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from fundamental.models.conversion import (
    BookConversion,
    ConversionMethod,
    ConversionStatus,
)


@pytest.fixture
def book_conversion() -> BookConversion:
    """Create a basic book conversion record."""
    return BookConversion(
        id=1,
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        original_file_path="/test/path.mobi",
        converted_file_path="/test/path.epub",
        conversion_method=ConversionMethod.MANUAL,
        status=ConversionStatus.COMPLETED,
    )


@pytest.mark.parametrize(
    ("completed_at", "expected_duration"),
    [
        (None, None),
        (10.0, 10.0),
        (30.0, 30.0),
    ],
)
def test_book_conversion_duration(
    book_conversion: BookConversion,
    completed_at: float | None,
    expected_duration: float | None,
) -> None:
    """Test duration property (covers lines 178-186)."""
    if completed_at is not None:
        now = datetime.now(UTC)
        book_conversion.created_at = now - timedelta(seconds=completed_at)
        book_conversion.completed_at = now
    else:
        book_conversion.completed_at = None

    duration = book_conversion.duration
    if expected_duration is None:
        assert duration is None
    else:
        assert duration is not None
        assert duration == pytest.approx(expected_duration, abs=1.0)


def test_book_conversion_duration_with_naive_created_at(
    book_conversion: BookConversion,
) -> None:
    """Test duration property with naive created_at (covers lines 178-180)."""
    now_utc = datetime.now(UTC)
    naive_created = now_utc.replace(tzinfo=None) - timedelta(seconds=10)
    book_conversion.created_at = naive_created
    book_conversion.completed_at = now_utc

    duration = book_conversion.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)


def test_book_conversion_duration_with_naive_completed_at(
    book_conversion: BookConversion,
) -> None:
    """Test duration property with naive completed_at (covers lines 182-184)."""
    now_utc = datetime.now(UTC)
    book_conversion.created_at = now_utc - timedelta(seconds=10)
    naive_completed = now_utc.replace(tzinfo=None)
    book_conversion.completed_at = naive_completed

    duration = book_conversion.duration
    assert duration is not None
    assert duration == pytest.approx(10.0, abs=1.0)
