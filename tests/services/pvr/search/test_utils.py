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

"""Tests for utility functions."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from bookcard.services.pvr.search.utils import (
    check_threshold,
    ensure_utc,
    normalize_text,
)


class TestEnsureUTC:
    """Test ensure_utc function."""

    @pytest.mark.parametrize(
        ("input_dt", "expected_tzinfo"),
        [
            (None, None),
            (datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC), UTC),
        ],
    )
    def test_ensure_utc(
        self, input_dt: datetime | None, expected_tzinfo: type[UTC] | None
    ) -> None:
        """Test ensure_utc with various datetime inputs.

        Parameters
        ----------
        input_dt : datetime | None
            Input datetime.
        expected_tzinfo : timezone | None
            Expected timezone info.
        """
        result = ensure_utc(input_dt)
        if input_dt is None:
            assert result is None
        else:
            assert result is not None
            assert result.tzinfo is not None
            if expected_tzinfo is UTC:
                assert result.tzinfo == UTC


class TestNormalizeText:
    """Test normalize_text function."""

    @pytest.mark.parametrize(
        ("input_text", "expected"),
        [
            (None, ""),
            ("", ""),
            ("  ", ""),
            ("Test", "test"),
            ("  Test  ", "test"),
            ("TEST", "test"),
            ("Test String", "test string"),
            ("  Mixed   Case  ", "mixed   case"),
        ],
    )
    def test_normalize_text(self, input_text: str | None, expected: str) -> None:
        """Test normalize_text with various inputs.

        Parameters
        ----------
        input_text : str | None
            Input text.
        expected : str
            Expected normalized output.
        """
        result = normalize_text(input_text)
        assert result == expected


class TestCheckThreshold:
    """Test check_threshold function."""

    @pytest.mark.parametrize(
        ("value", "threshold", "comparison", "expected"),
        [
            # No threshold - always True
            (None, None, lambda v, t: v >= t, True),
            (10, None, lambda v, t: v >= t, True),
            (0, None, lambda v, t: v >= t, True),
            # Value is None - False
            (None, 10, lambda v, t: v >= t, False),
            # Value meets threshold
            (10, 5, lambda v, t: v >= t, True),
            (100, 50, lambda v, t: v >= t, True),
            (10, 10, lambda v, t: v >= t, True),
            # Value doesn't meet threshold
            (5, 10, lambda v, t: v >= t, False),
            (0, 1, lambda v, t: v >= t, False),
            # Different comparison functions
            (5, 10, lambda v, t: v <= t, True),
            (15, 10, lambda v, t: v <= t, False),
            (10, 10, lambda v, t: v == t, True),
            (5, 10, lambda v, t: v == t, False),
        ],
    )
    def test_check_threshold(
        self,
        value: int | None,
        threshold: int | None,
        comparison: Callable[[int, int], bool],
        expected: bool,
    ) -> None:
        """Test check_threshold with various inputs.

        Parameters
        ----------
        value : int | None
            Value to check.
        threshold : int | None
            Threshold value.
        comparison : callable[[int, int], bool]
            Comparison function.
        expected : bool
            Expected result.
        """
        result = check_threshold(value, threshold, comparison)
        assert result == expected
