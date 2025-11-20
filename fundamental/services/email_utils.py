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

"""Email utility functions.

Provides shared utilities for email-related operations, following DRY
by centralizing common email functionality across services.
"""

from __future__ import annotations

import re
import unicodedata


def build_attachment_filename(
    author: str | None,
    title: str | None,
    extension: str | None,
) -> str:
    """Build a sanitized attachment filename.

    Parameters
    ----------
    author : str | None
        Author name to use in the filename.
    title : str | None
        Book title to use in the filename.
    extension : str | None
        File extension (e.g., 'epub', 'mobi') without leading dot.

    Returns
    -------
    str
        Sanitized attachment filename.
    """
    default_base = "Unknown Author - Unknown Book"

    author_part = (author or "").strip()
    title_part = (title or "").strip()

    if author_part and title_part:
        base = f"{author_part} - {title_part}"
    elif title_part:
        base = title_part
    elif author_part:
        base = f"{author_part} - Unknown Book"
    else:
        base = default_base

    # Normalize unicode characters
    normalized = unicodedata.normalize("NFKD", base)

    # Allow alphanumerics and a safe subset of punctuation
    allowed_chars = {" ", "-", "_", ".", "(", ")", "&", ",", "'", "+"}
    sanitized = "".join(c for c in normalized if c.isalnum() or c in allowed_chars)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")

    if not sanitized:
        sanitized = default_base

    # Limit base length to keep filenames manageable
    max_len = 150
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len].rstrip()

    ext = (extension or "").strip().lstrip(".")
    if ext:
        return f"{sanitized}.{ext.lower()}"

    return sanitized
