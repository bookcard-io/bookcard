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

"""Domain-specific exceptions for author operations.

Provides clear exception hierarchy for better error handling.
"""


class AuthorServiceError(Exception):
    """Base exception for author service errors."""


class AuthorNotFoundError(AuthorServiceError):
    """Raised when author cannot be found."""


class NoActiveLibraryError(AuthorServiceError):
    """Raised when no active library is configured."""


class InvalidPhotoFormatError(AuthorServiceError):
    """Raised when photo format is invalid."""


class PhotoNotFoundError(AuthorServiceError):
    """Raised when photo cannot be found."""


class PhotoStorageError(AuthorServiceError):
    """Raised when photo storage operations fail."""


class AuthorMetadataFetchError(AuthorServiceError):
    """Raised when author metadata fetch fails."""
