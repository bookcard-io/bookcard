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

"""Filename utilities for Calibre library operations.

Shared utilities for filename sanitization and path calculation.
Follows DRY principle by centralizing common logic.
"""


def sanitize_filename(name: str, max_length: int = 96) -> str:
    """Sanitize filename by removing invalid characters.

    Parameters
    ----------
    name : str
        Name to sanitize.
    max_length : int
        Maximum length for filename (default: 96).

    Returns
    -------
    str
        Sanitized filename.
    """
    invalid_chars = '<>:"/\\|?*'
    sanitized = "".join(c if c not in invalid_chars else "_" for c in name)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized.strip() or "Unknown"


def calculate_book_path(author_name: str | None, title: str | None) -> str | None:
    """Calculate book path from author name and title.

    Parameters
    ----------
    author_name : str | None
        Author name. If None, uses 'Unknown'.
    title : str | None
        Book title. If None, returns None.

    Returns
    -------
    str | None
        Book path string (Author/Title format) or None if title is missing.
    """
    if not title:
        return None

    author_name = author_name or "Unknown"
    author_dir = sanitize_filename(author_name)
    title_dir = sanitize_filename(title)
    return f"{author_dir}/{title_dir}".replace("\\", "/")
