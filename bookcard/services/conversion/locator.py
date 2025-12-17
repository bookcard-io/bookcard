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

"""Converter locator for discovering converter executables.

Handles discovery and validation of converter executables,
following SRP by focusing solely on converter location.
"""

import shutil
from pathlib import Path


class ConverterLocator:
    """Locates and validates converter executables.

    Discovers Calibre ebook-convert binary by checking Docker
    installation path and system PATH.

    Methods
    -------
    find_converter() -> Path | None
        Find the converter executable.
    """

    def find_converter(self) -> Path | None:
        """Get path to Calibre ebook-convert binary.

        Checks Docker installation path first, then falls back
        to PATH lookup.

        Returns
        -------
        Path | None
            Path to converter if found, None otherwise.
        """
        # First check Docker installation path
        docker_path = Path("/app/calibre/ebook-convert")
        if docker_path.exists():
            return docker_path

        # Fallback to PATH lookup
        converter = shutil.which("ebook-convert")
        if converter:
            return Path(converter)

        return None
