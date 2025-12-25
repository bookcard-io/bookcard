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

"""Utility functions for indexer search operations.

Provides helper functions to reduce code duplication and improve maintainability.
"""

from collections.abc import Callable
from datetime import UTC, datetime


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC-aware.

    Parameters
    ----------
    dt : datetime | None
        Datetime to ensure is UTC-aware.

    Returns
    -------
    datetime | None
        UTC-aware datetime, or None if input was None.
    """
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def normalize_text(text: str | None) -> str:
    """Normalize text for comparison.

    Parameters
    ----------
    text : str | None
        Text to normalize.

    Returns
    -------
    str
        Lowercased and stripped text, or empty string if None.
    """
    return (text or "").lower().strip()


def check_threshold(
    value: int | None,
    threshold: int | None,
    comparison: Callable[[int, int], bool],
) -> bool:
    """Check if value meets threshold criteria.

    Parameters
    ----------
    value : int | None
        Value to check.
    threshold : int | None
        Threshold value. If None, always returns True.
    comparison : callable[[int, int], bool]
        Comparison function (e.g., lambda v, t: v >= t).

    Returns
    -------
    bool
        True if threshold is None or value meets threshold, False otherwise.
    """
    if threshold is None:
        return True
    return value is not None and comparison(value, threshold)
