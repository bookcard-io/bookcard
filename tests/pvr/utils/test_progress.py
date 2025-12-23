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

"""Tests for progress and ETA calculation utilities."""

import pytest

from bookcard.pvr.utils.progress import ETACalculator, ProgressCalculator

# ============================================================================
# ProgressCalculator Tests
# ============================================================================


class TestProgressCalculatorFromPercentage:
    """Test ProgressCalculator.from_percentage method."""

    def test_from_percentage_default_max(self) -> None:
        """Test from_percentage with default max_value."""
        result = ProgressCalculator.from_percentage(50.0)
        assert result == 0.5

    @pytest.mark.parametrize(
        ("value", "max_value", "expected"),
        [
            (0.0, 100.0, 0.0),
            (25.0, 100.0, 0.25),
            (50.0, 100.0, 0.5),
            (75.0, 100.0, 0.75),
            (100.0, 100.0, 1.0),
            (150.0, 100.0, 1.0),  # Capped at 1.0
            (50.0, 200.0, 0.25),
            (100.0, 200.0, 0.5),
            (200.0, 200.0, 1.0),
        ],
    )
    def test_from_percentage_various_values(
        self, value: float, max_value: float, expected: float
    ) -> None:
        """Test from_percentage with various values."""
        result = ProgressCalculator.from_percentage(value, max_value)
        assert result == expected

    def test_from_percentage_zero_max(self) -> None:
        """Test from_percentage with zero max_value."""
        result = ProgressCalculator.from_percentage(50.0, 0.0)
        assert result == 0.0

    def test_from_percentage_negative_max(self) -> None:
        """Test from_percentage with negative max_value."""
        result = ProgressCalculator.from_percentage(50.0, -10.0)
        assert result == 0.0

    def test_from_percentage_exceeds_max(self) -> None:
        """Test from_percentage when value exceeds max_value."""
        result = ProgressCalculator.from_percentage(150.0, 100.0)
        assert result == 1.0

    def test_from_percentage_negative_value(self) -> None:
        """Test from_percentage with negative value."""
        result = ProgressCalculator.from_percentage(-10.0, 100.0)
        assert result == -0.1  # Not capped on negative side


class TestProgressCalculatorFromBytes:
    """Test ProgressCalculator.from_bytes method."""

    def test_from_bytes_basic(self) -> None:
        """Test from_bytes with basic values."""
        result = ProgressCalculator.from_bytes(500, 1000)
        assert result == 0.5

    @pytest.mark.parametrize(
        ("downloaded", "total", "expected"),
        [
            (0, 1000, 0.0),
            (250, 1000, 0.25),
            (500, 1000, 0.5),
            (750, 1000, 0.75),
            (1000, 1000, 1.0),
            (1500, 1000, 1.0),  # Capped at 1.0
            (500, 2000, 0.25),
            (1000, 2000, 0.5),
            (2000, 2000, 1.0),
        ],
    )
    def test_from_bytes_various_values(
        self, downloaded: int, total: int, expected: float
    ) -> None:
        """Test from_bytes with various values."""
        result = ProgressCalculator.from_bytes(downloaded, total)
        assert result == expected

    def test_from_bytes_zero_total(self) -> None:
        """Test from_bytes with zero total."""
        result = ProgressCalculator.from_bytes(500, 0)
        assert result == 0.0

    def test_from_bytes_negative_total(self) -> None:
        """Test from_bytes with negative total."""
        result = ProgressCalculator.from_bytes(500, -100)
        assert result == 0.0

    def test_from_bytes_zero_both(self) -> None:
        """Test from_bytes with both zero."""
        result = ProgressCalculator.from_bytes(0, 0)
        assert result == 0.0

    def test_from_bytes_exceeds_total(self) -> None:
        """Test from_bytes when downloaded exceeds total."""
        result = ProgressCalculator.from_bytes(1500, 1000)
        assert result == 1.0

    def test_from_bytes_negative_downloaded(self) -> None:
        """Test from_bytes with negative downloaded."""
        result = ProgressCalculator.from_bytes(-100, 1000)
        assert result == -0.1  # Not capped on negative side


# ============================================================================
# ETACalculator Tests
# ============================================================================


class TestETACalculatorFromSpeedAndRemaining:
    """Test ETACalculator.from_speed_and_remaining method."""

    def test_from_speed_and_remaining_basic(self) -> None:
        """Test from_speed_and_remaining with basic values."""
        result = ETACalculator.from_speed_and_remaining(1000, 5000)
        assert result == 5

    @pytest.mark.parametrize(
        ("speed", "remaining", "expected"),
        [
            (1000, 5000, 5),
            (500, 1000, 2),
            (2000, 10000, 5),
            (1, 100, 100),
            (100, 1, 0),  # 1/100 = 0.01, int(0.01) = 0
            (1024, 10240, 10),
        ],
    )
    def test_from_speed_and_remaining_various_values(
        self, speed: int, remaining: int, expected: int
    ) -> None:
        """Test from_speed_and_remaining with various values."""
        result = ETACalculator.from_speed_and_remaining(speed, remaining)
        assert result == expected

    def test_from_speed_and_remaining_none_speed(self) -> None:
        """Test from_speed_and_remaining with None speed."""
        result = ETACalculator.from_speed_and_remaining(None, 5000)
        assert result is None

    def test_from_speed_and_remaining_none_remaining(self) -> None:
        """Test from_speed_and_remaining with None remaining."""
        result = ETACalculator.from_speed_and_remaining(1000, None)
        assert result is None

    def test_from_speed_and_remaining_both_none(self) -> None:
        """Test from_speed_and_remaining with both None."""
        result = ETACalculator.from_speed_and_remaining(None, None)
        assert result is None

    def test_from_speed_and_remaining_zero_speed(self) -> None:
        """Test from_speed_and_remaining with zero speed."""
        result = ETACalculator.from_speed_and_remaining(0, 5000)
        assert result is None

    def test_from_speed_and_remaining_negative_speed(self) -> None:
        """Test from_speed_and_remaining with negative speed."""
        result = ETACalculator.from_speed_and_remaining(-100, 5000)
        assert result is None

    def test_from_speed_and_remaining_zero_remaining(self) -> None:
        """Test from_speed_and_remaining with zero remaining."""
        result = ETACalculator.from_speed_and_remaining(1000, 0)
        assert result is None

    def test_from_speed_and_remaining_negative_remaining(self) -> None:
        """Test from_speed_and_remaining with negative remaining."""
        result = ETACalculator.from_speed_and_remaining(1000, -100)
        assert result is None

    def test_from_speed_and_remaining_float_result(self) -> None:
        """Test from_speed_and_remaining returns int even if calculation is float."""
        # 1000 bytes / 300 bytes/sec = 3.333... seconds, should return 3
        result = ETACalculator.from_speed_and_remaining(300, 1000)
        assert result == 3
        assert isinstance(result, int)
