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

"""Codecs for decoding user setting values.

This module centralizes decoding logic for settings stored in `UserSetting.value`.
It prevents duplicated parsing behavior across services and tasks.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def decode_string_list(
    value: str,
    *,
    allow_csv_fallback: bool = True,
) -> list[str]:
    """Decode a setting value into a list of strings.

    Supports JSON array storage (recommended) and (optionally) a comma-separated
    fallback for backward compatibility.

    Parameters
    ----------
    value : str
        Raw setting value.
    allow_csv_fallback : bool, default=True
        Whether to fall back to comma-separated parsing if JSON decoding fails.

    Returns
    -------
    list[str]
        Decoded list of strings. Returns an empty list if no valid values exist.
    """
    try:
        decoded = json.loads(value)
        if isinstance(decoded, list):
            return [v for v in decoded if isinstance(v, str)]
    except (json.JSONDecodeError, TypeError):
        if allow_csv_fallback:
            return [part.strip() for part in value.split(",") if part.strip()]
        return []
    else:
        return []


def normalize_string_list(
    values: list[str],
    *,
    normalizer: Callable[[str], str] = lambda s: s,
    dedupe: bool = True,
) -> list[str]:
    """Normalize a list of strings.

    Parameters
    ----------
    values : list[str]
        Input string list.
    normalizer : Callable[[str], str], default=identity
        Normalization function to apply to each value (e.g., `str.upper`).
    dedupe : bool, default=True
        Whether to de-duplicate values while preserving order.

    Returns
    -------
    list[str]
        Normalized list.
    """
    normalized = [normalizer(v.strip()) for v in values if v.strip()]
    if not dedupe:
        return normalized
    seen: set[str] = set()
    result: list[str] = []
    for v in normalized:
        if v in seen:
            continue
        seen.add(v)
        result.append(v)
    return result
