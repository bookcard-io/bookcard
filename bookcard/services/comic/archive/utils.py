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

"""Utility helpers for comic archive handling."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from bookcard.services.comic.archive.exceptions import InvalidArchiveEntryNameError

IMAGE_EXTENSIONS: tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
)


def natural_sort_key(filename: str) -> tuple[int | str, ...]:
    """Generate a sort key for natural sorting of filenames.

    Parameters
    ----------
    filename : str
        Filename to generate sort key for.

    Returns
    -------
    tuple[int | str, ...]
        Sort key tuple.
    """
    parts: list[int | str] = []
    for part in re.split(r"(\d+)", filename):
        if part.isdigit():
            parts.append(int(part))
        else:
            parts.append(part.lower())
    return tuple(parts)


def is_image_entry(name: str) -> bool:
    """Return True if a filename looks like an image entry."""
    lower = name.lower()
    return lower.endswith(IMAGE_EXTENSIONS) and not lower.endswith("/")


def validate_archive_entry_name(name: str) -> None:
    """Validate an archive entry name for safety.

    Parameters
    ----------
    name : str
        Entry name inside the archive.

    Raises
    ------
    InvalidArchiveEntryNameError
        If the entry name is unsafe (absolute path, traversal, etc.).
    """
    if not name:
        msg = "Empty archive entry name"
        raise InvalidArchiveEntryNameError(msg)

    # Normalize to forward slashes (archives often use '/')
    normalized = name.replace("\\", "/")
    p = PurePosixPath(normalized)

    if p.is_absolute():
        msg = f"Absolute archive entry name: {name!r}"
        raise InvalidArchiveEntryNameError(msg)

    if any(part == ".." for part in p.parts):
        msg = f"Path traversal in archive entry: {name!r}"
        raise InvalidArchiveEntryNameError(msg)
