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

"""Conversion utility functions.

Provides shared utilities for book format conversion operations, following DRY
by centralizing common conversion functionality across services.
"""

from __future__ import annotations

from typing import NoReturn


def raise_conversion_error(message: str) -> NoReturn:
    """Raise a conversion error.

    Centralized function for raising conversion errors to follow DRY
    and satisfy linter requirements for abstracting raise statements.

    Conversion errors are runtime failures during the conversion process
    (e.g., Calibre command failures, file system issues, timeouts), not
    invalid input values.

    Parameters
    ----------
    message : str
        Error message describing the conversion failure.

    Raises
    ------
    RuntimeError
        Always raises with the provided error message.
    """
    raise RuntimeError(message) from None
