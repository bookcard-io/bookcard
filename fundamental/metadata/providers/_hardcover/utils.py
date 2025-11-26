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

"""Utility functions for Hardcover provider."""


def safe_string(value: object) -> str | None:
    """Convert value to string if truthy, else None.

    Parameters
    ----------
    value : Any
        Value to convert.

    Returns
    -------
    str | None
        String representation or None if falsy.
    """
    return str(value) if value else None


def get_first_edition(book_data: dict) -> dict | None:
    """Safely get the first edition from book data.

    Parameters
    ----------
    book_data : dict
        Book data dictionary.

    Returns
    -------
    dict | None
        First edition dictionary or None if not available.
    """
    editions = book_data.get("editions", [])
    if isinstance(editions, list) and editions:
        return editions[0]
    return None


# Common exception types for parsing
PARSE_EXCEPTIONS = (KeyError, ValueError, TypeError, AttributeError)
