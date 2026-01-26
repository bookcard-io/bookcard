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

"""Exceptions for the library scan task domain."""

from __future__ import annotations


class LibraryScanError(RuntimeError):
    """Base exception for library scan failures."""


class RedisUnavailableError(LibraryScanError):
    """Raised when a scan requires a message broker but none is available."""


class LibraryNotFoundError(LibraryScanError):
    """Raised when a requested library cannot be found."""


class ScanDispatchError(LibraryScanError):
    """Raised when a scan job cannot be dispatched to the broker."""


class ScanFailedError(LibraryScanError):
    """Raised when the scan state is marked as failed."""


class ScanStateUnavailableError(LibraryScanError):
    """Raised when scan state cannot be retrieved within retry limits."""
