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

"""Archive handlers for comic formats."""

from bookcard.services.comic.archive.handlers.base import ArchiveHandler
from bookcard.services.comic.archive.handlers.cb7 import CB7Handler
from bookcard.services.comic.archive.handlers.cbc import CBCHandler
from bookcard.services.comic.archive.handlers.cbr import CBRHandler
from bookcard.services.comic.archive.handlers.cbz import CBZHandler

__all__ = [
    "ArchiveHandler",
    "CB7Handler",
    "CBCHandler",
    "CBRHandler",
    "CBZHandler",
]
