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

"""Filesystem utilities."""

import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

# Characters that are invalid in filenames on various filesystems
INVALID_CHARS = re.compile(r'[\\:*?"<>|]')


def _sanitize(name: str, max_length: int = 245) -> str:
    """Sanitize a string for filesystem use.

    Follows patterns from Shelfmark project.
    """
    if not name:
        return ""

    sanitized = INVALID_CHARS.sub("_", name)
    sanitized = re.sub(r"^[\s.]+|[\s.]+$", "", sanitized)  # Strip whitespace and dots
    sanitized = re.sub(r"_+", "_", sanitized)  # Collapse underscores
    return sanitized[:max_length]


def sanitize_filename(name: str, max_length: int = 245) -> str:
    """Sanitize a string for use as a filename or path component."""
    return _sanitize(name, max_length)


@contextmanager
def atomic_file_stream(dest_path: Path) -> Generator[IO[bytes], None, None]:
    """Context manager for atomic file writing using a temporary file.

    Writes to a temporary .part file and renames it to dest_path on success.
    """
    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    try:
        with temp_path.open("wb") as f:
            yield f

        # Atomic rename
        temp_path.replace(dest_path)
    except Exception:
        # Cleanup on error
        if temp_path.exists():
            temp_path.unlink()
        raise
