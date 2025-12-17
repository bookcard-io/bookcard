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

"""Duplicate detection for books during upload/ingest.

Uses Strategy pattern for pluggable detection algorithms.
"""

from bookcard.services.duplicate_detection.book_duplicate_handler import (
    BookDuplicateHandler,
)
from bookcard.services.duplicate_detection.strategies import (
    FilenameDuplicateStrategy,
    FullFileHashDuplicateStrategy,
    TitleAuthorLevenshteinDuplicateStrategy,
)

__all__ = [
    "BookDuplicateHandler",
    "FilenameDuplicateStrategy",
    "FullFileHashDuplicateStrategy",
    "TitleAuthorLevenshteinDuplicateStrategy",
]
