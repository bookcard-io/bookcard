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

"""Exceptions for email send task.

Re-exports task exceptions for convenience.
"""

from bookcard.services.tasks.exceptions import (
    BookNotFoundError,
    EmailServerNotConfiguredError,
    LibraryNotConfiguredError,
    TaskCancelledError,
    TaskError,
)

__all__ = [
    "BookNotFoundError",
    "EmailServerNotConfiguredError",
    "LibraryNotConfiguredError",
    "TaskCancelledError",
    "TaskError",
]
