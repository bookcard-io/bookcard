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

"""File selection strategies for PVR import."""

from abc import ABC, abstractmethod
from pathlib import Path


class FileSelectionStrategy(ABC):
    """Strategy for selecting the best file from a group."""

    @abstractmethod
    def select_best_file(self, files: list[Path]) -> Path | None:
        """Select the best file from the list."""


class PreferenceBasedSelector(FileSelectionStrategy):
    """Selects best file based on format preferences and size."""

    def __init__(self, preferred_formats: list[str]) -> None:
        """Initialize selector."""
        self.preferred_formats = [f.lower() for f in preferred_formats]

    def select_best_file(self, files: list[Path]) -> Path | None:
        """Select best file from list based on preferences."""
        if not files:
            return None

        def sort_key(path: Path) -> tuple[int, int]:
            ext = path.suffix.lstrip(".").lower()
            try:
                priority = self.preferred_formats.index(ext)
            except ValueError:
                priority = 999
            # Secondary sort by file size (largest first)
            size = -path.stat().st_size
            return priority, size

        sorted_files = sorted(files, key=sort_key)
        return sorted_files[0] if sorted_files else None
