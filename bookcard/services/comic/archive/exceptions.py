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

"""Domain exceptions for comic archive operations."""


class ComicArchiveError(Exception):
    """Base exception for comic archive operations."""


class UnsupportedFormatError(ComicArchiveError):
    """Raised when an archive format is not supported."""


class PageNotFoundError(ComicArchiveError):
    """Raised when a requested page does not exist."""


class InvalidArchiveEntryNameError(ComicArchiveError):
    """Raised when an archive entry name is unsafe or invalid."""


class ArchiveReadError(ComicArchiveError):
    """Raised when the archive cannot be read for a non-corruption reason."""


class ArchiveCorruptedError(ComicArchiveError):
    """Raised when the archive appears corrupted or invalid."""


class ImageProcessingError(ComicArchiveError):
    """Raised when image processing (e.g., reading dimensions) fails."""
