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

"""Models and value objects for PVR import service."""

from dataclasses import dataclass
from enum import StrEnum


class FileType(StrEnum):
    """Types of tracked book files."""

    MAIN = "main"
    FORMAT = "format"
    ARTIFACT = "artifact"


class MatchScoreThresholds:
    """Thresholds for book matching scores."""

    STRONG_MATCH = 0.7
    WEAK_MATCH = 0.4


DEFAULT_FORMAT_PREFERENCE = ["epub", "mobi", "azw3", "pdf", "cbz", "cbr"]


@dataclass(frozen=True)
class BookMetadata:
    """Immutable value object for book metadata."""

    title: str
    author: str

    @property
    def normalized_title(self) -> str:
        """Return normalized title for comparison."""
        return self.title.lower().strip()

    @property
    def normalized_author(self) -> str:
        """Return normalized author for comparison."""
        return self.author.lower().strip()


@dataclass
class MatchScore:
    """Value object for match score."""

    value: float

    def is_strong_match(self) -> bool:
        """Check if match is strong."""
        return self.value > MatchScoreThresholds.STRONG_MATCH

    def is_acceptable_match(self) -> bool:
        """Check if match is acceptable."""
        return self.value > MatchScoreThresholds.WEAK_MATCH
