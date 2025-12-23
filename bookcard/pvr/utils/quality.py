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

"""Quality inference utilities for PVR indexers.

This module provides utilities for inferring book quality/format from titles,
following DRY principles by centralizing duplicate logic.
"""

# Quality patterns mapping quality names to search patterns
QUALITY_PATTERNS: dict[str, list[str]] = {
    "epub": ["epub"],
    "pdf": ["pdf"],
    "mobi": ["mobi"],
    "azw": ["azw", "kindle"],
}


def infer_quality_from_title(title: str) -> str | None:
    """Infer quality/format from title.

    Parameters
    ----------
    title : str
        Item title to analyze.

    Returns
    -------
    str | None
        Inferred quality (e.g., 'epub', 'pdf', 'mobi', 'azw') or None if not found.

    Examples
    --------
    >>> infer_quality_from_title(
    ...     "Book Title - EPUB"
    ... )
    'epub'
    >>> infer_quality_from_title(
    ...     "Book Title - Kindle Edition"
    ... )
    'azw'
    >>> infer_quality_from_title(
    ...     "Book Title"
    ... )
    None
    """
    title_lower = title.lower()
    for quality, patterns in QUALITY_PATTERNS.items():
        if any(pattern in title_lower for pattern in patterns):
            return quality
    return None
