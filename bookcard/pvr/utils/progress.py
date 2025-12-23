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

"""Progress and ETA calculation utilities for PVR system.

This module provides shared progress and ETA calculation utilities following SRP
by separating calculation logic from download client implementations.
"""


class ProgressCalculator:
    """Calculate download progress from various formats.

    This class provides static methods for calculating progress from different
    input formats, following SRP by separating progress calculation concerns.
    """

    @staticmethod
    def from_percentage(value: float, max_value: float = 100.0) -> float:
        """Calculate progress from percentage value.

        Parameters
        ----------
        value : float
            Current percentage value.
        max_value : float
            Maximum percentage value (default: 100.0).

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.

        Examples
        --------
        >>> ProgressCalculator.from_percentage(
        ...     50.0
        ... )
        0.5
        >>> ProgressCalculator.from_percentage(
        ...     75.0,
        ...     max_value=100.0,
        ... )
        0.75
        """
        if max_value <= 0:
            return 0.0
        progress = value / max_value
        return min(progress, 1.0)

    @staticmethod
    def from_bytes(downloaded: int, total: int) -> float:
        """Calculate progress from byte counts.

        Parameters
        ----------
        downloaded : int
            Bytes downloaded.
        total : int
            Total bytes to download.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.

        Examples
        --------
        >>> ProgressCalculator.from_bytes(
        ...     500, 1000
        ... )
        0.5
        >>> ProgressCalculator.from_bytes(
        ...     0, 0
        ... )
        0.0
        """
        if total <= 0:
            return 0.0
        return min(downloaded / total, 1.0)


class ETACalculator:
    """Calculate estimated time of arrival.

    This class provides static methods for calculating ETA from different
    input formats, following SRP by separating ETA calculation concerns.
    """

    @staticmethod
    def from_speed_and_remaining(
        speed_bytes_per_sec: int | None,
        remaining_bytes: int | None,
    ) -> int | None:
        """Calculate ETA from speed and remaining bytes.

        Parameters
        ----------
        speed_bytes_per_sec : int | None
            Download speed in bytes per second.
        remaining_bytes : int | None
            Remaining bytes to download.

        Returns
        -------
        int | None
            Estimated time to completion in seconds, or None if cannot calculate.

        Examples
        --------
        >>> ETACalculator.from_speed_and_remaining(
        ...     1000, 5000
        ... )
        5
        >>> ETACalculator.from_speed_and_remaining(
        ...     None, 5000
        ... )
        None
        """
        if not speed_bytes_per_sec or speed_bytes_per_sec <= 0:
            return None
        if not remaining_bytes or remaining_bytes <= 0:
            return None
        return int(remaining_bytes / speed_bytes_per_sec)
